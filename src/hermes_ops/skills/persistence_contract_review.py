from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from hermes_ops.skills.controlled_reader import SourceDocument, read_source_documents
from hermes_ops.skills.persistence_contract_models import (
    IdentityBindingFact,
    MutationIntentFact,
    PersistenceContractClassification as Classification,
    PersistenceContractFinding,
    PersistenceContractFindingKind as FindingKind,
    PersistenceContractReachability as Reachability,
    PersistenceContractReport,
    PersistenceContractReviewRequest,
    PersistenceMutationReviewRequest,
    PersistenceContractSeverity as Severity,
    ReadRequirementFact,
    StateTransitionIntentFact,
    WriteIntentFact,
)
from hermes_ops.skills.source_evidence import source_locator
from hermes_ops.skills.structural_ast import terminal_symbol


_NAME = r"[A-Za-z_][A-Za-z0-9_]*"
_INSERT = re.compile(rf"INSERT\s+INTO\s+({_NAME})\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)\Z", re.I)
_SELECT = re.compile(rf"SELECT\s+({_NAME}(?:\s*,\s*{_NAME})*|\*)\s+FROM\s+({_NAME})\s+WHERE\s+({_NAME})\s*=\s*\?\Z", re.I)
_UPDATE = re.compile(rf"UPDATE\s+({_NAME})\s+SET\s+(.+)\s+WHERE\s+({_NAME})\s*=\s*\?\Z", re.I)
_ASSIGNMENT = re.compile(rf"({_NAME})\s*=\s*(\?|[-+]?\d+(?:\.\d+)?|'[^']*'|\"[^\"]*\")\Z", re.I)
_MUTATION_UPDATE = re.compile(
    rf"UPDATE\s+({_NAME})\s+SET\s+(.+?)\s+WHERE\s+({_NAME})\s*=\s*\?"
    rf"(?:\s+AND\s+(.+))?\Z",
    re.I,
)
_DYNAMIC_SQL_MARKER = "__HERMES_DYNAMIC_SQL_VALUE__"


def _ref(document: SourceDocument, node: ast.AST) -> str:
    return source_locator(document.path, node)


def _name(node: ast.AST) -> str | None:
    return node.id if isinstance(node, ast.Name) else None


def _display(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Constant):
        return repr(node.value)
    return "<unsupported>"


