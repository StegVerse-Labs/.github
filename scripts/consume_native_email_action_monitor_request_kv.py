#!/usr/bin/env python3
"""KV-enforcing entrypoint for the standing native email action monitor.

This wrapper preserves the existing native-email consumer and provider route while
requiring a locally materialized KnowledgeVault before the canonical monitor can run.
The KV root may be supplied by the existing non-secret environment binding or recovered
from the resident runtime's validated provider-materialization receipt. The canonical
monitor subprocess is replaced only with the KV guard, which persists normalized failure
incidents with exact-byte readback before permitting ARCHIVE_IDS.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import consume_native_email_action_monitor_request as base

ENTRYPOINT = "scripts/consume_native_email_action_monitor_request_kv.py"
CANONICAL_MONITOR = "run_native_email_action_monitor.py"
GUARDED_MONITOR = SCRIPT_DIR / "run_native_email_action_monitor_kv_guard.py"
KV_RECEIPT_REL = Path("control/kv-provider-materialization/latest.json")
KV_RECEIPT_SCHEMA = "stegverse.kv.provider-materialization-receipt/v2"
KV_ENV_NAMES = ("STEGVERSE_KV_ROOT", "STEGVERSE_KV_PROVIDER_MATERIALIZED_ROOT")


def _recognized_kv_root(path: Path) -> bool:
    try:
        root = path.expanduser().resolve()
    except Exception:
        return False
    return bool(
        root.is_dir()
        and (root.name == "KnowledgeVault" or (root / "_System").is_dir() or (root / "00_Inbox").is_dir())
    )


def _load_object(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def resolve_kv_root(runtime: Path, values: Mapping[str, str]) -> tuple[Path | None, str]:
    for name in KV_ENV_NAMES:
        raw = str(values.get(name) or "").strip()
        if not raw:
            continue
        candidate = Path(raw)
        if _recognized_kv_root(candidate):
            return candidate.expanduser().resolve(), f"ENV:{name}"

    receipt = _load_object(runtime / KV_RECEIPT_REL)
    if receipt is None:
        return None, "NO_VALID_ENV_OR_RUNTIME_MATERIALIZATION_RECEIPT"
    if receipt.get("schema") != KV_RECEIPT_SCHEMA:
        return None, "RUNTIME_MATERIALIZATION_RECEIPT_SCHEMA_INVALID"
    if receipt.get("exact_readback_verified") is not True:
        return None, "RUNTIME_MATERIALIZATION_READBACK_NOT_VERIFIED"
    if receipt.get("credential_authority") != "TV/TVC":
        return None, "RUNTIME_MATERIALIZATION_CREDENTIAL_AUTHORITY_INVALID"
    if receipt.get("credential_material_persisted") is not False:
        return None, "RUNTIME_MATERIALIZATION_CREDENTIAL_BOUNDARY_INVALID"
    if receipt.get("consumer_received_provider_credential") is not False:
        return None, "RUNTIME_MATERIALIZATION_CONSUMER_CREDENTIAL_BOUNDARY_INVALID"
    raw = str(receipt.get("materialized_root") or "").strip()
    if not raw:
        return None, "RUNTIME_MATERIALIZATION_ROOT_MISSING"
    candidate = Path(raw)
    if not _recognized_kv_root(candidate):
        return None, "RUNTIME_MATERIALIZATION_ROOT_NOT_PRESENT"
    return candidate.expanduser().resolve(), "RUNTIME_CONTROL_RECEIPT"


def _request_context(source: Path, runtime: Path) -> tuple[dict[str, Any], str, str]:
    request_path = runtime / base.REQUEST_REL
    if not request_path.is_file():
        request_path = source / base.REQUEST_REL
    if not request_path.is_file():
        raise RuntimeError("native email resident request not materialized")
    request = base.load_json(request_path)
    base.ENTRYPOINT = ENTRYPOINT
    base.validate_request(request)
    return request, base.stable_hash(request), base.resolve_task_vector(source, runtime)


def consume(
    source_root: Path,
    runtime_root: Path,
    *,
    env: Mapping[str, str] | None = None,
    runner=subprocess.run,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    values = dict(os.environ if env is None else env)
    base.ENTRYPOINT = ENTRYPOINT

    kv_root, kv_source = resolve_kv_root(runtime, values)
    if kv_root is None:
        request, request_hash, cosv = _request_context(source, runtime)
        return base.pending(
            runtime,
            request,
            request_hash,
            "KV_ROOT_NOT_MATERIALIZED",
            handoff_task_id=base.TASK_ID,
            handoff_cosv_task_vector=cosv,
            kv_persistence_required=True,
            archive_permitted=False,
            kv_resolution_source=kv_source,
        )

    def guarded_runner(command, *args, **kwargs):
        cmd = [str(part) for part in command]
        if len(cmd) >= 2 and Path(cmd[1]).name == CANONICAL_MONITOR:
            if not GUARDED_MONITOR.is_file():
                raise RuntimeError("KV guarded native email monitor not materialized")
            cmd[1] = str(GUARDED_MONITOR)
            cmd.extend(["--kv-root", str(kv_root)])
            try:
                output_index = cmd.index("--output") + 1
                Path(cmd[output_index]).unlink(missing_ok=True)
            except (ValueError, IndexError):
                pass
        return runner(cmd, *args, **kwargs)

    result = base.consume(source, runtime, runner=guarded_runner, env=values)
    monitor = result.get("monitor_result") if isinstance(result, dict) else None
    kv_proof = monitor.get("kv_persistence") if isinstance(monitor, dict) else None
    monitor_attempted = bool(result.get("runtime_execution_attempted")) if isinstance(result, dict) else False
    kv_satisfied = bool(
        isinstance(kv_proof, dict)
        and kv_proof.get("state") == "KV_STORED_VERIFIED"
        and kv_proof.get("archive_after_kv_persistence") is True
        and kv_proof.get("exact_byte_readback_required") is True
    )

    if isinstance(result, dict):
        result.update({
            "kv_root": str(kv_root),
            "kv_resolution_source": kv_source,
            "kv_persistence_required": True,
            "kv_persistence_satisfied": kv_satisfied if monitor_attempted else False,
            "archive_after_kv_persistence_required": True,
            "kv_persistence": kv_proof,
        })
        if result.get("state") == "COMPLETED" and not kv_satisfied:
            result["state"] = "ATTEMPT_RECORDED"
            result["retry_allowed"] = True
            result["pending_reason"] = "KV_PERSISTENCE_PROOF_REQUIRED"
            result["continuation_required"] = True
            result["handoff_task_id"] = base.TASK_ID
            result["handoff_cosv_task_vector"] = base.resolve_task_vector(source, runtime)
            result["handoff_action"] = "RESOLVE_POINTER_AND_INITIATE_TASK_AGAIN"
        base.write_receipt(runtime, result)
    return result


def reusable_slot_satisfied(result: Mapping[str, Any]) -> bool:
    """A slot is satisfied only after an actual bounded monitor attempt succeeds.

    Infrastructure/pre-execution pending states and missing KV proof remain retryable
    in the same UTC-hour slot. A successful bounded monitor pass may remain logically
    nonterminal for the standing task while still satisfying that one hourly visit.
    """
    if result.get("runtime_execution_attempted") is not True:
        return False
    if result.get("pending_reason") == "KV_PERSISTENCE_PROOF_REQUIRED":
        return False
    return result.get("state") in {"ATTEMPT_RECORDED", "COMPLETED"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = consume(args.source_root, args.runtime_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if reusable_slot_satisfied(result) else 3


if __name__ == "__main__":
    raise SystemExit(main())
