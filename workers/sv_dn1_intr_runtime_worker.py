#!/usr/bin/env python3
"""Fenced Universal InTr adjacent-hop runtime worker for SV-DN-1."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from heartbeat_runtime.independent_oscillator import current_reference
from heartbeat_runtime.intr_derived_carrier import derive_intr_carrier_signal, recover_intr_packet_bytes
from heartbeat_runtime.intr_subsignal_runtime import (
    default_heartbeat_runtime_root,
    persist_local_intr_subsignal,
)

TASK_ID = "SV-DN1-INTR-RUNTIME-001"
WORKER_ID = "sv-dn1-intr-runtime-worker"
UPSTREAM_TASK_ID = "SV-DN1-RESIDENT-OBSERVER-001"
UPSTREAM_TRANSITION = "SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE"
ROUTE_ID = "SV-DN-1-HF-PUBLIC"
TRANSPORT_PROFILE = "stegverse.universal-intr.adjacent-hop/v1"
RECEIPT_SCHEMA = "stegverse.sv-dn1.intr-runtime-receipt/v1"
UNIVERSAL_POLICY_ID = "STEGVERSE-UNIVERSAL-INTR-TRANSPORT-001"
BOUNDARY_FROM = "EXTERNAL_SYSTEM"
BOUNDARY_TO = "STEGOS_ECOSYSTEM"

BOUND_STATE_ENV = "STEGVERSE_BOUND_STATE_ROOT"
RESIDENT_STATE_ENV = "STEGVERSE_SV_DN1_RESIDENT_STATE_ROOT"
SOURCE_ROOT_ENV = "STEGVERSE_SV_DN1_SOURCE_ROOT"

DEFAULT_BOUND_STATE = Path.home() / ".stegverse" / "state" / "sv-dn1-intr-runtime"
DEFAULT_RESIDENT_STATE = Path.home() / ".stegverse" / "state" / "sv-dn1-resident-observer"
DEFAULT_SOURCE_ROOT = Path.home() / ".stegverse" / "source" / "stegverse-demo-suite"

NODE_MARKERS = (Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json")
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GIT_ASKPASS",
    "HF_TOKEN", "HUGGINGFACE_TOKEN", "HUGGING_FACE_HUB_TOKEN",
    "GOOGLE_ACCESS_TOKEN", "GOOGLE_REFRESH_TOKEN", "OAUTH_TOKEN",
)

REQUIRED_SOURCE_FILES = (
    Path("scripts/sv_dn1_stegverse_interlock.py"),
    Path("config/sv_dn1_runtime_source_manifest.json"),
)


class UpstreamPending(RuntimeError):
    """Authentic resident observation evidence is not yet available."""


class SourceUnavailable(RuntimeError):
    """Exact locally materialized source is unavailable or ambiguous."""


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_ref(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise UpstreamPending(f"required upstream evidence not present: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def read_source_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SourceUnavailable(f"required materialized source not present: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SourceUnavailable(f"expected source JSON object: {path}")
    return value


def find_node() -> tuple[Path, dict[str, Any]]:
    for path in NODE_MARKERS:
        if path.is_file():
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise RuntimeError("sovereign node marker must be an object")
            if value.get("declared") is not True:
                raise RuntimeError("sovereign node is not declared")
            if value.get("credential_authority") != "TV/TVC":
                raise RuntimeError("credential authority must be TV/TVC")
            if value.get("github_token_required") is not False:
                raise RuntimeError("InTr runtime may not require GitHub token")
            return path, value
    raise RuntimeError("no declared sovereign StegVerse node marker is available")


def validate_invocation(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        raise RuntimeError("unexpected invocation schema")
    task = invocation.get("task") or {}
    if task.get("task_id") != TASK_ID:
        raise RuntimeError("unexpected task_id")
    if task.get("worker_id") != WORKER_ID:
        raise RuntimeError("unexpected worker_id")
    if not task.get("claim_id"):
        raise RuntimeError("canonical scheduler claim is required")
    timing = task.get("heartbeat_timing") or {}
    if not isinstance(timing.get("fencing_token"), int):
        raise RuntimeError("fresh fencing token is required")

    handoff = invocation.get("handoff") or {}
    authority = handoff.get("authority") or {}
    if authority.get("credential_authority") != "TV/TVC":
        raise RuntimeError("handoff credential authority drift")
    if authority.get("github_token_required") is not False:
        raise RuntimeError("handoff may not require GitHub token")
    if authority.get("non_tv_tvc_secret_or_token_allowed") is not False:
        raise RuntimeError("handoff permits non-TV/TVC secret/token")
    if authority.get("repository_writeback_authority") is not False:
        raise RuntimeError("InTr runtime may not write repositories")
    if authority.get("sdk_admission_authority") is not False:
        raise RuntimeError("InTr runtime may not claim SDK admission")
    if authority.get("canonical_protocol_adoption_authority") is not False:
        raise RuntimeError("InTr runtime may not adopt Universal Interlock")
    if authority.get("heartbeat_grants_execution_authority") is not False:
        raise RuntimeError("heartbeat may not grant InTr execution authority")

    contract = handoff.get("input_contract") or {}
    if contract.get("upstream_task_id") != UPSTREAM_TASK_ID:
        raise RuntimeError("upstream task drift")
    if contract.get("upstream_transition_id") != UPSTREAM_TRANSITION:
        raise RuntimeError("upstream transition drift")
    if contract.get("route_id") != ROUTE_ID:
        raise RuntimeError("route id drift")
    if contract.get("transport_profile") != TRANSPORT_PROFILE:
        raise RuntimeError("transport profile drift")
    if contract.get("runtime_receipt_schema") != RECEIPT_SCHEMA:
        raise RuntimeError("receipt schema drift")
    if contract.get("canonical_protocol_adopted") is not True:
        raise RuntimeError("canonical Universal InTr policy adoption must be acknowledged")
    if contract.get("universal_intr_policy_id") != UNIVERSAL_POLICY_ID:
        raise RuntimeError("Universal InTr policy identity drift")
    if contract.get("boundary_from") != BOUNDARY_FROM or contract.get("boundary_to") != BOUNDARY_TO:
        raise RuntimeError("Universal InTr adjacent boundary drift")
    if contract.get("interlock_required_per_hop") is not True:
        raise RuntimeError("Universal InTr requires Interlock at each completed hop")
    if contract.get("receipt_hash_chain_required") is not True:
        raise RuntimeError("Universal InTr requires chained hop receipts")
    if contract.get("production_interlock_runtime_activated") is not False:
        raise RuntimeError("global Interlock runtime activation cannot be preclaimed")
    return dict(task)


def bound_state_root() -> Path:
    raw = str(os.getenv(BOUND_STATE_ENV) or "").strip()
    root = Path(raw).expanduser().resolve() if raw else DEFAULT_BOUND_STATE.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def resident_state_root() -> Path:
    raw = str(os.getenv(RESIDENT_STATE_ENV) or "").strip()
    return Path(raw).expanduser().resolve() if raw else DEFAULT_RESIDENT_STATE.expanduser().resolve()


def source_root() -> Path:
    raw = str(os.getenv(SOURCE_ROOT_ENV) or "").strip()
    root = Path(raw).expanduser().resolve() if raw else DEFAULT_SOURCE_ROOT.expanduser().resolve()
    if not root.is_dir() or not all((root / rel).is_file() for rel in REQUIRED_SOURCE_FILES):
        raise SourceUnavailable(f"exact materialized demo-suite source root unavailable: {root}")
    return root


def load_destination_validator(root: Path):
    path = root / "scripts" / "sv_dn1_stegverse_interlock.py"
    spec = importlib.util.spec_from_file_location("sv_dn1_intr_destination_validator", path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise SourceUnavailable("destination validator loader unavailable")
    spec.loader.exec_module(module)
    return module


def validate_materialized_manifest(root: Path) -> dict[str, Any]:
    manifest = read_source_json(root / "config" / "sv_dn1_runtime_source_manifest.json")
    if manifest.get("schema") != "stegverse.sv-dn1.runtime-source-manifest/v1":
        raise SourceUnavailable("wrong SV-DN-1 runtime source manifest schema")
    if manifest.get("hash_profile") != "git-blob-sha1":
        raise SourceUnavailable("unsupported SV-DN-1 source hash profile")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise SourceUnavailable("runtime source manifest has no pinned files")
    validator_ref = files.get("scripts/sv_dn1_stegverse_interlock.py")
    if not isinstance(validator_ref, str) or len(validator_ref) != 40:
        raise SourceUnavailable("destination validator is not pinned by runtime source manifest")
    return manifest


def load_upstream() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    root = resident_state_root()
    receipt = read_json(root / "receipts" / "latest.json")
    capture = read_json(root / "observed" / "source-capture.json")
    exchange = read_json(root / "observed" / "exchange.json")
    return receipt, capture, exchange


def validate_upstream(receipt: Mapping[str, Any], capture: Mapping[str, Any], exchange: Mapping[str, Any]) -> None:
    if receipt.get("task_id") != UPSTREAM_TASK_ID:
        raise RuntimeError("resident task identity mismatch")
    if receipt.get("state") != "COMPLETE":
        raise UpstreamPending("resident observer is not COMPLETE")
    if receipt.get("transition_id") != UPSTREAM_TRANSITION:
        raise RuntimeError("resident transition identity mismatch")
    if receipt.get("runtime_source_pin_verified") is not True:
        raise RuntimeError("resident runtime source pin not verified")
    if receipt.get("raw_response_sha256_present") is not True:
        raise RuntimeError("resident raw response digest not proven")
    if receipt.get("semantic_exchange_valid") is not True:
        raise RuntimeError("resident semantic exchange not proven")
    for field in ("credential_used", "github_token_used", "repository_writeback_performed", "sdk_admitted"):
        if receipt.get(field) is not False:
            raise RuntimeError(f"resident receipt forbidden claim: {field}")

    if capture.get("schema_version") != "stegverse.sv-dn1.source-capture/v1":
        raise RuntimeError("wrong source capture schema")
    if capture.get("source_system") != "huggingface":
        raise RuntimeError("wrong source capture system")
    if capture.get("raw_sha256") != receipt.get("raw_response_sha256"):
        raise RuntimeError("resident capture/raw digest mismatch")
    claims = capture.get("claims") or {}
    if claims.get("credential_used") is not False:
        raise RuntimeError("credentialed source capture not admitted")
    if claims.get("hugging_face_endorsement_claimed") is not False:
        raise RuntimeError("Hugging Face endorsement claim forbidden")

    if exchange.get("schema_version") != "stegverse.sv-dn1.interlock-exchange/v1":
        raise RuntimeError("wrong semantic exchange schema")
    if exchange.get("source_system") != "huggingface":
        raise RuntimeError("wrong semantic exchange source system")
    if exchange.get("exchange_id") != receipt.get("semantic_exchange_id"):
        raise RuntimeError("resident exchange identity mismatch")
    if exchange.get("source_object", {}).get("native_ref") != capture.get("final_url"):
        raise RuntimeError("capture/exchange source reference mismatch")
    if exchange.get("source_object", {}).get("observed_at") != capture.get("observed_at"):
        raise RuntimeError("capture/exchange observation time mismatch")
    if exchange.get("raw_evidence", {}).get("preserved_native_fields") != capture.get("parsed_json"):
        raise RuntimeError("capture/exchange native JSON mismatch")
    if exchange.get("far_side_receipt", {}).get("authority_effect") != "NONE":
        raise RuntimeError("far-side authority drift")
    if exchange.get("intr", {}).get("authority_effect") != "NONE":
        raise RuntimeError("exchange InTr authority drift")
    if exchange.get("intr", {}).get("previous_receipt_hash") != exchange.get("far_side_receipt", {}).get("transformation_hash"):
        raise RuntimeError("far-side/InTr lineage mismatch")


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def build_hb_carrier_binding(exchange: Mapping[str, Any], intr_receipt: Mapping[str, Any], *, now_ns: int | None = None) -> dict[str, Any]:
    sample_ns = time.time_ns() if now_ns is None else int(now_ns)
    reference = current_reference(now_ns=sample_ns)
    packet_bytes = canonical(dict(exchange))
    packet_id = "SV-DN1-INTR-" + hashlib.sha256(str(exchange.get("exchange_id") or "").encode("utf-8")).hexdigest()[:24]
    payload_hash = "sha256:" + hashlib.sha256(packet_bytes).hexdigest()
    receipt_hash = str(intr_receipt.get("receipt_hash") or "")
    if receipt_hash.startswith("sha256:"):
        receipt_hash = receipt_hash.split(":", 1)[1]
    signal = derive_intr_carrier_signal(
        packet_id=packet_id,
        payload_hash=payload_hash,
        sampled_unix_ms=sample_ns // 1_000_000,
        packet_bytes=packet_bytes,
        intr_transport_profile=TRANSPORT_PROFILE,
        boundary_from=BOUNDARY_FROM,
        boundary_to=BOUNDARY_TO,
        packet_receipt_hash=receipt_hash,
    )
    if signal["carrier"]["heartbeat_epoch"] != reference["epoch"] or signal["carrier"]["heartbeat_reference"] != reference["heartbeat_id"]:
        raise RuntimeError("HB-derived carrier/reference sampling mismatch")
    if recover_intr_packet_bytes(signal) != packet_bytes:
        raise RuntimeError("HB-derived carrier failed exact InTr packet recovery")
    body = {
        "schema": "stegverse.sv-dn1.hb-intr-carrier-binding-receipt/v1",
        "state": "COMPLETE",
        "transition_id": "SV_DN1_HB_INTR_CARRIER_BOUND",
        "route_id": ROUTE_ID,
        "exchange_id": exchange.get("exchange_id"),
        "intr_receipt_hash": intr_receipt.get("receipt_hash"),
        "heartbeat_epoch": reference["epoch"],
        "heartbeat_reference": reference["heartbeat_id"],
        "heartbeat_phase_offset_ns": reference["phase_offset_ns"],
        "carrier_signal_id": signal["signal_id"],
        "carrier_packet_id": signal["intr"]["packet_id"],
        "carrier_binding_sha256": signal["carrier"]["carrier_binding_sha256"],
        "channel_slot": signal["carrier"]["channel_slot"],
        "phase_slots": signal["carrier"]["phase_slots"],
        "phase_offset_deg": signal["carrier"]["phase_offset_deg"],
        "packet_sha256": signal["intr"]["packet_sha256"],
        "packet_recovery_verified": True,
        "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
        "heartbeat_grants_authority": False,
        "derived_carrier_grants_authority": False,
        "intr_packet_governance_external_to_heartbeat": True,
        "credential_authority": "TV/TVC",
        "credential_used": False,
        "repository_writeback_performed": False,
        "sdk_admitted": False,
        "authority_effect": "NONE_CARRIER_ONLY",
    }
    return {"receipt": {**body, "receipt_hash": sha256_ref(body)}, "signal": signal}


def execute(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if any(truthy(os.getenv(name)) for name in HOSTED_ENV):
        raise RuntimeError("hosted environments cannot execute sovereign SV-DN-1 InTr traversal")
    present = [name for name in FORBIDDEN_CREDENTIAL_ENV if truthy(os.getenv(name))]
    if present:
        raise RuntimeError("credential-bearing environment forbidden for SV-DN-1 InTr: " + ",".join(sorted(present)))

    node_path, _ = find_node()
    task = validate_invocation(invocation)
    source = source_root()
    manifest = validate_materialized_manifest(source)
    resident_receipt, capture, exchange = load_upstream()
    validate_upstream(resident_receipt, capture, exchange)

    validator = load_destination_validator(source)
    blockers = validator.validate_exchange(dict(exchange))
    if blockers:
        raise RuntimeError("StegVerse destination validation blocked exchange: " + ",".join(blockers))

    context = invocation.get("context") or {}
    observed_at = str(context.get("observed_at") or exchange.get("source_object", {}).get("observed_at") or "")
    if not observed_at:
        raise RuntimeError("InTr observed_at is unavailable")

    body = {
        "schema_version": RECEIPT_SCHEMA,
        "route_id": ROUTE_ID,
        "exchange_id": exchange["exchange_id"],
        "state": "COMPLETE",
        "observed_at": observed_at,
        "transport_profile": TRANSPORT_PROFILE,
        "source_transform_hash": exchange["far_side_receipt"]["transformation_hash"],
        "previous_receipt_hash": exchange["intr"]["previous_receipt_hash"],
        "destination_validation": "PASS",
        "lineage_verified": True,
        "claims": {
            "canonical_protocol_adopted": True,
            "universal_intr_policy_id": UNIVERSAL_POLICY_ID,
            "boundary_from": BOUNDARY_FROM,
            "boundary_to": BOUNDARY_TO,
            "interlock_required_per_hop": True,
            "receipt_hash_chain_required": True,
            "runtime_activation_claimed": False,
            "production_interlock_runtime_activated": False,
            "sdk_admitted": False,
            "hugging_face_endorsement_claimed": False,
            "credential_used": False,
        },
        "authority_effect": "NONE",
    }
    receipt = {"receipt_hash": sha256_ref(body), **body}

    carrier = build_hb_carrier_binding(exchange, receipt)
    shared_carrier = persist_local_intr_subsignal(
        root=default_heartbeat_runtime_root(),
        signal=carrier["signal"],
    )
    carrier_receipt_body = {
        key: value for key, value in carrier["receipt"].items() if key != "receipt_hash"
    }
    carrier_receipt_body["shared_hb_signal_ref"] = shared_carrier["signal_ref"]
    carrier_receipt_body["shared_hb_signal_sha256"] = shared_carrier["signal_sha256"]
    carrier["receipt"] = {
        **carrier_receipt_body,
        "receipt_hash": sha256_ref(carrier_receipt_body),
    }

    bound = bound_state_root()
    atomic_json(bound / "observed" / "exchange.json", exchange)
    atomic_json(bound / "observed" / "carrier-signal.json", carrier["signal"])
    atomic_json(bound / "receipts" / "latest.json", receipt)
    atomic_json(bound / "receipts" / "carrier-binding.latest.json", carrier["receipt"])

    return {
        "schema": "stegverse.sv-dn1.intr-worker-completion/v1",
        "state": "COMPLETE",
        "transition_id": "SV_DN1_ROUTE_SPECIFIC_INTR_COMPLETE",
        "task_id": TASK_ID,
        "worker_id": WORKER_ID,
        "claim_id": task.get("claim_id"),
        "fencing_token": (task.get("heartbeat_timing") or {}).get("fencing_token"),
        "node_declaration_ref": str(node_path),
        "source_basis_commit": manifest.get("source_basis_commit"),
        "resident_claim_id": resident_receipt.get("claim_id"),
        "resident_raw_response_sha256": resident_receipt.get("raw_response_sha256"),
        "exchange_id": exchange["exchange_id"],
        "intr_receipt_hash": receipt["receipt_hash"],
        "hb_carrier_binding_receipt_hash": carrier["receipt"]["receipt_hash"],
        "hb_carrier_signal_id": carrier["signal"]["signal_id"],
        "hb_carrier_packet_sha256": carrier["signal"]["intr"]["packet_sha256"],
        "hb_carrier_packet_recovery_verified": True,
        "hb_shared_signal_ref": shared_carrier["signal_ref"],
        "hb_shared_signal_sha256": shared_carrier["signal_sha256"],
        "heartbeat_epoch": carrier["receipt"]["heartbeat_epoch"],
        "heartbeat_reference": carrier["receipt"]["heartbeat_reference"],
        "hb_carrier_channel_slot": carrier["receipt"]["channel_slot"],
        "hb_carrier_phase_offset_deg": carrier["receipt"]["phase_offset_deg"],
        "route_id": ROUTE_ID,
        "transport_profile": TRANSPORT_PROFILE,
        "destination_validation": "PASS",
        "lineage_verified": True,
        "credential_authority": "TV/TVC",
        "credential_used": False,
        "github_token_used": False,
        "repository_writeback_performed": False,
        "sdk_admitted": False,
        "canonical_protocol_adopted": True,
        "universal_intr_policy_id": UNIVERSAL_POLICY_ID,
        "boundary_from": BOUNDARY_FROM,
        "boundary_to": BOUNDARY_TO,
        "interlock_required_per_hop": True,
        "receipt_hash_chain_required": True,
        "runtime_activation_claimed": False,
        "production_interlock_runtime_activated": False,
        "authority_effect": "NONE",
    }


def completed_response(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED",
        "transition_id": "SV_DN1_ROUTE_SPECIFIC_INTR_COMPLETE",
        "transition_sequence": 1,
        "expected_next_transition": "SV_DN1_SDK_0B_GOVERNED_EXECUTION",
        "checkpoint_ref": "receipts/latest.json",
        "evidence_refs": ["observed/exchange.json", "observed/carrier-signal.json", "receipts/latest.json", "receipts/carrier-binding.latest.json"],
        "intr_receipt_hash": result.get("intr_receipt_hash"),
        "hb_carrier_binding_receipt_hash": result.get("hb_carrier_binding_receipt_hash"),
        "hb_shared_signal_ref": result.get("hb_shared_signal_ref"),
        "hb_shared_signal_sha256": result.get("hb_shared_signal_sha256"),
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
    }


def wait_response(exc: Exception, transition: str) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "HANDOFF_READY",
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": "SV_DN1_ROUTE_SPECIFIC_INTR_COMPLETE",
        "error": str(exc),
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
        "blocker": {
            "dependency_class": "UPSTREAM_EVIDENCE",
            "problem_statement": str(exc),
            "solution_required": True,
            "may_remain_blocked": False,
            "next_solution_action": "Allow the exact upstream machine-owned predecessor to complete; do not substitute fixture or hosted evidence.",
            "machine_observable_release_condition": "authentic resident observer receipt/capture/exchange and exact materialized source are present",
            "physical_additional_machine_required": False,
            "third_party_runtime_required": False,
            "github_token_required": False,
            "non_tv_tvc_secret_or_token_required": False,
            "human_action_required": False,
        },
    }


def blocked_response(exc: Exception) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "BLOCKED",
        "transition_id": "SV_DN1_INTR_RUNTIME_BLOCKED",
        "transition_sequence": 1,
        "expected_next_transition": "SV_DN1_ROUTE_SPECIFIC_INTR_COMPLETE",
        "error": str(exc),
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
        "blocker": {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": str(exc),
            "solution_required": True,
            "may_remain_blocked": False,
            "next_solution_action": "Repair the exact route-specific InTr validation/runtime predicate and retry this same fenced task without widening authority.",
            "machine_observable_release_condition": "canonical destination validation and route-specific lineage checks pass",
            "physical_additional_machine_required": False,
            "third_party_runtime_required": False,
            "github_token_required": False,
            "non_tv_tvc_secret_or_token_required": False,
            "human_action_required": False,
        },
    }


def main() -> int:
    try:
        raw = sys.stdin.readline()
        invocation = json.loads(raw)
        if not isinstance(invocation, dict):
            raise RuntimeError("worker invocation must be a JSON object")
        result = execute(invocation)
        print(json.dumps(completed_response(result), sort_keys=True))
        return 0
    except UpstreamPending as exc:
        print(json.dumps(wait_response(exc, "SV_DN1_RESIDENT_OBSERVATION_PENDING"), sort_keys=True))
        return 0
    except SourceUnavailable as exc:
        print(json.dumps(wait_response(exc, "SV_DN1_EXACT_SOURCE_MATERIALIZATION_PENDING"), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps(blocked_response(exc), sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
