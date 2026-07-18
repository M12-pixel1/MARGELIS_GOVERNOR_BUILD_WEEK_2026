from claim_guard import ClaimGuard
from models import ClaimFinding


def test_blocks_unsupported_numeric_and_universal_wording() -> None:
    review = ClaimGuard().inspect("The synthetic service reduces waiting time by 95% for every team.")
    assert review.blocked is True
    assert {item.rule_id for item in review.findings} == {
        "CG-NUMERIC-001",
        "CG-ABSOLUTE-001",
    }


def test_qualified_non_numeric_copy_is_clean() -> None:
    review = ClaimGuard().inspect(
        "The synthetic service is designed to help teams review onboarding workflows."
    )
    assert review.blocked is False
    assert review.findings == ()


def test_explicit_evidence_marker_allows_supported_sentence() -> None:
    review = ClaimGuard().inspect(
        "A synthetic benchmark measured an 18% change [evidence:demo-benchmark-01]."
    )
    assert review.blocked is False


def test_advisory_can_add_review_but_never_remove_deterministic_block() -> None:
    def advisory(_: str) -> list[ClaimFinding]:
        return [
            ClaimFinding(
                rule_id="ADVISORY",
                category="MODEL_ADVISORY",
                severity="review",
                excerpt="Synthetic review note",
                rationale="Additional review suggested.",
                source="test",
            )
        ]

    review = ClaimGuard().inspect(
        "The service improves results by 91%.", advisory_checker=advisory
    )
    assert review.blocked is True
    assert review.advisory_status == "completed"
    assert any(item.source == "test" for item in review.findings)


def test_advisory_failure_does_not_bypass_rule() -> None:
    def broken(_: str) -> list[ClaimFinding]:
        raise TimeoutError("synthetic timeout")

    review = ClaimGuard().inspect(
        "The service improves results by 91%.", advisory_checker=broken
    )
    assert review.blocked is True
    assert review.advisory_status == "unavailable:TimeoutError"
