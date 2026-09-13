#!/usr/bin/env python3
"""Trigger one reusable task and advance it automatically until a real boundary."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from workers import reusable_task_lifecycle as lifecycle

REGISTRY = ROOT / "data" / "reusable-task-registry.json"
CONSTRUCTOR = ROOT / "scripts" / "materialize_reusable_task_construct.py"
DEFAULT_RECEIPT_DIR = ROOT / "receipts" / "reusable-task"
NATIVE_EMAIL_PRIMARY = "scripts/consume_native_email_action_monitor_request.py"
NATIVE_EMAIL_KV_RUNNER = ROOT / "scripts" / "consume_native_email_action_monitor_request_kv.py"

BOUNDARY_COMPLETE = "COMPLETION_PREDICATES_REQUIRE_EVIDENCE_RECONCILIATION"
BOUNDARY_NO_RUNNER = "NO_EXECUTABLE_RUNNER_DECLARED"
BOUNDARY_MISSING_RUNNER = "DECLARED_RUNNER_NOT_MATERIALIZED"
BOUNDARY_RUNNER_FAILED = "DECLARED_RUNNER_STOPPED_BEFORE_COMPLETION"
BOUNDARY_MASTER_RECORDS = "MASTER_RECORDS_CUSTODY_RECONSTRUCTION_REQUIRED"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_constructor():
    spec = importlib.util.spec_from_file_location("reusable_task_constructor", CONSTRUCTOR)
    if spec is None or spec.loader is None:
        raise SystemExit("unable to load reusable task constructor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_definition(reusable_task_id: str) -> dict[str, Any]:
    registry = load_json(REGISTRY)
    matches = [x for x in registry.get("tasks", []) if x.get("reusable_task_id") == reusable_task_id]
    if len(matches) != 1:
        raise SystemExit(f"reusable task identity must resolve exactly once: {reusable_task_id}")
    return matches[0]


def manifest_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        reusable_task_id=args.reusable_task_id,
        invocation_id=args.invocation_id,
        parameters_json=args.parameters_json,
        task_id=args.task_id,
        cosv_task_vector=args.cosv_task_vector,
        output=None,
    )


def safe_runner_path(ref: str) -> Path:
    rel = Path(ref)
    if rel.is_absolute() or ".." in rel.parts or rel.suffix != ".py" or not rel.parts or rel.parts[0] != "scripts":
        raise SystemExit(f"runner template is outside admitted script surface: {ref}")
    return ROOT / rel


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_runner_command(primary_ref: str, primary_runner: Path, parameters: dict[str, Any]) -> list[str]:
    effective_runner = primary_runner
    if primary_ref == NATIVE_EMAIL_PRIMARY:
        if not NATIVE_EMAIL_KV_RUNNER.is_file():
            raise SystemExit("RT-NATIVE-EMAIL-ACTION-MONITOR-001 KV-enforcing runner is not materialized")
        effective_runner = NATIVE_EMAIL_KV_RUNNER
    command = [sys.executable, str(effective_runner)]
    if primary_ref == NATIVE_EMAIL_PRIMARY:
        runtime_raw = str(parameters.get("runtime_root") or "").strip()
        if not runtime_raw:
            raise SystemExit("RT-NATIVE-EMAIL-ACTION-MONITOR-001 requires parameters.runtime_root")
        source_raw = str(parameters.get("source_root") or ROOT).strip()
        command.extend([
            "--source-root", str(Path(source_raw).expanduser().resolve()),
            "--runtime-root", str(Path(runtime_raw).expanduser().resolve()),
        ])
    return command


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reusable-task-id", required=True)
    parser.add_argument("--invocation-id", required=True)
    parser.add_argument("--parameters-json", required=True)
    parser.add_argument("--task-id")
    parser.add_argument("--cosv-task-vector")
    parser.add_argument("--receipt")
    args = parser.parse_args()

    definition = resolve_definition(args.reusable_task_id)
    constructor = load_constructor()
    manifest = constructor.build_manifest(manifest_args(args))
    parameters = manifest.get("parameters")
    if not isinstance(parameters, dict):
        raise SystemExit("manifest parameters must be an object")

    receipt_path = Path(args.receipt) if args.receipt else DEFAULT_RECEIPT_DIR / f"{args.invocation_id}.latest.json"
    manifest_path = receipt_path.with_name(f"{args.invocation_id}.manifest.json")
    result_path = receipt_path.with_name(f"{args.invocation_id}.runner-result.json")
    expiry_path = receipt_path.with_name(f"{args.invocation_id}.runner-expiry.json")
    residual_path = receipt_path.with_name(f"{args.invocation_id}.residual-recording.json")
    custody_request_path = receipt_path.with_name(f"{args.invocation_id}.master-records-request.json")
    write_json(manifest_path, manifest)

    runners = definition.get("runner_templates", [])
    if not isinstance(runners, list):
        raise SystemExit("runner_templates must be a list")
    completion_predicates = definition.get("completion_predicates", [])
    if not isinstance(completion_predicates, list):
        raise SystemExit("completion_predicates must be a list")

    receipt: dict[str, Any] = {
        "schema": "stegverse.reusable-task-trigger-receipt/v1",
        "invocation_id": args.invocation_id,
        "reusable_task_id": args.reusable_task_id,
        "task_id": args.task_id,
        "cosv_task_vector": args.cosv_task_vector,
        "manifest_hash": manifest["manifest_hash"],
        "trigger_accepted": True,
        "automation_mode": "ADVANCE_UNTIL_COMPLETION_OR_GOVERNED_BOUNDARY",
        "automatic_steps_attempted": [],
        "completion_predicates": completion_predicates,
        "completion_claimed": False,
        "authority_effect": "NONE_ORCHESTRATION_ONLY",
        "authority": manifest["authority"],
        "continuation": None,
    }

    if not runners:
        receipt["state"] = "BOUNDARY_RECORDED"
        receipt["boundary"] = {
            "kind": BOUNDARY_NO_RUNNER,
            "reason": "Reusable identity has no executable runner entrypoint.",
            "manual_intermediate_coordination_required": False,
            "required_next_binding": "DECLARE_OR_REUSE_AN_EXISTING_MACHINE_EXECUTABLE_RUNNER_ENTRYPOINT",
        }
        receipt["continuation"] = "AUTOMATION_STOPS_HERE_UNTIL_EXECUTABLE_BINDING_EXISTS"
        write_json(receipt_path, receipt)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return

    runner_refs = [str(x) for x in runners]
    for ref in runner_refs:
        if not safe_runner_path(ref).is_file():
            receipt["state"] = "BOUNDARY_RECORDED"
            receipt["boundary"] = {
                "kind": BOUNDARY_MISSING_RUNNER,
                "runner_ref": ref,
                "reason": "A declared runner dependency is not present in the materialized runtime source.",
                "manual_intermediate_coordination_required": False,
            }
            receipt["continuation"] = "MATERIALIZE_DECLARED_RUNNER_DEPENDENCY_THEN_RETRIGGER"
            write_json(receipt_path, receipt)
            print(json.dumps(receipt, indent=2, sort_keys=True))
            return

    primary_ref = runner_refs[0]
    primary_runner = safe_runner_path(primary_ref)
    receipt["primary_runner_ref"] = primary_ref
    receipt["effective_runner_ref"] = (
        "scripts/consume_native_email_action_monitor_request_kv.py"
        if primary_ref == NATIVE_EMAIL_PRIMARY
        else primary_ref
    )
    receipt["runner_dependency_refs"] = runner_refs[1:]

    env = os.environ.copy()
    env["STEGVERSE_REUSABLE_TASK_MANIFEST"] = str(manifest_path)
    env["STEGVERSE_REUSABLE_TASK_INVOCATION_ID"] = args.invocation_id
    env["STEGVERSE_REUSABLE_TASK_ID"] = args.reusable_task_id
    env["STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON"] = args.parameters_json
    env["STEGVERSE_REUSABLE_TASK_RESULT_PATH"] = str(result_path)
    env["STEGVERSE_REUSABLE_TASK_COMPLETION_PREDICATES_JSON"] = json.dumps(completion_predicates, separators=(",", ":"))
    if args.task_id:
        env["STEGVERSE_REUSABLE_TASK_TRACKING_TASK_ID"] = args.task_id
        env["STEGVERSE_REUSABLE_TASK_TRACKING_COSV"] = args.cosv_task_vector or ""

    command = build_runner_command(primary_ref, primary_runner, parameters)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    receipt["automatic_steps_attempted"].append({
        "runner_ref": receipt["effective_runner_ref"],
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    })

    if completed.returncode != 0:
        receipt["state"] = "BOUNDARY_RECORDED"
        receipt["boundary"] = {
            "kind": BOUNDARY_RUNNER_FAILED,
            "runner_ref": receipt["effective_runner_ref"],
            "returncode": completed.returncode,
            "reason": "Primary declared runner stopped before completion.",
            "manual_intermediate_coordination_required": False,
        }
        receipt["continuation"] = "RESOLVE_RECORDED_RUNNER_BOUNDARY_THEN_RETRIGGER_OR_CONTINUE_INDEPENDENT_WORK"
        write_json(receipt_path, receipt)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return

    if not result_path.is_file():
        receipt["state"] = "AUTOMATABLE_STEPS_EXHAUSTED"
        receipt["boundary"] = {
            "kind": BOUNDARY_COMPLETE,
            "reason": "Primary runner returned successfully without standardized completion evidence.",
            "manual_intermediate_coordination_required": False,
        }
        receipt["continuation"] = "RECONCILE_DECLARED_COMPLETION_EVIDENCE_AND_CONTINUE_DEPENDENT_WORK_WHEN_SATISFIED"
        write_json(receipt_path, receipt)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return

    result = lifecycle.load_json(result_path)
    lifecycle.validate_runner_result(
        result,
        invocation_id=args.invocation_id,
        reusable_task_id=args.reusable_task_id,
        manifest_hash=manifest["manifest_hash"],
        completion_predicates=completion_predicates,
    )
    expiry = lifecycle.build_runner_expiry(
        invocation_id=args.invocation_id,
        reusable_task_id=args.reusable_task_id,
        manifest_hash=manifest["manifest_hash"],
        runner_ref=receipt["effective_runner_ref"],
        returncode=completed.returncode,
        result=result,
    )
    residual = lifecycle.build_residual_recording(
        manifest=manifest,
        runner_result=result,
        runner_expiry=expiry,
    )
    write_json(expiry_path, expiry)
    write_json(residual_path, residual)
    receipt["state"] = "RUNTIME_EVIDENCE_RECONCILED"
    receipt["boundary"] = {
        "kind": BOUNDARY_MASTER_RECORDS,
        "reason": "Runner completion evidence and expiry were observed; independent Master Records custody and reconstruction are required before entropy recovery.",
        "manual_intermediate_coordination_required": False,
    }
    receipt["runner_result_ref"] = str(result_path)
    receipt["runner_expiry_ref"] = str(expiry_path)
    receipt["residual_recording_ref"] = str(residual_path)
    receipt["continuation"] = "SUBMIT_EXACT_CUSTODY_REQUEST_TO_MASTER_RECORDS_THEN_FINALIZE_ENTROPY_AFTER_DESTINATION_RECONSTRUCTION"
    write_json(receipt_path, receipt)
    custody_request = lifecycle.build_custody_request(
        manifest=manifest,
        trigger_receipt=receipt,
        runner_result=result,
        runner_expiry=expiry,
        residual_recording=residual,
    )
    write_json(custody_request_path, custody_request)
    receipt["master_records_custody_request_ref"] = str(custody_request_path)
    write_json(receipt_path, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
