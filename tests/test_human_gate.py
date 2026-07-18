from pathlib import Path

import pytest

from agent import FixtureAgent, SYNTHETIC_SAFE_SENTENCE
from claim_guard import ClaimGuard
from evidence import Ed25519Signer, EvidenceLedger
from governor import Governor
from human_gate import HumanGate, HumanGateError
from models import ActionRequest


def setup_gate(tmp_path: Path):
    guard = ClaimGuard()
    ledger = EvidenceLedger(
        tmp_path, Ed25519Signer.load_or_create(tmp_path / "key" / "demo.pem")
    )
    return guard, HumanGate(guard, ledger), ledger


def r3_decision(text: str):
    return Governor().classify(
        ActionRequest(
            action_type="external_email_send",
            destination="person@example.test",
            content=text,
        )
    )


def test_unchanged_blocked_draft_cannot_be_approved(tmp_path) -> None:
    _, gate, _ = setup_gate(tmp_path)
    draft = FixtureAgent().draft()
    with pytest.raises(HumanGateError, match="corrected"):
        gate.correct_and_approve(
            flow_id="flow",
            original=draft,
            corrected_text=draft.text,
            risk=r3_decision(draft.text),
            actor_id="human",
        )


def test_still_unsafe_correction_cannot_be_approved(tmp_path) -> None:
    _, gate, _ = setup_gate(tmp_path)
    draft = FixtureAgent().draft()
    with pytest.raises(HumanGateError, match="blocking"):
        gate.correct_and_approve(
            flow_id="flow",
            original=draft,
            corrected_text=draft.text + " Another unsupported change of 84%.",
            risk=r3_decision(draft.text),
            actor_id="human",
        )


def test_corrected_draft_is_signed(tmp_path) -> None:
    guard, gate, ledger = setup_gate(tmp_path)
    draft = FixtureAgent().draft()
    review = guard.inspect(draft.text)
    corrected = draft.text
    for finding in review.findings:
        corrected = corrected.replace(finding.excerpt, SYNTHETIC_SAFE_SENTENCE)
    corrected_review, record = gate.correct_and_approve(
        flow_id="flow",
        original=draft,
        corrected_text=corrected,
        risk=r3_decision(draft.text),
        actor_id="human",
    )
    assert corrected_review.blocked is False
    assert record["event_type"] == "HUMAN_APPROVAL"
    assert ledger.verify("flow")["valid"] is True

