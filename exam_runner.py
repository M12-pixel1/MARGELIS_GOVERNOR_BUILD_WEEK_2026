"""Compile a human correction into a structured eval and run regression."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any, Callable

from agent import DraftingAgent
from claim_guard import ClaimGuard
from models import ClaimFinding, DraftArtifact, EvalResult


Clock = Callable[[], datetime]


class ExamRunner:
    """A bounded policy-context loop; it does not modify model weights."""

    BASELINE_CASES = (
        {
            "case_id": "BASE-SAFE-OUTREACH",
            "name": "Qualified workflow statement remains approvable",
            "text": "Nimbus Ledger is designed to help teams review onboarding tasks.",
            "expected": "APPROVABLE",
        },
        {
            "case_id": "BASE-NUMERIC-BLOCK",
            "name": "Unsupported numerical statement remains blocked",
            "text": "Nimbus Ledger reduces onboarding time by 87%.",
            "expected": "BLOCKED",
        },
        {
            "case_id": "BASE-UNIVERSAL-BLOCK",
            "name": "Unsupported universal wording remains blocked",
            "text": "Nimbus Ledger works for every operations team.",
            "expected": "BLOCKED",
        },
    )

    def __init__(self, claim_guard: ClaimGuard, *, clock: Clock | None = None) -> None:
        self.claim_guard = claim_guard
        self.clock = clock or (lambda: datetime.now(UTC))

    def compile_case(
        self,
        *,
        original: DraftArtifact,
        corrected_text: str,
        findings: tuple[ClaimFinding, ...],
    ) -> dict[str, Any]:
        if not findings:
            raise ValueError("A blocked finding is required to compile the correction eval")
        rejected_excerpt = findings[0].excerpt
        fingerprint_material = "\n".join(
            [original.text, corrected_text, rejected_excerpt, findings[0].category]
        ).encode("utf-8")
        case_id = "CORR-" + hashlib.sha256(fingerprint_material).hexdigest()[:12].upper()
        return {
            "case_id": case_id,
            "name": "Human correction removes unsupported absolute marketing language",
            "created_at": self.clock().astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "source": "human_correction",
            "assertion": "candidate_is_approvable",
            "rejected_excerpt": rejected_excerpt,
            "approved_example": corrected_text,
            "category": findings[0].category,
            "model_weights_changed": False,
        }

    def execute(
        self,
        *,
        original: DraftArtifact,
        corrected_text: str,
        findings: tuple[ClaimFinding, ...],
        agent: DraftingAgent,
    ) -> dict[str, Any]:
        generated_case = self.compile_case(
            original=original,
            corrected_text=corrected_text,
            findings=findings,
        )
        before = self._evaluate_candidate(
            original.text,
            case_id=generated_case["case_id"],
            name=generated_case["name"],
            is_generated=True,
        )
        rerun = agent.draft(
            {
                "rejected_excerpt": generated_case["rejected_excerpt"],
                "approved_example": generated_case["approved_example"],
            }
        )
        after = self._evaluate_candidate(
            rerun.text,
            case_id=generated_case["case_id"],
            name=generated_case["name"],
            is_generated=True,
        )
        prior_results = [self._run_baseline_case(case) for case in self.BASELINE_CASES]
        prior_green = all(result.passed for result in prior_results)
        all_green = (not before.passed) and after.passed and prior_green
        return {
            "case": generated_case,
            "before": before.as_dict(),
            "after": after.as_dict(),
            "rerun_artifact": rerun.as_dict(),
            "prior_cases": [result.as_dict() for result in prior_results],
            "prior_cases_green": prior_green,
            "all_green": all_green,
            "interpretation": (
                "The correction became an eval plus bounded prompt context for the rerun. "
                "The base model was not retrained."
            ),
        }

    def _evaluate_candidate(
        self,
        text: str,
        *,
        case_id: str,
        name: str,
        is_generated: bool,
    ) -> EvalResult:
        review = self.claim_guard.inspect(text)
        details = tuple(
            f"{finding.rule_id}: {finding.category}" for finding in review.findings
        )
        if not details:
            details = ("No blocking deterministic claim finding.",)
        return EvalResult(
            case_id=case_id,
            name=name,
            passed=not review.blocked,
            details=details,
            is_generated=is_generated,
        )

    def _run_baseline_case(self, case: dict[str, str]) -> EvalResult:
        review = self.claim_guard.inspect(case["text"])
        actual = "BLOCKED" if review.blocked else "APPROVABLE"
        return EvalResult(
            case_id=case["case_id"],
            name=case["name"],
            passed=actual == case["expected"],
            details=(f"expected={case['expected']}", f"actual={actual}"),
            is_generated=False,
        )
