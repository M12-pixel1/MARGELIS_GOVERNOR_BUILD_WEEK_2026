"""Append-only, Ed25519-signed evidence records with chain verification."""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any, Callable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


Clock = Callable[[], datetime]


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_hex(value: Any) -> str:
    data = value if isinstance(value, bytes) else canonical_json(value)
    return hashlib.sha256(data).hexdigest()


class Ed25519Signer:
    """Local demo signer. The public key attests integrity under this key."""

    def __init__(self, private_key: Ed25519PrivateKey) -> None:
        self._private_key = private_key
        public_bytes = self._private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        self.public_key_b64 = base64.b64encode(public_bytes).decode("ascii")
        self.key_id = hashlib.sha256(public_bytes).hexdigest()[:16]

    @classmethod
    def load_or_create(cls, path: Path) -> "Ed25519Signer":
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            private_key = serialization.load_pem_private_key(path.read_bytes(), password=None)
            if not isinstance(private_key, Ed25519PrivateKey):
                raise ValueError("Configured signing key is not Ed25519")
            return cls(private_key)

        private_key = Ed25519PrivateKey.generate()
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        path.write_bytes(pem)
        os.chmod(path, 0o600)
        return cls(private_key)

    def sign_hash(self, digest_hex: str) -> str:
        signature = self._private_key.sign(bytes.fromhex(digest_hex))
        return base64.b64encode(signature).decode("ascii")


class EvidenceLedger:
    """One isolated JSONL chain per demo flow."""

    def __init__(
        self,
        data_dir: Path,
        signer: Ed25519Signer,
        *,
        clock: Clock | None = None,
    ) -> None:
        self.data_dir = data_dir
        self.signer = signer
        self.clock = clock or (lambda: datetime.now(UTC))
        self._lock = Lock()

    def path_for(self, flow_id: str) -> Path:
        return self.data_dir / "flows" / flow_id / "evidence.jsonl"

    def append(
        self,
        *,
        flow_id: str,
        event_type: str,
        actor_id: str,
        decision: str,
        artifact_text: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        with self._lock:
            records = self.read(flow_id)
            previous_hash = records[-1]["record_hash"] if records else None
            seq = len(records) + 1
            timestamp = self.clock().astimezone(UTC).isoformat().replace("+00:00", "Z")
            core = {
                "schema_version": "1.0",
                "flow_id": flow_id,
                "seq": seq,
                "event_type": event_type,
                "timestamp_utc": timestamp,
                "actor_id": actor_id,
                "decision": decision,
                "artifact_hash": sha256_hex(artifact_text.encode("utf-8")),
                "payload_hash": sha256_hex(payload),
                "prev_hash": previous_hash,
                "key_id": self.signer.key_id,
            }
            record_hash = sha256_hex(core)
            record = {
                **core,
                "payload": payload,
                "record_hash": record_hash,
                "signature": self.signer.sign_hash(record_hash),
                "public_key": self.signer.public_key_b64,
            }
            path = self.path_for(flow_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            return record

    def read(self, flow_id: str) -> list[dict[str, Any]]:
        path = self.path_for(flow_id)
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
        return records

    def verify(self, flow_id: str) -> dict[str, Any]:
        return self.verify_records(self.read(flow_id))

    @staticmethod
    def verify_records(records: list[dict[str, Any]]) -> dict[str, Any]:
        errors: list[str] = []
        previous_hash: str | None = None
        expected_public_key: str | None = None
        for index, record in enumerate(records, start=1):
            try:
                if record.get("seq") != index:
                    errors.append(f"record {index}: sequence mismatch")
                if record.get("prev_hash") != previous_hash:
                    errors.append(f"record {index}: previous hash mismatch")
                if sha256_hex(record.get("payload")) != record.get("payload_hash"):
                    errors.append(f"record {index}: payload hash mismatch")

                core_keys = (
                    "schema_version",
                    "flow_id",
                    "seq",
                    "event_type",
                    "timestamp_utc",
                    "actor_id",
                    "decision",
                    "artifact_hash",
                    "payload_hash",
                    "prev_hash",
                    "key_id",
                )
                core = {key: record.get(key) for key in core_keys}
                recomputed_hash = sha256_hex(core)
                if recomputed_hash != record.get("record_hash"):
                    errors.append(f"record {index}: record hash mismatch")

                public_key_b64 = str(record.get("public_key", ""))
                if expected_public_key is None:
                    expected_public_key = public_key_b64
                elif public_key_b64 != expected_public_key:
                    errors.append(f"record {index}: signing key changed")
                public_bytes = base64.b64decode(public_key_b64, validate=True)
                key_id = hashlib.sha256(public_bytes).hexdigest()[:16]
                if key_id != record.get("key_id"):
                    errors.append(f"record {index}: key identifier mismatch")
                public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
                signature = base64.b64decode(str(record.get("signature", "")), validate=True)
                public_key.verify(signature, bytes.fromhex(str(record.get("record_hash", ""))))
                previous_hash = str(record.get("record_hash"))
            except (KeyError, TypeError, ValueError, InvalidSignature) as exc:
                errors.append(f"record {index}: signature or format error ({type(exc).__name__})")

        return {
            "valid": bool(records) and not errors,
            "record_count": len(records),
            "chain_head": previous_hash,
            "errors": errors,
        }

    def tamper_preview(self, flow_id: str) -> dict[str, Any]:
        records = self.read(flow_id)
        before = self.verify_records(records)
        changed = copy.deepcopy(records)
        if changed:
            changed[0]["payload"]["tampered"] = True
        after = self.verify_records(changed)
        return {"before": before, "after": after}