def _call_name(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    return terminal_symbol(node.func)


def _resolved(node: ast.AST, environment: dict[str, ast.AST]) -> ast.AST:
    seen: set[str] = set()
    while isinstance(node, ast.Name) and node.id in environment and node.id not in seen:
        seen.add(node.id)
        node = environment[node.id]
    return node


def _canonical_origin(node: ast.AST, environment: dict[str, ast.AST]) -> str:
    node = _resolved(node, environment)
    try:
        return ast.unparse(node)
    except (ValueError, TypeError):
        return "<unsupported>"


def _sql_text(node: ast.AST, environment: dict[str, ast.AST]) -> tuple[str | None, bool]:
    node = _resolved(node, environment)
    if isinstance(node, ast.Constant) and type(node.value) is str:
        return node.value, False
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        dynamic = False
        for value in node.values:
            if isinstance(value, ast.Constant) and type(value.value) is str:
                parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                parts.append(_DYNAMIC_SQL_MARKER)
                dynamic = True
            else:
                return None, True
        return "".join(parts), dynamic
    return None, True


def _mutation_from_execute(
    operation_symbol: str,
    document: SourceDocument,
    node: ast.Call,
    environment: dict[str, ast.AST],
    call_path: tuple[str, ...],
    references: tuple[str, ...],
) -> tuple[MutationIntentFact | None, str | None]:
    if not node.args:
        return None, "DYNAMIC_SQL_UNSUPPORTED"
    raw_sql, has_dynamic = _sql_text(node.args[0], environment)
    if raw_sql is None:
        return None, "DYNAMIC_SQL_UNSUPPORTED"
    sql = " ".join(raw_sql.split())
    if ";" in sql or re.search(r"\b(?:JOIN|OR|RETURNING|WITH|SELECT)\b", sql, re.I):
        return None, "SQL_SHAPE_UNSUPPORTED"
    match = _MUTATION_UPDATE.fullmatch(sql)
    if match is None:
        return None, "SQL_SHAPE_UNSUPPORTED"
    structural = " ".join(match.group(index) or "" for index in (1, 2, 3))
    if _DYNAMIC_SQL_MARKER in structural:
        return None, "DYNAMIC_SQL_UNSUPPORTED"
    suffix = match.group(4) or ""
    if has_dynamic and _DYNAMIC_SQL_MARKER not in suffix:
        return None, "DYNAMIC_SQL_UNSUPPORTED"
    assignment_matches = tuple(
        _ASSIGNMENT.fullmatch(item.strip()) for item in match.group(2).split(",")
    )
    if not assignment_matches or any(item is None for item in assignment_matches):
        return None, "SQL_SHAPE_UNSUPPORTED"
    params_node = _resolved(node.args[1], environment) if len(node.args) > 1 else None
    params = tuple(params_node.elts) if isinstance(params_node, (ast.Tuple, ast.List)) else ()
    parameter_index = 0
    assignments: list[tuple[str, str]] = []
    literal_columns: list[str] = []
    for assignment in assignment_matches:
        assert assignment is not None
        expression = assignment.group(2)
        if expression == "?":
            if parameter_index >= len(params):
                return None, "SQL_BINDING_MISMATCH"
            value = _canonical_origin(params[parameter_index], environment)
            parameter_index += 1
        else:
            value = expression.strip("'\"")
            literal_columns.append(assignment.group(1))
        assignments.append((assignment.group(1), value))
    if parameter_index >= len(params):
        return None, "SQL_BINDING_MISMATCH"
    predicate_origin = _canonical_origin(params[parameter_index], environment)
    sql_reference = _ref(document, node)
    return MutationIntentFact(
        operation_symbol,
        match.group(1),
        tuple(sorted(assignments)),
        match.group(3),
        predicate_origin,
        call_path,
        tuple(dict.fromkeys((*references, sql_reference))),
        tuple(sorted(literal_columns)),
    ), None


def _params(call: ast.Call) -> tuple[ast.AST, ...] | None:
    if len(call.args) < 2:
        return ()
    value = call.args[1]
    if isinstance(value, (ast.Tuple, ast.List)):
        return tuple(value.elts)
    return None


@dataclass
class _FunctionFacts:
    writes: list[WriteIntentFact]
    identities: list[IdentityBindingFact]
    reads: list[ReadRequirementFact]
    states: list[StateTransitionIntentFact]
    returned: set[str]
    limitations: set[str]


def _facts(document: SourceDocument, function: ast.FunctionDef | ast.AsyncFunctionDef) -> _FunctionFacts:
    result = _FunctionFacts([], [], [], [], set(), set())
    cursors: dict[str, WriteIntentFact] = {}
    row_symbols: set[str] = set()
    guarded_rows: set[str] = set()
    for node in ast.walk(function):
        if isinstance(node, ast.If) and isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not):
            symbol = _name(node.test.operand)
            if symbol and any(isinstance(item, ast.Return) and isinstance(item.value, ast.Constant) and item.value.value is False for item in node.body):
                guarded_rows.add(symbol)
        if isinstance(node, ast.Return) and node.value is not None:
            result.returned.update(
                item.id for item in ast.walk(node.value) if isinstance(item, ast.Name)
            )
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = _name(node.targets[0])
            value = node.value
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            target = "<discarded>"
            value = node.value
        else:
            continue
        if target is None:
            continue
        if isinstance(value, ast.Attribute) and value.attr == "lastrowid":
            cursor = _name(value.value)
            write = cursors.get(cursor or "")
            if write is not None:
                result.identities.append(IdentityBindingFact(cursor or "", target, "lastrowid", write.table, _ref(document, node)))
            else:
                result.limitations.add("IDENTITY_CURSOR_ORIGIN_UNKNOWN")
            continue
        fetch_kind = ""
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute) and value.func.attr == "fetchone":
            fetch_kind = "fetchone"
            value = value.func.value
            row_symbols.add(target)
        if not isinstance(value, ast.Call) or _call_name(value) != "execute" or not value.args:
            continue
        sql_node = value.args[0]
        if not isinstance(sql_node, ast.Constant) or type(sql_node.value) is not str:
            result.limitations.add("DYNAMIC_SQL_UNSUPPORTED")
            continue
        sql = " ".join(sql_node.value.split())
        upper = sql.upper()
        params = _params(value)
        if params is None:
            result.limitations.add("SQL_BINDING_UNSUPPORTED")
            continue
        match = _INSERT.fullmatch(sql)
        if match:
            columns = tuple(part.strip() for part in match.group(2).split(","))
            values = tuple(part.strip() for part in match.group(3).split(","))
            if any(re.fullmatch(_NAME, item) is None for item in columns) or values.count("?") != len(params):
                result.limitations.add("SQL_BINDING_MISMATCH")
                continue
            fact = WriteIntentFact(match.group(1), columns, tuple(_display(item) for item in params), target, _ref(document, node))
            result.writes.append(fact)
            cursors[target] = fact
            continue
        match = _SELECT.fullmatch(sql)
        if match and fetch_kind:
            if len(params) != 1:
                result.limitations.add("SQL_BINDING_MISMATCH")
                continue
            result.reads.append(ReadRequirementFact(match.group(2), tuple(part.strip() for part in match.group(1).split(",")), match.group(3), _display(params[0]), fetch_kind, target in guarded_rows, _ref(document, node)))
            continue
        match = _UPDATE.fullmatch(sql)
        if match:
            assignments = tuple(
                _ASSIGNMENT.fullmatch(item.strip())
                for item in match.group(2).split(",")
            )
            if any(item is None for item in assignments):
                result.limitations.add("SQL_SHAPE_UNSUPPORTED")
                continue
            placeholder_count = sum(item.group(2) == "?" for item in assignments if item) + 1
            if len(params) != placeholder_count:
                result.limitations.add("SQL_BINDING_MISMATCH")
                continue
            parameter_index = 0
            key_arg = params[-1]
            for assignment in assignments:
                assert assignment is not None
                expression = assignment.group(2)
                if expression == "?":
                    raw_value = _display(params[parameter_index])
                    parameter_index += 1
                else:
                    raw_value = expression.strip("'\"")
                result.states.append(StateTransitionIntentFact(match.group(1), assignment.group(1), raw_value, match.group(3), _display(key_arg), _ref(document, node)))
            continue
        if upper.startswith(("INSERT ", "SELECT ", "UPDATE ")):
            result.limitations.add("SQL_SHAPE_UNSUPPORTED")
    return result


