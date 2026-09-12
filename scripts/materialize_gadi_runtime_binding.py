#!/usr/bin/env python3
"""Materialize a non-authorizing GADI runtime-binding observation.

This projector reuses canonical HB runtime-presence/supervision evidence and the
validated retained StegBrowser/StegOS discovery observation. Runtime liveness and
runtime identity remain separate evidence classes: when the presence receipt omits
``resident.node_id``, identity may be supplied only by an existing canonical
sovereign-node declaration that is referenced by a COMPLETE sovereign bootstrap
receipt for the exact same runtime root. No identity is derived here.

The projector does not create a runtime, node, lease, claim/fence, InTr admission,
credential, or execution authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

TASK_ID = "GADI-RESIDENT-EXECUTION-001"
PARENT_TASK_ID = "GADI-001"
PROFILE_ID = "runtime-node:gadi-resident-execution-001"
PRESENCE_REL = Path("receipts/sovereign-host/runtime-presence.latest.json")
DISCOVERY_REL = Path("state/gadi-resident-execution/retained-node-discovery.json")
OUTPUT_REL = Path("state/gadi-resident-execution/runtime-binding.json")
DISCOVERY_SCHEMA = "stegverse.gadi-retained-node-discovery-observation/v1"
NODE_DECLARATION_SCHEMA = "stegverse.sovereign-node-declaration/v0.4"
BOOTSTRAP_SCHEMA = "stegverse.sovereign-runtime-self-bootstrap-receipt/v2"
CANONICAL_CARRIER_RUNTIME = "heartbeat_runtime.engine_v13.HeartbeatRuntime"
CANONICAL_WORKER_RUNTIME = "heartbeat_runtime.worker_runtime.WorkerCoordinator"
NODE_RE = re.compile(r"^SV-NODE-[0-9a-f]{24}$")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def canonical_hash(value: dict[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def default_node_marker() -> Path:
    return (Path.home() / ".stegverse" / "node.json").expanduser().resolve()


def default_bootstrap_receipt() -> Path:
    return (Path.home() / ".stegverse" / "heartbeat" / "bootstrap.latest.json").expanduser().resolve()


def _same_path(left: Any, right: Path) -> bool:
    if not nonempty(left):
        return False
    try:
        return Path(str(left)).expanduser().resolve() == right.expanduser().resolve()
    except Exception:
        return False


def resolve_declared_runtime_node(
    runtime: Path,
    *,
    node_marker: Path,
    bootstrap_receipt: Path,
) -> tuple[str | None, list[str], dict[str, Any]]:
    """Resolve an existing runtime-bound sovereign node declaration.

    The node declaration is identity evidence only. The bootstrap receipt must bind
    its exact path to the exact runtime root. This helper never derives or writes a
    node declaration.
    """
    errors: list[str] = []
    evidence: dict[str, Any] = {
        "node_marker_ref": str(node_marker),
        "bootstrap_receipt_ref": str(bootstrap_receipt),
        "node_marker_sha256": None,
        "bootstrap_receipt_sha256": None,
    }

    marker: dict[str, Any] = {}
    if not node_marker.is_file():
        errors.append("SOVEREIGN_NODE_DECLARATION_MISSING")
    else:
        try:
            marker = load(node_marker)
            evidence["node_marker_sha256"] = digest(node_marker)
        except Exception:
            errors.append("SOVEREIGN_NODE_DECLARATION_INVALID_JSON")

    node_id = marker.get("node_id") if marker else None
    if marker:
        if marker.get("schema") != NODE_DECLARATION_SCHEMA:
            errors.append("SOVEREIGN_NODE_DECLARATION_SCHEMA_MISMATCH")
        if marker.get("declared") is not True:
            errors.append("SOVEREIGN_NODE_NOT_DECLARED")
        if not isinstance(node_id, str) or NODE_RE.fullmatch(node_id) is None:
            errors.append("SOVEREIGN_NODE_DECLARATION_NODE_INVALID")
        if marker.get("credential_authority") != "TV/TVC":
            errors.append("SOVEREIGN_NODE_DECLARATION_CREDENTIAL_AUTHORITY_MISMATCH")
        authority_effect = str(marker.get("authority_effect") or "")
        if not authority_effect.endswith("NO_CREDENTIAL_OR_ROUTE_AUTHORITY"):
            errors.append("SOVEREIGN_NODE_DECLARATION_AUTHORITY_EFFECT_INVALID")

    bootstrap: dict[str, Any] = {}
    if not bootstrap_receipt.is_file():
        errors.append("SOVEREIGN_BOOTSTRAP_RECEIPT_MISSING")
    else:
        try:
            bootstrap = load(bootstrap_receipt)
            evidence["bootstrap_receipt_sha256"] = digest(bootstrap_receipt)
        except Exception:
            errors.append("SOVEREIGN_BOOTSTRAP_RECEIPT_INVALID_JSON")

    if bootstrap:
        if bootstrap.get("schema") != BOOTSTRAP_SCHEMA:
            errors.append("SOVEREIGN_BOOTSTRAP_SCHEMA_MISMATCH")
        if bootstrap.get("state") != "COMPLETE":
            errors.append("SOVEREIGN_BOOTSTRAP_NOT_COMPLETE")
        if not _same_path(bootstrap.get("runtime_root"), runtime):
            errors.append("SOVEREIGN_BOOTSTRAP_RUNTIME_ROOT_MISMATCH")
        if not _same_path(bootstrap.get("node_declaration_ref"), node_marker):
            errors.append("SOVEREIGN_BOOTSTRAP_NODE_DECLARATION_REF_MISMATCH")
        if bootstrap.get("credential_authority") != "TV/TVC":
            errors.append("SOVEREIGN_BOOTSTRAP_CREDENTIAL_AUTHORITY_MISMATCH")

    return (str(node_id) if not errors and isinstance(node_id, str) else None), errors, evidence


def materialize(
    runtime_root: Path,
    *,
    node_marker: Path | None = None,
    bootstrap_receipt: Path | None = None,
) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    presence_path = runtime / PRESENCE_REL
    discovery_path = runtime / DISCOVERY_REL
    marker_path = (node_marker or default_node_marker()).expanduser().resolve()
    bootstrap_path = (bootstrap_receipt or default_bootstrap_receipt()).expanduser().resolve()
    blockers: list[str] = []

    if not discovery_path.is_file():
        blockers.append("RETAINED_NODE_DISCOVERY_OBSERVATION_MISSING")
        discovery: dict[str, Any] = {}
    else:
        try:
            discovery = load(discovery_path)
        except Exception:
            discovery = {}
            blockers.append("RETAINED_NODE_DISCOVERY_OBSERVATION_INVALID_JSON")

    discovered_node = discovery.get("node_ref")
    if discovery:
        if discovery.get("schema") != DISCOVERY_SCHEMA:
            blockers.append("RETAINED_NODE_DISCOVERY_SCHEMA_MISMATCH")
        if discovery.get("task_id") != TASK_ID or discovery.get("parent_task_id") != PARENT_TASK_ID:
            blockers.append("RETAINED_NODE_DISCOVERY_TASK_MISMATCH")
        if discovery.get("state") != "CURRENT_RETAINED_NODE_DISCOVERY_OBSERVED":
            blockers.append("RETAINED_NODE_DISCOVERY_NOT_CURRENT")
        if not isinstance(discovered_node, str) or NODE_RE.fullmatch(discovered_node) is None:
            blockers.append("RETAINED_NODE_DISCOVERY_NODE_INVALID")
        if discovery.get("runtime_presence_observed") is not False:
            blockers.append("DISCOVERY_RUNTIME_PRESENCE_AUTHORITY_DRIFT")
        if discovery.get("runtime_supervision_observed") is not False:
            blockers.append("DISCOVERY_RUNTIME_SUPERVISION_AUTHORITY_DRIFT")
        if discovery.get("runtime_subject_bound") is not False:
            blockers.append("DISCOVERY_RUNTIME_BINDING_AUTHORITY_DRIFT")
        if discovery.get("execution_authority_granted") is not False:
            blockers.append("DISCOVERY_EXECUTION_AUTHORITY_DRIFT")
        if discovery.get("authority_effect") != "NONE_OBSERVATION_ONLY":
            blockers.append("DISCOVERY_AUTHORITY_EFFECT_INVALID")

    if not presence_path.is_file():
        blockers.append("RUNTIME_PRESENCE_RECEIPT_MISSING")
        presence: dict[str, Any] = {}
    else:
        try:
            presence = load(presence_path)
        except Exception:
            presence = {}
            blockers.append("RUNTIME_PRESENCE_RECEIPT_INVALID_JSON")

    resident = presence.get("resident") if isinstance(presence.get("resident"), dict) else {}
    heartbeat = presence.get("heartbeat_reference") if isinstance(presence.get("heartbeat_reference"), dict) else {}
    progress = presence.get("governed_progress") if isinstance(presence.get("governed_progress"), dict) else {}
    authority = presence.get("authority") if isinstance(presence.get("authority"), dict) else {}
    resident_node = resident.get("node_id")
    node_identity_source = "RUNTIME_PRESENCE_RECEIPT"
    declaration_evidence: dict[str, Any] = {
        "node_marker_ref": None,
        "bootstrap_receipt_ref": None,
        "node_marker_sha256": None,
        "bootstrap_receipt_sha256": None,
    }

    if not nonempty(resident_node):
        declared_node, declaration_errors, declaration_evidence = resolve_declared_runtime_node(
            runtime,
            node_marker=marker_path,
            bootstrap_receipt=bootstrap_path,
        )
        if declaration_errors:
            blockers.extend(declaration_errors)
            blockers.append("RESIDENT_NODE_ID_MISSING")
        else:
            resident_node = declared_node
            node_identity_source = "BOOTSTRAP_BOUND_SOVEREIGN_NODE_DECLARATION"

    if presence and presence.get("schema") != "stegverse.hb-runtime-presence-resident-observability/v1":
        blockers.append("RUNTIME_PRESENCE_SCHEMA_MISMATCH")
    if presence and presence.get("runtime_root") != str(runtime):
        blockers.append("RUNTIME_ROOT_SUBJECT_MISMATCH")
    if resident.get("runtime_alive_observed") is not True:
        blockers.append("RUNTIME_ALIVE_NOT_OBSERVED")
    if resident.get("present_worker_runtime_observed") is not True:
        blockers.append("PRESENT_WORKER_RUNTIME_NOT_OBSERVED")
    if resident.get("worker_cycle_fresh") is not True:
        blockers.append("WORKER_CYCLE_NOT_FRESH")
    if not nonempty(resident_node):
        blockers.append("RESIDENT_NODE_ID_MISSING")
    elif NODE_RE.fullmatch(str(resident_node)) is None:
        blockers.append("RESIDENT_NODE_ID_NOT_CANONICAL_STEGBROWSER_NODE")
    if nonempty(resident_node) and isinstance(discovered_node, str) and resident_node != discovered_node:
        blockers.append("DISCOVERED_NODE_RUNTIME_SUBJECT_MISMATCH")
    if heartbeat.get("heartbeat_grants_authority") is not False:
        blockers.append("HEARTBEAT_AUTHORITY_BOUNDARY_INVALID")
    if progress.get("runtime_signal_is_execution_receipt") is not False:
        blockers.append("RUNTIME_SIGNAL_EXECUTION_BOUNDARY_INVALID")
    if authority.get("credential_authority") != "TV/TVC":
        blockers.append("CREDENTIAL_AUTHORITY_MISMATCH")
    if authority.get("hb_authority_effect") != "NONE_REFERENCE_ONLY":
        blockers.append("HB_AUTHORITY_EFFECT_INVALID")
    if authority.get("projection_authority_effect") != "NONE_OBSERVATION_ONLY":
        blockers.append("PROJECTION_AUTHORITY_EFFECT_INVALID")
    if authority.get("github_token_runtime_authority") != "NONE":
        blockers.append("GITHUB_TOKEN_RUNTIME_AUTHORITY_INVALID")

    supervision_ref = resident.get("runtime_evidence_ref")
    supervision: dict[str, Any] = {}
    supervision_path: Path | None = None
    if not nonempty(supervision_ref):
        blockers.append("SUPERVISION_EVIDENCE_REF_MISSING")
    else:
        candidate = Path(str(supervision_ref))
        supervision_path = candidate if candidate.is_absolute() else runtime / candidate
        try:
            supervision_path = supervision_path.resolve()
            supervision_path.relative_to(runtime)
        except Exception:
            supervision_path = None
            blockers.append("SUPERVISION_EVIDENCE_ESCAPES_RUNTIME")
        if supervision_path is not None:
            if not supervision_path.is_file():
                blockers.append("SUPERVISION_EVIDENCE_MISSING")
            else:
                try:
                    supervision = load(supervision_path)
                except Exception:
                    blockers.append("SUPERVISION_EVIDENCE_INVALID_JSON")

    if supervision:
        if supervision.get("canonical_carrier_runtime") != CANONICAL_CARRIER_RUNTIME:
            blockers.append("CANONICAL_CARRIER_RUNTIME_IDENTITY_MISSING")
        if supervision.get("worker_runtime") != CANONICAL_WORKER_RUNTIME:
            blockers.append("CANONICAL_WORKER_RUNTIME_IDENTITY_MISSING")
        if supervision.get("carrier_active") is not True or supervision.get("worker_active") is not True:
            blockers.append("CANONICAL_SUPERVISION_NOT_ACTIVE")
        if supervision.get("separate_carrier_and_worker_processes") is not True:
            blockers.append("CARRIER_WORKER_SEPARATION_NOT_OBSERVED")
        if supervision.get("third_party_process_host_required") is not False:
            blockers.append("THIRD_PARTY_PROCESS_HOST_BOUNDARY_INVALID")
        if supervision.get("heartbeat_grants_execution_authority") is not False:
            blockers.append("SUPERVISION_HEARTBEAT_AUTHORITY_INVALID")

    blockers = sorted(set(blockers))
    if blockers:
        result = {
            "schema": "stegverse.gadi-runtime-binding-observation/v1",
            "task_id": TASK_ID,
            "parent_task_id": PARENT_TASK_ID,
            "profile_id": PROFILE_ID,
            "state": "RUNTIME_BINDING_UNOBSERVED_FAIL_CLOSED",
            "runtime_binding_ref": None,
            "runtime_root": str(runtime),
            "node_id": resident_node,
            "node_identity_source": node_identity_source,
            "discovered_node_ref": discovered_node,
            "source_discovery_ref": str(DISCOVERY_REL),
            "source_discovery_sha256": digest(discovery_path) if discovery_path.is_file() else None,
            "source_presence_ref": str(PRESENCE_REL),
            "source_presence_sha256": digest(presence_path) if presence_path.is_file() else None,
            **declaration_evidence,
            "blockers": blockers,
            "claim_or_fence_granted": False,
            "runtime_lease_granted": False,
            "execution_authority_granted": False,
            "heartbeat_grants_execution_authority": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "authority_effect": "NONE_OBSERVATION_ONLY",
        }
        write(runtime / OUTPUT_REL, result)
        return result

    core = {
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "profile_id": PROFILE_ID,
        "runtime_root": str(runtime),
        "node_id": str(resident_node),
        "node_identity_source": node_identity_source,
        "discovered_node_ref": str(discovered_node),
        "canonical_carrier_runtime": CANONICAL_CARRIER_RUNTIME,
        "canonical_worker_runtime": CANONICAL_WORKER_RUNTIME,
        "source_discovery_sha256": digest(discovery_path),
        "source_presence_sha256": digest(presence_path),
        "source_supervision_sha256": digest(supervision_path) if supervision_path is not None else None,
        "node_marker_sha256": declaration_evidence.get("node_marker_sha256"),
        "bootstrap_receipt_sha256": declaration_evidence.get("bootstrap_receipt_sha256"),
    }
    binding_hash = canonical_hash(core)
    result = {
        "schema": "stegverse.gadi-runtime-binding-observation/v1",
        **core,
        "state": "CURRENT_RUNTIME_SUBJECT_BOUND",
        "runtime_binding_ref": f"runtime://gadi/{binding_hash}",
        "source_discovery_ref": str(DISCOVERY_REL),
        "source_presence_ref": str(PRESENCE_REL),
        "source_supervision_ref": str(supervision_path.relative_to(runtime)) if supervision_path is not None else None,
        "node_marker_ref": declaration_evidence.get("node_marker_ref"),
        "bootstrap_receipt_ref": declaration_evidence.get("bootstrap_receipt_ref"),
        "retained_node_discovery_observed": True,
        "discovered_node_matches_runtime_subject": True,
        "runtime_alive_observed": True,
        "present_worker_runtime_observed": True,
        "worker_cycle_fresh": True,
        "claim_or_fence_granted": False,
        "runtime_lease_granted": False,
        "execution_authority_granted": False,
        "heartbeat_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }
    write(runtime / OUTPUT_REL, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--node-marker", type=Path, default=None)
    parser.add_argument("--bootstrap-receipt", type=Path, default=None)
    args = parser.parse_args()
    result = materialize(
        args.runtime_root,
        node_marker=args.node_marker,
        bootstrap_receipt=args.bootstrap_receipt,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] == "CURRENT_RUNTIME_SUBJECT_BOUND" else 2


if __name__ == "__main__":
    raise SystemExit(main())
