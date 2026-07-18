"""Human correction and approval boundary."""

from __future__ import annotations

from typing import Any

from claim_guard import ClaimGuard
from evidence import EvidenceLedger, sha256_hex
from models import ClaimReview, DraftArtifact, RiskDecision


class HumanGateError(ValueError):
    pass


class HumanGate:
    def __init__(self, claim_guard: ClaimGuard, ledger: EvidenceLedger) -> None:
        self.claim_guard = claim_guard
        self.ledger = ledger

    def correct_and_approve(
        self,
        *,
        flow_id: str,
        original: DraftArtifact,
        corrected_text: str,
        risk: RiskDecision,
        actor_id: str,
    ) -> tuple[ClaimReview, dict[str, Any]]:
        corrected_text = corrected_text.strip()
        actor_id = actor_id.strip()
        if not corrected_text:
            raise HumanGateError("Corrected text cannot be empty")
        if not actor_id:
            raise HumanGateError("A human actor identifier is required")
        if corrected_text == original.text.strip():
            raise HumanGateError("Blocked text must be corrected before approval")
        if not risk.human_gate_required:
            raise HumanGateError("This demo path expects an R3 human gate")

        review = self.claim_guard.inspect(corrected_text)
        if review.blocked:
            raise HumanGateError("Corrected text still contains a blocking claim")

        payload = {
            "input": original.text,
            "input_hash": sha256_hex(original.text.encode("utf-8")),
            "corrected_output": corrected_text,
            "corrected_output_hash": sha256_hex(corrected_text.encode("utf-8")),
            "risk_class": risk.risk_class,
            "human_gate": "approved_after_correction",
            "actor_identity_scope": "self_asserted_demo_actor",
        }
        record = self.ledger.append(
            flow_id=flow_id,
            event_type="HUMAN_APPROVAL",
            actor_id=actor_id,
            decision="APPROVED_AFTER_CORRECTION",
            artifact_text=corrected_text,
            payload=payload,
        )
        return review, record

