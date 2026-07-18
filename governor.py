"""Deterministic R0-R5 action classification for the demo."""

from __future__ import annotations

from models import ActionRequest, RiskDecision


class Governor:
    """Classify proposed actions without delegating authority to a model."""

    BLOCKED_DOMAINS = {"payments", "medical"}

    def classify(self, action: ActionRequest) -> RiskDecision:
        if action.domain in self.BLOCKED_DOMAINS:
            return RiskDecision(
                risk_class="R5",
                disposition="BLOCKED_BY_POLICY",
                human_gate_required=True,
                reasons=(f"{action.domain} actions are outside this demo's mandate",),
            )
        if action.external and action.action_type == "external_email_send":
            return RiskDecision(
                risk_class="R3",
                disposition="HUMAN_GATE_REQUIRED",
                human_gate_required=True,
                reasons=("proposed external communication", "reputational impact"),
            )
        if action.external:
            return RiskDecision(
                risk_class="R2",
                disposition="REVIEW_REQUIRED",
                human_gate_required=True,
                reasons=("external action",),
            )
        return RiskDecision(
            risk_class="R1",
            disposition="INTERNAL_ONLY",
            human_gate_required=False,
            reasons=("no external effect",),
        )