def _definitions(documents: tuple[SourceDocument, ...]) -> tuple[dict[str, tuple[SourceDocument, ast.FunctionDef | ast.AsyncFunctionDef]], set[str]]:
    values: dict[str, tuple[SourceDocument, ast.FunctionDef | ast.AsyncFunctionDef]] = {}
    duplicates: set[str] = set()
    for document in sorted(documents, key=lambda item: item.path):
        try:
            tree = ast.parse(document.text, filename=document.path)
        except (SyntaxError, ValueError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in values:
                    duplicates.add(node.name)
                else:
                    values[node.name] = (document, node)
    return values, duplicates


def _local_path(definitions: dict[str, tuple[SourceDocument, ast.FunctionDef | ast.AsyncFunctionDef]], request: PersistenceContractReviewRequest) -> tuple[tuple[str, ...], tuple[str, ...]]:
    for name in sorted(definitions):
        if name in {request.producer_symbol, request.consumer_symbol}:
            continue
        document, function = definitions[name]
        origins: dict[str, str] = {}
        producer_ref = consumer_ref = None
        for statement in function.body:
            if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.value, ast.Call) and _call_name(statement.value) == request.producer_symbol:
                symbol = _name(statement.targets[0])
                if symbol:
                    origins[symbol] = request.producer_symbol
                    producer_ref = _ref(document, statement)
            call = statement.value if isinstance(statement, (ast.Expr, ast.Return)) else None
            if isinstance(call, ast.Call) and _call_name(call) == request.consumer_symbol and any(_name(arg) in origins for arg in call.args):
                consumer_ref = _ref(document, statement)
        if producer_ref and consumer_ref:
            return (request.producer_symbol, name, request.consumer_symbol), (producer_ref, consumer_ref)
    return (), ()


