#!/usr/bin/env python3
"""Run one event-triggered CanonicalWork ingress cycle on the existing shared InTr admission.

The exact request is admitted in-process through the shared router's installed
CanonicalWork route (admit_canonical_work), which persists it write-once into
the durable queue. No listener, socket, timeout or receiver liveness is a
predicate of the ingress transition (DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from build_canonical_work_intr_request import resolve_task  # noqa: E402
import serve_hil_intr_materialization_ingress as transport_boundary  # noqa: E402
from workers import canonical_work_intr_ingress as relay_ingress  # noqa: E402
from workers import universal_intr_profiled_ingress as shared_ingress  # noqa: E402

DEFAULT_TASK_ID = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
INGRESS_SCHEMA = "stegverse.canonical-work-intr-materialization-ingress/v1"
CONSUMPTION_SCHEMA = "stegverse.canonical-work-intr-materialization-consumption/v1"
# No transport origin is declared here. An origin exists only when authentic
# provenance for it is supplied as explicit evidence (F50-01, F52-01, F52-02).
ORIGIN_PROVENANCE_PREDICATE = "CANONICAL_WORK_TRANSPORT_ORIGIN_AUTHENTICALLY_BOUND"
RETRY_ENTRYPOINT = "scripts/run_canonical_work_event_bootstrap.py::main"
FAIL_CLOSED_SCHEMA = "stegverse.canonical-work-event-bootstrap-fail-closed/v1"
# TVC_RELAY_EGRESS binds only through org-boundary/runtime/origin_attestation.py
# and a TV_EXPORT_HMAC_VERIFY surface the caller or materializer injects.
A4_VERIFIER_PREDICATE = relay_ingress.A4_VERIFIER_PREDICATE
BILATERAL_PREDICATE = relay_ingress.BILATERAL_PREDICATE
RELAY_EVIDENCE_FIELDS = ("authorization_id", "origin_organization", "origin_attestation")


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit("FAIL_CLOSED: " + reason)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object_required:{path}")
    return value


def validate_target_task(*, registry: Path, registry_shards: Path, task_id: str) -> dict[str, Any]:
    task, _ = resolve_task(task_id=task_id, registry=registry, registry_shards=registry_shards)
    require(task.get("task_id") == task_id, "canonical_task_identity_must_resolve_exactly_once")
    correlation_id = task.get("correlation_id")
    require(isinstance(correlation_id, str) and bool(correlation_id), "canonical_task_correlation_missing")
    coordination_state = task.get("coordination_state")
    active_pre_ingress = coordination_state == "ACTIVE" and task.get("checkout_state") in {"HANDOFF_READY", "CHECKED_OUT"}
    require(coordination_state == "PROPOSED" or active_pre_ingress, "canonical_task_not_ingress_projectable")
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


def run_builder(*, task_id: str, runtime: Path, registry: Path, registry_shards: Path, without_carrier_binding: bool) -> Path:
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
        "--registry-shards",
        str(registry_shards),
        "--payload-output",
        str(payload_dir),
        "--output",
        str(outbound),
    ]
    if without_carrier_binding:
        command.append("--without-carrier-binding")
    subprocess.run(command, cwd=str(ROOT), check=True)
    return outbound


def origin_fail_closed(detail: str, *, failed_predicate: str = ORIGIN_PROVENANCE_PREDICATE,
                       transport_origin: str | None = None) -> dict[str, Any]:
    return {
        "schema": FAIL_CLOSED_SCHEMA,
        "state": "FAIL_CLOSED",
        "disposition": "FAIL_CLOSED",
        "failed_predicate": failed_predicate,
        "detail": detail,
        "retry_entrypoint": RETRY_ENTRYPOINT,
        "admission_attempted": False,
        "queue_written": False,
        "receipt_written": False,
        "transport_origin": transport_origin,
        "carrier_binding_selects_origin": False,
        "authority_effect": "NONE_NO_EFFECT",
    }


def resolve_relay_provenance(evidence_path: Path, origin_verifier: Callable[..., Mapping[str, Any]] | None,
                             emission_verifier: Callable[[str], Mapping[str, Any] | None] | None = None) -> dict[str, Any]:
    """Bind TVC_RELAY_EGRESS from its evidence file and an injected TV/TVC verifier.

    The evidence carries the relay authorization id, the declared origin and the
    TV/TVC signature artifact. It is not proof: the ingress rebuilds the A4
    statement over the exact request and admits only on the authority's own
    receipt and on the claimed origin's own emission receipt for the packet.
    Without either verifier nothing is built, queued or receipted.
    """
    if origin_verifier is None:
        return origin_fail_closed(
            "--tvc-relay-authorization supplied but no TV_EXPORT_HMAC_VERIFY surface was injected; "
            "the relay origin is verified only through org-boundary/runtime/origin_attestation.py::verify",
            failed_predicate=A4_VERIFIER_PREDICATE, transport_origin=transport_boundary.ORIGIN_RELAY)
    if emission_verifier is None:
        return origin_fail_closed(
            "--tvc-relay-authorization supplied but no bilateral verifier was injected; a verified signature is "
            "not sender authentication without the claimed origin's emission receipt (" + relay_ingress.BILATERAL_SOURCE + ")",
            failed_predicate=BILATERAL_PREDICATE, transport_origin=transport_boundary.ORIGIN_RELAY)
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        evidence = None
    missing = [field for field in RELAY_EVIDENCE_FIELDS if not isinstance(evidence, dict) or not evidence.get(field)]
    if missing:
        return origin_fail_closed(f"--tvc-relay-authorization evidence lacks: {','.join(missing)}")
    return {
        "state": "BOUND",
        "transport_origin": transport_boundary.ORIGIN_RELAY,
        "authorization_id": str(evidence["authorization_id"]),
        "origin_organization": str(evidence["origin_organization"]),
        "origin_attestation": evidence["origin_attestation"],
        "origin_verifier": origin_verifier,
        "emission_verifier": emission_verifier,
        "carrier_binding_selects_origin": False,
    }


def resolve_transport_provenance(*, node_outbox_envelope: Path | None, tvc_relay_authorization: Path | None,
                                 origin_verifier: Callable[..., Mapping[str, Any]] | None = None,
                                 emission_verifier: Callable[[str], Mapping[str, Any] | None] | None = None) -> dict[str, Any]:
    """Resolve the transport origin from supplied authentic provenance only.

    TVC_RELAY_EGRESS binds through resolve_relay_provenance: relay evidence plus
    an injected TV/TVC verifier and bilateral verifier, with no default and no
    environment fallback.
    STEGOS_NODE_OUTBOX is unchanged and stays held unreachable here. Every other
    resolution is a no-effect FAIL_CLOSED naming what is missing. An HB carrier
    binding never selects an origin.
    """
    if node_outbox_envelope is None and tvc_relay_authorization is not None and tvc_relay_authorization.is_file():
        return resolve_relay_provenance(tvc_relay_authorization, origin_verifier, emission_verifier)
    missing = []
    for flag, path in (("--node-outbox-envelope", node_outbox_envelope), ("--tvc-relay-authorization", tvc_relay_authorization)):
        if path is None:
            missing.append(f"{flag} not supplied")
        elif not path.is_file():
            missing.append(f"{flag} evidence file absent: {path}")
        elif flag == "--tvc-relay-authorization":
            missing.append(f"{flag} supplied together with --node-outbox-envelope; exactly one origin is bound")
        else:
            missing.append(f"{flag} supplied but the admitted origin paths are held unreachable until the A4/TV-TVC surface exists")
    return origin_fail_closed("; ".join(missing))


def _origin_fail_closed_record(exc: BaseException) -> dict[str, Any] | None:
    """The ingress's no-effect FAIL_CLOSED record for a refused relay origin, if this is one."""
    record = getattr(exc, "record", None)
    if isinstance(record, dict) and record.get("state") == "FAIL_CLOSED" and record.get("failed_predicate"):
        return record
    return None


