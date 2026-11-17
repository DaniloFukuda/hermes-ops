from __future__ import annotations

import ast
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from hermes_ops.skills.controlled_reader import SourceDocument, read_source_documents
from hermes_ops.skills.state_guard_effect_models import (
    StateBindingFact,
    StateGuardEffectClassification as Classification,
    StateGuardEffectFinding,
    StateGuardEffectFindingKind as FindingKind,
    StateGuardEffectReachability as Reachability,
    StateGuardEffectReport,
    StateGuardEffectReviewRequest,
    StateGuardEffectSeverity as Severity,
    StatePathFact,
    StatePathStatus,
)
from hermes_ops.skills.source_evidence import source_locator
from hermes_ops.skills.structural_ast import terminal_symbol


@dataclass
class _Path:
    bindings: dict[str, str]
    status: StatePathStatus | None = None
    references: tuple[str, ...] = ()
    limitations: frozenset[str] = frozenset()


def _ref(document: SourceDocument, node: ast.AST) -> str:
    return source_locator(document.path, node)


def _call_terminal(node: ast.Call) -> str | None:
    return terminal_symbol(node.func)


def _literal(node: ast.AST) -> tuple[bool, Any]:
    if not isinstance(node, ast.Constant) or type(node.value) not in {str, int, bool, type(None)}:
        return False, None
    return True, node.value


def _same_literal(left: Any, right: Any) -> bool:
    return type(left) is type(right) and left == right


def _collection(node: ast.AST) -> tuple[bool, tuple[Any, ...]]:
    if not isinstance(node, (ast.Set, ast.Tuple, ast.List)):
        return False, ()
    values: list[Any] = []
    for item in node.elts:
        ok, value = _literal(item)
        if not ok:
            return False, ()
        values.append(value)
    return True, tuple(values)


def _contains_binding(node: ast.AST, path: _Path) -> bool:
    return any(isinstance(item, ast.Name) and item.id in path.bindings for item in ast.walk(node))


def _evaluate_guard(test: ast.AST, path: _Path, literal: Any) -> tuple[bool | None, str | None]:
    if isinstance(test, ast.BoolOp) and _contains_binding(test, path):
        return None, "STATE_GUARD_BOOLEAN_COMPOSITION_UNSUPPORTED"
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not) and isinstance(test.operand, ast.Call):
        if _contains_binding(test.operand, path):
            return None, "STATE_GUARD_HELPER_OPAQUE"
        return None, None
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or len(test.comparators) != 1:
        return None, None
    left = test.left
    right = test.comparators[0]
    if not isinstance(left, ast.Name) or left.id not in path.bindings:
        if isinstance(left, ast.Name):
            return None, "STATE_GUARD_WRONG_BINDING"
        return None, None
    operation = test.ops[0]
    if isinstance(operation, (ast.Eq, ast.NotEq)):
        ok, expected = _literal(right)
        if not ok:
            return None, "STATE_GUARD_DYNAMIC"
        equal = _same_literal(literal, expected)
        return (equal if isinstance(operation, ast.Eq) else not equal), None
    if isinstance(operation, (ast.In, ast.NotIn)):
        ok, values = _collection(right)
        if not ok:
            return None, "STATE_GUARD_COLLECTION_DYNAMIC"
        present = any(_same_literal(literal, item) for item in values)
        return (present if isinstance(operation, ast.In) else not present), None
    return None, "STATE_GUARD_DYNAMIC"


def _field_identity(source: str, field: str | None) -> str:
    return f"parameter:{source}:0" if field is None else f"field:{source}:{field}:0"


def _field_access(value: ast.AST, source: str, field: str) -> bool:
    if (
        isinstance(value, ast.Subscript)
        and isinstance(value.value, ast.Name)
        and value.value.id == source
    ):
        ok, key = _literal(value.slice)
        return ok and type(key) is str and key == field
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Attribute)
        and value.func.attr == "get"
        and isinstance(value.func.value, ast.Name)
        and value.func.value.id == source
        and len(value.args) == 1
        and not value.keywords
        and _literal(value.args[0]) == (True, field)
    )


def _assign(document: SourceDocument, statement: ast.Assign, path: _Path, request: StateGuardEffectReviewRequest) -> _Path:
    if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
        if _contains_binding(statement, path):
            return replace(path, status=StatePathStatus.UNKNOWN, limitations=path.limitations | {"STATE_BINDING_REDEFINED"}, references=path.references + (_ref(document, statement),))
        return path
    target = statement.targets[0].id
    value = statement.value
    bindings = dict(path.bindings)
    if isinstance(value, ast.Name) and value.id in bindings:
        bindings[target] = bindings[value.id]
        return replace(path, bindings=bindings, references=path.references + (_ref(document, statement),))
    binding = request.state_binding
    identity = _field_identity(binding.source_parameter, binding.field)
    if binding.field is not None and _field_access(value, binding.source_parameter, binding.field):
        bindings[target] = identity
        return replace(path, bindings=bindings, references=path.references + (_ref(document, statement),))
    if target in bindings:
        bindings.pop(target, None)
        code = "STATE_BINDING_TRANSFORMED" if _contains_binding(value, path) else "STATE_BINDING_REDEFINED"
        return replace(path, bindings=bindings, status=StatePathStatus.UNKNOWN, limitations=path.limitations | {code}, references=path.references + (_ref(document, statement),))
    return path


