#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SV-DN1-PRODUCTION-SOURCE-PREP-001"
VECTOR = "50000000102000"
BLOCKERS = {
    "CONTENT_ADDRESSED_SOURCE_PACKAGES_OR_ALREADY_LOCAL_ROOTS_REQUIRED_FOR_ANY_MISSING_COMPONENT",
    "SV_DN1_PRODUCTION_SOURCE_PREP_RECEIPT_NOT_YET_OBSERVED",
}

required = [
    "docs/SV_DN1_PRODUCTION_SOURCE_PREPARATION_MIRROR_HANDOFF.md",
    "docs/SV_DN1_PRODUCTION_SOURCE_PREP_COSV_MIRROR_HANDOFF.md",
    "handoffs/SV-DN1-PRODUCTION-SOURCE-PREP-001.json",
    "control/worker-registry.d/sv-dn1-production-source-prep-001.json",
    f"control/task-vectors/{TASK_ID}.json",
    "control/task-vector-index.json",
    "control/cosv-global-registry-coverage.json",
    "tests/test_sv_dn1_production_source_prep_cosv.py",
]
for rel in required:
    if not (ROOT / rel).is_file():
        raise SystemExit(f"missing SV-DN1 source prep COSV artifact: {rel}")

vector = json.loads((ROOT / f"control/task-vectors/{TASK_ID}.json").read_text(encoding="utf-8"))
registry = json.loads((ROOT / "control/worker-registry.d/sv-dn1-production-source-prep-001.json").read_text(encoding="utf-8"))
handoff = json.loads((ROOT / "handoffs/SV-DN1-PRODUCTION-SOURCE-PREP-001.json").read_text(encoding="utf-8"))
index = json.loads((ROOT / "control/task-vector-index.json").read_text(encoding="utf-8"))
coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text(encoding="utf-8"))

if vector.get("vector") != VECTOR or vector.get("authority_effect") != "NONE":
    raise SystemExit("SV-DN1 source prep vector mismatch or authority promotion")
if vector.get("exact_metrics", {}).get("blocker_count") != 3:
    raise SystemExit("SV-DN1 source prep blocker count mismatch")
task = registry["tasks"][0]
if set(task["admissible_existence"]["blockers"]) != BLOCKERS:
    raise SystemExit("SV-DN1 registry blocker parity mismatch")
if set(handoff["admissible_existence"]["blockers"]) != BLOCKERS:
    raise SystemExit("SV-DN1 handoff blocker parity mismatch")
rows = [x for x in index.get("tasks", []) if x.get("task_id") == TASK_ID]
if len(rows) != 1 or rows[0].get("vector") != VECTOR:
    raise SystemExit("SV-DN1 source prep index parity failure")
if TASK_ID in coverage.get("active_worker_task_ids_missing_canonical_cosv", []):
    raise SystemExit("SV-DN1 source prep remains active-unvectorized")
projection = coverage.get("sv_dn1_production_source_prep_projection", {})
if set(projection.get("blockers", [])) != BLOCKERS:
    raise SystemExit("SV-DN1 source prep projection blocker mismatch")
if projection.get("tvc_broker_head") != "b5288f9910ada26c6ab2e9bca3f7701afaae2cef":
    raise SystemExit("SV-DN1 source prep TVC broker head mismatch")
summary = coverage["worker_registry_summary"]
if summary["unique_task_ids_global_plus_fragments"] != 58:
    raise SystemExit("SV-DN1 worker denominator changed unexpectedly")
if summary["canonically_indexed_task_ids"] != 37 or summary["active_unvectorized_unique_task_ids"] != 14:
    raise SystemExit("SV-DN1 index/gap partition mismatch")
print("SV-DN1 production source prep COSV checks: PASS")
