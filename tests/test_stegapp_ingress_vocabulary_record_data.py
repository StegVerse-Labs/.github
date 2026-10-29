"""Scoped record-data repair for the StegApp native ingress bootstrap edge.

The proposal is data for scripts/apply_task_record_data.py, never a hand edit or
an admission receipt.  Tests execute plan/apply only on temporary copies.
"""
import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apply_task_record_data as atr  # noqa: E402

REGISTRY = ROOT / "data" / "canonical-task-registry.json"
SHARDS = ROOT / "data" / "canonical-task-records"
DATA = (ROOT / "data" / "registry-record-data" /
        "stegapp-ephemeral-composition-ingress-vocabulary.v1.json")
TASK = "STEGAPP-EPHEMERAL-COMPOSITION-001"
EXISTING = [
    "REVIEW_REGISTRATION_PROPOSAL",
    "RESOLVE_OWNER_SCOPE",
    "SOURCE_CANDIDATE_REPAIR",
    "NATIVE_ADMISSION_EVALUATION",
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class StegAppIngressVocabularyRecordDataTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)
        self.registry = self.dir / "canonical-task-registry.json"
        self.shards = self.dir / "canonical-task-records"
        shutil.copy2(REGISTRY, self.registry)
        self.shards.mkdir()
        shutil.copy2(SHARDS / f"{TASK}.json", self.shards / f"{TASK}.json")
        self.tip = load(REGISTRY)["generation"]
        self.data = load(DATA)

    def run_apply(self, payload, write=True, tip=None):
        return atr.apply(
            payload,
            registry_path=self.registry,
            task_shards=self.shards,
            tip_generation=self.tip if tip is None else tip,
            write=write,
            root=self.dir,
            validators=(),
        )

    def row(self):
        rows = [row for row in load(self.registry)["tasks"] if row.get("task_id") == TASK]
        self.assertEqual(len(rows), 1)
        return rows[0]

    def record(self):
        return load(self.shards / f"{TASK}.json")

    def test_data_is_one_exact_non_authorizing_row_field_edit(self):
        self.assertEqual(self.data["schema"], atr.DATA_SCHEMA)
        self.assertEqual(self.data["authority_effect"], "NONE")
        self.assertEqual(self.data["registry_generation_base"], self.tip)
        self.assertNotIn("register_from_record", self.data)
        self.assertNotIn("work_items", self.data)
        self.assertNotIn("human_actions", self.data)
        self.assertEqual(len(self.data["row_fields"]), 1)
        edit = self.data["row_fields"][0]
        self.assertEqual(edit["task_id"], TASK)
        self.assertEqual(edit["path"], ["allowed_next_transitions"])
        self.assertEqual(edit["before"], EXISTING)
        self.assertEqual(edit["after"], EXISTING + ["INGRESS_ADMITTED"])

    def test_preconditions_hold_on_exact_aggregate_row_and_shard(self):
        row, record = self.row(), self.record()
        self.assertEqual(row["coordination_state"], "PROPOSED")
        self.assertEqual(record["coordination_state"], "PROPOSED")
        self.assertEqual(row["checkout_state"], "UNCLAIMED")
        self.assertEqual(record["checkout_state"], "UNCLAIMED")
        self.assertEqual(row["allowed_next_transitions"], EXISTING)
        self.assertEqual(record["allowed_next_transitions"], EXISTING)
        self.assertFalse(record["worker_claim"]["claim_ref"])
        self.assertFalse(record["worker_claim"]["fence_ref"])
        self.assertFalse(record["completion"]["claimed"])
        self.assertFalse(record["completion"]["validated"])

    def test_plan_allows_tip_plus_one_and_writes_nothing(self):
        before = (self.registry.read_bytes(), (self.shards / f"{TASK}.json").read_bytes())
        report = self.run_apply(self.data, write=False)
        self.assertEqual(report["disposition"], "ALLOW")
        self.assertEqual(report["generation"], self.tip + 1)
        self.assertFalse(report["files_changed"])
        self.assertEqual(report["records_changed"], [f"{TASK}.json"])
        self.assertEqual(before, (self.registry.read_bytes(),
                                  (self.shards / f"{TASK}.json").read_bytes()))

    def test_apply_changes_only_transition_vocabulary_on_row_and_shard(self):
        base_registry = load(self.registry)
        base_record = self.record()
        self.assertEqual(self.run_apply(self.data)["disposition"], "ALLOW")
        registry = load(self.registry)
        row, record = self.row(), self.record()
        expected = copy.deepcopy(base_record)
        expected["allowed_next_transitions"] = EXISTING + ["INGRESS_ADMITTED"]
        self.assertEqual(record, expected)
        self.assertEqual(row, expected)
        self.assertEqual(record["coordination_state"], "PROPOSED")
        self.assertEqual(record["checkout_state"], "UNCLAIMED")
        self.assertIsNone(record["worker_claim"]["claim_ref"])
        self.assertIsNone(record["worker_claim"]["fence_ref"])
        self.assertFalse(record["completion"]["claimed"])
        self.assertFalse(record["completion"]["validated"])
        self.assertEqual(registry["generation"], self.tip + 1)
        registry["tasks"] = [row for row in registry["tasks"] if row.get("task_id") != TASK]
        registry["generation"] = base_registry["generation"]
        self.assertEqual(registry, base_registry)

    def test_reapply_is_no_change_with_no_generation_bump(self):
        self.run_apply(self.data)
        applied = (self.registry.read_bytes(), (self.shards / f"{TASK}.json").read_bytes())
        report = self.run_apply(self.data, tip=self.tip + 1)
        self.assertEqual((report["disposition"], report["files_changed"]), ("NO_CHANGE", False))
        self.assertEqual(applied, (self.registry.read_bytes(),
                                   (self.shards / f"{TASK}.json").read_bytes()))

    def test_stale_before_fails_closed_without_writing(self):
        payload = copy.deepcopy(self.data)
        payload["row_fields"][0]["before"] = EXISTING + ["HANDOFF_READY"]
        before = (self.registry.read_bytes(), (self.shards / f"{TASK}.json").read_bytes())
        with self.assertRaises(atr.Refused) as raised:
            self.run_apply(payload)
        self.assertEqual(raised.exception.result["disposition"], "FAIL_CLOSED")
        self.assertEqual(raised.exception.result["failure_code"],
                         "RECORD_DATA_ROW_FIELD_BEFORE_MISMATCH")
        self.assertEqual(before, (self.registry.read_bytes(),
                                  (self.shards / f"{TASK}.json").read_bytes()))

    def test_stale_generation_fence_fails_closed_without_writing(self):
        before = (self.registry.read_bytes(), (self.shards / f"{TASK}.json").read_bytes())
        with self.assertRaises(atr.Refused) as raised:
            self.run_apply(self.data, tip=self.tip - 1)
        self.assertEqual(raised.exception.result["failure_code"],
                         "REGISTRY_GENERATION_NOT_TIP_PLUS_ONE")
        self.assertEqual(before, (self.registry.read_bytes(),
                                  (self.shards / f"{TASK}.json").read_bytes()))


if __name__ == "__main__":
    unittest.main()
