from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001"
RECEIPT = ROOT / "receipts/stegos-sovereign-relay" / f"{TASK_ID}.json"


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"json_object_required:{path}")
    return value


def _require_path(name: str) -> Path:
    raw = os.environ.get(name)
    if not raw:
        raise RuntimeError(f"runtime_locator_missing:{name}")
    path = Path(raw).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"runtime_artifact_missing:{name}:{path}")
    return path


def _stegos_root() -> Path:
    raw = os.environ.get("STEGVERSE_STEGOS_ROOT")
    candidates = [Path(raw).expanduser().resolve()] if raw else []
    candidates += [ROOT.parent / "StegOS", Path.home() / "StegOS"]
    for candidate in candidates:
        if (candidate / "stegos/sovereign_relay_round_trip.py").is_file():
            return candidate
    raise RuntimeError("current_stegos_round_trip_source_not_found")


def main() -> int:
    stegos_root = _stegos_root()
    if str(stegos_root) not in sys.path:
        sys.path.insert(0, str(stegos_root))
    from stegos.sovereign_relay_round_trip import execute_sovereign_relay_round_trip

    binding_path = _require_path("STEGVERSE_RELAY_EGRESS_BINDING")
    authorization_path = _require_path("STEGVERSE_RELAY_EGRESS_AUTHORIZATION")
    payload_path = _require_path("STEGVERSE_RELAY_EGRESS_PAYLOAD")
    runtime_base_raw = os.environ.get("STEGVERSE_RELAY_RUNTIME_BASE")
    runtime_root = Path(runtime_base_raw).expanduser().resolve() if runtime_base_raw else (Path.home() / ".stegverse/runtime/ephemeral-relays").resolve()

    result = execute_sovereign_relay_round_trip(
        authorization=_load(authorization_path),
        binding=_load(binding_path),
        payload=payload_path.read_bytes(),
        runtime_root=runtime_root,
    )
    if result.get("state") != "RETURN_PATH_VERIFIED":
        raise RuntimeError("return_path_terminal_state_not_observed")
    if result.get("far_side_evidence_present") is not True or result.get("durable_return_queue_verified") is not True or result.get("interlock_ingestion_verified") is not True:
        raise RuntimeError("return_path_completion_predicate_failed")
    if result.get("canonical_transition_committed") is not False:
        raise RuntimeError("return_path_canonical_authority_violation")

    receipt = {
        "schema": "stegverse.worker-task-terminal-receipt/v1",
        "task_id": TASK_ID,
        "state": "COMPLETED",
        "transition_id": "SOVEREIGN_RELAY_RETURN_PATH_VERIFIED",
        "stegos_root": str(stegos_root),
        "runtime_root": str(runtime_root),
        "binding_ref": str(binding_path),
        "authorization_ref": str(authorization_path),
        "payload_ref": str(payload_path),
        "round_trip_result": result,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "canonical_transition_committed": False,
        "authority_effect": "NONE_RUNTIME_EVIDENCE_ONLY",
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if RECEIPT.exists() and RECEIPT.read_text(encoding="utf-8") != serialized:
        raise RuntimeError("terminal_receipt_write_once_collision")
    RECEIPT.write_text(serialized, encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
