from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.core.results import Status
from hermes_ops.skills.controlled_reader import SourceDocument, read_source_documents
from hermes_ops.skills.execution_models import (
    SkillExecutionEvidence,
    SkillExecutionResult,
    SkillExecutionStatus,
)
from hermes_ops.skills.execution_path_models import (
    ExecutionPathClassification,
    ExecutionPathFinding,
    ExecutionPathReport,
    ExecutionPathSeverity,
)
from hermes_ops.skills.mission_audit import normalize_structural_scope
from hermes_ops.skills.source_evidence import source_locator
from hermes_ops.skills.structural_ast import terminal_symbol


_SYMBOL = re.compile(r"[A-Za-z_]\w*\Z")


@dataclass(frozen=True, slots=True)
class _Definition:
    path: str
    node: ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(frozen=True, slots=True)
class _Domain:
    kind: str
    value: str
    description: str
    line: int
    subject: str | None = None


@dataclass(frozen=True, slots=True)
class _OriginFact:
    subject: str
    kind: str
    expression: str
    evidence_ref: str
    variant_expressions: tuple[str, ...] = ()
    variant_evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _DomainFact:
    subject: str
    kind: str
    value: str
    success_path_condition: str | None
    evidence_ref: str
    description: str
    line: int
    supporting_evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _GuardDerivedFact:
    subject: str
    binding_identity: str
    constraint_kind: str
    canonical_value: str | None
    guard_evidence_ref: str
    dominated_success_return_ref: str
    generation_id: str


@dataclass(frozen=True, slots=True)
class _ProducerEvidence:
    origin: _OriginFact | None
    domain: _DomainFact | None
    field_present_on_success: bool
    guard_fact_discovered_not_comparable: bool = False


@dataclass(frozen=True, slots=True)
class _Trace:
    path: tuple[str, ...]
    document: str
    line: int
    mapping_key: str | None = None
    destination_parameter: str | None = None
    transformations: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _FlowValue:
    source_symbol: str
    path: tuple[str, ...]
    mapping_key: str | None = None
    locally_bound: bool = False
    transformations: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _Edge:
    source_symbol: str
    destination_symbol: str
    source_value_identity: str
    destination_parameter: str
    document: str
    line: int
    propagation_kind: str


def _invalid(message: str) -> None:
    raise SkillExecutionError("SKILL_EXECUTION_INVALID", message)


def _call_name(node: ast.AST) -> str | None:
    return terminal_symbol(node)


def _simple_assignments(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, ast.AST]:
    assignments: dict[str, ast.AST] = {}
    for statement in ast.walk(node):
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
            if isinstance(target, ast.Name):
                assignments[target.id] = statement.value
    return assignments


def _expression_evidence(
    definition: _Definition,
    value: ast.AST,
    parameters: set[str],
    assignments: dict[str, ast.AST],
    line: int,
    subject: str,
    success_path_condition: str | None,
) -> tuple[_OriginFact | None, _DomainFact | None]:
    seen: set[str] = set()
    while isinstance(value, ast.Name) and value.id in assignments and value.id not in seen:
        seen.add(value.id)
        value = assignments[value.id]
    evidence_ref = f"{definition.path}:{line}"
    if isinstance(value, ast.Constant) and isinstance(value.value, (str, int, float, bool)):
        literal = repr(value.value)
        return (
            _OriginFact(subject, "literal", literal, evidence_ref),
            _DomainFact(
                subject,
                "literal",
                literal,
                success_path_condition,
                evidence_ref,
                f"literal value {literal}",
                line,
            ),
        )
    if isinstance(value, ast.Name) and value.id in parameters:
        return (
            _OriginFact(subject, "parameter", value.id, evidence_ref),
            _DomainFact(
                subject,
                "unconstrained",
                value.id,
                success_path_condition,
                evidence_ref,
                "caller-controlled value",
                line,
            ),
        )
    if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Div) and isinstance(value.left, ast.Name):
        expression = ast.unparse(value)
        return (
            _OriginFact(subject, "supported_transform", expression, evidence_ref),
            _DomainFact(
                subject,
                "under",
                value.left.id,
                success_path_condition,
                evidence_ref,
                f"value under {value.left.id}",
                line,
            ),
        )
    if isinstance(value, ast.Call):
        return _OriginFact(subject, "call", ast.unparse(value), evidence_ref), None
    if isinstance(value, ast.Attribute):
        return _OriginFact(subject, "attribute", ast.unparse(value), evidence_ref), None
    if isinstance(value, ast.Name):
        return _OriginFact(subject, "local_alias", value.id, evidence_ref), None
    return None, None