@dataclass
class _MutationCollection:
    intents: list[MutationIntentFact]
    limitations: set[str]


def _guard_name(test: ast.AST, expected: str) -> bool:
    return any(
        isinstance(item, ast.Call) and _call_name(item) == expected
        for item in ast.walk(test)
    )


def _bind_call(
    call: ast.Call,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    environment: dict[str, ast.AST],
) -> dict[str, ast.AST] | None:
    parameters = [item.arg for item in function.args.args]
    if parameters and parameters[0] in {"self", "cls"}:
        parameters = parameters[1:]
    if len(call.args) > len(parameters):
        return None
    bound = {
        name: _resolved(value, environment)
        for name, value in zip(parameters, call.args)
    }
    for keyword in call.keywords:
        if keyword.arg is None or keyword.arg not in parameters or keyword.arg in bound:
            return None
        bound[keyword.arg] = _resolved(keyword.value, environment)
    defaults = list(function.args.defaults)
    default_start = len(parameters) - len(defaults)
    for index, name in enumerate(parameters):
        if name not in bound and index >= default_start:
            bound[name] = defaults[index - default_start]
    return bound


def _may_reach_execute(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    definitions: dict[str, tuple[SourceDocument, ast.FunctionDef | ast.AsyncFunctionDef]],
    seen: frozenset[str] = frozenset(),
) -> bool:
    """Return whether a helper has a structural route to a DB-API execute call."""
    for item in ast.walk(function):
        if not isinstance(item, ast.Call):
            continue
        name = _call_name(item)
        if name == "execute":
            return True
        if name is None or name in seen:
            continue
        target = definitions.get(name)
        if target is not None and _may_reach_execute(
            target[1], definitions, seen | {name},
        ):
            return True
    return False


def _collect_expression_calls(
    expression: ast.AST,
    *,
    operation_symbol: str,
    document: SourceDocument,
    definitions: dict[str, tuple[SourceDocument, ast.FunctionDef | ast.AsyncFunctionDef]],
    duplicates: set[str],
    environment: dict[str, ast.AST],
    call_path: tuple[str, ...],
    references: tuple[str, ...],
    stack: frozenset[str],
    collection: _MutationCollection,
) -> None:
    calls = [item for item in ast.walk(expression) if isinstance(item, ast.Call)]
    for call in calls:
        name = _call_name(call)
        if name == "execute":
            sql, _ = _sql_text(call.args[0], environment) if call.args else (None, True)
            if sql is not None and not " ".join(sql.split()).upper().startswith("UPDATE "):
                continue
            intent, limitation = _mutation_from_execute(
                operation_symbol, document, call, environment, call_path,
                references,
            )
            if intent is not None:
                collection.intents.append(intent)
            elif limitation is not None:
                collection.limitations.add(limitation)
            continue
        if name is None or name in stack:
            continue
        if name in duplicates:
            collection.limitations.add("MUTATION_CALLEE_NOT_UNIQUE")
            continue
        target = definitions.get(name)
        if target is None:
            continue
        target_document, target_function = target
        bound = _bind_call(call, target_function, environment)
        if bound is None:
            if _may_reach_execute(target_function, definitions, frozenset({name})):
                collection.limitations.add("MUTATION_FORWARDING_UNSUPPORTED")
            continue
        edge = _ref(document, call)
        _collect_statements(
            target_function.body,
            operation_symbol=operation_symbol,
            document=target_document,
            definitions=definitions,
            duplicates=duplicates,
            environment=bound,
            call_path=(*call_path, name),
            references=tuple(dict.fromkeys((*references, edge))),
            stack=stack | {name},
            collection=collection,
        )


