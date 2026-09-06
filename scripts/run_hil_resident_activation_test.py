#!/usr/bin/env python3
"""Run the bounded HIL resident-runtime activation acceptance test.

This is an execution harness, not a receipt generator. It refuses hosted
GitHub/Render/Vercel/Cloudflare environments, runs the existing sovereign
bootstrap, sends one deterministic controlled Node->InTr materialization event
through the actual local HTTP ingress listener, invokes the existing HIL
materialization consumer, requires component-produced same-device ESRL LEASE_OPEN
evidence, and then requires the real HIL receipts from the materialized ESRL
runtime root.

PASS also requires the canonical resident dispatcher to have visited the HIL
consumer and the exact RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002 consumption
receipt to prove a terminal HIL transition. Merely observing a receiver receipt
or materialization receipt cannot substitute for the cross-task resident-request
consumption predicate.

Public Gateway observation is optional downstream evidence and is not an
activation prerequisite.

A PASS is authentic only when this script is executed on an eligible
StegVerse-owned/federated resident runtime with the current local HIL backend.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import consume_hil_intr_materialization_request as materialization  # noqa: E402
import serve_hil_intr_materialization_ingress as ingress  # noqa: E402

HOSTED_ENV = (
    "GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL",
    "CF_PAGES", "CLOUDFLARE_WORKERS",
)
CONTROLLED_PDF = b"%PDF-1.4\n% StegVerse HIL controlled resident activation test\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
RESIDENT_REQUEST_ID = "RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002"
TARGET_TASK = "SHWP-HIL-SOVEREIGN-RECEIVER-001"
RESIDENT_DISPATCH_REL = Path("receipts/sovereign-host/resident-request-dispatch.latest.json")
HIL_RESIDENT_CONSUMPTION_REL = Path("receipts/sovereign-host/hil-resident-execution-request-consumption.latest.json")


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_uri(value: object) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def select_materialization_result(batch: dict, materialization_id: str) -> dict:
    results = batch.get("results")
    if not isinstance(results, list):
        return {}
    for row in results:
        if isinstance(row, dict) and row.get("materialization_id") == materialization_id:
            return row
    return {}


def select_hil_dispatch_outcome(receipt: dict) -> dict:
    outcomes = receipt.get("outcomes")
    if not isinstance(outcomes, list):
        return {}
    for row in outcomes:
        if isinstance(row, dict) and row.get("consumer") == "hil":
            return row
    return {}


def validate_hil_dispatch_outcome(receipt: dict) -> bool:
    if receipt.get("schema") != "stegverse.resident-request-dispatch/v1":
        return False
    outcome = select_hil_dispatch_outcome(receipt)
    result = outcome.get("result") if isinstance(outcome.get("result"), dict) else {}
    return (
        outcome.get("attempted") is True
        and outcome.get("consumer_ref") == "scripts/consume_hil_resident_execution_request.py"
        and result.get("schema") == "stegverse.hil-resident-execution-request-consumption/v1"
        and result.get("request_id") == RESIDENT_REQUEST_ID
        and result.get("task_id") == TARGET_TASK
        and result.get("terminal_hil_transition_observed") is True
    )


def validate_hil_resident_consumption(receipt: dict) -> bool:
    return (
        receipt.get("schema") == "stegverse.hil-resident-execution-request-consumption/v1"
        and receipt.get("state") == "COMPLETED"
        and receipt.get("request_id") == RESIDENT_REQUEST_ID
        and receipt.get("task_id") == TARGET_TASK
        and receipt.get("mode") == "TARGETED_INDEPENDENT_TASK_CONTROL"
        and receipt.get("runtime_execution_attempted") is True
        and receipt.get("terminal_hil_transition_observed") is True
        and isinstance(receipt.get("terminal_hil_transition"), str)
        and bool(receipt.get("terminal_hil_transition"))
        and receipt.get("credential_authority") == "TV/TVC"
        and receipt.get("github_token_runtime_authority") == "NONE"
        and receipt.get("heartbeat_grants_execution_authority") is False
        and receipt.get("second_machine_required") is False
    )


def controlled_request(runtime_root: Path) -> tuple[dict, Path]:
    pdf_path = runtime_root / "controlled-input" / "hil-resident-activation-test.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists() and pdf_path.read_bytes() != CONTROLLED_PDF:
        raise RuntimeError("controlled_pdf_write_once_collision")
    pdf_path.write_bytes(CONTROLLED_PDF)
    payload_hash = digest_uri(CONTROLLED_PDF)
    seed = hashlib.sha256((str(runtime_root.resolve()) + "|" + payload_hash).encode()).hexdigest()
    body = {
        "schema": materialization.REQUEST_SCHEMA,
        "state": materialization.REQUEST_STATE,
        "materialization_id": "INTR-MAT-" + seed[:24],
        "operation_id": "HIL-RESIDENT-ACTIVATION-" + seed[24:40],
        "packet_id": "HIL-TEST-PACKET-" + seed[40:56],
        "payload_ref": str(pdf_path),
        "payload_hash": payload_hash,
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "transport_intent_hash": digest_uri({"operation": seed, "payload_hash": payload_hash}),
        "destination": dict(materialization.DESTINATION),
        "boundary_path": ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"],
        "downstream_owner_ref": materialization.DOWNSTREAM_OWNER,
        "event_triggered": True,
        "always_on_receiver_required": False,
        "second_user_device_required": False,
        "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
        "exact_packet_transport_retry_allowed": True,
        "blind_consequence_retry_allowed": False,
        "interlock_required": True,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "transport_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_transfer": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    body["request_hash"] = digest_uri(body)
    materialization.validate_request(body)
    return body, pdf_path


def node_trigger(request: dict) -> dict:
    seed = hashlib.sha256(request["request_hash"].encode()).hexdigest()
    entry = {
        "schema": ingress.NODE_OUTBOX_SCHEMA,
        "state": "LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY",
        "node_id": "SV-NODE-" + seed[:24],
        "interlock_id": "SV-IL-" + seed[24:48],
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "destination": request["destination"],
        "downstream_owner_ref": request["downstream_owner_ref"],
        "materialization_request": request,
        "network_delivery_observed": False,
        "runtime_materialization_observed": False,
        "receiver_receipt_observed": False,
        "tvc_receipt_observed": False,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_LOCAL_CONTINUITY_ONLY",
    }
    entry["outbox_entry_hash"] = digest_uri(entry)
    trigger = {
        "schema": ingress.NODE_TRIGGER_SCHEMA,
        "transport_origin": ingress.ORIGIN_NODE,
        "node_id": entry["node_id"],
        "interlock_id": entry["interlock_id"],
        "outbox_entry_hash": entry["outbox_entry_hash"],
        "node_outbox_entry": entry,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "authority_effect": "NONE_TRIGGER_ONLY",
    }
    trigger["trigger_sha256"] = digest_uri(trigger)
    return trigger


def post_node_trigger(runtime_root: Path, trigger: dict) -> dict:
    server = ingress.IngressServer(("127.0.0.1", 0), runtime_root, 1)
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    raw = canonical(trigger)
    req = Request(
        f"http://127.0.0.1:{port}{ingress.INGRESS_PATH}",
        data=raw,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-StegVerse-Transport": "InTr",
            "X-StegVerse-Transport-Origin": ingress.ORIGIN_NODE,
            "X-StegVerse-Payload-SHA256": hashlib.sha256(raw).hexdigest(),
        },
    )
    try:
        with urlopen(req, timeout=10) as response:
            receipt = json.loads(response.read().decode("utf-8"))
    finally:
        thread.join(timeout=10)
        server.server_close()
    if receipt.get("state") != "INGRESS_ADMITTED":
        raise RuntimeError("controlled_node_ingress_not_admitted")
    return receipt


def run(command: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False, timeout=3600)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_root.resolve()
    runtime = args.runtime_root.resolve()

    if any(truthy(os.environ.get(name)) for name in HOSTED_ENV):
        print(json.dumps({"state": "REJECTED", "reason": "HOSTED_VALIDATION_ENVIRONMENT_NOT_AUTHENTIC_RUNTIME"}))
        return 2

    env = dict(os.environ)
    for key in ("GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN"):
        env.pop(key, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"

    bootstrap = run(
        [sys.executable, str(source / "scripts/bootstrap_sovereign_runtime.py"),
         "--source-root", str(source), "--runtime-root", str(runtime),
         "--skip-post-bootstrap-stegfin"],
        cwd=source, env=env,
    )

    request, pdf_path = controlled_request(runtime)
    trigger = node_trigger(request)
    ingress_receipt = post_node_trigger(runtime, trigger)

    consumed = run(
        [sys.executable, str(runtime / "scripts/consume_hil_intr_materialization_request.py"),
         "--source-root", str(source), "--runtime-root", str(runtime)],
        cwd=runtime, env=env,
    )

    materialization_latest = runtime / "receipts/sovereign-host/hil-intr-materialization-consumption.latest.json"
    materialization_batch = load(materialization_latest) if materialization_latest.is_file() else {}
    materialization_result = select_materialization_result(materialization_batch, request["materialization_id"])
    esrl_lease_open = (
        materialization_result.get("state") == "MATERIALIZATION_EXECUTION_ATTEMPTED"
        and materialization_result.get("esrl_lease_state") == "LEASE_OPEN"
        and materialization_result.get("esrl_runtime_instantiated") is True
        and materialization_result.get("esrl_local_identity_verified") is True
        and materialization_result.get("same_device_execution_required") is True
        and materialization_result.get("requires_other_machine") is False
        and materialization_result.get("hil_public_https_rendezvous_observed") is False
        and materialization_result.get("public_gateway_readiness_verified") is False
    )

    execution_runtime_raw = materialization_result.get("esrl_runtime_root")
    execution_runtime = Path(str(execution_runtime_raw)).resolve() if isinstance(execution_runtime_raw, str) and execution_runtime_raw else None
    execution_runtime_valid = execution_runtime is not None and execution_runtime.is_dir()

    evidence = {
        "resident_request_dispatch": runtime / RESIDENT_DISPATCH_REL,
        "hil_resident_request_consumption": runtime / HIL_RESIDENT_CONSUMPTION_REL,
        "hil_intr_ingress": runtime / "receipts/sovereign-network/hil-intr-ingress.latest.json",
        "hil_materialization_consumption": materialization_latest,
        "resident_targeted_execution": (
            execution_runtime / "receipts/sovereign-host/resident-targeted-execution.latest.json"
            if execution_runtime_valid else runtime / "__missing_esrl_runtime__/resident-targeted-execution.latest.json"
        ),
        "hil_receiver": (
            execution_runtime / "receipts/hil-sovereign-receiver/SHWP-HIL-SOVEREIGN-RECEIVER-001.json"
            if execution_runtime_valid else runtime / "__missing_esrl_runtime__/SHWP-HIL-SOVEREIGN-RECEIVER-001.json"
        ),
    }
    observed = {name: path.is_file() for name, path in evidence.items()}
    dispatch_receipt = load(evidence["resident_request_dispatch"]) if observed["resident_request_dispatch"] else {}
    consumption_receipt = load(evidence["hil_resident_request_consumption"]) if observed["hil_resident_request_consumption"] else {}
    dispatch_ok = validate_hil_dispatch_outcome(dispatch_receipt)
    consumption_ok = validate_hil_resident_consumption(consumption_receipt)
    receiver = load(evidence["hil_receiver"]) if observed["hil_receiver"] else {}
    claim_ok = (
        isinstance(receiver.get("claim_id"), str)
        and bool(receiver.get("claim_id"))
        and isinstance(receiver.get("fencing_token"), int)
        and not isinstance(receiver.get("fencing_token"), bool)
    )
    ready = receiver.get("receiver_ready") is True
    passed = (
        all(observed.values())
        and dispatch_ok
        and consumption_ok
        and esrl_lease_open
        and execution_runtime_valid
        and claim_ok
        and ready
        and ingress_receipt.get("state") == "INGRESS_ADMITTED"
        and consumed.returncode == 0
    )

    result = {
        "schema": "stegverse.hil-resident-activation-acceptance/v1",
        "state": "PASS" if passed else "INCOMPLETE",
        "authentic_runtime_required": True,
        "hosted_validation_environment_rejected": True,
        "bootstrap_returncode": bootstrap.returncode,
        "materialization_consumer_returncode": consumed.returncode,
        "controlled_pdf_ref": str(pdf_path),
        "controlled_pdf_sha256": digest_uri(CONTROLLED_PDF),
        "controlled_materialization_id": request["materialization_id"],
        "canonical_resident_request_id": RESIDENT_REQUEST_ID,
        "ingress_state": ingress_receipt.get("state"),
        "resident_dispatch_hil_terminal_consumption_observed": dispatch_ok,
        "hil_resident_request_consumption_observed": consumption_ok,
        "esrl_lease_open_observed": esrl_lease_open,
        "same_device_execution_required": materialization_result.get("same_device_execution_required") is True,
        "requires_other_machine": materialization_result.get("requires_other_machine") is True,
        "public_observation_is_downstream_optional": materialization_result.get("public_observation_is_downstream_optional") is True,
        "public_gateway_readiness_verified": materialization_result.get("public_gateway_readiness_verified") is True,
        "public_gateway_origin": materialization_result.get("public_gateway_origin"),
        "execution_runtime_root": str(execution_runtime) if execution_runtime_valid else None,
        "evidence_observed": observed,
        "hil_fresh_claim_fence_observed": claim_ok,
        "hil_receiver_ready_observed": ready,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "g18_completion_required": False,
        "g18_claim_or_fence_consumed": False,
        "authority_effect": "NONE_TEST_OBSERVATION_ONLY",
        "observed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "remaining_after_pass": [
            "exact PDF custody receipt through receiver submission",
            "post-restart exact-byte reconstruction proof",
            "TVC HIL receiving/lifecycle receipt",
        ],
    }
    out = runtime / "receipts/sovereign-host/hil-resident-activation-test.latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
