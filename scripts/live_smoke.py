"""Opt-in end-to-end smoke check against the configured live GPT-5.6 model."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from agent import OpenAIResponsesAgent, SYNTHETIC_SAFE_SENTENCE
from demo_service import DemoService


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required for the live smoke check")

    agent = OpenAIResponsesAgent.from_env()
    with tempfile.TemporaryDirectory(prefix="margelis-governor-live-") as directory:
        service = DemoService(data_dir=Path(directory), agent=agent)
        flow = service.start_flow()
        if flow["draft"]["mode"] != "live":
            raise SystemExit("FAIL: draft did not use live mode")
        if flow["stage"] != "BLOCKED":
            raise SystemExit("FAIL: first live draft did not reach the expected Claim Guard stop")

        corrected = flow["draft"]["text"]
        for finding in flow["claim_review"]["findings"]:
            if finding["severity"] == "block":
                corrected = corrected.replace(finding["excerpt"], SYNTHETIC_SAFE_SENTENCE)
        flow = service.correct_and_approve(
            flow["flow_id"],
            corrected_text=corrected,
            actor_id="Live smoke human gate",
        )
        flow = service.run_regression(flow["flow_id"])
        verification = service.verify(flow["flow_id"])
        if flow["stage"] != "REGRESSION_PASSED" or not verification["valid"]:
            raise SystemExit("FAIL: live rerun or Evidence Passport verification failed")
        print(
            "PASS: live GPT draft blocked, human correction signed, fresh rerun passed, "
            "prior evals green, Evidence Passport verified"
        )


if __name__ == "__main__":
    main()

