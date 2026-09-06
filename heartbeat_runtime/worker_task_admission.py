"""Fail-closed pre-initiation review for StegVerse worker tasks.

Admission review is evidence-only and must complete before new worker authority
artifacts may be minted by the existing WorkerCoordinator.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .independent_oscillator import encode_heartbeat_id

SCHEMA = "stegverse.worker-task-admission-packet/v1"
VERDICTS = {"ADMIT", "UPDATE", "RETIRE", "BLOCK"}

TASK_COSV_NOTATION = "L R U I V G O C M T B E A P"
TASK_TERNARY_POSITIONS = {1, 8, 9, 11, 12, 13}
TASK_QUANTITY_POSITIONS = {2, 3, 4, 5, 6, 7, 10}


def _task_cosv(task: dict[str, Any]) -> tuple[dict[str, Any] | None, bool]:
    """Return the task COSV projection and whether a declared binding is valid."""
    source_ref = task.get("source_state_vector_ref")
    machine = task.get("machine_readable_state")
    cosv = machine.get("cosv") if isinstance(machine, dict) else None
    if source_ref in (None, ""):
        return None, True
    if not isinstance(cosv, dict):
        return None, False
    vector = cosv.get("vector")
    if (
        cosv.get("profile") != "task.v1"
        or cosv.get("notation") != TASK_COSV_NOTATION
        or cosv.get("width") != 14
        or cosv.get("vector_state") != "EMITTED"
        or cosv.get("authority_effect") != "NONE"
        or not isinstance(vector, str)
        or len(vector) != 14
        or not vector.isdigit()
    ):
        return cosv, False
    digits = [int(x) for x in vector]
    if any(digits[i] not in (0, 1, 2) for i in TASK_TERNARY_POSITIONS):
        return cosv, False
    if any(digits[i] not in range(10) for i in TASK_QUANTITY_POSITIONS):
        return cosv, False
    return cosv, True


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _readme_impact(task: dict[str, Any], handoff: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Evaluate the functional-change README completeness contract.

    Existing tasks remain compatible until they explicitly enter this gate. Any
    functional mutation initiated under the StegVerse session-entry contract must
    set ``readme_impact_required=true`` in the task or handoff. Once required, the
    review fails closed unless either the material functional effect is reflected
    in README.md or a non-material determination carries evidence and rationale.
    """
    required = bool(task.get("readme_impact_required") or handoff.get("readme_impact_required"))
    raw = task.get("readme_impact")
    if not isinstance(raw, dict):
        raw = handoff.get("readme_impact")
    impact = dict(raw) if isinstance(raw, dict) else {}

    if not required:
        return {
            "required": False,
            "declared": bool(impact),
            "material_function_change": impact.get("material_function_change"),
            "disposition": "LEGACY_OR_NONFUNCTIONAL_GATE_NOT_REQUIRED",
            "authority_effect": "NONE",
        }, True

    if not impact:
        return {
            "required": True,
            "declared": False,
            "material_function_change": None,
            "disposition": "README_IMPACT_UNDECLARED",
            "authority_effect": "NONE",
        }, False

    material = impact.get("material_function_change")
    evidence_refs = [str(item) for item in impact.get("evidence_refs", []) if str(item).strip()]
    readme_path = str(impact.get("readme_path") or "").strip()
    readme_updated = impact.get("readme_updated_in_change_set") is True
    no_update_reason = str(impact.get("no_readme_update_reason") or "").strip()

    if material is True:
        complete = bool(readme_updated and readme_path and evidence_refs)
        disposition = "README_UPDATED_FOR_MATERIAL_FUNCTION_CHANGE" if complete else "MATERIAL_FUNCTION_CHANGE_REQUIRES_README_UPDATE"
    elif material is False:
        complete = bool(no_update_reason and evidence_refs)
        disposition = "NONMATERIAL_CHANGE_EVIDENCE_SUPPORTED" if complete else "NONMATERIAL_DETERMINATION_REQUIRES_REASON_AND_EVIDENCE"
    else:
        complete = False
        disposition = "MATERIALITY_UNDECLARED"

    return {
        "required": True,
        "declared": True,
        "material_function_change": material,
        "readme_path": readme_path or None,
        "readme_updated_in_change_set": bool(readme_updated),
        "no_readme_update_reason": no_update_reason or None,
        "evidence_refs": evidence_refs,
        "disposition": disposition,
        "authority_effect": "NONE",
    }, complete


