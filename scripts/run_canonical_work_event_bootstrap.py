#!/usr/bin/env python3
"""Run one event-triggered CanonicalWork ingress cycle on the existing shared InTr listener.

This bootstrap does not define a second listener, heartbeat, oscillator, scheduler,
or WorkerCoordinator. It instantiates the repository's existing shared Universal
InTr Server for one loopback request, builds the request through the canonical
builder (including the HB-derived carrier binding by default), waits for the
non-authorizing CanonicalWork consumer receipt, and writes a proposed post-ingress
registry projection into the supplied runtime root.

The selected task MUST already exist exactly once in the canonical Task Registry,
MUST still be PROPOSED, and MUST explicitly allow INGRESS_ADMITTED as its next
transition. This bootstrap never creates task identity or claim/fence authority.

It fails closed unless CanonicalWork routing is already installed in the shared
router. Successful execution proves only the bounded ingress/consumption cycle it
actually observes; it does not prove WorkerCoordinator claim/fence, governed work,
Master Records reconciliation, egress, or completion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from workers import universal_intr_profiled_ingress as shared_ingress  # noqa: E402

DEFAULT_TASK_ID = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
INGRESS_SCHEMA = "stegverse.canonical-work-intr-materialization-ingress/v1"
CONSUMPTION_SCHEMA = "stegverse.canonical-work-intr-materialization-consumption/v1"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit("FAIL_CLOSED: " + reason)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object_required:{path}")
    return value


def validate_target_task(*, registry: Path, task_id: str) -> dict[str, Any]:
    document = load(registry)
    matches = [task for task in document.get("tasks", []) if task.get("task_id") == task_id]
    require(len(matches) == 1, "canonical_task_identity_must_resolve_exactly_once")
    task = matches[0]
    correlation_id = task.get("correlation_id")
    require(isinstance(correlation_id, str) and bool(correlation_id), "canonical_task_correlation_missing")
    require(task.get("coordination_state") == "PROPOSED", "canonical_task_not_proposed_for_ingress")
    require("INGRESS_ADMITTED" in task.get("allowed_next_transitions", []), "canonical_task_ingress_not_allowed")
    claim = task.get("worker_claim", {})
    require(claim.get("authority") == "WORKERCOORDINATOR", "canonical_task_workercoordinator_authority_missing")
    require(claim.get("projection_only") is True, "canonical_task_claim_projection_boundary_invalid")
    require(claim.get("claim_ref") is None and claim.get("fence_ref") is None, "canonical_task_already_has_claim_or_fence_projection")
    authority = task.get("authority_model", {})
    require(authority.get("task_registry_mints_execution_authority") is False, "canonical_task_registry_authority_drift")
    require(authority.get("interlock_intr_required_for_governed_ingress_egress") is True, "canonical_task_intr_boundary_missing")
    return task


def require_shared_route() -> None:
    profile = shared_ingress.profile(False)
    profiles = profile.get("profiles", [])
    require("CanonicalWork:Coordination" in profiles, "canonical_work_profile_not_installed_in_shared_router")
    require(hasattr(shared_ingress, "admit_canonical_work"), "canonical_work_admit_binding_missing")
    require(hasattr(shared_ingress, "is_canonical_work"), "canonical_work_route_predicate_missing")
    require(profile.get("heartbeat_derived_carrier") is not None, "hb_derived_carrier_profile_missing")
    require(profile.get("execution_authority") == "NONE", "shared_ingress_execution_authority_drift")


def run_builder(*, task_id: str, runtime: Path, registry: Path, without_carrier_binding: bool) -> Path:
    outbound = runtime / "outbound" / "canonical-work-request.json"
    payload_dir = runtime / "intr-payloads" / "canonical-work"
    outbound.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(ROOT / "scripts" / "build_canonical_work_intr_request.py"),
        task_id,
        "--operation",
        "TASK_INGRESS",
        "--registry",
        str(registry),
        "--payload-output",
        str(payload_dir),
        "--output",
        str(outbound),
    ]
    if without_carrier_binding:
        command.append("--without-carrier-binding")
    subprocess.run(command, cwd=str(ROOT), check=True)
    return outbound


def post_one(*, runtime: Path, request_path: Path) -> dict[str, Any]:
    server = shared_ingress.Server(("127.0.0.1", 0), runtime, 1)
    host, port = server.server_address
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    raw = request_path.read_bytes()
    request = urllib.request.Request(
        f"http://{host}:{port}{shared_ingress.INGRESS_PATH}",
        data=raw,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-StegVerse-Transport": "InTr",
            "X-StegVerse-Transport-Origin": "SOVEREIGN_NODE",
            "X-StegVerse-Payload-SHA256": hashlib.sha256(raw).hexdigest(),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status = int(response.status)
            body = json.loads(response.read().decode("utf-8"))
    finally:
        thread.join(timeout=10)
        server.server_close()
    require(status == 202, f"unexpected_ingress_http_status:{status}")
    require(isinstance(body, dict), "ingress_response_object_required")
    require(body.get("schema") == INGRESS_SCHEMA and body.get("state") == "INGRESS_ADMITTED", "canonical_work_ingress_not_admitted")
    require(body.get("claim_or_fence_minted") is False, "ingress_minted_claim_or_fence")
    return body


def wait_for_consumption(*, runtime: Path, materialization_id: str, timeout_seconds: float) -> Path:
    path = runtime / "receipts" / "sovereign-host" / "canonical-work-intr-materialization" / f"{materialization_id}.json"
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if path.is_file():
            value = load(path)
            require(value.get("schema") == CONSUMPTION_SCHEMA, "consumption_schema_mismatch")
            require(value.get("state") == "INGRESS_BOUND_COORDINATION_PROJECTED", "consumption_state_mismatch")
            require(value.get("claim_or_fence_minted") is False, "consumption_minted_claim_or_fence")
            return path
        time.sleep(0.05)
    raise SystemExit("FAIL_CLOSED: canonical_work_consumption_receipt_timeout")


def project_registry(*, task_id: str, registry: Path, ingress_path: Path, consumption_path: Path, runtime: Path) -> Path:
    output = runtime / "projections" / "canonical-task-registry.after-ingress.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "apply_admitted_canonical_work_projection.py"),
            "--registry",
            str(registry),
            "--ingress-receipt",
            str(ingress_path),
            "--consumption-receipt",
            str(consumption_path),
            "--output",
            str(output),
        ],
        cwd=str(ROOT),
        check=True,
    )
    projected = load(output)
    tasks = [task for task in projected.get("tasks", []) if task.get("task_id") == task_id]
    require(len(tasks) == 1 and tasks[0].get("coordination_state") == "INGRESS_ADMITTED", "post_ingress_registry_projection_invalid")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    parser.add_argument("--registry", default=str(ROOT / "data" / "canonical-task-registry.json"))
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--consumer-timeout-seconds", type=float, default=5.0)
    parser.add_argument("--without-carrier-binding", action="store_true")
    args = parser.parse_args()

    require_shared_route()
    runtime = Path(args.runtime_root).expanduser().resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    registry = Path(args.registry).expanduser().resolve()
    validate_target_task(registry=registry, task_id=args.task_id)

    request_path = run_builder(task_id=args.task_id, runtime=runtime, registry=registry, without_carrier_binding=args.without_carrier_binding)
    request = load(request_path)
    ingress = post_one(runtime=runtime, request_path=request_path)
    materialization_id = str(ingress["materialization_id"])
    ingress_path = runtime / "receipts" / "sovereign-network" / "canonical-work-intr-ingress" / f"{materialization_id}.json"
    require(ingress_path.is_file(), "write_once_ingress_receipt_missing")
    consumption_path = wait_for_consumption(runtime=runtime, materialization_id=materialization_id, timeout_seconds=args.consumer_timeout_seconds)
    projection_path = project_registry(task_id=args.task_id, registry=registry, ingress_path=ingress_path, consumption_path=consumption_path, runtime=runtime)

    receipt = {
        "schema": "stegverse.canonical-work-event-bootstrap-receipt/v1",
        "state": "INGRESS_CONSUMPTION_AND_PROJECTION_OBSERVED",
        "task_id": args.task_id,
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "request_ref": str(request_path),
        "ingress_receipt_ref": str(ingress_path),
        "consumption_receipt_ref": str(consumption_path),
        "proposed_registry_projection_ref": str(projection_path),
        "heartbeat_carrier_present": request.get("carrier_binding") is not None,
        "heartbeat_carrier_grants_authority": False,
        "oscillator_advanced_by_bootstrap": False,
        "shared_listener_implementation": "workers.universal_intr_profiled_ingress.Server",
        "second_listener_implementation_created": False,
        "workercoordinator_claim_or_fence_observed": False,
        "master_records_reconciliation_observed": False,
        "task_execution_observed": False,
        "task_egress_or_closure_observed": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "INGRESS_EVIDENCE_AND_PROJECTION_ONLY",
    }
    out = runtime / "receipts" / "sovereign-host" / "canonical-work-event-bootstrap.latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
