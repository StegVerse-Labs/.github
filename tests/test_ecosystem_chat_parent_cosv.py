from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)


class EcosystemChatParentCOSVTests(unittest.TestCase):
    def test_parent_task_vector_is_visible_and_canonical(self) -> None:
        record = json.loads((ROOT / "control" / "task-vectors" / "SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json").read_text())
        registry = json.loads((ROOT / "control" / "worker-registry.json").read_text())
        matches = [row for row in registry["tasks"] if row.get("task_id") == "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"]
        self.assertEqual(len(matches), 1)
        task = matches[0]

        self.assertEqual(record["profile"], "task.v1")
        self.assertEqual(record["level"], "task")
        self.assertEqual(record["exact_metrics"]["symbol_order"], "LRUIVGOCMTBEAP")
        self.assertTrue(cosv.validate_record(record))

        expected = cosv.encode_task({
            "lifecycle": "MACHINE_OWNED",
            "archive_ready": False,
            "unassigned_work": 0,
            "chat_owned_implementation": 0,
            "chat_owned_validation": 0,
            "chat_owned_integration": 0,
            "chat_owned_observation": 0,
            "chat_owned_credentials": 0,
            "canonical_owner_installed": True,
            "thread_required": False,
            "blocker_count": 0,
            "evidence_complete": False,
            "activated": False,
            "propagated": False,
        })
        self.assertEqual(expected, "50000000100000")
        self.assertEqual(record["vector"], expected)
        self.assertEqual(task["source_state_vector_ref"], "control/task-vectors/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json")
        self.assertEqual(task["machine_readable_state"]["cosv"]["vector"], record["vector"])
        self.assertEqual(task["machine_readable_state"]["cosv"]["vector_state"], "EMITTED")
        self.assertEqual(task["machine_readable_state"]["cosv"]["authority_effect"], "NONE")
        self.assertEqual(task["state"], "HANDOFF_READY")
        self.assertIsNone(task["claim_id"])
        self.assertFalse(task["archive_eligible"])
        fragment = json.loads((ROOT / "control" / "worker-registry.d" / "ecosystem-chat-sovereign-inference-parent-001.json").read_text())
        self.assertEqual(fragment["vector_projection_owner"], "control/worker-registry.json")
        self.assertFalse(fragment["vector_duplicate_source_allowed"])
        self.assertNotIn("source_state_vector_ref", fragment["tasks"][0])


if __name__ == "__main__":
    unittest.main()
