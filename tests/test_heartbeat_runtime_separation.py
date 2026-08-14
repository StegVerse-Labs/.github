import json
import unittest
from pathlib import Path

from heartbeat_runtime.runtime_separation import build_carrier_observation, build_control_plane_coordination, project_legacy_registry

ROOT = Path(__file__).resolve().parents[1]


class HeartbeatRuntimeSeparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.legacy = json.loads((ROOT / "control" / "heartbeat-subsignals.json").read_text(encoding="utf-8"))

    def test_carrier_projection_has_no_worker_claim_or_fence_payload(self):
        carrier = build_carrier_observation(self.legacy)
        text = json.dumps(carrier, sort_keys=True)
        self.assertNotIn('"claim_id"', text)
        self.assertNotIn('"fencing_token"', text)
        self.assertNotIn('"active_leases"', text)
        self.assertNotIn('"worker_registry_ref"', text)
        self.assertEqual(carrier["carrier"]["role"], "REGULATORY_CARRIER_REFERENCE_FRAME")
        self.assertEqual(carrier["authority"]["credential_authority"], "TV/TVC")
        self.assertFalse(carrier["authority"]["heartbeat_grants_execution_authority"])
        self.assertFalse(carrier["authority"]["master_records_action_authority"])

    def test_control_plane_retains_coordination_without_heartbeat_authority(self):
        control = build_control_plane_coordination(self.legacy, ["StegVerse-Labs/StegBrain#860:WORKER_CLOSURE_MISSING"])
        legacy_worker = self.legacy["subsignals"]["worker_coordination"]
        self.assertEqual(control["worker_coordination"]["active_leases"], legacy_worker["active_leases"])
        self.assertFalse(control["observed_reference"]["heartbeat_is_authority"])
        self.assertFalse(control["authority"]["heartbeat_grants_execution_authority"])
        self.assertFalse(control["authority"]["signal_grants_execution_authority"])
        self.assertFalse(control["authority"]["master_records_action_authority"])
        self.assertEqual(control["authority"]["credential_authority"], "TV/TVC")
        self.assertFalse(control["authority"]["github_token_runtime_authority"])

    def test_projection_is_pure_and_does_not_mutate_legacy_state(self):
        before = json.dumps(self.legacy, sort_keys=True)
        carrier, control = project_legacy_registry(self.legacy)
        after = json.dumps(self.legacy, sort_keys=True)
        self.assertEqual(before, after)
        self.assertEqual(carrier["generation"], control["generation"])

    def test_contract_includes_all_required_transition_domains(self):
        contract = json.loads((ROOT / "control" / "runtime-separation-contract.json").read_text(encoding="utf-8"))
        self.assertEqual(
            set(contract["required_domains"]),
            {"StegVerse-Labs", "DEMO", "TEST", "StegVerse-org", "StegGhost"},
        )
        self.assertEqual(contract["nervous_system_owner"], "StegVerse-Labs/StegBrain#860")
        self.assertEqual(contract["master_records_role"], "PASSIVE_CUSTODY_AND_QUERYABLE_EVIDENCE")
        self.assertFalse(contract["authority"]["non_tv_tvc_secret_or_token_required"])


if __name__ == "__main__":
    unittest.main()