def _dict_item(value: ast.Dict, expected_key: str) -> ast.AST | None:
    matches = [
        item
        for key, item in zip(value.keys, value.values)
        if isinstance(key, ast.Constant) and key.value == expected_key
    ]
    return matches[0] if len(matches) == 1 else None


def _explicit_success(value: ast.AST) -> bool | None:
    if not isinstance(value, ast.Dict):
        return None
    marker = _dict_item(value, "success")
    if isinstance(marker, ast.Constant) and type(marker.value) is bool:
        return marker.value
    return None


def _explicit_failure_branch(node: ast.If) -> bool:
    return bool(
        not node.orelse
        and len(node.body) == 1
        and isinstance(node.body[0], ast.Return)
        and node.body[0].value is not None
        and _explicit_success(node.body[0].value) is False
    )


def _returned_binding(value: ast.AST, mapping_key: str | None) -> str | None:
    if mapping_key is not None:
        if not isinstance(value, ast.Dict):
            return None
        value = _dict_item(value, mapping_key)
    return value.id if isinstance(value, ast.Name) else None


def _guard_derived_domain(
    definition: _Definition,
    mapping_key: str | None,
    variants: list[ast.Return],
) -> tuple[_DomainFact | None, bool, bool]:
    """Derive only linear, generation-aware facts that dominate every variant."""
    potential_guard = any(
        isinstance(candidate, ast.If) and _explicit_failure_branch(candidate)
        for candidate in ast.walk(definition.node)
    )
    bindings: dict[str, str] = {}
    generations: dict[str, int] = {}
    for argument in (
        *definition.node.args.posonlyargs,
        *definition.node.args.args,
        *definition.node.args.kwonlyargs,
    ):
        bindings[argument.arg] = f"parameter:{argument.arg}:0"
        generations[argument.arg] = 0
    active: dict[str, list[tuple[str, str | None, str, str]]] = {}
    per_return: dict[int, tuple[_GuardDerivedFact, ...]] = {}
    saw_guard = False
    invalid = False

    for statement in definition.node.body:
        if isinstance(statement, ast.Assign):
            if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
                invalid = True
                break
            target = statement.targets[0].id
            if isinstance(statement.value, ast.Name) and statement.value.id in bindings:
                bindings[target] = bindings[statement.value.id]
            else:
                if active:
                    invalid = True
                    break
                generations[target] = generations.get(target, 0) + 1
                bindings[target] = f"local:{target}:{generations[target]}:{statement.lineno}"
            continue
        if isinstance(statement, ast.If):
            if not _explicit_failure_branch(statement):
                invalid = True
                break
            saw_guard = True
            test = statement.test
            subject: str | None = None
            kind: str | None = None
            canonical: str | None = None
            if (
                isinstance(test, ast.UnaryOp)
                and isinstance(test.op, ast.Not)
                and isinstance(test.operand, ast.Name)
            ):
                subject, kind = test.operand.id, "TRUTHY"
            elif (
                isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and len(test.ops) == 1
                and isinstance(test.ops[0], ast.NotEq)
                and len(test.comparators) == 1
                and isinstance(test.comparators[0], ast.Constant)
                and isinstance(test.comparators[0].value, (str, int, float, bool, type(None)))
            ):
                subject, kind = test.left.id, "EQUAL_LITERAL"
                canonical = repr(test.comparators[0].value)
            elif (
                isinstance(test, ast.UnaryOp)
                and isinstance(test.op, ast.Not)
                and isinstance(test.operand, ast.Call)
                and len(test.operand.args) == 1
                and isinstance(test.operand.args[0], ast.Name)
            ):
                subject, kind = test.operand.args[0].id, "OPAQUE_PREDICATE"
                canonical = ast.unparse(test.operand.func)
            else:
                invalid = True
                break
            identity = bindings.get(subject)
            if identity is None:
                invalid = True
                break
            active.setdefault(identity, []).append(
                (kind, canonical, source_locator(definition.path, statement), subject)
            )
            continue
        if isinstance(statement, ast.Return) and statement.value is not None:
            if _explicit_success(statement.value) is not True:
                continue
            returned = _returned_binding(statement.value, mapping_key)
            identity = bindings.get(returned or "")
            facts = ()
            if identity is not None:
                return_ref = source_locator(definition.path, statement)
                facts = tuple(
                    _GuardDerivedFact(
                        mapping_key or "return", identity, kind, canonical,
                        guard_ref, return_ref, identity,
                    )
                    for kind, canonical, guard_ref, _subject in active.get(identity, ())
                )
            per_return[statement.lineno] = facts
            continue
        if isinstance(statement, (ast.AnnAssign, ast.AugAssign, ast.For, ast.AsyncFor, ast.While, ast.Match, ast.Try, ast.With, ast.AsyncWith)):
            invalid = True
            break
        if active and isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            invalid = True
            break

    if invalid or not saw_guard or any(item.lineno not in per_return for item in variants):
        return None, False, saw_guard or potential_guard
    signatures = [
        {(fact.constraint_kind, fact.canonical_value) for fact in per_return[item.lineno]}
        for item in variants
    ]
    common = set.intersection(*signatures) if signatures else set()
    comparable = sorted(
        (item for item in common if item[0] in {"TRUTHY", "EQUAL_LITERAL"}),
        key=lambda item: (0 if item[0] == "EQUAL_LITERAL" else 1, item[1] or ""),
    )
    if comparable:
        kind, canonical = comparable[0]
        exemplar = next(
            fact for fact in per_return[variants[0].lineno]
            if (fact.constraint_kind, fact.canonical_value) == (kind, canonical)
        )
        domain_kind = "truthy" if kind == "TRUTHY" else "literal"
        value = exemplar.subject if canonical is None else canonical
        description = (
            f"{exemplar.subject} is truthy on every explicit success path"
            if kind == "TRUTHY"
            else f"{exemplar.subject} equals {canonical} on every explicit success path"
        )
        evidence = tuple(dict.fromkeys(
            ref
            for variant in variants
            for fact in per_return[variant.lineno]
            if (fact.constraint_kind, fact.canonical_value) == (kind, canonical)
            for ref in (fact.guard_evidence_ref, fact.dominated_success_return_ref)
        ))
        return _DomainFact(
            mapping_key or "return", domain_kind, value,
            "guard dominates every explicit success return",
            exemplar.guard_evidence_ref, description,
            int(exemplar.guard_evidence_ref.rsplit(":", 1)[1]), evidence,
        ), False, True
    opaque = any(
        kind == "OPAQUE_PREDICATE"
        for facts in signatures
        for kind, _value in facts
    )
    return None, opaque, True


