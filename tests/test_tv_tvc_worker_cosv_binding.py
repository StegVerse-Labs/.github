from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "control" / "worker-registry.d" / "tv-tvc-resident-proof-001.json"
HANDOFF = ROOT / "handoffs" / "SHWP-TV-TVC-RESIDENT-PROOF-001.json"
NOTATION = "L R U I V G O C M T B E A P"
SOURCE_REF = "StegVerse-Labs/TVC/tasks/TVC-TV-CREDENTIAL-MIGRATION-089.json#machine_readable_state.cosv"


class TvTvcWorkerCosvBindingTests(unittest.TestCase):
    def _assert_cosv(self, value: dict) -> None:
        self.assertEqual(value["profile"], "task.v1")
        self.assertEqual(value["canonical_profile_ref"], "management/COSV_PROFILE_V1.json")
        self.assertEqual(value["notation"], NOTATION)
        self.assertEqual(value["width"], 14)
        self.assertRegex(value["vector"], r"^[0-9]{14}$")
        self.assertEqual(value["vector_state"], "EMITTED")
        self.assertEqual(value["authority_effect"], "NONE")

    def test_registry_task_exposes_vector_and_owner_vector_reference(self) -> None:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        task = data["tasks"][0]
        self.assertEqual(task["task_id"], "SHWP-TV-TVC-RESIDENT-PROOF-001")
        self.assertEqual(task["source_state_vector_ref"], SOURCE_REF)
        self._assert_cosv(task["machine_readable_state"]["cosv"])

    def test_handoff_task_matches_registry_vector_binding(self) -> None:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["tasks"][0]
        handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))["task"]
        self.assertEqual(handoff["source_state_vector_ref"], SOURCE_REF)
        self.assertEqual(
            handoff["machine_readable_state"]["cosv"]["vector"],
            registry["machine_readable_state"]["cosv"]["vector"],
        )
        self._assert_cosv(handoff["machine_readable_state"]["cosv"])

    def test_vector_domains_are_canonical(self) -> None:
        task = json.loads(REGISTRY.read_text(encoding="utf-8"))["tasks"][0]
        digits = [int(x) for x in task["machine_readable_state"]["cosv"]["vector"]]
        for index in (1, 8, 9, 11, 12, 13):
            self.assertIn(digits[index], (0, 1, 2))
        for index in (2, 3, 4, 5, 6, 7, 10):
            self.assertIn(digits[index], range(10))


if __name__ == "__main__":
    unittest.main()
