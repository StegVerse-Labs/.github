from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OBSERVATION_ONLY_MODE = "CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION"
DEFAULT_WORKER_FRESHNESS_WINDOW_SECONDS = 60.0
CANONICAL_CARRIER_RUNTIME = "heartbeat_runtime.engine_v13.HeartbeatRuntime"
CANONICAL_WORKER_RUNTIME = "heartbeat_runtime.worker_runtime.WorkerCoordinator"
PORTABLE_CHECKOUT_SCHEMA = "stegverse.workercoordinator-portable-checkout-receipt/v1"
PORTABLE_AUTHORITY_OWNER = "StegVerse-Labs/.github WorkerCoordinator"
PORTABLE_AUTHORITY_DOMAIN = "INDEPENDENT_TASK_CONTROL"
PORTABLE_EXECUTION_SURFACE = "CURRENT_USER_IPHONE"


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


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _activation_runtime_alive(activation: dict[str, Any]) -> tuple[bool, str]:
    """Recognize canonical runtime-local activation evidence without inventing liveness."""
    if not activation:
        return False, "UNOBSERVED"

    predicates = activation.get("predicates") if isinstance(activation.get("predicates"), dict) else {}
    if (
        predicates.get("native_service_active") is True
        and predicates.get("continuous_runtime_live") is True
    ):
        return True, "PREDICATE_PROOF_COMPATIBILITY"

    if activation.get("registration_kind") == "stegverse-ephemeral-console":
        alive = (
            activation.get("active") is True
            and activation.get("carrier_active") is True
            and activation.get("worker_active") is True
            and activation.get("separate_carrier_and_worker_processes") is True
            and activation.get("stegverse_process_supervision") is True
            and activation.get("canonical_carrier_runtime") == CANONICAL_CARRIER_RUNTIME
            and activation.get("worker_runtime") == CANONICAL_WORKER_RUNTIME
            and activation.get("third_party_process_host_required") is False
            and activation.get("heartbeat_grants_execution_authority") is False
        )
        return alive, "EPHEMERAL_CONSOLE_SERVICE_RECEIPT"

    alive = (
        activation.get("active") is True
        and activation.get("carrier_active") is True
        and activation.get("worker_active") is True
        and activation.get("native_process_supervision_only") is True
        and activation.get("separate_carrier_and_worker_processes") is True
        and activation.get("third_party_process_host_required") is False
    )
    return alive, "CANONICAL_SERVICE_RECEIPT"


def _self_heal_runtime_alive(receipt: dict[str, Any]) -> tuple[bool, str]:
    """Recognize the existing carrier-owned WorkerCoordinator self-heal receipt.

    This evidence is process supervision only. It never grants task authority and is
    accepted only when it describes the canonical v13 carrier + WorkerCoordinator,
    both processes are explicitly active, and no third-party process host is required.
    """
    if not receipt:
        return False, "UNOBSERVED"
    alive = (
        receipt.get("active") is True
        and receipt.get("carrier_active") is True
        and receipt.get("worker_active") is True
        and receipt.get("worker_task_capable_cycle_observed") is True
        and receipt.get("separate_carrier_and_worker_processes") is True
        and receipt.get("canonical_carrier_runtime") == CANONICAL_CARRIER_RUNTIME
        and receipt.get("worker_runtime") == CANONICAL_WORKER_RUNTIME
        and receipt.get("third_party_process_host_required") is False
        and receipt.get("heartbeat_grants_execution_authority") is False
        and receipt.get("authority_effect") == "NONE_SUPERVISION_ONLY"
    )
    return alive, "CARRIER_SELF_HEAL_SUPERVISION_RECEIPT"


