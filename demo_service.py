"""Stateful orchestration for the one Build Week demonstration flow."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from threading import Lock
from typing import Any

from agent import DraftingAgent, build_agent_from_env
from claim_guard import ClaimGuard
from evidence import Ed25519Signer, EvidenceLedger
from exam_runner import ExamRunner
from governor import Governor
from human_gate import HumanGate
from models import ActionRequest, FlowState


class FlowError(RuntimeError):
    pass


class FlowNotFound(FlowError):
    pass


class DemoService:
    def __init__(
        self,
        *,
        data_dir: Path | None = None,
        agent: DraftingAgent | None = None,
    ) -> None:
        self.data_dir = data_dir or Path(os.environ.get("MARGELIS_DATA_DIR", ".demo-data"))
        self.agent = agent or build_agent_from_env()
        self.claim_guard = ClaimGuard()
        self.governor = Governor()
        signer = Ed25519Signer.load_or_create(self.data_dir / "signing" / "demo-key.pem")
        self.ledger = EvidenceLedger(self.data_dir, signer)
        self.human_gate = HumanGate(self.claim_guard, self.ledger)
        self.exam_runner = ExamRunner(self.claim_guard)
        self.flows: dict[str, FlowState] = {}
        self._lock = Lock()

    def start_flow(self) -> dict[str, Any]:
        flow_id = str(uuid.uuid4())
        draft = self.agent.draft()
        action = ActionRequest(
            action_type="external_email_send",
            destination="alex@aster-retail.example",
            content=draft.text,
            external=True,
            domain="sales",
        )
        risk = self.governor.classify(action)
        claim_review = self.claim_guard.inspect(
            draft.text,
            advisory_checker=self.agent.advisory_claim_review,
        )
        stage = "BLOCKED" if claim_review.blocked else "REVIEW_REQUIRED"
        flow = FlowState(
            flow_id=flow_id,
            stage=stage,
            draft=draft,
            risk=risk,
            claim_review=claim_review,
        )

        self._record_event(
            flow,
            event_type="DRAFT_CREATED",
            actor_id=f"governed-agent:{draft.model}",
            decision="PROPOSED_NOT_SENT",
            artifact_text=draft.text,
            payload={
                "artifact_text": draft.text,
                "model": draft.model,
                "mode": draft.mode,
                "response_id": draft.response_id,
                "synthetic_destination": action.destination,
            },
        )
        self._record_event(
            flow,
            event_type="RISK_CLASSIFIED",
            actor_id="deterministic-governor",
            decision=risk.disposition,
            artifact_text=draft.text,
            payload=risk.as_dict(),
        )
        self._record_event(
            flow,
            event_type="CLAIM_REVIEWED",
            actor_id="claim-guard",
            decision="STOPPED" if claim_review.blocked else "REVIEW_REQUIRED",
            artifact_text=draft.text,
            payload=claim_review.as_dict(),
        )
        with self._lock:
            self.flows[flow_id] = flow
        return flow.public_dict()

    def correct_and_approve(
        self,
        flow_id: str,
        *,
        corrected_text: str,
        actor_id: str,
    ) -> dict[str, Any]:
        flow = self._get(flow_id)
        if flow.stage != "BLOCKED":
            raise FlowError(f"Correction is not allowed from stage {flow.stage}")
        corrected_review, record = self.human_gate.correct_and_approve(
            flow_id=flow.flow_id,
            original=flow.draft,
            corrected_text=corrected_text,
            risk=flow.risk,
            actor_id=actor_id,
        )
        flow.corrected_text = corrected_text.strip()
        flow.approval_record = self._record_summary(record)
        flow.stage = "SIGNED"
        flow.events.append(flow.approval_record)
        flow.events[-1]["corrected_review"] = corrected_review.as_dict()
        return flow.public_dict()

    def run_regression(self, flow_id: str) -> dict[str, Any]:
        flow = self._get(flow_id)
        if flow.stage not in {"SIGNED", "REGRESSION_FAILED"}:
            raise FlowError(f"Regression is not allowed from stage {flow.stage}")
        if not flow.corrected_text:
            raise FlowError("A human correction is required before regression")
        report = self.exam_runner.execute(
            original=flow.draft,
            corrected_text=flow.corrected_text,
            findings=flow.claim_review.findings,
            agent=self.agent,
        )
        flow.correction_case = report["case"]
        flow.regression = report
        self._record_event(
            flow,
            event_type="EVAL_CREATED",
            actor_id="exam-runner",
            decision="STRUCTURED_EVAL_STORED",
            artifact_text=str(report["case"]),
            payload=report["case"],
        )
        self._record_event(
            flow,
            event_type="REGRESSION_RUN",
            actor_id="exam-runner",
            decision="PASS" if report["all_green"] else "FAIL",
            artifact_text=report["rerun_artifact"]["text"],
            payload={
                "before": report["before"],
                "after": report["after"],
                "prior_cases": report["prior_cases"],
                "all_green": report["all_green"],
                "rerun_model": report["rerun_artifact"]["model"],
                "rerun_mode": report["rerun_artifact"]["mode"],
                "rerun_response_id": report["rerun_artifact"]["response_id"],
            },
        )
        flow.stage = "REGRESSION_PASSED" if report["all_green"] else "REGRESSION_FAILED"
        return flow.public_dict()

    def get_flow(self, flow_id: str) -> dict[str, Any]:
        return self._get(flow_id).public_dict()

    def passport(self, flow_id: str) -> dict[str, Any]:
        self._get(flow_id)
        records = self.ledger.read(flow_id)
        return {"records": records, "verification": self.ledger.verify_records(records)}

    def verify(self, flow_id: str) -> dict[str, Any]:
        self._get(flow_id)
        return self.ledger.verify(flow_id)

    def tamper_check(self, flow_id: str) -> dict[str, Any]:
        self._get(flow_id)
        return self.ledger.tamper_preview(flow_id)

    def _get(self, flow_id: str) -> FlowState:
        try:
            return self.flows[flow_id]
        except KeyError as exc:
            raise FlowNotFound(f"Unknown flow: {flow_id}") from exc

    def _record_event(
        self,
        flow: FlowState,
        *,
        event_type: str,
        actor_id: str,
        decision: str,
        artifact_text: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        record = self.ledger.append(
            flow_id=flow.flow_id,
            event_type=event_type,
            actor_id=actor_id,
            decision=decision,
            artifact_text=artifact_text,
            payload=payload,
        )
        summary = self._record_summary(record)
        flow.events.append(summary)
        return summary

    @staticmethod
    def _record_summary(record: dict[str, Any]) -> dict[str, Any]:
        return {
            "seq": record["seq"],
            "event_type": record["event_type"],
            "actor_id": record["actor_id"],
            "decision": record["decision"],
            "timestamp_utc": record["timestamp_utc"],
            "record_hash": record["record_hash"],
            "prev_hash": record["prev_hash"],
            "key_id": record["key_id"],
            "signature": record["signature"],
        }

