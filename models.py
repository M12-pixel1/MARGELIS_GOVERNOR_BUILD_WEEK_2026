"""Typed records shared by the isolated Build Week demo."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class DraftArtifact:
    text: str
    model: str
    mode: str
    response_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActionRequest:
    action_type: str
    destination: str
    content: str
    external: bool = True
    domain: str = "sales"


@dataclass(frozen=True)
class RiskDecision:
    risk_class: str
    disposition: str
    human_gate_required: bool
    reasons: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["reasons"] = list(self.reasons)
        return data


@dataclass(frozen=True)
class ClaimFinding:
    rule_id: str
    category: str
    severity: str
    excerpt: str
    rationale: str
    source: str = "deterministic"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClaimReview:
    blocked: bool
    findings: tuple[ClaimFinding, ...] = ()
    advisory_status: str = "not_requested"

    def as_dict(self) -> dict[str, Any]:
        return {
            "blocked": self.blocked,
            "findings": [finding.as_dict() for finding in self.findings],
            "advisory_status": self.advisory_status,
        }


@dataclass(frozen=True)
class EvalResult:
    case_id: str
    name: str
    passed: bool
    details: tuple[str, ...] = ()
    is_generated: bool = False

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["details"] = list(self.details)
        return data


@dataclass
class FlowState:
    flow_id: str
    stage: str
    draft: DraftArtifact
    risk: RiskDecision
    claim_review: ClaimReview
    corrected_text: str | None = None
    approval_record: dict[str, Any] | None = None
    correction_case: dict[str, Any] | None = None
    regression: dict[str, Any] | None = None
    events: list[dict[str, Any]] = field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "stage": self.stage,
            "draft": self.draft.as_dict(),
            "risk": self.risk.as_dict(),
            "claim_review": self.claim_review.as_dict(),
            "corrected_text": self.corrected_text,
            "approval_record": self.approval_record,
            "correction_case": self.correction_case,
            "regression": self.regression,
            "events": self.events,
        }

