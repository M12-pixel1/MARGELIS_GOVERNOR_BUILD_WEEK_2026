from agent import FixtureAgent, SYNTHETIC_SAFE_SENTENCE
from demo_service import DemoService


def safe_correction(flow: dict) -> str:
    text = flow["draft"]["text"]
    for finding in flow["claim_review"]["findings"]:
        if finding["severity"] == "block":
            text = text.replace(finding["excerpt"], SYNTHETIC_SAFE_SENTENCE)
    return text


def test_full_hero_flow_is_reproducible(tmp_path) -> None:
    service = DemoService(data_dir=tmp_path, agent=FixtureAgent())
    flow = service.start_flow()
    assert flow["draft"]["mode"] == "fixture"
    assert flow["risk"]["risk_class"] == "R3"
    assert flow["claim_review"]["blocked"] is True
    assert flow["stage"] == "BLOCKED"

    flow = service.correct_and_approve(
        flow["flow_id"],
        corrected_text=safe_correction(flow),
        actor_id="Tomas — test human",
    )
    assert flow["stage"] == "SIGNED"
    assert flow["approval_record"]["signature"]

    flow = service.run_regression(flow["flow_id"])
    assert flow["stage"] == "REGRESSION_PASSED"
    assert flow["regression"]["before"]["passed"] is False
    assert flow["regression"]["after"]["passed"] is True
    assert flow["regression"]["prior_cases_green"] is True

    verified = service.verify(flow["flow_id"])
    assert verified["valid"] is True
    tamper = service.tamper_check(flow["flow_id"])
    assert tamper["before"]["valid"] is True
    assert tamper["after"]["valid"] is False


def test_flows_have_separate_chains(tmp_path) -> None:
    service = DemoService(data_dir=tmp_path, agent=FixtureAgent())
    one = service.start_flow()
    two = service.start_flow()
    assert one["flow_id"] != two["flow_id"]
    assert service.passport(one["flow_id"])["records"][0]["flow_id"] == one["flow_id"]
    assert service.passport(two["flow_id"])["records"][0]["flow_id"] == two["flow_id"]