def _walk(
    document: SourceDocument,
    statements: list[ast.stmt],
    paths: list[_Path],
    request: StateGuardEffectReviewRequest,
    *,
    finalize: bool = True,
) -> list[_Path]:
    current = paths
    for statement in statements:
        next_paths: list[_Path] = []
        for path in current:
            if path.status is not None:
                next_paths.append(path)
                continue
            reference = _ref(document, statement)
            if isinstance(statement, ast.Assign):
                if (
                    isinstance(statement.value, ast.Call)
                    and _call_terminal(statement.value) == request.expected_effect_symbol
                ):
                    next_paths.append(replace(
                        path,
                        status=StatePathStatus.ACCEPTED,
                        references=path.references + (reference,),
                    ))
                else:
                    next_paths.append(_assign(document, statement, path, request))
            elif isinstance(statement, (ast.Return, ast.Raise)):
                next_paths.append(replace(path, status=StatePathStatus.REJECTED, references=path.references + (reference,)))
            elif isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
                if _call_terminal(statement.value) == request.expected_effect_symbol:
                    next_paths.append(replace(path, status=StatePathStatus.ACCEPTED, references=path.references + (reference,)))
                elif _contains_binding(statement.value, path):
                    next_paths.append(replace(path, status=StatePathStatus.UNKNOWN, limitations=path.limitations | {"STATE_GUARD_HELPER_OPAQUE"}, references=path.references + (reference,)))
                else:
                    next_paths.append(path)
            elif isinstance(statement, ast.If):
                decision, limitation = _evaluate_guard(statement.test, path, request.input_state_literal)
                base = replace(path, references=path.references + (reference,))
                if limitation == "STATE_GUARD_WRONG_BINDING":
                    next_paths.append(replace(base, status=StatePathStatus.UNKNOWN, limitations=base.limitations | {limitation}))
                elif limitation is not None:
                    next_paths.append(replace(base, status=StatePathStatus.UNKNOWN, limitations=base.limitations | {limitation}))
                elif decision is True:
                    next_paths.extend(_walk(document, statement.body, [base], request, finalize=False))
                elif decision is False:
                    next_paths.extend(_walk(document, statement.orelse, [base], request, finalize=False) if statement.orelse else [base])
                else:
                    next_paths.extend(_walk(document, statement.body, [replace(base, bindings=dict(base.bindings))], request, finalize=False))
                    next_paths.extend(_walk(document, statement.orelse, [replace(base, bindings=dict(base.bindings))], request, finalize=False) if statement.orelse else [replace(base, bindings=dict(base.bindings))])
            elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While, ast.Try, ast.Match, ast.With, ast.AsyncWith)):
                next_paths.append(replace(path, status=StatePathStatus.UNKNOWN, limitations=path.limitations | {"STATE_CONTROL_FLOW_UNSUPPORTED"}, references=path.references + (reference,)))
            elif isinstance(statement, (ast.AnnAssign, ast.AugAssign)) and _contains_binding(statement, path):
                next_paths.append(replace(path, status=StatePathStatus.UNKNOWN, limitations=path.limitations | {"STATE_BINDING_REDEFINED"}, references=path.references + (reference,)))
            else:
                next_paths.append(path)
        current = next_paths
    if finalize:
        return [replace(path, status=StatePathStatus.REJECTED) if path.status is None else path for path in current]
    return current


def _definitions(documents: tuple[SourceDocument, ...], symbol: str) -> list[tuple[SourceDocument, ast.FunctionDef | ast.AsyncFunctionDef]]:
    found = []
    for document in documents:
        try:
            module = ast.parse(document.text)
        except SyntaxError:
            continue
        for node in ast.walk(module):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol:
                found.append((document, node))
    return found


def _all_effect_refs(document: SourceDocument, operation: ast.AST, symbol: str) -> tuple[str, ...]:
    return tuple(sorted({
        _ref(document, node)
        for node in ast.walk(operation)
        if isinstance(node, ast.Call) and _call_terminal(node) == symbol
    }))