def _collect_statements(
    statements: list[ast.stmt],
    *,
    operation_symbol: str,
    document: SourceDocument,
    definitions: dict[str, tuple[SourceDocument, ast.FunctionDef | ast.AsyncFunctionDef]],
    duplicates: set[str],
    environment: dict[str, ast.AST],
    call_path: tuple[str, ...],
    references: tuple[str, ...],
    stack: frozenset[str],
    collection: _MutationCollection,
) -> None:
    local = dict(environment)
    for statement in statements:
        values: list[ast.AST] = []
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            value = statement.value
            if value is not None:
                values.append(value)
                target = (
                    statement.targets[0]
                    if isinstance(statement, ast.Assign) and len(statement.targets) == 1
                    else statement.target if isinstance(statement, ast.AnnAssign) else None
                )
                if isinstance(target, ast.Name):
                    local[target.id] = _resolved(value, local)
        elif isinstance(statement, (ast.Expr, ast.Return)) and statement.value is not None:
            values.append(statement.value)
        elif isinstance(statement, ast.If):
            values.append(statement.test)
            for branch in (statement.body, statement.orelse):
                _collect_statements(
                    branch,
                    operation_symbol=operation_symbol, document=document,
                    definitions=definitions, duplicates=duplicates,
                    environment=dict(local), call_path=call_path,
                    references=references, stack=stack, collection=collection,
                )
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            _collect_statements(
                statement.body,
                operation_symbol=operation_symbol, document=document,
                definitions=definitions, duplicates=duplicates,
                environment=dict(local), call_path=call_path,
                references=references, stack=stack, collection=collection,
            )
        elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
            for branch in (statement.body, statement.orelse):
                _collect_statements(
                    branch,
                    operation_symbol=operation_symbol, document=document,
                    definitions=definitions, duplicates=duplicates,
                    environment=dict(local), call_path=call_path,
                    references=references, stack=stack, collection=collection,
                )
        elif isinstance(statement, ast.Try):
            branches = [statement.body, statement.orelse, statement.finalbody]
            branches.extend(handler.body for handler in statement.handlers)
            for branch in branches:
                _collect_statements(
                    branch,
                    operation_symbol=operation_symbol, document=document,
                    definitions=definitions, duplicates=duplicates,
                    environment=dict(local), call_path=call_path,
                    references=references, stack=stack, collection=collection,
                )
        for value in values:
            _collect_expression_calls(
                value,
                operation_symbol=operation_symbol, document=document,
                definitions=definitions, duplicates=duplicates,
                environment=local, call_path=call_path, references=references,
                stack=stack, collection=collection,
            )


def _deduplicate_mutations(intents: list[MutationIntentFact]) -> tuple[MutationIntentFact, ...]:
    grouped: dict[tuple[Any, ...], MutationIntentFact] = {}
    for intent in intents:
        key = (
            intent.table, intent.assignments, intent.predicate_column,
            intent.predicate_value_origin, intent.call_path,
            intent.literal_assignment_columns,
        )
        previous = grouped.get(key)
        if previous is None:
            grouped[key] = intent
        else:
            grouped[key] = MutationIntentFact(
                intent.operation_symbol, intent.table, intent.assignments,
                intent.predicate_column, intent.predicate_value_origin,
                intent.call_path,
                tuple(sorted(set((*previous.evidence_references, *intent.evidence_references)))),
                intent.literal_assignment_columns,
            )
    return tuple(grouped[key] for key in sorted(grouped, key=repr))


