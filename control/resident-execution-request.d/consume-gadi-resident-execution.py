#!/usr/bin/env python3
"""Consume the canonical GADI resident-execution request.

This adapter does not implement an actuator. It reuses the merged micro-node
GADI resident consumer and requires already-observed WorkerCoordinator claim/fence,
InTr admission, runtime binding, and controlled pre-authorized actuator result.
Missing runtime evidence fails closed and is never promoted into execution truth.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REQUEST_REL = Path("control/resident-execution-request.d/gadi-resident-execution-001.json")
RECEIPT_REL = Path("receipts/sovereign-host/gadi-resident-execution-consumption.latest.json")
TASK_ID = "GADI-RESIDENT-EXECUTION-001"
PARENT_TASK_ID = "GADI-001"
REQUEST_ID = "RESIDENT-EXEC-GADI-001"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def write_receipt(runtime: Path, receipt: dict[str, Any]) -> None:
    path = runtime / RECEIPT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def resolve_micro_node_root(runtime_root: Path) -> Path:
    configured = os.environ.get("STEGVERSE_MICRO_NODE_ROOT", "").strip()
    candidates = []
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.extend([
        runtime_root / "StegVerse-002" / "micro-node-runtime",
        runtime_root / "micro-node-runtime",
        Path.home() / ".stegverse" / "source" / "micro-node-runtime",
    ])
    for candidate in candidates:
        module = candidate.resolve() / "micro_node" / "gadi_resident_consumer.py"
        if module.is_file():
            return candidate.resolve()
    raise RuntimeError("merged micro-node GADI resident consumer source not materialized")


def load_consumer_module(micro_root: Path):
    path = micro_root / "micro_node" / "gadi_resident_consumer.py"
    spec = importlib.util.spec_from_file_location("stegverse_gadi_resident_consumer", path)
    require(spec is not None and spec.loader is not None, "cannot load GADI resident consumer module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def consume(source_root: Path, runtime_root: Path) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        request_path = source / REQUEST_REL
    require(request_path.is_file(), "resident execution request not materialized")
    request = load_json(request_path)

    require(request.get("schema") == "stegverse.resident-execution-request/v1", "request schema mismatch")
    require(request.get("request_id") == REQUEST_ID, "request id mismatch")
    require(request.get("state") == "REQUESTED", "request state mismatch")
    require(request.get("task_id") == TASK_ID, "request task mismatch")
    require(request.get("parent_task_id") == PARENT_TASK_ID, "request parent mismatch")
    require(request.get("mode") == "GADI_RESIDENT_DEFENSIVE_EXECUTION", "request mode mismatch")
    require(request.get("credential_authority") == "TV/TVC", "credential authority mismatch")
    require(request.get("github_token_runtime_authority") == "NONE", "GitHub runtime authority mismatch")
    require(request.get("heartbeat_grants_execution_authority") is False, "heartbeat authority mismatch")
    require(request.get("request_granted_authority") is False, "request authority mismatch")
    require(request.get("second_machine_required") is False, "second-machine invariant mismatch")
    require(request.get("network_source_fetch_allowed") is False, "network source fetch must remain disabled")
    require(request.get("requires_current_workercoordinator_claim_fence") is True, "claim/fence requirement missing")
    require(request.get("requires_current_intr_admission") is True, "InTr requirement missing")
    require(request.get("requires_exact_runtime_binding") is True, "runtime binding requirement missing")
    require(request.get("requires_preauthorized_controlled_actuator") is True, "actuator requirement missing")

    command_rel = Path(str(request["command_state_ref"]))
    context_rel = Path(str(request["execution_context_ref"]))
    actuator_rel = Path(str(request["actuator_result_ref"]))
    for rel in (command_rel, context_rel, actuator_rel):
        require(not rel.is_absolute() and ".." not in rel.parts, f"unsafe runtime evidence path: {rel}")

    command_path = runtime / command_rel
    context_path = runtime / context_rel
    actuator_path = runtime / actuator_rel
    require(command_path.is_file(), "current GADI resident command not observed")
    require(context_path.is_file(), "current WorkerCoordinator execution context not observed")
    require(actuator_path.is_file(), "controlled pre-authorized actuator result not observed")

    command = load_json(command_path)
    context_data = load_json(context_path)
    actuator_result = load_json(actuator_path)

    require(context_data.get("task_id") == TASK_ID, "execution context task mismatch")
    require(context_data.get("parent_task_id") == PARENT_TASK_ID, "execution context parent mismatch")
    require(context_data.get("workercoordinator_authority_observed") is True, "WorkerCoordinator observation missing")
    require(isinstance(context_data.get("worker_claim_ref"), str) and context_data["worker_claim_ref"].strip(), "worker claim missing")
    require(isinstance(context_data.get("fence_ref"), str) and context_data["fence_ref"].strip(), "fence missing")
    require(context_data.get("runtime_lease_observed") is False, "parallel runtime lease forbidden")

    require(actuator_result.get("preauthorized_controlled_surface") is True, "actuator surface is not pre-authorized/controlled")
    require(actuator_result.get("credential_material_exposed") is not True, "credential material exposure forbidden")
    require(actuator_result.get("authority_effect") in {None, "NONE", "NONE_EXECUTION_EVIDENCE_ONLY"}, "actuator authority drift")
    require(actuator_result.get("execution_subject") == context_data.get("execution_subject"), "actuator subject/context mismatch")
    require(actuator_result.get("control_surface") == context_data.get("control_surface"), "actuator control-surface/context mismatch")
    require(actuator_result.get("target_class") == context_data.get("target_class"), "actuator target/context mismatch")
    require(actuator_result.get("runtime_binding_ref") in {None, context_data.get("runtime_binding_ref")}, "actuator runtime binding mismatch")
    require(actuator_result.get("intr_decision_ref") in {None, command.get("intr_decision_ref")}, "actuator InTr decision mismatch")

    micro_root = resolve_micro_node_root(runtime)
    consumer = load_consumer_module(micro_root)
    execution_context = consumer.WorkerExecutionContext(
        worker_claim_ref=str(context_data["worker_claim_ref"]),
        fence_ref=str(context_data["fence_ref"]),
        runtime_binding_ref=str(context_data.get("runtime_binding_ref", "")),
        control_surface=str(context_data.get("control_surface", "")),
        target_class=str(context_data.get("target_class", "")),
        execution_subject=str(context_data.get("execution_subject", "")),
        workercoordinator_authority_observed=True,
        runtime_lease_observed=False,
    )

    def observed_actuator_result(_command, _context):
        return actuator_result

    micro_receipt = consumer.consume_resident_defensive_command(
        command=command,
        context=execution_context,
        actuator=observed_actuator_result,
    )

    receipt = {
        "schema": "stegverse.gadi-resident-execution-request-consumption/v1",
        "state": "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED",
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "request_id": REQUEST_ID,
        "resident_consumer_ref": request["resident_consumer_ref"],
        "micro_node_root": str(micro_root),
        "worker_claim_ref": micro_receipt["worker_claim_ref"],
        "fence_ref": micro_receipt["fence_ref"],
        "intr_decision_ref": micro_receipt["intr_decision_ref"],
        "runtime_binding_ref": micro_receipt["runtime_binding_ref"],
        "execution_subject": micro_receipt["execution_subject"],
        "control_surface": micro_receipt["control_surface"],
        "target_class": micro_receipt["target_class"],
        "command_consumed": micro_receipt["command_consumed"],
        "observed_state": micro_receipt["observed_state"],
        "effect_observed": micro_receipt["effect_observed"],
        "reassessment_required": micro_receipt["reassessment_required"],
        "stop_condition_observed": micro_receipt["stop_condition_observed"],
        "credential_material_exposed": False,
        "request_granted_authority": False,
        "execution_authority_minted": False,
        "scheduler_created": False,
        "runtime_created": False,
        "master_records_reconciliation_claimed": False,
        "second_machine_required": False,
        "authority_effect": "NONE_EXECUTION_EVIDENCE_ONLY",
        "micro_node_receipt": micro_receipt,
    }
    write_receipt(runtime, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Consume canonical GADI resident execution request")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = consume(args.source_root, args.runtime_root)
    except Exception as exc:
        receipt = {
            "schema": "stegverse.gadi-resident-execution-request-consumption/v1",
            "state": "GADI_RESIDENT_EXECUTION_BLOCKED_FAIL_CLOSED",
            "task_id": TASK_ID,
            "parent_task_id": PARENT_TASK_ID,
            "request_id": REQUEST_ID,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "request_granted_authority": False,
            "execution_authority_minted": False,
            "master_records_reconciliation_claimed": False,
            "authority_effect": "NONE_FAIL_CLOSED",
        }
        write_receipt(args.runtime_root.expanduser().resolve(), receipt)
        print(json.dumps(receipt, sort_keys=True))
        return 1
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
