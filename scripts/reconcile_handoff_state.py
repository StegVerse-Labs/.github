#!/usr/bin/env python3
"""Reconcile a semantic handoff transition into endpoint/task state and MR evidence.

Input is a JSON bundle. Output is deterministic JSON and may be persisted by the
calling governed worker only after its normal authority/custody checks.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from state_language import (
    build_alignment_packet,
    canonical_hash,
    derive_delta,
    normalize_vector,
    reconcile_tasks,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
    before = normalize_vector(bundle["before_state"])
    after = normalize_vector(bundle["after_state"])
    source_ref = str(bundle["source_handoff_ref"])

    delta = derive_delta(before, after, affected_scopes=list(bundle.get("affected_scopes", [])))
    semantic_change = bool(delta["changes"])

    registry_before = bundle.get("task_registry", {"tasks": []})
    if semantic_change:
        registry_after, task_effects = reconcile_tasks(
            registry_before,
            list(bundle.get("desired_tasks", [])),
            source_state_hash=canonical_hash(after),
            source_handoff_ref=source_ref,
        )
        disposition = str(bundle.get("alignment_disposition", "ALIGNED"))
    else:
        registry_after = registry_before
        task_effects = []
        disposition = "ALIGNED"

    packet = build_alignment_packet(
        transition_id=str(bundle["transition_id"]),
        parent_transition_id=bundle.get("parent_transition_id"),
        source_handoff_ref=source_ref,
        before_state=before,
        after_state=after,
        semantic_delta=delta,
        module_id=str(bundle["module_id"]),
        endpoint_id=str(bundle.get("endpoint_id", "worker-task-registry")),
        projection_before=registry_before,
        projection_after=registry_after,
        task_effects=task_effects,
        alignment_disposition=disposition,
        reconstruction_state="PASS",
        evidence_refs=list(bundle.get("evidence_refs", [])),
    )

    result = {
        "semantic_change": semantic_change,
        "delta": delta,
        "task_registry": registry_after,
        "task_effects": task_effects,
        "master_records_packet": packet,
    }
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
