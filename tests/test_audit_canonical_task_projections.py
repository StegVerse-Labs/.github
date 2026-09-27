"""Fail-closed structural checks and non-authorizing projection classifications."""
import unittest
import json
import tempfile
from pathlib import Path
from scripts.audit_canonical_task_projections import evaluate, load_shards


class ProjectionAuditTest(unittest.TestCase):
    def fixture(self):
        reg = {"generation": 226, "tasks": [{"task_id": "A", "coordination_state": "ACTIVE",
                    "cosv": "50000000100000"}]}
        shards = {"A": {"task_id": "A", "coordination_state": "ACTIVE",
                    "cosv": "50000000100000"},
                  "B": {"task_id": "B", "coordination_state": "ACTIVE",
                    "cosv": "50000000102000"}}
        index = {"tasks": [{"task_id": "A", "vector": "50000000100000"},
                           {"task_id": "B", "vector": "50000000102000"}]}
        return reg, shards, index

    def test_missing_aggregate_is_existing_shard_not_new_task(self):
        r = evaluate(*self.fixture())
        self.assertEqual(r["shards_absent_from_aggregate"], ["B"])
        self.assertEqual(r["interpretation"]["missing_aggregate_row"],
                         "RECONCILE_EXISTING_OWNER_NOT_NEW_REGISTRATION")
        self.assertEqual(r["structural_errors"], [])

    def test_omitted_checked_out_owner_is_prioritized_without_admission(self):
        reg, shards, index = self.fixture()
        shards["B"]["checkout_state"] = "CHECKED_OUT"
        result = evaluate(reg, shards, index)
        self.assertEqual(result["omitted_checked_out_owner_shards"], ["B"])
        self.assertNotIn("B", [r["task_id"] for r in reg["tasks"]])

    def test_verified_session_note_sidecar_is_not_task_shard(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / 'A.json').write_text(json.dumps({'task_id': 'A'}))
            (folder / 'A.current-session-note.json').write_text(json.dumps({'goal_task_id': 'A', 'session_claim': 'CURRENT_SESSION'}))
            shards, notes = load_shards(folder)
            self.assertEqual(sorted(shards), ['A'])
            self.assertEqual(notes, ['A.current-session-note.json'])

    def test_malformed_session_note_is_not_silently_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / 'A.current-session-note.json').write_text(json.dumps({'goal_task_id': 'DIFFERENT'}))
            shards, notes = load_shards(folder)
            self.assertEqual(notes, [])
            self.assertIn('A.current-session-note', shards)
            self.assertTrue(evaluate({'generation': 1, 'tasks': []}, shards, {'tasks': []})['structural_errors'])

    def test_distinct_tasks_may_share_cosv(self):
        reg, shards, index = self.fixture()
        shards["B"]["cosv"] = "50000000100000"
        index["tasks"][1]["vector"] = "50000000100000"
        r = evaluate(reg, shards, index)
        self.assertEqual(r["cosv_conflicts_where_both_emitted"], [])

    def test_same_task_cosv_mismatch_is_reported(self):
        reg, shards, index = self.fixture()
        index["tasks"][0]["vector"] = "50000000102000"
        r = evaluate(reg, shards, index)
        self.assertEqual(r["cosv_conflicts_where_both_emitted"][0]["task_id"], "A")

    def test_shard_drift_is_never_silently_promoted(self):
        reg, shards, index = self.fixture()
        shards["A"]["coordination_state"] = "RETIRED"
        r = evaluate(reg, shards, index)
        self.assertEqual(r["shard_aggregate_drift"][0]["differences"]["coordination_state"],
                         {"aggregate": "ACTIVE", "shard": "RETIRED"})
        self.assertEqual(reg["tasks"][0]["coordination_state"], "ACTIVE")

    def test_duplicate_identity_is_structural_failure(self):
        reg, shards, index = self.fixture()
        reg["tasks"].append(dict(reg["tasks"][0]))
        r = evaluate(reg, shards, index)
        self.assertEqual(r["structural_errors"][0]["duplicate_task_id"], "A")

    def test_mismatched_shard_filename_is_structural_failure(self):
        reg, shards, index = self.fixture()
        shards["B"]["task_id"] = "OTHER"
        r = evaluate(reg, shards, index)
        self.assertEqual(r["structural_errors"][0]["shard"], "B")

    def test_index_only_task_is_not_invented_aggregate_failure(self):
        reg, shards, index = self.fixture()
        index["tasks"].append({"task_id": "C", "vector": "50000000100000"})
        r = evaluate(reg, shards, index)
        self.assertIn("C", r["indexed_not_in_aggregate"])
        self.assertEqual(r["authority_effect"], "NONE_READ_ONLY")


if __name__ == "__main__":
    unittest.main()