def _producer_evidence(
    definition: _Definition, mapping_key: str | None = None
) -> _ProducerEvidence:
    node = definition.node
    parameters = {
        argument.arg
        for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
    }
    attribute_sources: dict[str, str] = {}
    for candidate in ast.walk(node):
        if isinstance(candidate, ast.Assign) and isinstance(candidate.value, ast.Name):
            for target in candidate.targets:
                if isinstance(target, ast.Attribute):
                    attribute_sources[ast.unparse(target)] = candidate.value.id
    returns = sorted(
        (
            candidate
            for candidate in ast.walk(node)
            if isinstance(candidate, ast.Return) and candidate.value is not None
        ),
        key=lambda candidate: candidate.lineno,
    )
    explicit_successes = [item for item in returns if _explicit_success(item.value) is True]
    if explicit_successes:
        variants = explicit_successes
        success_condition = "mapping field 'success' is literal True"
    elif returns:
        variants = returns
        success_condition = None
    else:
        return _ProducerEvidence(None, None, False)

    assignments = _simple_assignments(node)
    origins: list[_OriginFact] = []
    domains: list[_DomainFact] = []
    for returned in variants:
        value = returned.value
        if mapping_key is not None:
            if not isinstance(value, ast.Dict) or (value := _dict_item(value, mapping_key)) is None:
                return _ProducerEvidence(None, None, False)
        subject = mapping_key or "return"
        origin, domain = _expression_evidence(
            definition,
            value,
            parameters,
            assignments,
            returned.lineno,
            subject,
            success_condition,
        )
        if domain is None and isinstance(value, ast.Attribute):
            source = attribute_sources.get(ast.unparse(value))
            if source in parameters:
                evidence_ref = source_locator(definition.path, returned)
                origin = _OriginFact(subject, "parameter_attribute", source, evidence_ref)
                domain = _DomainFact(
                    subject,
                    "unconstrained",
                    source,
                    success_condition,
                    evidence_ref,
                    "caller-controlled value",
                    returned.lineno,
                )
        if origin is None:
            return _ProducerEvidence(None, None, True)
        origins.append(origin)
        if domain is not None:
            domains.append(domain)

    if not origins:
        return _ProducerEvidence(None, None, False)
    if all(item == origins[0] for item in origins):
        origin = origins[0]
    else:
        ordered_origins = tuple(sorted(origins, key=lambda item: (item.expression, item.evidence_ref)))
        first = ordered_origins[0]
        origin = _OriginFact(
            first.subject,
            "variants",
            "multiple explicit origins",
            first.evidence_ref,
            tuple(item.expression for item in ordered_origins),
            tuple(item.evidence_ref for item in ordered_origins),
        )
    domain: _DomainFact | None = None
    if len(domains) == len(variants):
        signatures = {(item.kind, item.value) for item in domains}
        if len(signatures) == 1:
            first = domains[0]
            description = first.description
            if mapping_key is not None:
                description = f"mapping field {mapping_key!r} containing {description}"
            domain = _DomainFact(
                first.subject,
                first.kind,
                first.value,
                first.success_path_condition,
                first.evidence_ref,
                description,
                first.line,
            )
    guard_domain, opaque_guard, saw_guard = _guard_derived_domain(
        definition, mapping_key, variants
    )
    if guard_domain is not None:
        domain = guard_domain
    elif saw_guard and domain is not None and domain.kind == "unconstrained":
        domain = None
    return _ProducerEvidence(origin, domain, True, opaque_guard)