def post_one(*, runtime: Path, request_path: Path, provenance: dict[str, Any], admit: Any = None) -> dict[str, Any]:
    """Admit the bound transport body through the shared router's CanonicalWork route, in-process."""
    require(provenance.get("state") == "BOUND", "transport_origin_provenance_unbound")
    origin = provenance.get("transport_origin")
    require(origin in {transport_boundary.ORIGIN_NODE, transport_boundary.ORIGIN_RELAY}, "transport_origin_provenance_invalid")
    raw = provenance["transport_body"] if origin == transport_boundary.ORIGIN_NODE else request_path.read_bytes()
    headers = {
        "Content-Type": "application/json",
        "X-StegVerse-Transport": "InTr",
        "X-StegVerse-Transport-Origin": origin,
        "X-StegVerse-Payload-SHA256": hashlib.sha256(raw).hexdigest(),
    }
    kwargs: dict[str, Any] = {}
    if origin == transport_boundary.ORIGIN_RELAY:
        headers["X-StegVerse-Authorization-Id"] = str(provenance["authorization_id"])
        headers[relay_ingress.ORIGIN_ORGANIZATION_HEADER] = str(provenance["origin_organization"])
        headers[relay_ingress.ORIGIN_ATTESTATION_HEADER] = json.dumps(provenance["origin_attestation"], sort_keys=True)
        kwargs["origin_verifier"] = provenance["origin_verifier"]
        kwargs["emission_verifier"] = provenance.get("emission_verifier")
    admit = admit or getattr(shared_ingress, "admit_canonical_work", None)
    require(callable(admit), "canonical_work_admit_binding_missing")
    try:
        body = admit(runtime_root=runtime, body=raw, headers=headers, **kwargs)
    except ValueError as exc:
        if _origin_fail_closed_record(exc) is not None:
            raise
        raise SystemExit("FAIL_CLOSED: canonical_work_intr_admission_refused:" + str(exc)) from exc
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