def _portable_checkout_observed(receipt: dict[str, Any]) -> tuple[bool, str]:
    """Recognize an authentic task-scoped portable WorkerCoordinator checkout.

    A portable checkout proves that the canonical WorkerCoordinator claim/fence
    transaction actually ran on CURRENT_USER_IPHONE for the exact receipt subject.
    It is not native process-presence evidence, heartbeat authority, request
    consumption, task execution, or task completion.
    """
    if not receipt:
        return False, "UNOBSERVED"
    valid = (
        receipt.get("schema") == PORTABLE_CHECKOUT_SCHEMA
        and receipt.get("canonical_authority_owner") == PORTABLE_AUTHORITY_OWNER
        and receipt.get("authority_domain") == PORTABLE_AUTHORITY_DOMAIN
        and receipt.get("execution_surface") == PORTABLE_EXECUTION_SURFACE
        and isinstance(receipt.get("task_id"), str)
        and bool(receipt.get("task_id"))
        and isinstance(receipt.get("worker_id"), str)
        and bool(receipt.get("worker_id"))
        and isinstance(receipt.get("claim_id"), str)
        and bool(receipt.get("claim_id"))
        and isinstance(receipt.get("fencing_token"), int)
        and receipt.get("fencing_token") > 0
        and receipt.get("heartbeat_granted_authority") is False
        and receipt.get("credential_authority") == "TV/TVC"
        and receipt.get("github_token_runtime_authority") == "NONE"
        and receipt.get("global_workercoordinator_authority") is True
        and receipt.get("stegos_device_task_authority") is False
        and receipt.get("external_non_stegverse_machine_required") is False
        and receipt.get("parallel_workercoordinator_claim_issuance_allowed") is False
        and receipt.get("authority_effect") == "CANONICAL_WORKERCOORDINATOR_CLAIM_FENCE"
    )
    return valid, "PORTABLE_WORKERCOORDINATOR_CHECKOUT_RECEIPT"


