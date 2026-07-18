import copy
from datetime import UTC, datetime

from evidence import Ed25519Signer, EvidenceLedger


def fixed_clock() -> datetime:
    return datetime(2026, 7, 18, 9, 30, tzinfo=UTC)


def build_ledger(tmp_path):
    signer = Ed25519Signer.load_or_create(tmp_path / "keys" / "key.pem")
    return EvidenceLedger(tmp_path, signer, clock=fixed_clock)


def test_signed_chain_verifies_and_tampering_fails(tmp_path) -> None:
    ledger = build_ledger(tmp_path)
    flow_id = "flow-evidence-test"
    ledger.append(
        flow_id=flow_id,
        event_type="DRAFT_CREATED",
        actor_id="agent",
        decision="PROPOSED_NOT_SENT",
        artifact_text="synthetic draft",
        payload={"artifact_text": "synthetic draft"},
    )
    ledger.append(
        flow_id=flow_id,
        event_type="HUMAN_APPROVAL",
        actor_id="human",
        decision="APPROVED_AFTER_CORRECTION",
        artifact_text="corrected synthetic draft",
        payload={"corrected_output": "corrected synthetic draft"},
    )

    records = ledger.read(flow_id)
    verified = ledger.verify_records(records)
    assert verified["valid"] is True
    assert verified["record_count"] == 2

    payload_tamper = copy.deepcopy(records)
    payload_tamper[0]["payload"]["artifact_text"] = "edited"
    assert ledger.verify_records(payload_tamper)["valid"] is False

    link_tamper = copy.deepcopy(records)
    link_tamper[1]["prev_hash"] = "0" * 64
    assert ledger.verify_records(link_tamper)["valid"] is False

    signature_tamper = copy.deepcopy(records)
    signature_tamper[1]["signature"] = signature_tamper[0]["signature"]
    assert ledger.verify_records(signature_tamper)["valid"] is False


def test_key_is_reused_without_entering_repo_data(tmp_path) -> None:
    path = tmp_path / "keys" / "key.pem"
    signer_one = Ed25519Signer.load_or_create(path)
    signer_two = Ed25519Signer.load_or_create(path)
    assert signer_one.key_id == signer_two.key_id
    assert path.stat().st_mode & 0o777 == 0o600


def test_tamper_preview_preserves_real_ledger(tmp_path) -> None:
    ledger = build_ledger(tmp_path)
    ledger.append(
        flow_id="preview",
        event_type="TEST",
        actor_id="system",
        decision="RECORDED",
        artifact_text="artifact",
        payload={"value": "original"},
    )
    result = ledger.tamper_preview("preview")
    assert result["before"]["valid"] is True
    assert result["after"]["valid"] is False
    assert ledger.verify("preview")["valid"] is True

