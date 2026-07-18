from governor import Governor
from models import ActionRequest


def test_external_email_is_r3_and_requires_human_gate() -> None:
    decision = Governor().classify(
        ActionRequest(
            action_type="external_email_send",
            destination="person@example.test",
            content="Synthetic draft",
        )
    )
    assert decision.risk_class == "R3"
    assert decision.disposition == "HUMAN_GATE_REQUIRED"
    assert decision.human_gate_required is True


def test_payments_and_medical_are_blocked_by_default() -> None:
    governor = Governor()
    for domain in ("payments", "medical"):
        decision = governor.classify(
            ActionRequest(
                action_type="review",
                destination="internal",
                content="Synthetic task",
                external=False,
                domain=domain,
            )
        )
        assert decision.risk_class == "R5"
        assert decision.disposition == "BLOCKED_BY_POLICY"


def test_internal_draft_is_lower_risk() -> None:
    decision = Governor().classify(
        ActionRequest(
            action_type="draft",
            destination="internal",
            content="Synthetic note",
            external=False,
        )
    )
    assert decision.risk_class == "R1"
    assert decision.human_gate_required is False