def _returned_domain(definition: _Definition, mapping_key: str | None = None) -> _Domain | None:
    domain = _producer_evidence(definition, mapping_key).domain
    if domain is None:
        return None
    return _Domain(domain.kind, domain.value, domain.description, domain.line, domain.subject)


def _raises(branch: list[ast.stmt]) -> bool:
    return any(isinstance(candidate, ast.Raise) for statement in branch for candidate in ast.walk(statement))


def _returns_false(branch: list[ast.stmt]) -> bool:
    return any(
        isinstance(candidate, ast.Return)
        and isinstance(candidate.value, ast.Constant)
        and candidate.value.value is False
        for statement in branch
        for candidate in ast.walk(statement)
    )


def _consumer_requirement(
    definition: _Definition, preferred_parameter: str | None = None
) -> _Domain | None:
    aliases: dict[str, tuple[str, str]] = {}
    for candidate in ast.walk(definition.node):
        if not isinstance(candidate, ast.Assign) or len(candidate.targets) != 1:
            continue
        target = candidate.targets[0]
        if not isinstance(target, ast.Name):
            continue
        value = candidate.value
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Attribute)
            and value.func.attr == "strip"
            and not value.args
            and isinstance(value.func.value, ast.Call)
            and _call_name(value.func.value.func) == "str"
            and len(value.func.value.args) == 1
            and isinstance(value.func.value.args[0], ast.Name)
        ):
            aliases[target.id] = (value.func.value.args[0].id, "stripped")
        elif (
            isinstance(value, ast.Call)
            and len(value.args) >= 1
            and isinstance(value.args[0], ast.Name)
        ):
            aliases[target.id] = (value.args[0].id, "call_result")
    for candidate in ast.walk(definition.node):
        if not isinstance(candidate, ast.If) or not (
            _raises(candidate.body) or _returns_false(candidate.body)
        ):
            continue
        test = candidate.test
        if (
            isinstance(test, ast.UnaryOp)
            and isinstance(test.op, ast.Not)
            and isinstance(test.operand, ast.Name)
        ):
            tested = test.operand.id
            subject, transform = aliases.get(tested, (tested, "direct"))
            if preferred_parameter is not None and subject != preferred_parameter:
                continue
            if transform == "call_result":
                description = f"successful continuation requires call result for {subject} to be truthy"
                return _Domain("predicate", subject, description, candidate.lineno, subject)
            description = (
                f"stripped string from {subject} must be non-empty"
                if transform == "stripped"
                else f"{subject} must be truthy/non-empty"
            )
            return _Domain("truthy", subject, description, candidate.lineno, subject)
        if (
            isinstance(test, ast.UnaryOp)
            and isinstance(test.op, ast.Not)
            and isinstance(test.operand, ast.Call)
            and isinstance(test.operand.func, ast.Attribute)
            and test.operand.func.attr == "is_relative_to"
            and len(test.operand.args) == 1
            and isinstance(test.operand.args[0], ast.Name)
        ):
            root = test.operand.args[0].id
            return _Domain("under", root, f"value must be under {root}", candidate.lineno)
        if (
            isinstance(test, ast.Compare)
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.NotEq)
            and len(test.comparators) == 1
            and isinstance(test.comparators[0], ast.Constant)
        ):
            literal = repr(test.comparators[0].value)
            return _Domain("literal", literal, f"value must equal {literal}", candidate.lineno)
    return None


