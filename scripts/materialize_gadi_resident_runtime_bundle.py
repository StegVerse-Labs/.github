#!/usr/bin/env python3
"""Materialize the GADI resident runtime bundle from already-observed source artifacts.

This script does not mint claims, fences, InTr decisions, runtime bindings, or actuator
results. It only validates and projects already-observed local evidence into the exact
files consumed by the GADI resident preflight/dispatcher.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_ID = "GADI-RESIDENT-EXECUTION-001"
PARENT_TASK_ID = "GADI-001"
SOURCE_DIR = Path("state/gadi-resident-execution/source")
COMMAND_SOURCE = SOURCE_DIR / "stegos-command.json"
INTR_SOURCE = SOURCE_DIR / "intr-admission.json"
CLAIM_SOURCE = SOURCE_DIR / "worker-claim.json"
ACTUATOR_SOURCE = SOURCE_DIR / "actuator-observation.json"
OUT_DIR = Path("state/gadi-resident-execution")
COMMAND_OUT = OUT_DIR / "command.json"
CONTEXT_OUT = OUT_DIR / "execution-context.json"
ACTUATOR_OUT = OUT_DIR / "actuator-result.json"
MANIFEST_OUT = OUT_DIR / "materialization.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def materialize(runtime_root: Path) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    blockers: list[str] = []
    source_paths = {
        "command": runtime / COMMAND_SOURCE,
        "intr": runtime / INTR_SOURCE,
        "claim": runtime / CLAIM_SOURCE,
        "actuator": runtime / ACTUATOR_SOURCE,
    }
    source: dict[str, dict[str, Any]] = {}
    source_sha: dict[str, str] = {}
    for name, path in source_paths.items():
        if not path.is_file():
            blockers.append(f"{name.upper()}_SOURCE_MISSING")
            continue
        try:
            source[name] = load(path)
            source_sha[name] = sha256(path)
        except Exception:
            blockers.append(f"{name.upper()}_SOURCE_INVALID_JSON")

    command = source.get("command", {})
    intr = source.get("intr", {})
    claim = source.get("claim", {})
    actuator = source.get("actuator", {})

    if command:
        command_state = command.get("command_state", command.get("state"))
        if command_state != "READY_FOR_RESIDENT_EXECUTION": blockers.append("COMMAND_NOT_READY")
        if command.get("task_id") not in (None, PARENT_TASK_ID, TASK_ID): blockers.append("COMMAND_TASK_MISMATCH")
        if not nonempty(command.get("intr_decision_ref")): blockers.append("COMMAND_INTR_REF_MISSING")
        if not nonempty(command.get("runtime_binding_ref")): blockers.append("COMMAND_RUNTIME_BINDING_MISSING")
        if command.get("intr_admission_observed") is not True: blockers.append("COMMAND_INTR_ADMISSION_NOT_OBSERVED")

    if intr:
        if intr.get("state") != "ADMITTED": blockers.append("INTR_NOT_ADMITTED")
        if not nonempty(intr.get("intr_decision_ref")): blockers.append("INTR_DECISION_REF_MISSING")
        if not nonempty(intr.get("runtime_binding_ref")): blockers.append("INTR_RUNTIME_BINDING_MISSING")

    if claim:
        if claim.get("task_id") != TASK_ID: blockers.append("CLAIM_TASK_MISMATCH")
        if claim.get("parent_task_id") not in (None, PARENT_TASK_ID): blockers.append("CLAIM_PARENT_MISMATCH")
        if claim.get("state") not in {"CLAIMED", "ACTIVE"}: blockers.append("WORKER_CLAIM_NOT_CURRENT")
        for field, code in (("worker_claim_ref","WORKER_CLAIM_REF_MISSING"),("fence_ref","FENCE_REF_MISSING"),("runtime_binding_ref","CLAIM_RUNTIME_BINDING_MISSING"),("control_surface","CONTROL_SURFACE_MISSING"),("target_class","TARGET_CLASS_MISSING"),("execution_subject","EXECUTION_SUBJECT_MISSING")):
            if not nonempty(claim.get(field)): blockers.append(code)
        if claim.get("workercoordinator_authority_observed") is not True: blockers.append("WORKERCOORDINATOR_NOT_OBSERVED")

    if actuator:
        if actuator.get("preauthorized_controlled_surface") is not True: blockers.append("ACTUATOR_NOT_PREAUTHORIZED")
        if actuator.get("credential_material_exposed") is True: blockers.append("CREDENTIAL_EXPOSURE_FORBIDDEN")
        for field in ("control_surface", "target_class", "execution_subject"):
            if not nonempty(actuator.get(field)): blockers.append(f"ACTUATOR_{field.upper()}_MISSING")

    if command and intr:
        if command.get("intr_decision_ref") != intr.get("intr_decision_ref"): blockers.append("INTR_DECISION_REF_MISMATCH")
        if command.get("runtime_binding_ref") != intr.get("runtime_binding_ref"): blockers.append("INTR_RUNTIME_BINDING_MISMATCH")
    if command and claim and command.get("runtime_binding_ref") != claim.get("runtime_binding_ref"):
        blockers.append("COMMAND_CLAIM_RUNTIME_BINDING_MISMATCH")
    if claim and actuator:
        for field in ("control_surface", "target_class", "execution_subject"):
            if claim.get(field) != actuator.get(field): blockers.append(f"CLAIM_ACTUATOR_{field.upper()}_MISMATCH")
    if command and actuator and actuator.get("intr_decision_ref") not in (None, command.get("intr_decision_ref")):
        blockers.append("ACTUATOR_INTR_DECISION_MISMATCH")
    if claim and actuator and actuator.get("runtime_binding_ref") not in (None, claim.get("runtime_binding_ref")):
        blockers.append("ACTUATOR_RUNTIME_BINDING_MISMATCH")

    blockers = sorted(set(blockers))
    ready = not blockers
    manifest = {
        "schema": "stegverse.gadi-resident-runtime-materialization/v1",
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "state": "MATERIALIZED_READY_FOR_PREFLIGHT" if ready else "MATERIALIZATION_BLOCKED_FAIL_CLOSED",
        "ready": ready,
        "blockers": blockers,
        "source_sha256": dict(sorted(source_sha.items())),
        "authority_minted": False,
        "execution_claimed": False,
        "activation_claimed": False,
    }
    if ready:
        context = {
            "task_id": TASK_ID,
            "parent_task_id": PARENT_TASK_ID,
            "workercoordinator_authority_observed": True,
            "worker_claim_ref": claim["worker_claim_ref"],
            "fence_ref": claim["fence_ref"],
            "runtime_binding_ref": claim["runtime_binding_ref"],
            "control_surface": claim["control_surface"],
            "target_class": claim["target_class"],
            "execution_subject": claim["execution_subject"],
            "runtime_lease_observed": False,
            "source_worker_claim_sha256": source_sha["claim"],
        }
        projected_actuator = dict(actuator)
        projected_actuator.setdefault("runtime_binding_ref", claim["runtime_binding_ref"])
        projected_actuator.setdefault("intr_decision_ref", command["intr_decision_ref"])
        write(runtime / COMMAND_OUT, command)
        write(runtime / CONTEXT_OUT, context)
        write(runtime / ACTUATOR_OUT, projected_actuator)
        manifest["outputs"] = {
            "command": str(COMMAND_OUT),
            "execution_context": str(CONTEXT_OUT),
            "actuator_result": str(ACTUATOR_OUT),
        }
    write(runtime / MANIFEST_OUT, manifest)
    return manifest


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--runtime-root", type=Path, required=True)
    args = p.parse_args()
    result = materialize(args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
