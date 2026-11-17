"""Hermetic historical controls for HERMES-0025 AC-32–AC-35."""

from dataclasses import asdict
import json

from hermes_ops.skills.controlled_reader import SourceDocument
from hermes_ops.skills.state_guard_effect_models import (
    StateBindingRequest,
    StateGuardEffectClassification,
    StateGuardEffectFindingKind,
    StateGuardEffectReachability,
    StateGuardEffectReviewRequest,
)
from hermes_ops.skills.state_guard_effect_review import review_state_guard_effect_documents


LOGICAL_PATH = "services/whatsapp_document_batch_service.py"
BUGGY_SOURCE = '''
def handle_confirm_cancellation(active_batch):
    status = active_batch["status"]
    if status not in {"awaiting_cancellation_confirmation"}:
        return False
    cancel_batch(active_batch)
    return True
'''
FIXED_SOURCE = '''
def handle_confirm_cancellation(active_batch):
    status = active_batch["status"]
    if status not in {"awaiting_cancellation_confirmation", "awaiting_client_type"}:
        return False
    cancel_batch(active_batch)
    return True
'''


def _historical_document(source: str) -> SourceDocument:
    return SourceDocument(LOGICAL_PATH, source, len(source.encode("utf-8")))


def test_same_blind_request_distinguishes_historical_buggy_and_fixed_snapshots() -> None:
    """Spec: HERMES-0025 / AC-32–AC-35; HERMES-0026 / AC-20–AC-24."""
    request = StateGuardEffectReviewRequest(
        operation_symbol="handle_confirm_cancellation",
        state_binding=StateBindingRequest("active_batch", "status"),
        input_state_literal="awaiting_client_type",
        expected_effect_symbol="cancel_batch",
        structural_scope=(LOGICAL_PATH,),
    )
    serialized_request_before = json.dumps(asdict(request), sort_keys=True)

    buggy = review_state_guard_effect_documents((_historical_document(BUGGY_SOURCE),), request)
    fixed = review_state_guard_effect_documents((_historical_document(FIXED_SOURCE),), request)

    assert json.dumps(asdict(request), sort_keys=True) == serialized_request_before
    assert buggy.classification is StateGuardEffectClassification.CONFIRMED_CONTRACT_MISMATCH
    assert buggy.reachability is StateGuardEffectReachability.CONFIRMED
    assert len(buggy.findings) == 1
    assert buggy.findings[0].kind is StateGuardEffectFindingKind.STATE_EFFECT_COVERAGE_MISMATCH
    assert fixed.classification is StateGuardEffectClassification.CONTRACT_STRUCTURALLY_ALIGNED
    assert fixed.reachability is StateGuardEffectReachability.CONFIRMED
    assert fixed.findings == ()
