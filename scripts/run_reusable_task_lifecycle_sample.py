#!/usr/bin/env python3
from __future__ import annotations
import json, os
from pathlib import Path

def main() -> None:
    manifest_path = Path(os.environ["STEGVERSE_REUSABLE_TASK_MANIFEST"])
    result_path = Path(os.environ["STEGVERSE_REUSABLE_TASK_RESULT_PATH"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest.get("expected_evidence") or []
    if not isinstance(expected, list):
        raise SystemExit("expected_evidence must be a list")
    result = {
        "schema": "stegverse.reusable-task-runner-result/v1",
        "invocation_id": manifest["invocation_id"],
        "reusable_task_id": manifest["reusable_task_id"],
        "manifest_hash": manifest["manifest_hash"],
        "runtime_observed": True,
        "completion_evidence_observed": True,
        "completion_predicates_satisfied": expected,
        "operation": "BOUNDED_LOCAL_LIFECYCLE_SAMPLE",
        "side_effects": "NONE",
        "authority_effect": "NONE"
    }
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