def _consumer_has_precondition_candidate(
    definition: _Definition, preferred_parameter: str | None
) -> bool:
    for candidate in ast.walk(definition.node):
        if not isinstance(candidate, ast.If) or not (
            _raises(candidate.body) or _returns_false(candidate.body)
        ):
            continue
        names = {item.id for item in ast.walk(candidate.test) if isinstance(item, ast.Name)}
        if preferred_parameter is None or preferred_parameter in names:
            return True
    return False


def _parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef, *, qualified_call: bool = False
) -> tuple[str, ...]:
    parameters = tuple(
        argument.arg
        for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
    )
    if qualified_call and parameters and parameters[0] in {"self", "cls"}:
        return parameters[1:]
    return parameters


class _FlowAnalyzer:
    def __init__(
        self,
        documents: tuple[tuple[str, ast.Module], ...],
        index: dict[str, tuple[_Definition, ...]],
        producer: str,
        consumer: str,
    ) -> None:
        self.documents = documents
        self.index = index
        self.producer = producer
        self.consumer = consumer
        self.traces: list[_Trace] = []
        self.edges: list[_Edge] = []

    def run(self) -> tuple[_Trace, ...]:
        definitions = sorted(
            (definition for items in self.index.values() for definition in items),
            key=lambda item: (item.path, item.node.lineno, item.node.name),
        )
        for definition in definitions:
            if definition.node.name != self.producer:
                self._statements(definition, definition.node.body, {}, frozenset({id(definition.node)}))
        unique = {
            (
                trace.path,
                trace.document,
                trace.line,
                trace.mapping_key,
                trace.destination_parameter,
                trace.transformations,
            ): trace
            for trace in self.traces
        }
        return tuple(sorted(unique.values(), key=lambda item: (item.document, item.line, item.path)))

    def _statements(
        self,
        definition: _Definition,
        statements: list[ast.stmt],
        environment: dict[str, _FlowValue],
        active: frozenset[int],
    ) -> _FlowValue | None:
        returned: _FlowValue | None = None
        for statement in statements:
            if isinstance(statement, ast.Assign):
                value = self._expression(definition, statement.value, environment, active)
                for target in statement.targets:
                    if isinstance(target, ast.Name):
                        if value is None:
                            environment.pop(target.id, None)
                        else:
                            environment[target.id] = _FlowValue(
                                value.source_symbol,
                                value.path,
                                value.mapping_key,
                                True,
                                value.transformations,
                                value.evidence_references,
                            )
            elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                value = (
                    self._expression(definition, statement.value, environment, active)
                    if statement.value is not None
                    else None
                )
                if value is None:
                    environment.pop(statement.target.id, None)
                else:
                    environment[statement.target.id] = _FlowValue(
                        value.source_symbol,
                        value.path,
                        value.mapping_key,
                        True,
                        value.transformations,
                        value.evidence_references,
                    )
            elif isinstance(statement, ast.Expr):
                self._expression(definition, statement.value, environment, active)
            elif isinstance(statement, ast.Return) and statement.value is not None:
                returned = self._expression(definition, statement.value, environment, active)
            elif isinstance(statement, ast.If):
                self._expression(definition, statement.test, environment, active)
                self._statements(definition, statement.body, dict(environment), active)
                self._statements(definition, statement.orelse, dict(environment), active)
        return returned

    def _expression(
        self,
        definition: _Definition,
        expression: ast.AST,
        environment: dict[str, _FlowValue],
        active: frozenset[int],
    ) -> _FlowValue | None:
        if isinstance(expression, ast.Name):
            return environment.get(expression.id)
        if isinstance(expression, ast.Subscript):
            base = self._expression(definition, expression.value, environment, active)
            key = expression.slice
            if base is None or not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                return None
            return _FlowValue(
                base.source_symbol,
                base.path,
                key.value,
                base.locally_bound,
                base.transformations,
                base.evidence_references,
            )
        if not isinstance(expression, ast.Call):
            return None
        name = _call_name(expression.func)
        if name is None:
            return None
        if name == self.producer:
            return _FlowValue(
                self.producer,
                (self.producer,),
                evidence_references=(source_locator(definition.path, expression),),
            )
        arguments = [self._expression(definition, item, environment, active) for item in expression.args]
        carrying = [(index, value) for index, value in enumerate(arguments) if value is not None]
        if not carrying:
            return None
        argument_index, value = carrying[0]
        qualified = isinstance(expression.func, ast.Attribute)
        targets = self.index.get(name, ())
        if len(targets) != 1:
            return None
        target = targets[0]
        parameters = _parameters(target.node, qualified_call=qualified)
        if argument_index >= len(parameters):
            return None
        destination_parameter = parameters[argument_index]
        edge_reference = source_locator(definition.path, expression)
        evidence_references = tuple(dict.fromkeys((*value.evidence_references, edge_reference)))
        path = value.path
        if value.locally_bound and definition.node.name not in path:
            path = (*path, definition.node.name)
        self.edges.append(
            _Edge(
                value.source_symbol,
                name,
                value.mapping_key or "return",
                destination_parameter,
                definition.path,
                expression.lineno,
                "QUALIFIED_CALL" if qualified else "DIRECT_CALL",
            )
        )
        if name == self.consumer:
            self.traces.append(
                _Trace(
                    (*path, self.consumer),
                    definition.path,
                    expression.lineno,
                    value.mapping_key,
                    destination_parameter,
                    value.transformations,
                    evidence_references,
                )
            )
            return value
        if id(target.node) in active:
            return None
        forwarded_path = (*path, name)
        transition = _returned_domain(target)
        transformations = value.transformations
        if transition is not None and transition.kind != "unconstrained":
            transformations = (*transformations, name)
        forwarded: dict[str, _FlowValue] = {}
        for index, argument in carrying:
            if index < len(parameters):
                forwarded[parameters[index]] = _FlowValue(
                    argument.source_symbol,
                    forwarded_path,
                    argument.mapping_key,
                    False,
                    transformations,
                    evidence_references,
                )
        result = self._statements(target, target.node.body, forwarded, active | {id(target.node)})
        return result or _FlowValue(
            value.source_symbol,
            forwarded_path,
            value.mapping_key,
            False,
            transformations,
            evidence_references,
        )