def invoke_immediate_successor(*, task_id: str, runtime: Path) -> dict[str, Any]:
    """Immediately evaluate the admitted task through the existing WorkerCoordinator.

    This is the state-dependent continuation edge. It creates no scheduler,
    dispatcher, heartbeat authority, claim authority, or transition authority.
    The existing targeted WorkerCoordinator path performs all ordinary
    admission/claim/fence/InTr checks or Master Records organization records.
    """
    command = [
        sys.executable,
        str(ROOT / "scripts" / "run_worker_runtime.py"),
        "--root",
        str(runtime),
        "--task-id",
        task_id,
    ]
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=1200,
    )
    result = None
    for line in reversed([line.strip() for line in completed.stdout.splitlines() if line.strip()]):
        try:
            candidate = json.loads(line)
        except Exception:
            continue
        if isinstance(candidate, dict):
            result = candidate
            break
    return {
        "attempted": True,
        "command": command,
        "returncode": completed.returncode,
        "result": result,
        "stderr_tail": completed.stderr[-2000:],
        "carrier_trigger_required": False,
        "workercoordinator_remains_claim_fence_authority": True,
        "interlock_intr_remains_transition_authority": True,
        "master_records_limited_to_organization_records_and_reconstruction": True,
        "authority_effect": "NONE_STATE_DEPENDENT_CONTINUATION_CALL_ONLY",
    }


def persist_registry(*, task_id: str, registry: Path, registry_shards: Path, ingress_path: Path, consumption_path: Path) -> Path:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "apply_admitted_canonical_work_projection.py"),
            "--registry",
            str(registry),
            "--task-shards",
            str(registry_shards),
            "--ingress-receipt",
            str(ingress_path),
            "--consumption-receipt",
            str(consumption_path),
            "--apply",
        ],
        cwd=str(ROOT),
        check=True,
    )
    def runtime_ingress_state(task: dict[str, Any]) -> str | None:
        refs = task.get("runtime_refs")
        return refs.get("ingress_state") if isinstance(refs, dict) else None

    def valid_projected_state(task: dict[str, Any]) -> bool:
        if task.get("coordination_state") == "INGRESS_ADMITTED":
            return True
        return (
            task.get("coordination_state") == "ACTIVE"
            and task.get("checkout_state") == "CHECKED_OUT"
            and runtime_ingress_state(task) == "INGRESS_ADMITTED"
        )

    registry_value = load(registry)
    matches = [task for task in registry_value.get("tasks", []) if task.get("task_id") == task_id]
    if matches:
        require(len(matches) == 1 and valid_projected_state(matches[0]), "persisted_post_ingress_registry_invalid")
        return registry
    shard = registry_shards / f"{task_id}.json"
    require(shard.is_file(), "persisted_post_ingress_task_shard_missing")
    projected = load(shard)
    require(projected.get("task_id") == task_id and valid_projected_state(projected), "persisted_post_ingress_shard_invalid")
    return shard


def main() -> int:
    """The command line injects no TV/TVC verifier, so a relay run from it fails
    closed on A4_TV_TVC_ORIGIN_VERIFIER_PRESENT_AT_CUSTODY_OWNER."""
    return run(origin_verifier=None, emission_verifier=None)


