#!/usr/bin/env python3
"""Visit the GADI runtime only when current non-claim evidence is ready.

This wrapper does not create InTr admission, runtime binding, actuator evidence, or a
WorkerCoordinator claim. It locally resolves/validates the three non-claim source
classes. Only when those exact inputs are coherent and the separated carrier reference
already exists does it invoke the canonical targeted WorkerCoordinator entry point,
which remains the sole claim/fence authority.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "GADI-RESIDENT-EXECUTION-001"
SOURCE_DIR = Path("state/gadi-resident-execution/source")
COMMAND = SOURCE_DIR / "stegos-command.json"
INTR = SOURCE_DIR / "intr-admission.json"
ACTUATOR = SOURCE_DIR / "actuator-observation.json"
CARRIER = Path("control/heartbeat-carrier-runtime-state.json")
WORKER_RUNNER = Path("scripts/run_worker_runtime.py")
RECEIPT = Path("receipts/sovereign-host/gadi-targeted-runtime-readiness.latest.json")
CONSUMPTION = Path("receipts/sovereign-host/gadi-resident-execution-consumption.latest.json")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical_intr(value: dict[str, Any]) -> dict[str, Any]:
    nested = value.get("admission")
    return nested if isinstance(nested, dict) else value


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def readiness(source_root: Path, runtime_root: Path, *, runner=subprocess.run) -> dict[str, Any]:
    source = source_root.resolve()
    runtime = runtime_root.resolve()
    resolver = runtime / "scripts/resolve_gadi_resident_runtime_sources.py"
    if not resolver.is_file():
        resolver = source / "scripts/resolve_gadi_resident_runtime_sources.py"
    blockers: list[str] = []
    resolution: dict[str, Any] | None = None
    if not resolver.is_file():
        blockers.append("SOURCE_RESOLVER_NOT_MATERIALIZED")
    else:
        completed = runner(
            [sys.executable, str(resolver), "--runtime-root", str(runtime), "--defer-worker-claim"],
            cwd=runtime, capture_output=True, text=True, check=False, timeout=120,
        )
        resolution = parse_last_json(completed.stdout)
        if completed.returncode != 0 or not isinstance(resolution, dict) or resolution.get("state") != "SOURCE_RESOLUTION_COMPLETE":
            blockers.append("NONCLAIM_SOURCE_RESOLUTION_BLOCKED")

    values: dict[str, dict[str, Any]] = {}
    for name, rel in (("command", COMMAND), ("intr", INTR), ("actuator", ACTUATOR)):
        path = runtime / rel
        if not path.is_file():
            blockers.append(f"{name.upper()}_SOURCE_MISSING")
            continue
        try:
            values[name] = load(path)
        except Exception:
            blockers.append(f"{name.upper()}_SOURCE_INVALID_JSON")

    command = values.get("command", {})
    intr = canonical_intr(values.get("intr", {})) if values.get("intr") else {}
    actuator = values.get("actuator", {})

    if command:
        if command.get("task_id") not in ("GADI-001", TASK_ID, None): blockers.append("COMMAND_TASK_MISMATCH")
        if command.get("command_state", command.get("state")) != "READY_FOR_RESIDENT_EXECUTION": blockers.append("COMMAND_NOT_READY")
        if command.get("intr_admission_observed") is not True: blockers.append("COMMAND_INTR_ADMISSION_NOT_OBSERVED")
        for field in ("intr_decision_ref", "runtime_binding_ref", "control_surface", "target_class"):
            if not nonempty(command.get(field)): blockers.append(f"COMMAND_{field.upper()}_MISSING")
    if intr:
        if intr.get("state") != "ADMITTED": blockers.append("INTR_NOT_ADMITTED")
        if not nonempty(intr.get("intr_decision_ref")): blockers.append("INTR_DECISION_REF_MISSING")
    if actuator:
        if actuator.get("preauthorized_controlled_surface") is not True: blockers.append("ACTUATOR_NOT_PREAUTHORIZED")
        if actuator.get("credential_material_exposed") is True: blockers.append("CREDENTIAL_EXPOSURE_FORBIDDEN")
        for field in ("execution_subject", "control_surface", "target_class"):
            if not nonempty(actuator.get(field)): blockers.append(f"ACTUATOR_{field.upper()}_MISSING")
    if command and intr and command.get("intr_decision_ref") != intr.get("intr_decision_ref"):
        blockers.append("INTR_DECISION_REF_MISMATCH")
    if command and actuator:
        if command.get("control_surface") != actuator.get("control_surface"): blockers.append("CONTROL_SURFACE_MISMATCH")
        if command.get("target_class") != actuator.get("target_class"): blockers.append("TARGET_CLASS_MISMATCH")
        if actuator.get("intr_decision_ref") not in (None, command.get("intr_decision_ref")): blockers.append("ACTUATOR_INTR_DECISION_MISMATCH")
        if actuator.get("runtime_binding_ref") not in (None, command.get("runtime_binding_ref")): blockers.append("ACTUATOR_RUNTIME_BINDING_MISMATCH")

    carrier_present = (runtime / CARRIER).is_file()
    if not carrier_present:
        blockers.append("SEPARATED_CARRIER_REFERENCE_NOT_PRESENT")
    blockers = sorted(set(blockers))
    return {
        "schema": "stegverse.gadi-targeted-runtime-readiness/v1",
        "task_id": TASK_ID,
        "state": "NONCLAIM_RUNTIME_EVIDENCE_READY" if not blockers else "NONCLAIM_RUNTIME_EVIDENCE_PENDING",
        "ready": not blockers,
        "blockers": blockers,
        "source_resolution": resolution,
        "separated_carrier_reference_present": carrier_present,
        "workercoordinator_claim_created": False,
        "targeted_execution_attempted": False,
        "authority_effect": "NONE_READINESS_ONLY",
    }


def execute(source_root: Path, runtime_root: Path, *, runner=subprocess.run) -> dict[str, Any]:
    source = source_root.resolve()
    runtime = runtime_root.resolve()
    result = readiness(source, runtime, runner=runner)
    if not result["ready"]:
        write(runtime / RECEIPT, result)
        return result
    worker = runtime / WORKER_RUNNER
    if not worker.is_file():
        worker = source / WORKER_RUNNER
    if not worker.is_file():
        result = {**result, "state":"WORKER_RUNTIME_NOT_MATERIALIZED", "ready":False, "blockers":["WORKER_RUNTIME_NOT_MATERIALIZED"]}
        write(runtime / RECEIPT, result)
        return result
    completed = runner(
        [sys.executable, str(worker), "--root", str(runtime), "--task-id", TASK_ID],
        cwd=runtime, capture_output=True, text=True, check=False, timeout=1800,
    )
    worker_result = parse_last_json(completed.stdout)
    consumption = load(runtime / CONSUMPTION) if (runtime / CONSUMPTION).is_file() else None
    consumed = isinstance(consumption, dict) and consumption.get("state") == "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED"
    result = {
        **result,
        "state": "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED" if consumed else "TARGETED_WORKER_RUNTIME_VISITED_NO_CONSUMPTION",
        "targeted_execution_attempted": True,
        "worker_runtime_returncode": completed.returncode,
        "worker_runtime_result": worker_result,
        "consumption_receipt_observed": consumed,
        "workercoordinator_claim_created_by_wrapper": False,
        "authority_effect": "NONE_OR_EXISTING_WORKERCOORDINATOR_AUTHORITY_ONLY",
    }
    write(runtime / RECEIPT, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = execute(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