def _find_traces(
    documents: tuple[tuple[str, ast.Module], ...],
    index: dict[str, tuple[_Definition, ...]],
    producer: str,
    consumer: str,
) -> tuple[_Trace, ...]:
    return _FlowAnalyzer(documents, index, producer, consumer).run()


def _parse_documents(documents: tuple[SourceDocument, ...]) -> tuple[tuple[str, ast.Module], ...]:
    parsed: list[tuple[str, ast.Module]] = []
    for document in documents:
        if Path(document.path).suffix not in {".py", ".pyi"}:
            continue
        try:
            tree = ast.parse(document.text, filename=document.path)
        except SyntaxError as exc:
            raise SkillExecutionError(
                "EXECUTION_PATH_PARSE_FAILED",
                "An authorized Python source file could not be parsed",
            ) from exc
        parsed.append((document.path, tree))
    return tuple(parsed)


def _parse_sources(target: Any, scope: tuple[str, ...]) -> tuple[tuple[str, ast.Module], ...]:
    inventory = read_source_documents(target, allowed_paths=scope)
    return _parse_documents(inventory.documents)


def _definitions(documents: tuple[tuple[str, ast.Module], ...]) -> dict[str, tuple[_Definition, ...]]:
    index: dict[str, list[_Definition]] = {}
    for path, tree in documents:
        for candidate in ast.walk(tree):
            if isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)):
                index.setdefault(candidate.name, []).append(_Definition(path, candidate))
    return {name: tuple(items) for name, items in index.items()}


def _report(
    classification: ExecutionPathClassification,
    producer: str,
    consumer: str,
    scope: tuple[str, ...],
    *,
    path: tuple[str, ...] = (),
    findings: tuple[ExecutionPathFinding, ...] = (),
    references: tuple[str, ...] = (),
    limitations: tuple[str, ...] = (),
) -> ExecutionPathReport:
    return ExecutionPathReport(1, classification, producer, consumer, path, findings, references, limitations, scope)


