import json
import unittest
from pathlib import Path

from state_language.test_queue_manifold import (
    apply_test_disposition,
    build_queue_manifold,
    select_candidate_bundle,
    validate_bundle_instruction,
    validate_descriptor,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "test_queue_manifold.v1.json"


class TestQueueManifoldGovernanceTests(unittest.TestCase):
    def fixture(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def snapshot(self, version=1, heartbeat=None):
        data = self.fixture()
        return build_queue_manifold(
            data["tests"],
            manifold_version=version,
            available_capabilities=data["available_capabilities"],
            available_evidence=data["available_evidence"],
            heartbeat_observation=heartbeat,
        )

    def test_by_id(self, test_id):
        return next(item for item in self.fixture()["tests"] if item["test_id"] == test_id)

    def test_individual_queue_projection_is_heartbeat_independent(self):
        snapshot = self.snapshot()
        self.assertIsNone(snapshot["heartbeat_observation"])
        self.assertFalse(snapshot["direct_test_execution_heartbeat_dependency"])
        self.assertEqual(snapshot["execution_authority"], "INDEPENDENT_ADMITTED_CLAIM_FENCE")
        self.assertEqual(snapshot["credential_authority"], "TV/TVC")
        self.assertEqual(snapshot["authority_effect"], "NONE")

    def test_heartbeat_reference_is_optional_and_non_authorizing(self):
        snapshot = self.snapshot(
            heartbeat={
                "schema": "stegverse.heartbeat-governed-manifold-observation/v1",
                "carrier_epoch": 45,
                "carrier_generation": 9,
                "authority_effect": "NONE_OBSERVATION_ONLY",
            }
        )
        self.assertTrue(snapshot["heartbeat_observation"]["reference_only"])
        self.assertEqual(snapshot["heartbeat_observation"]["carrier_epoch"], 45)
        self.assertEqual(snapshot["execution_authority"], "INDEPENDENT_ADMITTED_CLAIM_FENCE")

        with self.assertRaisesRegex(ValueError, "cannot grant queue authority"):
            self.snapshot(heartbeat={"authority_effect": "EXECUTE"})

    def test_readiness_and_dependency_projection_is_deterministic(self):
        first = self.snapshot()
        second = self.snapshot()
        self.assertEqual(first, second)

        states = {
            row["test_id"]: row["projected_lifecycle_state"]
            for row in first["tests"]
        }
        self.assertEqual(states, {
            "TQ-001": "READY",
            "TQ-002": "READY",
            "TQ-003": "READY",
            "TQ-004": "READY",
            "TQ-005": "EXECUTED",
        })
        self.assertEqual(first["coherency_groups"], {
            "integration": ["TQ-004", "TQ-005"],
            "route-validation": ["TQ-001", "TQ-002"],
            "schema-validation": ["TQ-003"],
        })

    def test_missing_capability_or_evidence_blocks_without_dropping_test(self):
        data = self.fixture()
        snapshot = build_queue_manifold(
            data["tests"],
            manifold_version=1,
            available_capabilities=["python"],
            available_evidence=["evidence:baseline"],
        )
        rows = {row["test_id"]: row for row in snapshot["tests"]}
        self.assertEqual(rows["TQ-001"]["projected_lifecycle_state"], "BLOCKED")
        self.assertIn("capabilities:network-observation", rows["TQ-001"]["readiness_blockers"])
        self.assertIn("evidence:evidence:route", rows["TQ-001"]["readiness_blockers"])
        self.assertEqual({row["test_id"] for row in snapshot["tests"]}, {
            "TQ-001", "TQ-002", "TQ-003", "TQ-004", "TQ-005"
        })

    def test_minimum_distinguishing_bundle_defers_equivalent_test_explicitly(self):
        snapshot = self.snapshot()
        bundle = select_candidate_bundle(snapshot, capacity_units=3)
        self.assertEqual(bundle["selected_test_ids"], ["TQ-001", "TQ-003"])
        self.assertEqual(len(bundle["deferred_equivalent_tests"]), 1)
        deferred = bundle["deferred_equivalent_tests"][0]
        self.assertEqual(deferred["test_id"], "TQ-002")
        self.assertEqual(
            deferred["reason"],
            "AWAIT_BUNDLE_EVIDENCE_FOR_EQUIVALENT_DISTINGUISHING_SIGNATURE",
        )
        self.assertTrue(deferred["distinguishing_signature"].startswith("sha256:"))
        self.assertEqual(bundle["unselected_ready_test_ids"], ["TQ-004"])
        self.assertFalse(bundle["execution_authority_granted"])
        self.assertFalse(bundle["claim_or_fence_minted"])
        self.assertFalse(bundle["heartbeat_authority_granted"])
        self.assertEqual(bundle["authority_effect"], "NONE")

    def test_bundle_does_not_silently_terminalize_equivalent_test(self):
        snapshot = self.snapshot()
        bundle = select_candidate_bundle(snapshot, capacity_units=3)
        row = next(row for row in snapshot["tests"] if row["test_id"] == "TQ-002")
        self.assertEqual(row["projected_lifecycle_state"], "READY")
        self.assertTrue(any(item["test_id"] == "TQ-002" for item in bundle["deferred_equivalent_tests"]))

    def test_stale_bundle_invalidated_by_version_change(self):
        snapshot = self.snapshot(version=1)
        bundle = select_candidate_bundle(snapshot, capacity_units=3)
        current = self.snapshot(version=2)
        with self.assertRaisesRegex(ValueError, "STALE_MANIFOLD_VERSION"):
            validate_bundle_instruction(bundle, current)

    def test_stale_bundle_invalidated_by_state_hash_change(self):
        data = self.fixture()
        snapshot = self.snapshot(version=1)
        bundle = select_candidate_bundle(snapshot, capacity_units=3)
        changed_tests = json.loads(json.dumps(data["tests"]))
        changed_tests[0]["urgency"] = 91
        current = build_queue_manifold(
            changed_tests,
            manifold_version=1,
            available_capabilities=data["available_capabilities"],
            available_evidence=data["available_evidence"],
        )
        with self.assertRaisesRegex(ValueError, "STALE_MANIFOLD_HASH"):
            validate_bundle_instruction(bundle, current)

    def test_terminal_disposition_requires_evidence_and_never_grants_authority(self):
        descriptor = self.test_by_id("TQ-001")
        with self.assertRaisesRegex(ValueError, "requires evidence"):
            apply_test_disposition(descriptor, new_state="EXECUTED", evidence_refs=[])

        receipt = apply_test_disposition(
            descriptor,
            new_state="EXECUTED",
            evidence_refs=["receipt:test-run-001"],
        )
        self.assertEqual(receipt["new_state"], "EXECUTED")
        self.assertFalse(receipt["silent_drop"])
        self.assertFalse(receipt["execution_authority_granted"])
        self.assertEqual(receipt["credential_authority"], "TV/TVC")
        self.assertEqual(receipt["authority_effect"], "NONE")

    def test_satisfied_by_bundle_requires_bundle_identity(self):
        descriptor = self.test_by_id("TQ-002")
        with self.assertRaisesRegex(ValueError, "requires bundle_id"):
            apply_test_disposition(
                descriptor,
                new_state="SATISFIED_BY_BUNDLE",
                evidence_refs=["receipt:bundle-evidence"],
            )
        receipt = apply_test_disposition(
            descriptor,
            new_state="SATISFIED_BY_BUNDLE",
            evidence_refs=["receipt:bundle-evidence"],
            bundle_id="bundle-abc",
        )
        self.assertEqual(receipt["bundle_id"], "bundle-abc")

    def test_person_specific_route_and_authority_escalation_fail_closed(self):
        descriptor = self.test_by_id("TQ-001")
        bad = dict(descriptor)
        bad["person_specific_route"] = True
        with self.assertRaisesRegex(ValueError, "person-specific"):
            validate_descriptor(bad)

        bad = dict(descriptor)
        bad["authority_effect"] = "EXECUTE"
        with self.assertRaisesRegex(ValueError, "cannot grant authority"):
            validate_descriptor(bad)

    def test_claimed_test_requires_independent_claim_ref(self):
        descriptor = self.test_by_id("TQ-001")
        bad = dict(descriptor)
        bad["lifecycle_state"] = "CLAIMED"
        bad["execution_claim_ref"] = None
        with self.assertRaisesRegex(ValueError, "independently admitted"):
            validate_descriptor(bad)

    def test_capacity_scaling_does_not_change_authority_semantics(self):
        snapshot = self.snapshot()
        small = select_candidate_bundle(snapshot, capacity_units=1)
        large = select_candidate_bundle(snapshot, capacity_units=100)
        for bundle in (small, large):
            self.assertFalse(bundle["execution_authority_granted"])
            self.assertFalse(bundle["claim_or_fence_minted"])
            self.assertFalse(bundle["heartbeat_authority_granted"])
            self.assertEqual(bundle["credential_authority"], "TV/TVC")
            self.assertEqual(bundle["authority_effect"], "NONE")
        self.assertGreaterEqual(len(large["selected_test_ids"]), len(small["selected_test_ids"]))


if __name__ == "__main__":
    unittest.main()
