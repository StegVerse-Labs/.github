#!/usr/bin/env python3
"""Visit the GADI runtime only when current non-claim evidence is ready.

This wrapper does not create InTr admission, runtime authority, actuator evidence, or a
WorkerCoordinator claim. It first observes the existing same-device retained-resident
discovery contract, then reads the already-persisted current-iPhone discovery receipt
for that exact node through the existing loopback listener, and only then refreshes the
non-authorizing GADI runtime-binding observation from canonical runtime-presence
evidence. WorkerCoordinator may be visited only when all three current observations
agree on the same retained subject and the remaining non-claim inputs are coherent.
"""
from __future__ import annotations

import argparse
import hashlib
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
DISCOVERY = Path("state/gadi-resident-execution/retained-resident-discovery.json")
DISCOVERY_OBSERVER = Path("scripts/observe_gadi_retained_resident_discovery.py")
CURRENT_IPHONE_RECEIPT = Path("state/gadi-resident-execution/current-iphone-discovery-receipt-readback.json")
CURRENT_IPHONE_RECEIPT_OBSERVER = Path("scripts/observe_gadi_current_iphone_discovery_receipt.py")
BINDING = Path("state/gadi-resident-execution/runtime-binding.json")
BINDING_PROJECTOR = Path("scripts/materialize_gadi_runtime_binding.py")
CARRIER = Path("control/heartbeat-carrier-runtime-state.json")
WORKER_RUNNER = Path("scripts/run_worker_runtime.py")
RECEIPT = Path("receipts/sovereign-host/gadi-targeted-runtime-readiness.latest.json")
CONSUMPTION = Path("receipts/sovereign-host/gadi-resident-execution-consumption.latest.json")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def digest_if_present(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


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
    blockers: list[str] = []

    discovery_observer = runtime / DISCOVERY_OBSERVER
    if not discovery_observer.is_file():
        discovery_observer = source / DISCOVERY_OBSERVER
    discovery_observation: dict[str, Any] | None = None
    if not discovery_observer.is_file():
        blockers.append("RETAINED_RESIDENT_DISCOVERY_OBSERVER_NOT_MATERIALIZED")
    else:
        completed = runner(
            [sys.executable, str(discovery_observer), "--runtime-root", str(runtime)],
            cwd=runtime, capture_output=True, text=True, check=False, timeout=30,
        )
        discovery_observation = parse_last_json(completed.stdout)
        if (
            completed.returncode != 0
            or not isinstance(discovery_observation, dict)
            or discovery_observation.get("state") != "CURRENT_RETAINED_RESIDENT_DISCOVERY_OBSERVED"
            or not nonempty(discovery_observation.get("target_node_ref"))
        ):
            blockers.append("CURRENT_RETAINED_RESIDENT_DISCOVERY_NOT_OBSERVED")

    receipt_observer = runtime / CURRENT_IPHONE_RECEIPT_OBSERVER
    if not receipt_observer.is_file():
        receipt_observer = source / CURRENT_IPHONE_RECEIPT_OBSERVER
    receipt_observation: dict[str, Any] | None = None
    discovered_node = discovery_observation.get("target_node_ref") if isinstance(discovery_observation, dict) else None
    discovery_current = (
        isinstance(discovery_observation, dict)
        and discovery_observation.get("state") == "CURRENT_RETAINED_RESIDENT_DISCOVERY_OBSERVED"
        and nonempty(discovered_node)
    )
    if not receipt_observer.is_file():
        blockers.append("CURRENT_IPHONE_RECEIPT_OBSERVER_NOT_MATERIALIZED")
    elif discovery_current:
        completed = runner(
            [
                sys.executable, str(receipt_observer),
                "--runtime-root", str(runtime),
                "--node-ref", str(discovered_node),
            ],
            cwd=runtime, capture_output=True, text=True, check=False, timeout=30,
        )
        receipt_observation = parse_last_json(completed.stdout)
        if (
            completed.returncode != 0
            or not isinstance(receipt_observation, dict)
            or receipt_observation.get("state") != "CURRENT_RETAINED_RESIDENT_CURRENT_IPHONE_RECEIPT_READBACK_OBSERVED"
            or receipt_observation.get("target_node_ref") != discovered_node
        ):
            blockers.append("CURRENT_RETAINED_RESIDENT_CURRENT_IPHONE_RECEIPT_NOT_OBSERVED")
    else:
        blockers.append("CURRENT_RETAINED_RESIDENT_CURRENT_IPHONE_RECEIPT_NOT_OBSERVED")

    receipt_current = (
        isinstance(receipt_observation, dict)
        and receipt_observation.get("state") == "CURRENT_RETAINED_RESIDENT_CURRENT_IPHONE_RECEIPT_READBACK_OBSERVED"
        and receipt_observation.get("target_node_ref") == discovered_node
    )

    binding_projector = runtime / BINDING_PROJECTOR
    if not binding_projector.is_file():
        binding_projector = source / BINDING_PROJECTOR
    binding_observation: dict[str, Any] | None = None
    if not binding_projector.is_file():
        blockers.append("RUNTIME_BINDING_PROJECTOR_NOT_MATERIALIZED")
    elif receipt_current:
        completed = runner(
            [sys.executable, str(binding_projector), "--runtime-root", str(runtime)],
            cwd=runtime, capture_output=True, text=True, check=False, timeout=120,
        )
        binding_observation = parse_last_json(completed.stdout)
        if (
            completed.returncode != 0
            or not isinstance(binding_observation, dict)
            or binding_observation.get("state") != "CURRENT_RUNTIME_SUBJECT_BOUND"
            or not nonempty(binding_observation.get("runtime_binding_ref"))
        ):
            blockers.append("CURRENT_RUNTIME_SUBJECT_BINDING_NOT_OBSERVED")
    else:
        blockers.append("CURRENT_RUNTIME_SUBJECT_BINDING_NOT_OBSERVED")

    if (
        discovery_current
        and receipt_current
        and discovery_observation.get("target_node_ref") != receipt_observation.get("target_node_ref")
    ):
        blockers.append("DISCOVERY_CURRENT_IPHONE_RECEIPT_SUBJECT_MISMATCH")

    if (
        discovery_current
        and isinstance(binding_observation, dict)
        and binding_observation.get("state") == "CURRENT_RUNTIME_SUBJECT_BOUND"
        and discovery_observation.get("target_node_ref") != binding_observation.get("node_id")
    ):
        blockers.append("DISCOVERY_RUNTIME_SUBJECT_MISMATCH")

    if (
        receipt_current
        and isinstance(binding_observation, dict)
        and binding_observation.get("state") == "CURRENT_RUNTIME_SUBJECT_BOUND"
        and receipt_observation.get("target_node_ref") != binding_observation.get("node_id")
    ):
        blockers.append("CURRENT_IPHONE_RECEIPT_RUNTIME_SUBJECT_MISMATCH")

    resolver = runtime / "scripts/resolve_gadi_resident_runtime_sources.py"
    if not resolver.is_file():
        resolver = source / "scripts/resolve_gadi_resident_runtime_sources.py"
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
    if binding_observation and binding_observation.get("state") == "CURRENT_RUNTIME_SUBJECT_BOUND" and command:
        if command.get("runtime_binding_ref") != binding_observation.get("runtime_binding_ref"):
            blockers.append("COMMAND_RUNTIME_BINDING_NOT_CURRENT_SUBJECT")
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
        "retained_resident_discovery_observation": discovery_observation,
        "current_iphone_discovery_receipt_readback": receipt_observation,
        "runtime_binding_observation": binding_observation,
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
    consumption_path = runtime / CONSUMPTION
    before_consumption_sha = digest_if_present(consumption_path)
    completed = runner(
        [sys.executable, str(worker), "--root", str(runtime), "--task-id", TASK_ID],
        cwd=runtime, capture_output=True, text=True, check=False, timeout=1800,
    )
    worker_result = parse_last_json(completed.stdout)
    after_consumption_sha = digest_if_present(consumption_path)
    fresh_receipt = after_consumption_sha is not None and after_consumption_sha != before_consumption_sha
    consumption = load(consumption_path) if fresh_receipt else None
    consumed = fresh_receipt and isinstance(consumption, dict) and consumption.get("state") == "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED"
    result = {
        **result,
        "state": "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED" if consumed else "TARGETED_WORKER_RUNTIME_VISITED_NO_NEW_CONSUMPTION",
        "targeted_execution_attempted": True,
        "worker_runtime_returncode": completed.returncode,
        "worker_runtime_result": worker_result,
        "consumption_receipt_changed_by_invocation": fresh_receipt,
        "consumption_receipt_sha256_before": before_consumption_sha,
        "consumption_receipt_sha256_after": after_consumption_sha,
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
