from __future__ import annotations

import json
import os
from pathlib import Path

TASK_ID = "KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001"
REQ = Path("data/current-evidence-reuse-requirements/KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001.json")
TASK = Path("data/canonical-task-records/KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001.json")
G7 = Path("evidence/global-runtime-evidence-closure-001/original/stegverse-org-allocator-TASK-2026-0011-G7-v2.json")
SV001 = Path("control/portable-workercoordinator-packages/sv001-bounded-autonomy.json")
CURRENT = Path("runtime-state/kv-bound-ephemeral-browser-projection/current-observations.json")


def load(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def node_context():
    paths = []
    explicit = str(os.environ.get("STEGVERSE_SOVEREIGN_NODE_MARKER") or "").strip()
    if explicit:
        paths.append(Path(explicit).expanduser())
    paths += [Path.home() / ".stegverse" / "node.json", Path("/etc/stegverse/node.json")]
    for path in paths:
        if path.is_file():
            try:
                marker = load(path)
            except Exception:
                continue
            if marker.get("node_id"):
                return {"connectivity_state": "ESTABLISHED", "node_id": marker["node_id"], "device_continuity_id": marker.get("device_continuity_id", ""), "route_source": str(path)}
    return {"connectivity_state": "UNRESOLVED"}


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
        "require_exact_node_route_match": True,
        "require_device_continuity_match_when_observed": True,
    })
    task = load(source / TASK)
    claim = task.get("worker_claim") or {}
    ecosystem = {"task_id": task.get("task_id"), "coordination_state": task.get("coordination_state"), "worker_claim_ref": claim.get("claim_ref"), "fence_ref": claim.get("fence_ref"), "invalidated_event_refs": [], "invalidated_predicates": []}
    g7 = load(source / G7)
    receipt = (g7.get("node_journal_entry") or {}).get("receipt") or {}
    events = [{"event_ref": str(G7), "evidence_class": "CANONICAL_ALLOCATOR_REPLAY", "verification_modes": {"REPLAY": (g7.get("node_journal_replay") or {}).get("state")}, "node_id": receipt.get("node_id"), "device_continuity_id": receipt.get("device_continuity_id"), "observed_predicates": ["AUTHENTIC_TASK_2026_0011_CLAIM_AND_FENCE_OBSERVED"]}]
    sv001 = load(source / SV001)
    rows = ((sv001.get("terminal_execution") or {}).get("duplicates_retained_non_custodial")) or []
    match = next((row for row in rows if isinstance(row, dict) and row.get("node_id") == receipt.get("node_id") and row.get("same_execution_reconstruction") == "PASS"), None)
    if match:
        events.append({"event_ref": str(SV001) + "#current-iphone-reconstruction", "evidence_class": "WORKERCOORDINATOR_RUNTIME_RECONSTRUCTION", "verification_modes": {"RECONSTRUCTION": "PASS"}, "node_id": match.get("node_id"), "observed_predicates": ["CURRENT_IPHONE_RUNTIME_AUTHENTIC"]})
    current = load(runtime / CURRENT) if (runtime / CURRENT).is_file() else {"observed_predicates": []}
    return {"node_context": node_context(), "current_requirements": requirements, "ecosystem_state": ecosystem, "indexed_events": events, "current_observations": current, "input_derived_automatically": True, "user_interaction_required": False}