def _dynamic_effect_refs(
    document: SourceDocument,
    operation: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[str, ...]:
    parameters = {
        item.arg
        for item in (
            *operation.args.posonlyargs,
            *operation.args.args,
            *operation.args.kwonlyargs,
        )
    }
    references = set()
    for node in ast.walk(operation):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if (
            isinstance(function, ast.Name)
            and function.id in parameters
        ) or isinstance(function, (ast.Call, ast.Subscript)):
            references.add(_ref(document, node))
    return tuple(sorted(references))


def _report(
    request: StateGuardEffectReviewRequest,
    classification: Classification,
    *,
    reachability: Reachability = Reachability.UNKNOWN,
    binding_fact: StateBindingFact | None = None,
    paths: tuple[StatePathFact, ...] = (),
    findings: tuple[StateGuardEffectFinding, ...] = (),
    evidence: tuple[str, ...] = (),
    limitations: tuple[str, ...] = (),
) -> StateGuardEffectReport:
    return StateGuardEffectReport(
        1, classification, request.operation_symbol, request.state_binding,
        request.input_state_literal, request.expected_effect_symbol, reachability,
        binding_fact, paths, findings, tuple(sorted(set(evidence))),
        tuple(sorted(set(limitations))), request.structural_scope,
    )


def review_state_guard_effect_documents(
    documents: tuple[SourceDocument, ...],
    request: StateGuardEffectReviewRequest,
) -> StateGuardEffectReport:
    if type(request) is not StateGuardEffectReviewRequest:
        raise TypeError("State guard effect core requires its request type")
    definitions = _definitions(documents, request.operation_symbol)
    if len(definitions) != 1:
        return _report(request, Classification.INSUFFICIENT_EVIDENCE, limitations=("STATE_OPERATION_NOT_UNIQUE",))
    document, operation = definitions[0]
    parameters = {
        item.arg for item in (*operation.args.posonlyargs, *operation.args.args, *operation.args.kwonlyargs)
    }
    source = request.state_binding.source_parameter
    if source not in parameters:
        return _report(request, Classification.INSUFFICIENT_EVIDENCE, limitations=("STATE_SOURCE_PARAMETER_NOT_FOUND",), evidence=(_ref(document, operation),))
    effect_refs = _all_effect_refs(document, operation, request.expected_effect_symbol)
    if not effect_refs:
        dynamic_refs = _dynamic_effect_refs(document, operation)
        diagnostic = (
            "EXPECTED_EFFECT_CALL_DYNAMIC"
            if dynamic_refs
            else "EXPECTED_EFFECT_NOT_FOUND"
        )
        return _report(
            request,
            Classification.INSUFFICIENT_EVIDENCE,
            limitations=(diagnostic,),
            evidence=(_ref(document, operation), *dynamic_refs),
        )
    identity = _field_identity(source, request.state_binding.field)
    bindings = {source: identity} if request.state_binding.field is None else {}
    initial_ref = _ref(document, operation)
    paths = _walk(document, operation.body, [_Path(bindings, references=(initial_ref,))], request)
    if request.state_binding.field is not None and not any(identity in path.bindings.values() for path in paths):
        return _report(request, Classification.INSUFFICIENT_EVIDENCE, limitations=("STATE_BINDING_NOT_DISCOVERABLE",), evidence=(initial_ref, *effect_refs))
    path_facts = tuple(sorted(
        (StatePathFact(path.status or StatePathStatus.UNKNOWN, tuple(dict.fromkeys(path.references))) for path in paths),
        key=lambda item: (item.status.value, item.evidence_references),
    ))
    limitations = {item for path in paths for item in path.limitations}
    accepted = [path for path in paths if path.status is StatePathStatus.ACCEPTED]
    unknown = [path for path in paths if path.status is StatePathStatus.UNKNOWN]
    binding_refs = tuple(sorted({ref for path in paths for ref in path.references if ref not in effect_refs}))
    binding_fact = StateBindingFact(source, request.state_binding.field, identity, identity, binding_refs or (initial_ref,))
    evidence = tuple(ref for path in paths for ref in path.references) + effect_refs
    if accepted:
        return _report(request, Classification.CONTRACT_STRUCTURALLY_ALIGNED, reachability=Reachability.CONFIRMED, binding_fact=binding_fact, paths=path_facts, evidence=evidence, limitations=tuple(limitations))
    if unknown:
        limitations.add("STATE_PATH_PARTIALLY_UNKNOWN")
        return _report(request, Classification.INSUFFICIENT_EVIDENCE, binding_fact=binding_fact, paths=path_facts, evidence=evidence, limitations=tuple(limitations))
    finding = StateGuardEffectFinding(
        FindingKind.STATE_EFFECT_COVERAGE_MISMATCH,
        request.operation_symbol,
        request.state_binding,
        request.input_state_literal,
        request.expected_effect_symbol,
        "The declared input state is structurally blocked before the expected call effect.",
        Severity.MEDIUM,
        tuple(sorted(set(evidence))),
    )
    return _report(request, Classification.CONFIRMED_CONTRACT_MISMATCH, reachability=Reachability.CONFIRMED, binding_fact=binding_fact, paths=path_facts, findings=(finding,), evidence=evidence, limitations=tuple(limitations))


def review_state_guard_effect(target: str | Path, request: StateGuardEffectReviewRequest) -> StateGuardEffectReport:
    inventory = read_source_documents(target, allowed_paths=request.structural_scope)
    return review_state_guard_effect_documents(inventory.documents, request)