def _mutation_finding(
    kind: FindingKind,
    request: PersistenceMutationReviewRequest,
    intent: MutationIntentFact,
    summary: str,
) -> PersistenceContractFinding:
    severity = Severity.LOW if kind is FindingKind.MUTATION_STATE_MISMATCH else Severity.MEDIUM
    return PersistenceContractFinding(
        kind, summary, severity, intent.evidence_references,
        request.target_table, request.identity_column,
        intent.table, intent.predicate_column,
    )


def _compare_mutation(
    request: PersistenceMutationReviewRequest,
    intent: MutationIntentFact,
) -> tuple[PersistenceContractFinding | None, str | None]:
    if intent.table != request.target_table:
        return _mutation_finding(
            FindingKind.MUTATION_TARGET_TABLE_MISMATCH, request, intent,
            f"Observed mutation table {intent.table!r} differs from target {request.target_table!r}.",
        ), None
    if intent.predicate_column != request.identity_column:
        return _mutation_finding(
            FindingKind.MUTATION_TARGET_KEY_MISMATCH, request, intent,
            f"Observed mutation key {intent.predicate_column!r} differs from target identity key {request.identity_column!r}.",
        ), None
    if request.expected_state_column is None:
        return None, None
    assignments = dict(intent.assignments)
    if request.expected_state_column not in assignments:
        return None, "EXPECTED_MUTATION_STATE_UNRESOLVED"
    if request.expected_state_column not in intent.literal_assignment_columns:
        return None, "EXPECTED_MUTATION_STATE_NOT_LITERAL"
    actual = assignments[request.expected_state_column]
    if actual != request.expected_state_value:
        return _mutation_finding(
            FindingKind.MUTATION_STATE_MISMATCH, request, intent,
            f"Observed mutation state {actual!r} differs from expected state {request.expected_state_value!r}.",
        ), None
    return None, None


