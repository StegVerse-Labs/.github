from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "STEGHEALTH-KV-INTERLOCK-PRODUCTION-ENDPOINT-001"
VECTOR = "60000000111000"
RT_ID = "RT-CANONICAL-WORK-PORTABLE-DISPATCH-001"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class StegHealthReusablePortableDispatchBindingTests(unittest.TestCase):
    def test_cosv_pointer_is_constructor_valid(self) -> None:
        vector = json.loads((ROOT / f"control/task-vectors/{TASK_ID}.json").read_text(encoding="utf-8"))
        index = json.loads((ROOT / f"control/task-vector-index.d/{TASK_ID}.json").read_text(encoding="utf-8"))
        self.assertEqual(vector["identity"], f"StegVerse-Labs/.github:task:{TASK_ID}")
        self.assertEqual(vector["vector"], VECTOR)
        self.assertEqual(index["task_id"], TASK_ID)
        self.assertEqual(index["vector"], VECTOR)
        self.assertEqual(index["source_state_vector_ref"], f"control/task-vectors/{TASK_ID}.json")
        self.assertEqual(index["authority_effect"], "NONE")

        constructor = load_module("steghealth_reusable_constructor", ROOT / "scripts/materialize_reusable_task_construct.py")
        manifest = constructor.build_manifest(argparse.Namespace(
            reusable_task_id=RT_ID,
            invocation_id=f"{TASK_ID}:PORTABLE-DISPATCH",
            parameters_json=json.dumps({
                "source_root": "/canonical/local/source",
                "runtime_root": "/resident/runtime",
                "only_consumer": "canonical_work_coordination",
                "goal_task_id": TASK_ID,
            }, sort_keys=True),
            task_id=TASK_ID,
            cosv_task_vector=VECTOR,
            output=None,
        ))
        self.assertEqual(manifest["task_id"], TASK_ID)
        self.assertEqual(manifest["cosv_task_vector"], VECTOR)
        self.assertEqual(manifest["reusable_task_id"], RT_ID)
        self.assertEqual(manifest["parameters"]["only_consumer"], "canonical_work_coordination")
        self.assertEqual(manifest["parameters"]["goal_task_id"], TASK_ID)

    def test_scheduler_supports_distinct_context_slot_without_changing_legacy_slot(self) -> None:
        scheduler = load_module("steghealth_neutral_scheduler", ROOT / "scripts/run_reusable_task_scheduler.py")
        now = scheduler.parse_now("2026-09-20T18:00:00Z")
        legacy = scheduler.slot_id(RT_ID, now)
        scoped = scheduler.slot_id(RT_ID, now, TASK_ID)
        self.assertEqual(legacy, "rt-canonical-work-portable-dispatch-001-20260920T18Z")
        self.assertEqual(scoped, "steghealth-kv-interlock-production-endpoint-001-20260920T18Z")
        self.assertNotEqual(legacy, scoped)


if __name__ == "__main__":
    unittest.main()
