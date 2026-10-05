import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_task_registry_health_monitor.py"
spec = importlib.util.spec_from_file_location("task_health_monitor", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class TaskRegistryHealthCoordinationTests(unittest.TestCase):
    def test_registry_truth_overrides_shard_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "registry.json"
            shards = root / "records"
            shards.mkdir()
            registry.write_text(json.dumps({
                "tasks": [{
                    "task_id": "TASK-1",
                    "coordination_state": "ACTIVE",
                    "checkout_state": "CHECKED_OUT",
                }]
            }), encoding="utf-8")
            (shards / "TASK-1.json").write_text(json.dumps({
                "task_id": "TASK-1",
                "coordination_state": "RETIRED",
                "checkout_state": "RETIRED",
                "shard_only_detail": "preserved",
            }), encoding="utf-8")
            with mock.patch.object(module, "MONOLITHIC_REGISTRY", registry), mock.patch.object(module, "SHARDED_RECORDS", shards):
                rows = module._all_records()
            self.assertEqual(rows[0]["coordination_state"], "ACTIVE")
            self.assertEqual(rows[0]["checkout_state"], "CHECKED_OUT")
            self.assertEqual(rows[0]["shard_only_detail"], "preserved")

    def test_claim_reference_without_workercoordinator_fence_is_not_checkout(self):
        record = {
            "coordination_state": "ACTIVE",
            "worker_claim": {
                "authority": "WORKERCOORDINATOR",
                "claim_ref": "docs/HANDOFF.md",
                "fence_ref": None,
                "projection_only": True,
            },
        }
        self.assertFalse(module._checked_out(record))


    def test_terminal_task_with_historical_claim_fence_is_not_checkout(self):
        self.assertFalse(module._checked_out({
            "task_id": "TASK-RETIRED",
            "coordination_state": "RETIRED",
            "checkout_state": "DECOMPOSED_AT_PROMPT_LIMIT",
            "worker_claim": {
                "authority": "WORKERCOORDINATOR",
                "claim_ref": "CLAIM-OLD",
                "fence_ref": "FENCE-OLD",
                "projection_only": False,
            },
        }))

    def test_explicit_checkout_state_remains_checkout(self):
        self.assertTrue(module._checked_out({
            "coordination_state": "ACTIVE",
            "checkout_state": "CHECKED_OUT",
        }))

    def test_checked_out_without_active_worker_claim_is_coordination_state_unverified(self):
        record = {
            "task_id": "TASK-1",
            "coordination_state": "ACTIVE",
            "checkout_state": "CHECKED_OUT",
        }
        obs = module._checked_out_coordination_observation(record, set())
        self.assertIsNotNone(obs)
        self.assertEqual(obs["posture"], "COORDINATION_STATE_UNVERIFIED")
        self.assertFalse(obs["recovery_required"])

    def test_checked_out_with_active_worker_claim_defers_to_worker_return_review(self):
        record = {
            "task_id": "TASK-1",
            "coordination_state": "ACTIVE",
            "checkout_state": "CHECKED_OUT",
        }
        self.assertIsNone(module._checked_out_coordination_observation(record, {"TASK-1"}))

    def test_master_records_absence_without_stegdb_comparison_requires_reconciliation(self):
        now = datetime(2026, 9, 19, 23, 0, tzinfo=timezone.utc)
        record = {
            "task_id": "TASK-1",
            "worker_return_obligation": {
                "ref": "RETURN-1",
                "expected_return_by": "2026-09-19T22:00:00Z",
                "master_records_subject_binding": "subject-1",
                "master_records_return_ref": "does/not/exist.json",
            },
        }
        obs = module._worker_return_observation(record, now)
        self.assertEqual(obs["posture"], "RECONCILIATION_REQUIRED")
        self.assertFalse(obs["recovery_required"])

    def test_stegdb_missing_plus_master_records_absence_allows_recovery_classification(self):
        now = datetime(2026, 9, 19, 23, 0, tzinfo=timezone.utc)
        record = {
            "task_id": "TASK-1",
            "worker_return_obligation": {
                "ref": "RETURN-1",
                "expected_return_by": "2026-09-19T22:00:00Z",
                "master_records_subject_binding": "subject-1",
                "master_records_return_ref": "does/not/exist.json",
                "stegdb_comparison_ref": "StegVerse-Labs/StegDB:comparison/RETURN-1",
                "stegdb_comparison_status": "MISSING",
            },
        }
        obs = module._worker_return_observation(record, now)
        self.assertEqual(obs["posture"], "RETURN_OVERDUE")
        self.assertTrue(obs["recovery_required"])
        self.assertEqual(obs["stegdb_comparison_status"], "MISSING")

    def test_stegdb_stale_does_not_misclassify_runtime_failure(self):
        now = datetime(2026, 9, 19, 23, 0, tzinfo=timezone.utc)
        record = {
            "task_id": "TASK-1",
            "worker_return_obligation": {
                "ref": "RETURN-1",
                "expected_return_by": "2026-09-19T22:00:00Z",
                "master_records_subject_binding": "subject-1",
                "master_records_return_ref": "does/not/exist.json",
                "stegdb_comparison_ref": "StegVerse-Labs/StegDB:comparison/RETURN-1",
                "stegdb_comparison_status": "STALE",
            },
        }
        obs = module._worker_return_observation(record, now)
        self.assertEqual(obs["posture"], "RECONCILIATION_REQUIRED")
        self.assertFalse(obs["recovery_required"])


    def test_repository_artifact_conflict_is_health_failure(self):
        records = [{"task_id": "TASK-1", "coordination_state": "ACTIVE"}]
        bindings = [{"task_id": "TASK-1", "repository": "StegVerse-Labs/Site", "pull_request": 42, "branch": "repair/task-1", "source_head": "abc"}]
        observations = [{"repository": "StegVerse-Labs/Site", "pull_request": 42, "state": "OPEN", "mergeability": "CONFLICTING", "behind_by": 3}]
        findings = module._repository_lifecycle_findings(records, bindings, observations)
        self.assertTrue(any(row["posture"] == "REPOSITORY_ARTIFACT_CONFLICTED" and row["recovery_required"] for row in findings))

    def test_terminal_task_with_open_pr_is_blocked_without_exception(self):
        records = [{"task_id": "TASK-1", "coordination_state": "RETIRED"}]
        bindings = [{"task_id": "TASK-1", "repository": "StegVerse-Labs/.github", "pull_request": 99, "branch": "task-1", "source_head": "def"}]
        observations = [{"repository": "StegVerse-Labs/.github", "pull_request": 99, "state": "OPEN", "mergeability": "CLEAN", "behind_by": 0}]
        findings = module._repository_lifecycle_findings(records, bindings, observations)
        self.assertTrue(any(row["posture"] == "TASK_TERMINAL_WITH_NONTERMINAL_REPOSITORY_ARTIFACT" for row in findings))

    def test_terminal_task_open_pr_may_carry_explicit_retained_exception(self):
        records = [{"task_id": "TASK-1", "coordination_state": "RETIRED", "repository_lifecycle_exception_ref": "evidence/exception.json"}]
        bindings = [{"task_id": "TASK-1", "repository": "StegVerse-Labs/.github", "pull_request": 99}]
        observations = [{"repository": "StegVerse-Labs/.github", "pull_request": 99, "state": "OPEN", "mergeability": "CLEAN"}]
        findings = module._repository_lifecycle_findings(records, bindings, observations)
        self.assertFalse(any(row["posture"] == "TASK_TERMINAL_WITH_NONTERMINAL_REPOSITORY_ARTIFACT" for row in findings))

    def test_supersession_requires_predecessor_terminalization(self):
        records = [{"task_id": "TASK-1", "coordination_state": "ACTIVE"}]
        bindings = [{"task_id": "TASK-1", "repository": "StegVerse-Labs/.github", "pull_request": 10}]
        observations = [{"repository": "StegVerse-Labs/.github", "pull_request": 10, "state": "OPEN", "superseded_by_pull_request": 11}]
        findings = module._repository_lifecycle_findings(records, bindings, observations)
        self.assertTrue(any(row["posture"] == "SUPERSESSION_NOT_ATOMIC" for row in findings))

    def test_one_repository_artifact_cannot_bind_multiple_tasks(self):
        records = [{"task_id": "TASK-1", "coordination_state": "ACTIVE"}, {"task_id": "TASK-2", "coordination_state": "ACTIVE"}]
        bindings = [
            {"task_id": "TASK-1", "repository": "StegVerse-Labs/Site", "pull_request": 42},
            {"task_id": "TASK-2", "repository": "StegVerse-Labs/Site", "pull_request": 42},
        ]
        observations = [{"repository": "StegVerse-Labs/Site", "pull_request": 42, "state": "OPEN"}]
        findings = module._repository_lifecycle_findings(records, bindings, observations)
        self.assertTrue(any(row["posture"] == "MULTIPLE_CANONICAL_TASK_BINDINGS" for row in findings))



if __name__ == "__main__":
    unittest.main()
