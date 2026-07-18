"""Fail-closed claim checks with optional model advisory findings."""

from __future__ import annotations

import re
from collections.abc import Callable

from models import ClaimFinding, ClaimReview

AdvisoryChecker = Callable[[str], list[ClaimFinding]]


class ClaimGuard:
    """Block unsupported numerical or universal marketing statements."""

    _percentage = re.compile(r"(?<!\w)\d{1,3}(?:\.\d+)?%(?!\w)", re.IGNORECASE)
    _universal = re.compile(r"\b(?:all|always|every|never)\b", re.IGNORECASE)
    _evidence_marker = re.compile(r"(?:\[evidence:[^\]]+\]|source\s*:)", re.IGNORECASE)

    def inspect(
        self,
        text: str,
        *,
        supported_claims: tuple[str, ...] = (),
        advisory_checker: AdvisoryChecker | None = None,
    ) -> ClaimReview:
        findings: list[ClaimFinding] = []
        for sentence in self._sentences(text):
            has_percentage = bool(self._percentage.search(sentence))
            has_universal = bool(self._universal.search(sentence))
            has_evidence = bool(self._evidence_marker.search(sentence))
            explicitly_supported = any(
                supported.lower() in sentence.lower() for supported in supported_claims
            )

            if has_percentage and not (has_evidence or explicitly_supported):
                findings.append(
                    ClaimFinding(
                        rule_id="CG-NUMERIC-001",
                        category="UNSUPPORTED_NUMERIC_CLAIM",
                        severity="block",
                        excerpt=sentence,
                        rationale="A numerical marketing statement has no attached evidence reference.",
                    )
                )
            if has_universal and not (has_evidence or explicitly_supported):
                findings.append(
                    ClaimFinding(
                        rule_id="CG-ABSOLUTE-001",
                        category="UNSUPPORTED_ABSOLUTE_CLAIM",
                        severity="block",
                        excerpt=sentence,
                        rationale="Universal wording is unsupported in the supplied evidence set.",
                    )
                )

        advisory_status = "not_requested"
        if advisory_checker is not None:
            try:
                advisory_findings = advisory_checker(text)
                findings.extend(advisory_findings)
                advisory_status = "completed"
            except Exception as exc:  # advisory failure cannot weaken deterministic controls
                advisory_status = f"unavailable:{type(exc).__name__}"

        findings = self._deduplicate(findings)
        return ClaimReview(
            blocked=any(finding.severity == "block" for finding in findings),
            findings=tuple(findings),
            advisory_status=advisory_status,
        )

    @staticmethod
    def _sentences(text: str) -> list[str]:
        chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
        return [chunk.strip() for chunk in chunks if chunk.strip()]

    @staticmethod
    def _deduplicate(findings: list[ClaimFinding]) -> list[ClaimFinding]:
        seen: set[tuple[str, str]] = set()
        unique: list[ClaimFinding] = []
        for finding in findings:
            key = (finding.rule_id, finding.excerpt.casefold())
            if key not in seen:
                seen.add(key)
                unique.append(finding)
        return unique
