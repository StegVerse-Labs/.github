from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

TASK_ID = "KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001"
REQ = Path("data/current-evidence-reuse-requirements/KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001.json")
TASK = Path("data/canonical-task-records/KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001.json")
G7 = Path("evidence/global-runtime-evidence-closure-001/original/stegverse-org-allocator-TASK-2026-0011-G7-v2.json")
SV001 = Path("control/portable-workercoordinator-packages/sv001-bounded-autonomy.json")
CURRENT = Path("runtime-state/kv-bound-ephemeral-browser-projection/current-observations.json")
DISCOVERY = Path("scripts/observe_gadi_retained_resident_discovery.py")
IPHONE_READBACK = Path("scripts/observe_gadi_current_iphone_discovery_receipt.py")
SHA_URI = re.compile(r"^sha256:[0-9a-f]{64}$")


def load(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def _module(path: Path, name: str):
    repository_root = str(path.resolve().parents[1])
    added = repository_root not in sys.path
    if added:
        sys.path.insert(0, repository_root)
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"module unavailable: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if added:
            try:
                sys.path.remove(repository_root)
            except ValueError:
                pass


def current_retained_iphone_route(source: Path):
    discovery = _module(source / DISCOVERY, "kv_route_discovery")
    readback = _module(source / IPHONE_READBACK, "kv_route_iphone_readback")
    for base in discovery.LOCAL_BASES:
        state, _raw, observed = discovery._probe(base)
        if state != "REACHABLE" or not isinstance(observed, dict):
            continue
        node_ref = str(observed.get("target_node_ref") or "")
        rstate, _rraw, wrapper = readback._probe(base, node_ref)
        if rstate != "REACHABLE" or not isinstance(wrapper, dict) or wrapper.get("state") != "EVIDENCE_AVAILABLE":
            continue
        evidence = wrapper.get("evidence") or {}
        projected = wrapper.get("_projected") or {}
        receipt1 = str(evidence.get("node_receipt_1_sha256") or "")
        if evidence.get("execution_surface") != "CURRENT_USER_IPHONE":
            continue
        if evidence.get("node_origin") != "STEGBROWSER_RESIDENT":
            continue
        if evidence.get("site_projection_observed") is not True:
            continue
        if not SHA_URI.fullmatch(receipt1):
            continue
        if projected.get("node_ref") != node_ref:
            continue
        return {
            "connectivity_state": "ESTABLISHED",
            "retained_node_ref": node_ref,
            "execution_surface": "CURRENT_USER_IPHONE",
            "node_origin": "STEGBROWSER_RESIDENT",
            "node_receipt_1_sha256": receipt1,
            "source_device_hb_reference": projected.get("source_device_hb_reference"),
            "current_observed_hb_reference": projected.get("current_observed_hb_reference"),
            "retained_node_observation_ref": projected.get("observation_ref"),
            "route_source": base + "/api/resident-rendezvous/v1/evidence/current-iphone-discovery",
            "authority_effect": "NONE_EVIDENCE_READ_ONLY",
        }
    return {"connectivity_state": "UNRESOLVED", "authority_effect": "NONE_EVIDENCE_READ_ONLY"}


def build_payload(source_root: Path, runtime_root: Path):
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    requirements = load(source / REQ)
    requirements.update({
        "required_coordination_state": "ACTIVE",
        "required_worker_claim_ref": "TASK-2026-0011:G7",
        "required_fence_ref": "FENCE7",
        "accepted_verification_modes": ["REPLAY", "RECONSTRUCTION"],
        "accepted_evidence_classes": ["CANONICAL_ALLOCATOR_REPLAY", "WORKERCOORDINATOR_RUNTIME_RECONSTRUCTION"],
        "require_exact_node_route_match": False,
        "require_device_continuity_match_when_observed": False,
    })
    task = load(source / TASK)
    claim = task.get("worker_claim") or {}
    ecosystem = {
        "task_id": task.get("task_id"),
        "coordination_state": task.get("coordination_state"),
        "worker_claim_ref": claim.get("claim_ref"),
        "fence_ref": claim.get("fence_ref"),
        "invalidated_event_refs": [],
        "invalidated_predicates": [],
    }
    g7 = load(source / G7)
    receipt = (g7.get("node_journal_entry") or {}).get("receipt") or {}
    events = [{
        "event_ref": str(G7),
        "evidence_class": "CANONICAL_ALLOCATOR_REPLAY",
        "verification_modes": {"REPLAY": (g7.get("node_journal_replay") or {}).get("state")},
        "node_id": receipt.get("node_id"),
        "device_continuity_id": receipt.get("device_continuity_id"),
        "observed_predicates": ["AUTHENTIC_TASK_2026_0011_CLAIM_AND_FENCE_OBSERVED"],
    }]
    sv001 = load(source / SV001)
    rows = ((sv001.get("terminal_execution") or {}).get("duplicates_retained_non_custodial")) or []
    match = next((row for row in rows if isinstance(row, dict) and row.get("node_id") == receipt.get("node_id") and row.get("same_execution_reconstruction") == "PASS"), None)
    if match:
        events.append({
            "event_ref": str(SV001) + "#current-iphone-reconstruction",
            "evidence_class": "WORKERCOORDINATOR_RUNTIME_RECONSTRUCTION",
            "verification_modes": {"RECONSTRUCTION": "PASS"},
            "node_id": match.get("node_id"),
            "observed_predicates": ["CURRENT_IPHONE_RUNTIME_AUTHENTIC"],
        })

    route = current_retained_iphone_route(source)
    current = load(runtime / CURRENT) if (runtime / CURRENT).is_file() else {"observed_predicates": []}
    current_predicates = set(current.get("observed_predicates") or [])
    if route.get("connectivity_state") == "ESTABLISHED":
        current_predicates.add("CURRENT_RETAINED_IPHONE_ROUTE_OBSERVED")
    current["observed_predicates"] = sorted(current_predicates)
    current["retained_iphone_route"] = route

    return {
        "node_context": route,
        "current_requirements": requirements,
        "ecosystem_state": ecosystem,
        "indexed_events": events,
        "current_observations": current,
        "input_derived_automatically": True,
        "user_interaction_required": False,
    }