def review_persistence_mutation_documents(
    documents: tuple[SourceDocument, ...],
    request: PersistenceMutationReviewRequest,
) -> PersistenceContractReport:
    if type(documents) is not tuple or any(type(item) is not SourceDocument for item in documents):
        raise TypeError("Persistence mutation core requires SourceDocument values")
    if type(request) is not PersistenceMutationReviewRequest:
        raise TypeError("Persistence mutation core requires its request type")
    definitions, duplicates = _definitions(documents)
    limitations = {"TRANSACTION_SEMANTICS_UNKNOWN"}
    collection = _MutationCollection([], set())
    target = definitions.get(request.operation_symbol)
    if target is None or request.operation_symbol in duplicates:
        limitations.add("MUTATION_OPERATION_NOT_UNIQUE")
        intents: tuple[MutationIntentFact, ...] = ()
    else:
        document, function = target
        if request.activation_guard_symbol is None:
            branches = [(function.body, ())]
        else:
            guarded = [
                item for item in ast.walk(function)
                if isinstance(item, ast.If)
                and _guard_name(item.test, request.activation_guard_symbol)
            ]
            if not guarded:
                limitations.add("ACTIVATION_GUARD_NOT_DISCOVERABLE")
            branches = [
                (item.body, (_ref(document, item),)) for item in guarded
            ]
        for body, guard_refs in branches:
            _collect_statements(
                body,
                operation_symbol=request.operation_symbol,
                document=document,
                definitions=definitions,
                duplicates=duplicates,
                environment={},
                call_path=(request.operation_symbol,),
                references=guard_refs,
                stack=frozenset({request.operation_symbol}),
                collection=collection,
            )
        limitations.update(collection.limitations)
        intents = _deduplicate_mutations(collection.intents)
    findings_and_limits = [_compare_mutation(request, item) for item in intents]
    comparison_limits = {limit for _, limit in findings_and_limits if limit is not None}
    findings = tuple(
        sorted(
            (finding for finding, _ in findings_and_limits if finding is not None),
            key=lambda item: (item.kind.value, item.evidence_references),
        )
    )
    limitations.update(comparison_limits)
    aligned_count = sum(
        finding is None and limit is None for finding, limit in findings_and_limits
    )
    mismatch_count = sum(finding is not None for finding, _ in findings_and_limits)
    if not intents:
        limitations.add("NO_REACHABLE_MUTATION")
        classification = Classification.INSUFFICIENT_EVIDENCE
    elif comparison_limits or collection.limitations:
        classification = (
            Classification.POTENTIAL_CONTRACT_MISMATCH
            if findings else Classification.INSUFFICIENT_EVIDENCE
        )
    elif mismatch_count and aligned_count:
        classification = Classification.POTENTIAL_CONTRACT_MISMATCH
    elif mismatch_count:
        kinds = {item.kind for item in findings}
        classification = (
            Classification.CONFIRMED_CONTRACT_MISMATCH
            if len(kinds) == 1 else Classification.POTENTIAL_CONTRACT_MISMATCH
        )
    else:
        classification = Classification.CONTRACT_STRUCTURALLY_ALIGNED
    references = tuple(sorted({ref for item in intents for ref in item.evidence_references}))
    path = intents[0].call_path if intents and all(item.call_path == intents[0].call_path for item in intents) else ()
    reachability = Reachability.CONFIRMED if intents and path else Reachability.UNKNOWN
    states = tuple(
        StateTransitionIntentFact(
            item.table, column, value, item.predicate_column,
            item.predicate_value_origin, item.evidence_references[-1],
        )
        for item in intents for column, value in item.assignments
    )
    return PersistenceContractReport(
        1, classification, request.operation_symbol, request.operation_symbol,
        request.dialect, request.target_table, request.identity_column,
        path, reachability, (), (), (), states, findings, references,
        tuple(sorted(limitations)), request.structural_scope, intents,
    )


