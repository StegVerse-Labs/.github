from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from heartbeat_runtime.coordination_ledger import (
    CoordinationLedgerError,
    compose_coordination_ledger,
    load_composed_coordination_ledger,
    validate_worker_claim_coverage,
)

ROOT = Path(__file__).resolve().parents[1]


class CoordinationLedgerCompositionTests(unittest.TestCase):
    def base(self):
        return {
            "schema": "stegverse.cross-task-coordination-ledger/v1",
            "authority": {"runtime_truth_authority_effect": "NONE"},
            "goals": [{"goal_id": "G"}],
            "tasks": [],
            "predicates": [{"predicate_id": "P0", "state": "UNKNOWN", "authoritative_producer": "base"}],
            "evidence": [],
            "claims": [],
            "gaps": [],
        }

    def fragment(self, fragment_id="F1", predicate_id="P1"):
        return {
            "schema": "stegverse.cross-task-coordination-fragment/v1",
            "fragment_id": fragment_id,
            "authority_effect": "NONE_COORDINATION_ONLY",
            "predicates": [
                {
                    "predicate_id": predicate_id,
                    "state": "UNKNOWN",
                    "authoritative_producer": "fragment",
                    "semantic_predicate_id": "resident_request_consumed",
                    "subject_binding": {"request_id": fragment_id},
                }
            ],
            "gaps": [
                {
                    "predicate_id": predicate_id,
                    "subject_binding": {"request_id": fragment_id},
                    "rejected_because": ["NO_QUALIFYING_EVIDENCE_OBSERVED"],
                    "required_producer": "fragment",
                    "action_without_collision": "consume existing producer",
                }
            ],
        }

    def worker_task(self, claim_id="CLAIM-1", **overrides):
        task = {
            "task_id": "TASK-1",
            "goal_id": "GOAL-1",
            "state": "BLOCKED",
            "handoff_ref": "handoffs/TASK-1.json",
            "executor_binding": "BOUND",
            "worker_id": "worker-1",
            "worker_instance_id": "worker-1-HB7-G9",
            "claim_id": claim_id,
            "heartbeat_timing": {"fencing_token": 9},
            "archive_eligible": False,
        }
        task.update(overrides)
        return task

    def worker_registry(self, *tasks):
        return {
            "schema": "stegverse.heartbeat-worker-registry/v0.1",
            "generation": 9,
            "updated_at": "2026-09-05T00:00:00Z",
            "workers": [],
            "tasks": list(tasks),
        }

    def claim_row(self, claim_id="CLAIM-1", **overrides):
        row = {
            "claim_id": claim_id,
            "task_id": "TASK-1",
            "state": "ACTIVE",
            "scope": {"repositories": ["StegVerse-Labs/.github"], "paths": ["control/x.json"]},
            "fencing_token": 9,
            "worker_id": "worker-1",
            "worker_instance_id": "worker-1-HB7-G9",
            "authority_effect": "COORDINATION_ONLY",
        }
        row.update(overrides)
        return row

    def test_composes_fragment_without_mutating_base(self):
        base = self.base()
        result = compose_coordination_ledger(base, [self.fragment()])
        self.assertEqual([p["predicate_id"] for p in base["predicates"]], ["P0"])
        self.assertEqual([p["predicate_id"] for p in result["predicates"]], ["P0", "P1"])
        self.assertEqual(result["composition"]["fragment_ids"], ["F1"])
        self.assertEqual(result["composition"]["authority_effect"], "NONE")

    def test_duplicate_predicate_fails_closed(self):
        with self.assertRaises(CoordinationLedgerError):
            compose_coordination_ledger(self.base(), [self.fragment(predicate_id="P0")])

    def test_duplicate_fragment_id_fails_closed(self):
        with self.assertRaises(CoordinationLedgerError):
            compose_coordination_ledger(self.base(), [self.fragment(), self.fragment()])

    def test_invalid_authority_effect_fails_closed(self):
        fragment = self.fragment()
        fragment["authority_effect"] = "EXECUTION"
        with self.assertRaises(CoordinationLedgerError):
            compose_coordination_ledger(self.base(), [fragment])

    def test_loader_uses_sorted_fragment_filenames(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            control = root / "control"
            fragments = control / "cross-task-coordination.d"
            fragments.mkdir(parents=True)
            (control / "cross-task-coordination.json").write_text(json.dumps(self.base()), encoding="utf-8")
            (fragments / "b.json").write_text(json.dumps(self.fragment("F-B", "P-B")), encoding="utf-8")
            (fragments / "a.json").write_text(json.dumps(self.fragment("F-A", "P-A")), encoding="utf-8")
            result = load_composed_coordination_ledger(control / "cross-task-coordination.json")
            self.assertEqual(result["composition"]["fragment_ids"], ["F-A", "F-B"])
            self.assertEqual([p["predicate_id"] for p in result["predicates"]], ["P0", "P-A", "P-B"])

    def test_worker_claim_coverage_accepts_exact_unreleased_bound_mirror(self):
        ledger = self.base()
        ledger["claims"] = [self.claim_row()]
        result = validate_worker_claim_coverage(ledger, self.worker_registry(self.worker_task()))
        self.assertEqual(result["validated_claim_ids"], ["CLAIM-1"])
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertFalse(result["runtime_execution_inferred"])

    def test_worker_claim_coverage_rejects_missing_coordination_mirror(self):
        with self.assertRaisesRegex(CoordinationLedgerError, "unmirrored active WorkerCoordinator claim"):
            validate_worker_claim_coverage(self.base(), self.worker_registry(self.worker_task()))

    def test_worker_claim_coverage_rejects_identity_drift(self):
        ledger = self.base()
        ledger["claims"] = [self.claim_row(fencing_token=10)]
        with self.assertRaisesRegex(CoordinationLedgerError, "identity mismatch"):
            validate_worker_claim_coverage(ledger, self.worker_registry(self.worker_task()))

    def test_worker_claim_coverage_rejects_stale_worker_bound_active_mirror(self):
        ledger = self.base()
        ledger["claims"] = [self.claim_row()]
        registry = self.worker_registry(self.worker_task(state="COMPLETED", archive_eligible=True))
        with self.assertRaisesRegex(CoordinationLedgerError, "stale active WorkerCoordinator coordination claim"):
            validate_worker_claim_coverage(ledger, registry)

    def test_non_worker_coordination_claim_is_not_forced_into_worker_registry(self):
        ledger = self.base()
        ledger["claims"] = [{
            "claim_id": "COORD-ONLY",
            "task_id": "TASK-X",
            "state": "ACTIVE",
            "scope": {"repositories": ["StegVerse-Labs/.github"], "paths": ["docs/x.md"]},
            "authority_effect": "COORDINATION_ONLY",
        }]
        result = validate_worker_claim_coverage(ledger, self.worker_registry())
        self.assertEqual(result["validated_claim_ids"], [])

    def test_repository_composed_ledger_covers_current_worker_claims(self):
        result = load_composed_coordination_ledger(ROOT / "control" / "cross-task-coordination.json")
        coverage = result["composition"].get("worker_claim_coverage")
        self.assertIsInstance(coverage, dict)
        self.assertEqual(coverage["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
