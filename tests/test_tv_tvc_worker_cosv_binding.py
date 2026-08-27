from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "control" / "worker-registry.d" / "tv-tvc-resident-proof-001.json"
HANDOFF = ROOT / "handoffs" / "SHWP-TV-TVC-RESIDENT-PROOF-001.json"
NOTATION = "L R U I V G O C M T B E A P"
SOURCE_REF = "control/task-vectors/SHWP-TV-TVC-RESIDENT-PROOF-001.json"
OWNER_SOURCE_REF = "StegVerse-Labs/TVC/tasks/TVC-TV-CREDENTIAL-MIGRATION-089.json#machine_readable_state.cosv"
LOCAL_VECTOR = ROOT / SOURCE_REF

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
        task = json.loads(REGISTRY.read_text(encoding="utf-8"))["tasks"][0]
        self.assertEqual(task["task_id"], "SHWP-TV-TVC-RESIDENT-PROOF-001")
        self.assertEqual(task["source_state_vector_ref"], SOURCE_REF)
        self.assertEqual(task["canonical_source_state_vector_ref"], OWNER_SOURCE_REF)
        self._assert_cosv(task["machine_readable_state"]["cosv"])
        record = json.loads(LOCAL_VECTOR.read_text(encoding="utf-8"))
        self.assertEqual(record["identity"], "StegVerse-Labs/.github:task:SHWP-TV-TVC-RESIDENT-PROOF-001")
        self.assertEqual(record["source_owner_ref"], OWNER_SOURCE_REF)
        self.assertEqual(record["vector"], task["machine_readable_state"]["cosv"]["vector"])

    def test_handoff_task_matches_registry_vector_binding(self) -> None:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["tasks"][0]
        handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))["task"]
        self.assertEqual(handoff["source_state_vector_ref"], OWNER_SOURCE_REF)
        self.assertEqual(handoff["machine_readable_state"]["cosv"]["vector"], registry["machine_readable_state"]["cosv"]["vector"])
        self._assert_cosv(handoff["machine_readable_state"]["cosv"])

    def test_vector_domains_are_canonical(self) -> None:
        task = json.loads(REGISTRY.read_text(encoding="utf-8"))["tasks"][0]
        digits = [int(x) for x in task["machine_readable_state"]["cosv"]["vector"]]
        for index in (1, 8, 9, 11, 12, 13):
            self.assertIn(digits[index], (0, 1, 2))
        for index in (2, 3, 4, 5, 6, 7, 10):
            self.assertIn(digits[index], range(10))


    def test_registry_task_is_independently_claimable_with_local_cost_basis(self) -> None:
        task = json.loads(REGISTRY.read_text(encoding="utf-8"))["tasks"][0]
        admission = task["admission"]
        self.assertEqual(admission["authority_domain"], "INDEPENDENT_TASK_CONTROL")
        self.assertEqual(admission["claim_state"], "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM")
        self.assertTrue(admission["fresh_fence_required"])
        self.assertEqual(admission["minimum_fencing_token_exclusive"], 21)
        self.assertFalse(admission["heartbeat_grants_execution_authority"])
        self.assertFalse(admission["carrier_trigger_required"])
        self.assertEqual(task["cost_basis_ref"], "cost-basis/worker-runtime/tv-tvc-resident-proof.json")
        cost = json.loads((ROOT / task["cost_basis_ref"]).read_text(encoding="utf-8"))
        self.assertEqual(cost["task_class"], "tv_tvc_resident_operational_proof")
        self.assertGreaterEqual(cost["hb_estimate"]["expiry_candidate_beats"], 1)
        self.assertNotEqual(cost["hb_estimate"]["confidence"], "NONE")

    def test_handoff_binds_targeted_one_shot_without_g18_reuse(self) -> None:
        handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
        activation = handoff["activation"]
        target = activation["targeted_execution"]
        self.assertEqual(activation["carrier"], "heartbeat_reference_only")
        self.assertEqual(activation["authority_domain"], "INDEPENDENT_TASK_CONTROL")
        self.assertFalse(activation["carrier_trigger_required"])
        self.assertEqual(activation["executor_binding"], "AUTHORIZED")
        self.assertTrue(activation["authorization_ref"])
        self.assertEqual(
            target["argv"],
            ["python", "scripts/run_worker_runtime.py", "--task-id", "SHWP-TV-TVC-RESIDENT-PROOF-001"],
        )
        self.assertFalse(target["g18_bootstrap_allowed"])
        self.assertFalse(target["compatibility_carrier_packet_consumption"])
        self.assertFalse(target["unrelated_worker_execution"])
        self.assertFalse(target["heartbeat_grants_execution_authority"])
        self.assertEqual(target["credential_authority"], "TV/TVC")
        self.assertEqual(target["github_token_runtime_authority"], "NONE")

if __name__ == "__main__":
    unittest.main()
