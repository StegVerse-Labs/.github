#!/usr/bin/env python3
"""Verify exact HIL bytes after controlled sovereign receiver restart/replacement.

Consumes canonical browser observation evidence for the SAME submission, then
restarts only the receiver process identified by the HIL WorkerCoordinator
receipt. TV/TVC reconstruction authentication is consumed transiently from the
runtime environment and is never emitted, logged, or persisted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import time
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from workers.hil_sovereign_receiver_bridge import launch_receiver, verify_receiver

TASK_ID = "SHWP-HIL-SOVEREIGN-RECEIVER-001"
WORKER_RECEIPT_REL = Path("receipts/hil-sovereign-receiver") / f"{TASK_ID}.json"
OUTPUT_REL = Path("receipts/hil-sovereign-receiver/post-restart-reconstruction.latest.json")
OBSERVATION_SCHEMA = "stegverse.hil.canonical-observation-evidence/v1"
WORKER_SCHEMA = "stegverse.hil.sovereign-receiver-worker-receipt/v0.1"
RECEIPT_SCHEMA = "stegverse.hil.post-restart-reconstruction/v1"
EXPECTED_RECEIVER_SCHEMA = "HIL-RECEIVER-RECEIPT-v2"
CREDENTIAL_AUTHORITY = "TV/TVC"

JsonReader = Callable[[str, float], Mapping[str, Any]]
BytesReader = Callable[[str, str, float], tuple[bytes, Mapping[str, str]]]
Killer = Callable[[int], None]
Launcher = Callable[..., Any]
ReadyVerifier = Callable[[str], Mapping[str, Any]]


class PredicatePending(RuntimeError):
    pass


class ReconstructionFailure(RuntimeError):
    pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ReconstructionFailure(reason)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReconstructionFailure(f"json_object_required:{path}")
    return value


def _digest_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _parse_digest_uri(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
        raise ReconstructionFailure(f"{label}_invalid")
    digest = value[7:]
    if any(ch not in "0123456789abcdef" for ch in digest):
        raise ReconstructionFailure(f"{label}_invalid")
    return digest


def _validate_observation(value: Mapping[str, Any]) -> tuple[str, str, str]:
    _require(value.get("schema") == OBSERVATION_SCHEMA, "observation_schema_invalid")
    _require(value.get("state") == "OBSERVED", "observation_not_observed")
    _require(value.get("receiver_schema") == EXPECTED_RECEIVER_SCHEMA, "receiver_schema_invalid")
    _require(value.get("custody_state") == "EXACT_BYTES_PERSISTED", "custody_not_persisted")
    _require(value.get("registry_state") == "RECORDED", "registry_not_recorded")
    _require(value.get("exact_byte_reconstruction") == "PASS", "initial_exact_byte_reconstruction_not_pass")
    _require(value.get("tvc_lifecycle_intent_observed") is True, "tvc_lifecycle_intent_not_observed")
    _require(value.get("tvc_receiving_receipt_observed") is False, "unexpected_tvc_receiving_receipt_claim")
    _require(value.get("receiver_restart_reconstruction_observed") is False, "restart_already_claimed_by_source_observation")
    _require(value.get("runtime_activation_claimed") is False, "browser_observation_cannot_claim_runtime_activation")
    _require(value.get("credential_used") is False, "browser_observation_credential_use_forbidden")
    submission_id = value.get("submission_id")
    receipt_id = value.get("receiver_receipt_id")
    _require(isinstance(submission_id, str) and bool(submission_id), "submission_id_required")
    _require(isinstance(receipt_id, str) and bool(receipt_id), "receiver_receipt_id_required")
    expected_digest = _parse_digest_uri(value.get("controlled_pdf_sha256"), "controlled_pdf_sha256")
    _require(value.get("retrieved_pdf_sha256") == "sha256:" + expected_digest, "pre_restart_retrieved_hash_mismatch")
    return submission_id, receipt_id, expected_digest


def _validate_worker_receipt(value: Mapping[str, Any]) -> tuple[str, Path, str, int]:
    _require(value.get("schema") == WORKER_SCHEMA, "worker_receipt_schema_invalid")
    _require(value.get("task_id") == TASK_ID, "worker_task_id_invalid")
    _require(value.get("receiver_ready") is True, "worker_receiver_not_ready")
    _require(value.get("credential_authority") == CREDENTIAL_AUTHORITY, "worker_credential_authority_invalid")
    _require(value.get("github_token_runtime_authority") == "NONE", "worker_github_authority_forbidden")
    _require(value.get("non_tv_tvc_secret_or_token_used") is False, "worker_non_tv_tvc_secret_forbidden")
    _require(value.get("third_party_runtime_required") is False, "worker_third_party_runtime_forbidden")
    base_url = value.get("base_url")
    adapter_root_raw = value.get("adapter_root")
    durable_root_raw = value.get("durable_state_root")
    receiver_pid = value.get("receiver_pid")
    _require(isinstance(base_url, str) and (base_url.startswith("http://127.0.0.1:") or base_url.startswith("http://localhost:")), "worker_base_url_must_be_loopback")
    _require(isinstance(adapter_root_raw, str) and bool(adapter_root_raw), "worker_adapter_root_required")
    _require(isinstance(durable_root_raw, str) and bool(durable_root_raw), "worker_durable_root_required")
    if not isinstance(receiver_pid, int) or isinstance(receiver_pid, bool) or receiver_pid <= 1:
        raise PredicatePending("CONTROLLED_RECEIVER_PID_NOT_AVAILABLE")
    adapter_root = Path(adapter_root_raw).expanduser().resolve()
    durable_root = Path(durable_root_raw).expanduser().resolve()
    _require(adapter_root.is_dir(), "worker_adapter_root_missing")
    _require(durable_root.is_dir(), "worker_durable_root_missing")
    return base_url.rstrip("/"), adapter_root, str(durable_root), receiver_pid


def _default_json_reader(url: str, timeout: float) -> Mapping[str, Any]:
    request = Request(url, headers={"Accept": "application/json", "Cache-Control": "no-store"})
    try:
        with urlopen(request, timeout=timeout) as response:
            value = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, HTTPError, json.JSONDecodeError) as exc:
        raise ReconstructionFailure(f"json_probe_failed:{type(exc).__name__}") from exc
    _require(isinstance(value, dict), "json_probe_object_required")
    return value


def _default_bytes_reader(url: str, review_token: str, timeout: float) -> tuple[bytes, Mapping[str, str]]:
    request = Request(
        url,
        headers={
            "Accept": "application/pdf",
            "Cache-Control": "no-store",
            "X-SteGVerse-HIL-Review-Token": review_token,
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            data = response.read()
            headers = {key.lower(): value for key, value in response.headers.items()}
    except (OSError, URLError, HTTPError) as exc:
        raise ReconstructionFailure(f"exact_bytes_probe_failed:{type(exc).__name__}") from exc
    return data, headers


def _default_killer(pid: int) -> None:
    os.kill(pid, signal.SIGTERM)


def _status(reader: JsonReader, base_url: str, submission_id: str, expected_digest: str, timeout: float) -> dict[str, Any]:
    value = dict(reader(f"{base_url}/api/hil/submissions/{submission_id}/status", timeout))
    _require(value.get("schema_version") == "HIL-SUBMISSION-STATUS-v1", "submission_status_schema_invalid")
    _require(value.get("submission_id") == submission_id, "submission_status_id_mismatch")
    _require(value.get("submitted_file_sha256") == expected_digest, "submission_status_hash_mismatch")
    _require(value.get("custody_state") == "EXACT_BYTES_PERSISTED", "submission_status_custody_invalid")
    _require(value.get("registry_state") == "RECORDED", "submission_status_registry_invalid")
    authority = value.get("authority")
    _require(isinstance(authority, Mapping), "submission_status_authority_required")
    _require(all(authority.get(key) is False for key in ("execution", "acceptance", "publication", "master_record_append")), "submission_status_authority_drift")
    return value


def _wait_ready(verifier: ReadyVerifier, base_url: str, attempts: int = 30, delay: float = 0.25) -> Mapping[str, Any]:
    last: Mapping[str, Any] | None = None
    for _ in range(attempts):
        try:
            last = verifier(base_url)
        except Exception:
            last = None
        if isinstance(last, Mapping) and last.get("state") == "READY":
            return last
        time.sleep(delay)
    raise ReconstructionFailure("replacement_receiver_not_ready")


def verify_post_restart(
    *,
    runtime_root: Path,
    observation_path: Path,
    env: Mapping[str, str] | None = None,
    json_reader: JsonReader = _default_json_reader,
    bytes_reader: BytesReader = _default_bytes_reader,
    killer: Killer = _default_killer,
    launcher: Launcher = launch_receiver,
    ready_verifier: ReadyVerifier = verify_receiver,
    timeout: float = 10.0,
) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    observation = _load(observation_path.expanduser().resolve())
    submission_id, receipt_id, expected_digest = _validate_observation(observation)

    worker_path = runtime / WORKER_RECEIPT_REL
    if not worker_path.is_file():
        raise PredicatePending("HIL_RECEIVER_WORKER_RECEIPT_NOT_AVAILABLE")
    worker = _load(worker_path)
    base_url, adapter_root, durable_root_str, receiver_pid = _validate_worker_receipt(worker)
    durable_root = Path(durable_root_str)

    values = dict(os.environ if env is None else env)
    review_token = values.get("STEGVERSE_HIL_REVIEW_TOKEN", "")
    if not review_token:
        raise PredicatePending("TVC_RECONSTRUCTION_AUTH_NOT_OBSERVED")

    before = _status(json_reader, base_url, submission_id, expected_digest, timeout)

    try:
        killer(receiver_pid)
    except ProcessLookupError:
        raise PredicatePending("CONTROLLED_RECEIVER_PID_NOT_RUNNING")
    except PermissionError as exc:
        raise ReconstructionFailure("controlled_receiver_termination_not_permitted") from exc

    replacement = launcher(adapter_root, durable_root, port=int(base_url.rsplit(":", 1)[1]), env=values)
    replacement_pid = getattr(replacement, "pid", None)
    _require(isinstance(replacement_pid, int) and replacement_pid > 1, "replacement_receiver_pid_invalid")
    ready = _wait_ready(ready_verifier, base_url)
    _require(ready.get("credential_authority") == CREDENTIAL_AUTHORITY, "replacement_receiver_credential_authority_invalid")
    _require(ready.get("github_token_runtime_authority") == "NONE", "replacement_receiver_github_authority_forbidden")

    after = _status(json_reader, base_url, submission_id, expected_digest, timeout)
    exact, headers = bytes_reader(
        f"{base_url}/api/hil/submissions/{submission_id}/exact-bytes",
        review_token,
        timeout,
    )
    returned_digest = _digest_hex(exact)
    _require(returned_digest == expected_digest, "post_restart_exact_byte_hash_mismatch")
    normalized_headers = {str(k).lower(): str(v) for k, v in headers.items()}
    _require(normalized_headers.get("x-stegverse-hil-submission-id") == submission_id, "reconstruction_submission_header_mismatch")
    _require(normalized_headers.get("x-stegverse-hil-submitted-sha256") == expected_digest, "reconstruction_hash_header_mismatch")
    _require(normalized_headers.get("x-stegverse-hil-reconstruction-state") == "EXACT_BYTES_HASH_VERIFIED", "reconstruction_state_header_invalid")

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "state": "PASS",
        "submission_id": submission_id,
        "receiver_receipt_id": receipt_id,
        "source_observation_schema": OBSERVATION_SCHEMA,
        "source_observation_state": "OBSERVED",
        "prior_receiver_pid": receiver_pid,
        "replacement_receiver_pid": replacement_pid,
        "same_durable_state_root": True,
        "receiver_ready_after_restart": True,
        "status_before_restart": before,
        "status_after_restart": after,
        "expected_pdf_sha256": "sha256:" + expected_digest,
        "returned_pdf_sha256": "sha256:" + returned_digest,
        "reconstruction_state": "EXACT_BYTES_HASH_VERIFIED",
        "receiver_restart_reconstruction_observed": True,
        "tvc_lifecycle_intent_observed": True,
        "tvc_receiving_receipt_observed": False,
        "private_review_completed": False,
        "publication_authorized": False,
        "master_record_authorized": False,
        "credential_authority": CREDENTIAL_AUTHORITY,
        "credential_value_exposed": False,
        "github_token_runtime_authority": "NONE",
        "second_user_device_required": False,
        "g18_completion_required": False,
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }
    out = runtime / OUTPUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify HIL exact bytes after controlled receiver restart.")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--observation-evidence", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify_post_restart(runtime_root=args.runtime_root, observation_path=args.observation_evidence)
    except PredicatePending as exc:
        result = {
            "schema": RECEIPT_SCHEMA,
            "state": "PREDICATE_PENDING",
            "reason": str(exc),
            "credential_authority": CREDENTIAL_AUTHORITY,
            "credential_value_exposed": False,
            "github_token_runtime_authority": "NONE",
            "second_user_device_required": False,
            "authority_effect": "NONE",
        }
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        result = {
            "schema": RECEIPT_SCHEMA,
            "state": "FAIL_CLOSED",
            "reason": f"{type(exc).__name__}:{exc}",
            "credential_authority": CREDENTIAL_AUTHORITY,
            "credential_value_exposed": False,
            "github_token_runtime_authority": "NONE",
            "authority_effect": "NONE",
        }
        print(json.dumps(result, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