def project(
    runtime_root: Path,
    evidence_refs: dict[str, str] | None = None,
    *,
    observed_at: datetime | None = None,
    worker_freshness_window_seconds: float = DEFAULT_WORKER_FRESHNESS_WINDOW_SECONDS,
) -> dict[str, Any]:
    root = runtime_root.expanduser().resolve()
    carrier_path = root / "control/heartbeat-carrier-runtime-state.json"
    worker_path = root / "control/worker-runtime-state.json"
    control_path = root / "control/worker-control-plane-coordination.json"
    activation_path = root / "receipts/sovereign-host/activation.latest.json"
    self_heal_path = root / "receipts/sovereign-host/ephemeral-process.latest.json"

    carrier = _load(carrier_path) or {}
    worker = _load(worker_path) or {}
    activation = _load(activation_path) or {}
    self_heal = _load(self_heal_path) or {}

    activation_runtime_alive, activation_evidence_kind = _activation_runtime_alive(activation)
    self_heal_runtime_alive, self_heal_evidence_kind = _self_heal_runtime_alive(self_heal)
    if activation_runtime_alive:
        runtime_alive = True
        runtime_evidence_kind = activation_evidence_kind
        runtime_evidence_path = activation_path
        runtime_evidence = activation
    elif self_heal_runtime_alive:
        runtime_alive = True
        runtime_evidence_kind = self_heal_evidence_kind
        runtime_evidence_path = self_heal_path
        runtime_evidence = self_heal
    else:
        runtime_alive = False
        runtime_evidence_kind = activation_evidence_kind if activation else self_heal_evidence_kind
        runtime_evidence_path = activation_path if activation else self_heal_path
        runtime_evidence = activation if activation else self_heal

    task_capable = (
        worker.get("schema") == "stegverse.worker-runtime-state/v1"
        and worker.get("observation_mode") != OBSERVATION_ONLY_MODE
        and isinstance(worker.get("runtime_tick"), int)
    )

    now = observed_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)
    last_cycle_at = _parse_timestamp(worker.get("last_cycle_at"))
    worker_cycle_age_seconds = (
        (now - last_cycle_at).total_seconds() if last_cycle_at is not None else None
    )
    worker_cycle_fresh = (
        isinstance(worker_cycle_age_seconds, float)
        and worker_cycle_age_seconds >= 0.0
        and worker_cycle_age_seconds <= float(worker_freshness_window_seconds)
    )
    present_worker_runtime = runtime_alive and task_capable and worker_cycle_fresh

    carrier_epoch = carrier.get("epoch")
    worker_epoch = worker.get("last_observed_carrier_epoch")
    freshness_correlated = (
        isinstance(carrier_epoch, int)
        and isinstance(worker_epoch, int)
        and worker_epoch == carrier_epoch
    )

    evidence = {}
    refs = evidence_refs or {}
    for name, rel in sorted(refs.items()):
        evidence[name] = _summary(root / rel)

    portable_checkout_path = root / refs["portable_checkout"] if isinstance(refs.get("portable_checkout"), str) else None
    portable_checkout = _load(portable_checkout_path) if portable_checkout_path is not None else None
    portable_checkout_valid, portable_evidence_kind = _portable_checkout_observed(portable_checkout or {})

    request_observed = evidence.get("request", {}).get("observed", False)
    consumption_observed = evidence.get("consumption", {}).get("observed", False)
    execution_observed = evidence.get("execution", {}).get("observed", False)
    reconstruction_observed = evidence.get("reconstruction", {}).get("observed", False)

    # This aggregate answers whether one of the already-canonical WorkerCoordinator
    # execution surfaces has been directly observed. It deliberately does not turn
    # HB progression, static portable package presence, or a checkout into task
    # execution/completion evidence.
    task_control_runtime_observed = present_worker_runtime or portable_checkout_valid

    return {
        "schema": "stegverse.hb-runtime-presence-resident-observability/v1",
        "runtime_root": str(root),
        "resident": {
            "node_id": runtime_evidence.get("node_id") or runtime_evidence.get("sovereign_node") or None,
            "runtime_alive_observed": runtime_alive,
            "activation_evidence_observed": bool(activation),
            "self_heal_supervision_evidence_observed": bool(self_heal),
            "runtime_evidence_kind": runtime_evidence_kind,
            "runtime_evidence_ref": str(runtime_evidence_path),
            "task_capable_worker_observed": task_capable,
            "present_worker_runtime_observed": present_worker_runtime,
            "task_control_runtime_observed": task_control_runtime_observed,
            "worker_runtime_tick": worker.get("runtime_tick"),
            "worker_observation_mode": worker.get("observation_mode"),
            "worker_last_cycle_at": worker.get("last_cycle_at"),
            "worker_cycle_age_seconds": worker_cycle_age_seconds,
            "worker_cycle_fresh": worker_cycle_fresh,
            "worker_freshness_window_seconds": float(worker_freshness_window_seconds),
            "presence_requires_fresh_worker_cycle": True,
            "native_process_presence_is_universal_runtime_requirement": False,
        },
        "portable_workercoordinator": {
            "observed": portable_checkout_valid,
            "evidence_kind": portable_evidence_kind,
            "evidence_ref": str(portable_checkout_path) if portable_checkout_path is not None else None,
            "task_id": (portable_checkout or {}).get("task_id") if portable_checkout_valid else None,
            "worker_id": (portable_checkout or {}).get("worker_id") if portable_checkout_valid else None,
            "claim_id": (portable_checkout or {}).get("claim_id") if portable_checkout_valid else None,
            "fencing_token": (portable_checkout or {}).get("fencing_token") if portable_checkout_valid else None,
            "execution_surface": (portable_checkout or {}).get("execution_surface") if portable_checkout_valid else None,
            "proves_task_execution": False,
            "proves_task_completion": False,
            "heartbeat_grants_authority": False,
            "authority_effect": "NONE_OBSERVATION_ONLY",
        },
        "heartbeat_reference": {
            "carrier_state_observed": bool(carrier),
            "carrier_epoch": carrier_epoch,
            "carrier_generation": carrier.get("generation"),
            "worker_last_observed_carrier_epoch": worker_epoch,
            "freshness_correlated": freshness_correlated,
            "heartbeat_grants_authority": False,
            "continuous_process_required_for_progression": False,
            "progression_dependency": "OSCILLATOR_ONLY",
        },
        "governed_progress": {
            "request_observed": request_observed,
            "consumption_observed": consumption_observed,
            "execution_observed": execution_observed,
            "reconstruction_observed": reconstruction_observed,
            "runtime_signal_is_execution_receipt": False,
            "portable_checkout_is_execution_receipt": False,
        },
        "evidence": evidence,
        "control_plane": _summary(control_path),
        "activation": _summary(activation_path),
        "self_heal_supervision": _summary(self_heal_path),
        "authority": {
            "credential_authority": "TV/TVC",
            "hb_authority_effect": "NONE_REFERENCE_ONLY",
            "projection_authority_effect": "NONE_OBSERVATION_ONLY",
            "github_token_runtime_authority": "NONE",
        },
    }
