from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

OBSERVATION_ONLY_MODE = "CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION"


def _load(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def _digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _summary(path: Path) -> dict[str, Any]:
    value = _load(path)
    if value is None:
        return {"observed": False, "ref": str(path), "sha256": None, "schema": None, "state": None}
    return {
        "observed": True,
        "ref": str(path),
        "sha256": _digest(path),
        "schema": value.get("schema"),
        "state": value.get("state") or value.get("transition") or value.get("status"),
    }


def project(runtime_root: Path, evidence_refs: dict[str, str] | None = None) -> dict[str, Any]:
    root = runtime_root.expanduser().resolve()
    carrier_path = root / "control/heartbeat-carrier-runtime-state.json"
    worker_path = root / "control/worker-runtime-state.json"
    control_path = root / "control/worker-control-plane-coordination.json"
    activation_path = root / "receipts/sovereign-host/activation.latest.json"

    carrier = _load(carrier_path) or {}
    worker = _load(worker_path) or {}
    activation = _load(activation_path) or {}
    predicates = activation.get("predicates") if isinstance(activation.get("predicates"), dict) else {}

    activation_observed = bool(activation)
    runtime_alive = (
        activation_observed
        and predicates.get("native_service_active") is True
        and predicates.get("continuous_runtime_live") is True
    )
    task_capable = (
        worker.get("schema") == "stegverse.worker-runtime-state/v1"
        and worker.get("observation_mode") != OBSERVATION_ONLY_MODE
        and isinstance(worker.get("runtime_tick"), int)
    )

    carrier_epoch = carrier.get("epoch")
    worker_epoch = worker.get("last_observed_carrier_epoch")
    freshness_correlated = (
        isinstance(carrier_epoch, int)
        and isinstance(worker_epoch, int)
        and worker_epoch == carrier_epoch
    )

    evidence = {}
    for name, rel in sorted((evidence_refs or {}).items()):
        evidence[name] = _summary(root / rel)

    request_observed = evidence.get("request", {}).get("observed", False)
    consumption_observed = evidence.get("consumption", {}).get("observed", False)
    execution_observed = evidence.get("execution", {}).get("observed", False)
    reconstruction_observed = evidence.get("reconstruction", {}).get("observed", False)

    return {
        "schema": "stegverse.hb-runtime-presence-resident-observability/v1",
        "runtime_root": str(root),
        "resident": {
            "node_id": activation.get("node_id") or activation.get("sovereign_node") or None,
            "runtime_alive_observed": runtime_alive,
            "task_capable_worker_observed": task_capable,
            "worker_runtime_tick": worker.get("runtime_tick"),
            "worker_observation_mode": worker.get("observation_mode"),
        },
        "heartbeat_reference": {
            "carrier_state_observed": bool(carrier),
            "carrier_epoch": carrier_epoch,
            "carrier_generation": carrier.get("generation"),
            "worker_last_observed_carrier_epoch": worker_epoch,
            "freshness_correlated": freshness_correlated,
            "heartbeat_grants_authority": False,
        },
        "governed_progress": {
            "request_observed": request_observed,
            "consumption_observed": consumption_observed,
            "execution_observed": execution_observed,
            "reconstruction_observed": reconstruction_observed,
            "runtime_signal_is_execution_receipt": False,
        },
        "evidence": evidence,
        "control_plane": _summary(control_path),
        "activation": _summary(activation_path),
        "authority": {
            "credential_authority": "TV/TVC",
            "hb_authority_effect": "NONE_REFERENCE_ONLY",
            "projection_authority_effect": "NONE_OBSERVATION_ONLY",
            "github_token_runtime_authority": "NONE",
        },
    }