def review_worker_task_admission(
    *,
    root: Path,
    task: dict[str, Any],
    handoff: dict[str, Any],
    registry: dict[str, Any],
    carrier_epoch: int,
    trigger_source: str,
    execution_authorized: bool,
    dependencies_complete: bool,
    worker_resolved: bool,
    semantic_state_current: bool,
) -> dict[str, Any]:
    """Build a fresh non-authorizing packet and return a fail-closed verdict."""
    reasons: list[str] = []
    state = str(task.get("state") or "")
    terminal = state in {"COMPLETED", "RETIRED", "SUPERSEDED", "ARCHIVED"} or bool(task.get("archive_eligible"))
    stale_assignment = any(task.get(k) not in (None, "") for k in ("worker_id", "worker_instance_id", "claim_id"))
    timing = task.get("heartbeat_timing") or {}
    stale_authority = timing.get("fencing_token") not in (None, 0)
    credential_ok = (task.get("credential_authority") in (None, "TV/TVC") and handoff.get("credential_authority") in (None, "TV/TVC"))
    github_token_ok = task.get("github_token_runtime_authority") in (None, "NONE") and handoff.get("github_token_runtime_authority") in (None, "NONE")
    handoff_task_id = ((handoff.get("task") or {}).get("task_id") or handoff.get("task_id"))
    handoff_matches = handoff_task_id in (None, task.get("task_id"))
    task_cosv, task_cosv_valid = _task_cosv(task)
    readme_impact, readme_impact_complete = _readme_impact(task, handoff)
    predicates = {
        "task_handoff_ready": state == "HANDOFF_READY",
        "task_not_terminal": not terminal,
        "no_existing_assignment": not stale_assignment,
        "no_existing_fence": not stale_authority,
        "semantic_state_current": bool(semantic_state_current),
        "dependencies_complete": bool(dependencies_complete),
        "execution_authorized": bool(execution_authorized),
        "worker_resolved": bool(worker_resolved),
        "credential_authority_tvc_only": bool(credential_ok),
        "github_token_runtime_authority_none": bool(github_token_ok),
        "handoff_task_identity_matches": bool(handoff_matches),
        "source_state_vector_valid": bool(task_cosv_valid),
        "readme_impact_complete": bool(readme_impact_complete),
    }
    if terminal:
        verdict = "RETIRE"
        reasons.append("TASK_TERMINAL_OR_ARCHIVE_ELIGIBLE")
    elif not handoff_matches or not semantic_state_current:
        verdict = "UPDATE"
        if not handoff_matches:
            reasons.append("HANDOFF_TASK_IDENTITY_STALE")
        if not semantic_state_current:
            reasons.append("SOURCE_STATE_STALE")
    else:
        failed = [name for name, ok in predicates.items() if not ok]
        if failed:
            verdict = "BLOCK"
            reasons.extend(failed)
        else:
            verdict = "ADMIT"
            reasons.append("ALL_PREINITIATION_PREDICATES_PASS")
    packet = {
        "schema": SCHEMA,
        "task_id": str(task.get("task_id") or ""),
        "goal_id": task.get("goal_id"),
        "heartbeat_id": encode_heartbeat_id(int(carrier_epoch)),
        "carrier_epoch": int(carrier_epoch),
        "trigger_source": str(trigger_source),
        "review": {"verdict": verdict, "reasons": sorted(reasons), "predicates": predicates},
        "readme_impact": readme_impact,
        "source_refs": {
            "handoff_ref": task.get("handoff_ref"),
            "cost_basis_ref": task.get("cost_basis_ref"),
            "source_state_vector_ref": task.get("source_state_vector_ref"),
        },
        "operational_state_vector": None if task_cosv is None else {
            "profile": task_cosv.get("profile"),
            "notation": task_cosv.get("notation"),
            "vector": task_cosv.get("vector"),
            "vector_state": task_cosv.get("vector_state"),
            "authority_effect": "NONE",
        },
        "digests": {
            "task_sha256": _sha(task),
            "handoff_sha256": _sha(handoff),
            "registry_sha256": _sha(registry),
        },
        "authority": {
            "credential_authority": "TV/TVC",
            "review_grants_execution_authority": False,
            "heartbeat_grants_execution_authority": False,
            "github_token_runtime_authority": "NONE",
            "claim_authority": False,
            "fence_authority": False,
            "lease_authority": False,
        },
    }
    packet["packet_sha256"] = _sha(packet)
    return packet


def persist_admission_receipt(root: Path, packet: dict[str, Any]) -> Path:
    """Persist review evidence only; persistence grants no authority."""
    if packet.get("schema") != SCHEMA or packet.get("review", {}).get("verdict") not in VERDICTS:
        raise ValueError("invalid worker admission packet")
    task_id = str(packet["task_id"]).replace("/", "_")
    hb = str(packet["heartbeat_id"])
    digest = str(packet["packet_sha256"])[:16]
    path = Path(root) / "receipts" / "worker-task-admission" / f"{task_id}-{hb}-{digest}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


__all__ = ["SCHEMA", "VERDICTS", "review_worker_task_admission", "persist_admission_receipt"]