def review_execution_path(
    target: Any,
    producer_symbol: Any,
    consumer_symbol: Any,
    *,
    include_paths: tuple[str, ...] = (),
    mission: str | None = None,
) -> ExecutionPathReport:
    del mission  # Optional context is reserved but cannot alter evidence in v1.
    if type(producer_symbol) is not str or _SYMBOL.fullmatch(producer_symbol) is None:
        _invalid("Producer symbol must be a simple Python identifier")
    if type(consumer_symbol) is not str or _SYMBOL.fullmatch(consumer_symbol) is None:
        _invalid("Consumer symbol must be a simple Python identifier")
    if type(include_paths) is not tuple or any(type(item) is not str for item in include_paths):
        _invalid("include_paths must be a tuple of strings")
    root = Path(target).resolve()
    scope = normalize_structural_scope(include_paths, root)
    inventory = read_source_documents(target, allowed_paths=scope)
    return review_execution_path_documents(
        inventory.documents, producer_symbol, consumer_symbol, structural_scope=scope
    )


def review_execution_path_documents(
    source_documents: tuple[SourceDocument, ...],
    producer_symbol: Any,
    consumer_symbol: Any,
    *,
    structural_scope: tuple[str, ...] = (),
) -> ExecutionPathReport:
    if type(producer_symbol) is not str or _SYMBOL.fullmatch(producer_symbol) is None:
        _invalid("Producer symbol must be a simple Python identifier")
    if type(consumer_symbol) is not str or _SYMBOL.fullmatch(consumer_symbol) is None:
        _invalid("Consumer symbol must be a simple Python identifier")
    if type(source_documents) is not tuple or any(
        type(item) is not SourceDocument for item in source_documents
    ):
        _invalid("Execution path core requires source documents")
    if type(structural_scope) is not tuple or any(type(item) is not str for item in structural_scope):
        _invalid("structural_scope must be a tuple of strings")
    scope = tuple(sorted(set(structural_scope)))
    documents = _parse_documents(source_documents)
    index = _definitions(documents)
    producers, consumers = index.get(producer_symbol, ()), index.get(consumer_symbol, ())
    if len(producers) != 1 or len(consumers) != 1:
        return _report(
            ExecutionPathClassification.INSUFFICIENT_EVIDENCE,
            producer_symbol,
            consumer_symbol,
            scope,
            limitations=("SYMBOL_DEFINITION_NOT_UNIQUE",),
        )
    producer, consumer = producers[0], consumers[0]
    traces = _find_traces(documents, index, producer_symbol, consumer_symbol)
    trace = traces[0] if len(traces) == 1 else None
    producer_evidence = _producer_evidence(
        producer, trace.mapping_key if trace is not None else None
    )
    produced = (
        _Domain(
            producer_evidence.domain.kind,
            producer_evidence.domain.value,
            producer_evidence.domain.description,
            producer_evidence.domain.line,
            producer_evidence.domain.subject,
        )
        if producer_evidence.domain is not None
        else None
    )
    required = _consumer_requirement(
        consumer, trace.destination_parameter if trace is not None else None
    )
    consumer_candidate = _consumer_has_precondition_candidate(
        consumer, trace.destination_parameter if trace is not None else None
    )
    if trace is not None and required is None and not consumer_candidate:
        diagnostics = []
        if produced is None:
            diagnostics.append(
                "PRODUCER_ORIGIN_DISCOVERED_DOMAIN_UNKNOWN"
                if producer_evidence.origin is not None
                and producer_evidence.field_present_on_success
                else "PRODUCER_GUARANTEE_NOT_DISCOVERABLE"
            )
        diagnostics.append("NO_COMPARABLE_CONSUMER_CONTRACT")
        origin_references = (
            producer_evidence.origin.variant_evidence_refs
            if producer_evidence.origin is not None
            else ()
        )
        return _report(
            ExecutionPathClassification.PATH_PROVEN_NO_COMPARABLE_CONTRACT,
            producer_symbol,
            consumer_symbol,
            scope,
            path=trace.path,
            references=tuple(dict.fromkeys((*origin_references, *trace.evidence_references))),
            limitations=tuple(diagnostics),
        )
    if produced is None or required is None or len(traces) != 1:
        missing = []
        if produced is None:
            missing.append(
                "PRODUCER_GUARD_FACT_DISCOVERED_NOT_COMPARABLE"
                if producer_evidence.guard_fact_discovered_not_comparable
                else (
                    "PRODUCER_ORIGIN_DISCOVERED_DOMAIN_UNKNOWN"
                    if producer_evidence.origin is not None
                    and producer_evidence.field_present_on_success
                    else "PRODUCER_GUARANTEE_NOT_DISCOVERABLE"
                )
            )
        if required is None: missing.append("CONSUMER_PRECONDITION_NOT_DISCOVERABLE")
        if len(traces) == 0: missing.append("NO_EXECUTABLE_PATH")
        if len(traces) > 1: missing.append("EXECUTABLE_PATH_NOT_UNIQUE")
        return _report(
            ExecutionPathClassification.INSUFFICIENT_EVIDENCE,
            producer_symbol,
            consumer_symbol,
            scope,
            path=traces[0].path if len(traces) == 1 else (),
            references=traces[0].evidence_references if len(traces) == 1 else (),
            limitations=tuple(missing),
        )
    assert trace is not None
    current = produced
    for intermediate in trace.transformations:
        definitions = index.get(intermediate, ())
        if len(definitions) != 1 or (transition := _returned_domain(definitions[0])) is None:
            return _report(
                ExecutionPathClassification.POTENTIAL_MISMATCH,
                producer_symbol,
                consumer_symbol,
                scope,
                path=trace.path,
                limitations=("INTERMEDIATE_TRANSFORMATION_NOT_DISCOVERABLE",),
            )
        current = transition
    comparable = True
    if required.kind == "truthy":
        if current.kind == "truthy":
            compatible = True
        elif current.kind == "literal":
            try:
                compatible = bool(ast.literal_eval(current.value))
            except (SyntaxError, ValueError):
                compatible = False
        else:
            compatible = False
    elif required.kind == "literal" and current.kind == "truthy":
        comparable = False
        compatible = False
    elif required.kind == "predicate":
        compatible = False
    else:
        compatible = current.kind == required.kind and current.value == required.value
    references = tuple(dict.fromkeys((
        *(producer_evidence.domain.supporting_evidence_refs if producer_evidence.domain else ()),
        f"{producer.path}:{produced.line}",
        f"{trace.document}:{trace.line}",
        f"{consumer.path}:{required.line}",
    )))
    if compatible:
        return _report(
            ExecutionPathClassification.NO_MISMATCH,
            producer_symbol,
            consumer_symbol,
            scope,
            path=trace.path,
            references=references,
        )
    if not comparable:
        return _report(
            ExecutionPathClassification.INSUFFICIENT_EVIDENCE,
            producer_symbol,
            consumer_symbol,
            scope,
            path=trace.path,
            references=references,
            limitations=("PRODUCER_GUARANTEE_NOT_COMPARABLE",),
        )
    confirmed = current.kind in {"literal", "unconstrained"}
    classification = (
        ExecutionPathClassification.CONFIRMED_MISMATCH
        if confirmed
        else ExecutionPathClassification.POTENTIAL_MISMATCH
    )
    finding = ExecutionPathFinding(
        producer_symbol,
        produced.description,
        consumer_symbol,
        required.description,
        trace.path,
        f"The produced domain ({current.description}) does not guarantee {required.description}.",
        f"A reachable call passes {current.description} to {consumer_symbol}.",
        ExecutionPathSeverity.HIGH if confirmed else ExecutionPathSeverity.MEDIUM,
        references,
    )
    return _report(
        classification,
        producer_symbol,
        consumer_symbol,
        scope,
        path=trace.path,
        findings=(finding,),
        references=references,
    )


def run_execution_path_review(
    target: Any,
    producer_symbol: Any,
    consumer_symbol: Any,
    *,
    include_paths: tuple[str, ...] = (),
    mission: str | None = None,
) -> SkillExecutionResult:
    report = review_execution_path(
        target,
        producer_symbol,
        consumer_symbol,
        include_paths=include_paths,
        mission=mission,
    )
    findings = report.classification in {
        ExecutionPathClassification.CONFIRMED_MISMATCH,
        ExecutionPathClassification.POTENTIAL_MISMATCH,
    }
    insufficient = report.classification is ExecutionPathClassification.INSUFFICIENT_EVIDENCE
    status = (
        SkillExecutionStatus.COMPLETED_WITH_FINDINGS
        if findings
        else SkillExecutionStatus.COMPLETED_WITH_INSUFFICIENT_EVIDENCE
        if insufficient
        else SkillExecutionStatus.PASSED
    )
    evidence = SkillExecutionEvidence(
        "execution_path_review",
        Status.WARNING if findings or insufficient else Status.OK,
        "Execution path review completed.",
        report,
        report.classification.value,
    )
    return SkillExecutionResult("execution-path-review", status, 3 if findings or insufficient else 0, (evidence,))