def run(*, origin_verifier: Callable[..., Mapping[str, Any]] | None,
        emission_verifier: Callable[[str], Mapping[str, Any] | None] | None = None) -> int:
    """One cycle. `origin_verifier` is the custody owner's TV/TVC surface and
    `emission_verifier` the existing recorded_emission over the claimed origin's
    chain, both injected by the materializer; there is no default and no
    environment fallback."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    parser.add_argument("--registry", default=str(ROOT / "data" / "canonical-task-registry.json"))
    parser.add_argument("--registry-shards", default=str(ROOT / "data" / "canonical-task-records"))
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--consumer-timeout-seconds", type=float, default=5.0)
    parser.add_argument("--without-carrier-binding", action="store_true")
    parser.add_argument("--node-outbox-envelope", type=Path, help="existing validated node-trigger/outbox envelope evidence file")
    parser.add_argument("--tvc-relay-authorization", type=Path, help="existing TVC relay authorization evidence file")
    args = parser.parse_args()

    provenance = resolve_transport_provenance(node_outbox_envelope=args.node_outbox_envelope, tvc_relay_authorization=args.tvc_relay_authorization,
                                              origin_verifier=origin_verifier, emission_verifier=emission_verifier)
    if provenance.get("state") != "BOUND":
        print(json.dumps(provenance, indent=2, sort_keys=True))
        return 2

    require_shared_route()
    runtime = Path(args.runtime_root).expanduser().resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    registry = Path(args.registry).expanduser().resolve()
    registry_shards = Path(args.registry_shards).expanduser().resolve()
    validate_target_task(registry=registry, registry_shards=registry_shards, task_id=args.task_id)

    request_path = run_builder(
        task_id=args.task_id,
        runtime=runtime,
        registry=registry,
        registry_shards=registry_shards,
        without_carrier_binding=args.without_carrier_binding,
    )
    request = load(request_path)
    try:
        ingress = post_one(runtime=runtime, request_path=request_path, provenance=provenance)
    except ValueError as exc:
        refused = _origin_fail_closed_record(exc)
        if refused is None:
            raise
        print(json.dumps({**refused, "retry_entrypoint": RETRY_ENTRYPOINT}, indent=2, sort_keys=True))
        return 2
    materialization_id = str(ingress["materialization_id"])
    ingress_path = runtime / "receipts" / "sovereign-network" / "canonical-work-intr-ingress" / f"{materialization_id}.json"
    require(ingress_path.is_file(), "write_once_ingress_receipt_missing")
    consumption_path = wait_for_consumption(runtime=runtime, materialization_id=materialization_id, timeout_seconds=args.consumer_timeout_seconds)
    persisted_registry_path = persist_registry(
        task_id=args.task_id,
        registry=registry,
        registry_shards=registry_shards,
        ingress_path=ingress_path,
        consumption_path=consumption_path,
    )
    immediate_successor = invoke_immediate_successor(
        task_id=args.task_id,
        runtime=runtime,
    )

    receipt = {
        "schema": "stegverse.canonical-work-event-bootstrap-receipt/v1",
        "state": "INGRESS_CONSUMPTION_AND_PROJECTION_OBSERVED",
        "task_id": args.task_id,
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "request_ref": str(request_path),
        "ingress_receipt_ref": str(ingress_path),
        "governed_disposition": ingress.get("disposition"),
        "governed_disposition_authority": ingress.get("disposition_authority"),
        "governed_disposition_evidence_refs": [str(ingress_path), str(consumption_path)],
        "consumption_receipt_ref": str(consumption_path),
        "proposed_registry_projection_ref": str(persisted_registry_path),
        "persisted_registry_ref": str(persisted_registry_path),
        "resident_registry_state_persisted": True,
        "heartbeat_carrier_present": request.get("carrier_binding") is not None,
        "heartbeat_carrier_grants_authority": False,
        "oscillator_advanced_by_bootstrap": False,
        "shared_ingress_admission_implementation": "workers.universal_intr_profiled_ingress.admit_canonical_work",
        "in_process_write_once_admission": True,
        "receiver_liveness_predicate": False,
        "second_listener_implementation_created": False,
        "immediate_successor_evaluation": immediate_successor,
        "workercoordinator_claim_or_fence_observed": bool(
            isinstance(immediate_successor.get("result"), dict)
            and immediate_successor["result"].get("workers_activated", 0)
        ),
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
