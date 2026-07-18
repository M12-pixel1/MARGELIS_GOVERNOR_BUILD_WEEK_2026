from datetime import UTC, datetime

from agent import FixtureAgent, SYNTHETIC_SAFE_SENTENCE
from claim_guard import ClaimGuard
from exam_runner import ExamRunner


def fixed_clock() -> datetime:
    return datetime(2026, 7, 18, 10, 0, tzinfo=UTC)


def test_correction_becomes_eval_that_fails_then_passes() -> None:
    guard = ClaimGuard()
    agent = FixtureAgent()
    original = agent.draft()
    original_review = guard.inspect(original.text)
    corrected = original.text
    for finding in original_review.findings:
        corrected = corrected.replace(finding.excerpt, SYNTHETIC_SAFE_SENTENCE)

    runner = ExamRunner(guard, clock=fixed_clock)
    report = runner.execute(
        original=original,
        corrected_text=corrected,
        findings=original_review.findings,
        agent=agent,
    )

    assert report["before"]["passed"] is False
    assert report["after"]["passed"] is True
    assert report["prior_cases_green"] is True
    assert report["all_green"] is True
    assert report["case"]["source"] == "human_correction"
    assert report["case"]["model_weights_changed"] is False
    assert report["rerun_artifact"]["mode"] == "fixture"


def test_generated_case_id_is_stable_and_not_executable_code() -> None:
    guard = ClaimGuard()
    original = FixtureAgent().draft()
    review = guard.inspect(original.text)
    corrected = original.text.replace(review.findings[0].excerpt, SYNTHETIC_SAFE_SENTENCE)
    runner = ExamRunner(guard, clock=fixed_clock)
    first = runner.compile_case(
        original=original, corrected_text=corrected, findings=review.findings
    )
    second = runner.compile_case(
        original=original, corrected_text=corrected, findings=review.findings
    )
    assert first["case_id"] == second["case_id"]
    assert set(first) == {
        "case_id",
        "name",
        "created_at",
        "source",
        "assertion",
        "rejected_excerpt",
        "approved_example",
        "category",
        "model_weights_changed",
    }