def review_persistence_contract_documents(documents: tuple[SourceDocument, ...], request: PersistenceContractReviewRequest) -> PersistenceContractReport:
    if type(documents) is not tuple or any(type(item) is not SourceDocument for item in documents):
        raise TypeError("Persistence contract core requires a tuple of SourceDocument values")
    if type(request) is not PersistenceContractReviewRequest:
        raise TypeError("Persistence contract core requires a PersistenceContractReviewRequest")
    definitions, duplicates = _definitions(documents)
    base_limitations = {"TRANSACTION_SEMANTICS_UNKNOWN"}
    if request.producer_symbol in duplicates or request.consumer_symbol in duplicates or request.producer_symbol not in definitions or request.consumer_symbol not in definitions:
        base_limitations.add("TARGET_SYMBOL_UNRESOLVED")
        return PersistenceContractReport(1, Classification.INSUFFICIENT_EVIDENCE, request.producer_symbol, request.consumer_symbol, request.dialect, request.target_table, request.identity_column, (), Reachability.UNKNOWN, (), (), (), (), (), (), tuple(sorted(base_limitations)), request.structural_scope)
    producer_doc, producer_node = definitions[request.producer_symbol]
    consumer_doc, consumer_node = definitions[request.consumer_symbol]
    producer = _facts(producer_doc, producer_node)
    consumer = _facts(consumer_doc, consumer_node)
    limitations = base_limitations | producer.limitations | consumer.limitations
    path, path_refs = _local_path(definitions, request)
    reachability = Reachability.CONFIRMED if path else Reachability.UNKNOWN
    facts_refs = tuple(sorted({item.evidence_reference for item in (*producer.writes, *producer.identities, *consumer.reads, *producer.states, *consumer.states)} | set(path_refs)))
    essential_identity = [item for item in producer.identities if item.identity_symbol in producer.returned]
    target_reads = [item for item in consumer.reads if item.table == request.target_table]
    selected_reads = target_reads if target_reads else consumer.reads
    if len(essential_identity) != 1 or len(selected_reads) != 1:
        limitations.add("ESSENTIAL_CONTRACT_FACTS_UNRESOLVED")
        classification = Classification.INSUFFICIENT_EVIDENCE
        findings: tuple[PersistenceContractFinding, ...] = ()
    else:
        identity = essential_identity[0]
        write = next((item for item in producer.writes if item.cursor_symbol == identity.cursor_symbol), None)
        read = selected_reads[0]
        candidates: list[PersistenceContractFinding] = []
        if write is None:
            limitations.add("ESSENTIAL_CONTRACT_FACTS_UNRESOLVED")
        elif write.table != request.target_table or read.table != request.target_table:
            observed = write.table if write.table != request.target_table else read.table
            candidates.append(PersistenceContractFinding(FindingKind.TARGET_TABLE_MISMATCH, f"Observed persistence table {observed!r} differs from target {request.target_table!r}.", Severity.MEDIUM, tuple(sorted({write.evidence_reference, read.evidence_reference})), request.target_table, request.identity_column, observed, read.predicate_column))
        if read.predicate_column != request.identity_column:
            candidates.append(PersistenceContractFinding(FindingKind.TARGET_KEY_MISMATCH, f"Observed read key {read.predicate_column!r} differs from target identity key {request.identity_column!r}.", Severity.MEDIUM, (read.evidence_reference,), request.target_table, request.identity_column, read.table, read.predicate_column))
        consumer_parameters = {argument.arg for argument in consumer_node.args.args}
        if read.predicate_value_identity not in consumer_parameters:
            limitations.add("READ_IDENTITY_ORIGIN_UNKNOWN")
        if request.expected_state is not None:
            matching = [item for item in (*producer.states, *consumer.states) if item.table == request.target_table and item.predicate_column == request.identity_column]
            if matching and matching[-1].value != request.expected_state:
                state = matching[-1]
                candidates.append(PersistenceContractFinding(FindingKind.STATE_INTENT_MISMATCH, f"Observed state intent {state.value!r} differs from expected state {request.expected_state!r}.", Severity.LOW, (state.evidence_reference,), request.target_table, request.identity_column, state.table, state.predicate_column))
            elif not matching:
                limitations.add("EXPECTED_STATE_INTENT_UNRESOLVED")
        if candidates:
            classification = Classification.CONFIRMED_CONTRACT_MISMATCH
            findings = tuple(sorted(candidates, key=lambda item: (item.kind.value, item.evidence_references)))
        elif "READ_IDENTITY_ORIGIN_UNKNOWN" in limitations or "EXPECTED_STATE_INTENT_UNRESOLVED" in limitations:
            classification = Classification.INSUFFICIENT_EVIDENCE
            findings = ()
        else:
            classification = Classification.CONTRACT_STRUCTURALLY_ALIGNED
            findings = ()
    return PersistenceContractReport(1, classification, request.producer_symbol, request.consumer_symbol, request.dialect, request.target_table, request.identity_column, path, reachability, tuple(sorted(producer.writes, key=lambda item: item.evidence_reference)), tuple(sorted(producer.identities, key=lambda item: item.evidence_reference)), tuple(sorted(consumer.reads, key=lambda item: item.evidence_reference)), tuple(sorted((*producer.states, *consumer.states), key=lambda item: item.evidence_reference)), findings, facts_refs, tuple(sorted(limitations)), request.structural_scope)


def review_persistence_contract(target: str | Path, request: PersistenceContractReviewRequest) -> PersistenceContractReport:
    inventory = read_source_documents(target, allowed_paths=request.structural_scope)
    return review_persistence_contract_documents(inventory.documents, request)
