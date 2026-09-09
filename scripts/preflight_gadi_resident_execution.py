#!/usr/bin/env python3
"""Fail-closed preflight for GADI-RESIDENT-EXECUTION-001 runtime evidence.

This tool does not execute a defensive action. It validates whether the exact
runtime evidence bundle required by the canonical resident consumer is present,
coherent, and ready for consumption, and emits deterministic blocker codes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_ID = "GADI-RESIDENT-EXECUTION-001"
PARENT_TASK_ID = "GADI-001"
REQUEST_REL = Path("control/resident-execution-request.d/gadi-resident-execution-001.json")
OUTPUT_REL = Path("state/gadi-resident-execution/preflight.json")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add(blockers: list[dict[str, str]], code: str, detail: str) -> None:
    blockers.append({"code": code, "detail": detail})


def preflight(source_root: Path, runtime_root: Path) -> dict[str, Any]:
    source = source_root.resolve()
    runtime = runtime_root.resolve()
    blockers: list[dict[str, str]] = []

    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        request_path = source / REQUEST_REL
    if not request_path.is_file():
        add(blockers, "REQUEST_MISSING", str(request_path))
        request: dict[str, Any] = {}
    else:
        request = load_json(request_path)

    if request:
        if request.get("task_id") != TASK_ID:
            add(blockers, "REQUEST_TASK_MISMATCH", str(request.get("task_id")))
        if request.get("parent_task_id") != PARENT_TASK_ID:
            add(blockers, "REQUEST_PARENT_MISMATCH", str(request.get("parent_task_id")))
        if request.get("state") != "REQUESTED":
            add(blockers, "REQUEST_STATE_INVALID", str(request.get("state")))

    refs = {
        "command": request.get("command_state_ref"),
        "execution_context": request.get("execution_context_ref"),
        "actuator_result": request.get("actuator_result_ref"),
    }
    loaded: dict[str, dict[str, Any]] = {}
    digests: dict[str, str] = {}

    for name, raw in refs.items():
        if not isinstance(raw, str) or not raw.strip():
            add(blockers, f"{name.upper()}_REF_MISSING", "request reference absent")
            continue
        rel = Path(raw)
        if rel.is_absolute() or ".." in rel.parts:
            add(blockers, f"{name.upper()}_REF_UNSAFE", raw)
            continue
        path = runtime / rel
        if not path.is_file():
            add(blockers, f"{name.upper()}_MISSING", raw)
            continue
        try:
            loaded[name] = load_json(path)
            digests[name] = digest(path)
        except Exception as exc:
            add(blockers, f"{name.upper()}_INVALID_JSON", str(exc))

    command = loaded.get("command", {})
    context = loaded.get("execution_context", {})
    actuator = loaded.get("actuator_result", {})

    if command:
        if command.get("state") != "READY_FOR_RESIDENT_EXECUTION":
            add(blockers, "COMMAND_NOT_READY", str(command.get("state")))
        if not command.get("intr_decision_ref"):
            add(blockers, "INTR_DECISION_REF_MISSING", "command lacks current InTr decision ref")
        if not command.get("runtime_binding_ref"):
            add(blockers, "COMMAND_RUNTIME_BINDING_MISSING", "command lacks runtime binding ref")

    if context:
        if context.get("task_id") != TASK_ID:
            add(blockers, "CONTEXT_TASK_MISMATCH", str(context.get("task_id")))
        if context.get("parent_task_id") != PARENT_TASK_ID:
            add(blockers, "CONTEXT_PARENT_MISMATCH", str(context.get("parent_task_id")))
        if context.get("workercoordinator_authority_observed") is not True:
            add(blockers, "WORKERCOORDINATOR_NOT_OBSERVED", "claim authority observation false/missing")
        if not context.get("worker_claim_ref"):
            add(blockers, "WORKER_CLAIM_REF_MISSING", "current claim ref absent")
        if not context.get("fence_ref"):
            add(blockers, "FENCE_REF_MISSING", "current fence ref absent")
        if not context.get("runtime_binding_ref"):
            add(blockers, "CONTEXT_RUNTIME_BINDING_MISSING", "runtime binding absent")
        if context.get("runtime_lease_observed") is not False:
            add(blockers, "PARALLEL_RUNTIME_LEASE_FORBIDDEN", "runtime_lease_observed must be false")

    if actuator:
        if actuator.get("preauthorized_controlled_surface") is not True:
            add(blockers, "ACTUATOR_NOT_PREAUTHORIZED", "controlled surface predicate false/missing")
        if actuator.get("credential_material_exposed") is True:
            add(blockers, "CREDENTIAL_EXPOSURE_FORBIDDEN", "actuator result reports credential exposure")

    if command and context:
        if command.get("runtime_binding_ref") != context.get("runtime_binding_ref"):
            add(blockers, "RUNTIME_BINDING_MISMATCH", "command/context runtime binding refs differ")
    if actuator and context:
        for field, code in (
            ("execution_subject", "SUBJECT_BINDING_MISMATCH"),
            ("control_surface", "CONTROL_SURFACE_BINDING_MISMATCH"),
            ("target_class", "TARGET_CLASS_BINDING_MISMATCH"),
        ):
            if actuator.get(field) != context.get(field):
                add(blockers, code, f"{field} differs between context and actuator result")
    if actuator and command and actuator.get("intr_decision_ref") not in (None, command.get("intr_decision_ref")):
        add(blockers, "ACTUATOR_INTR_DECISION_MISMATCH", "actuator and command InTr refs differ")

    blockers = sorted(blockers, key=lambda x: (x["code"], x["detail"]))
    result = {
        "schema": "stegverse.gadi-resident-execution-preflight/v1",
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "state": "READY_FOR_RESIDENT_CONSUMPTION" if not blockers else "BLOCKED_FAIL_CLOSED",
        "ready": not blockers,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "evidence_sha256": dict(sorted(digests.items())),
        "execution_claimed": False,
        "activation_claimed": False,
    }
    out = runtime / OUTPUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--runtime-root", type=Path, required=True)
    args = p.parse_args()
    result = preflight(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
