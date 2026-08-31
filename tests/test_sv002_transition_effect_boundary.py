from __future__ import annotations
import json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(rel):
    return json.loads((ROOT/rel).read_text(encoding="utf-8"))

class SV002TransitionEffectBoundaryTests(unittest.TestCase):
    def test_principal_effect_is_transition_element_derived(self):
        h=read("handoffs/SHWP-SV002-SELF-CHARACTERIZATION-001.json")
        v=read("control/task-vectors/SHWP-SV002-SELF-CHARACTERIZATION-001.json")
        self.assertEqual(h["authority"]["policy_version"],"sv002-self-characterization-v0.2")
        self.assertFalse(h["authority"]["authority_transfer_assumed"])
        self.assertEqual(h["authority"]["authority_effect_resolution"],"DERIVED_FROM_APPLICABLE_TRANSITION_ELEMENTS")
        self.assertFalse(v["authority_transfer_assumed"])
        self.assertEqual(v["authority_effect_resolution"],"DERIVED_FROM_APPLICABLE_TRANSITION_ELEMENTS")
        self.assertEqual(v["authority_effect"],"NONE")
        self.assertEqual(v["authority_effect_scope"],"TASK_VECTOR_PROJECTION_ONLY")

    def test_registration_and_request_packets_remain_non_authorizing(self):
        reg=read("control/worker-registry.d/sv002-self-characterization-001.json")
        req=read("control/resident-execution-request.d/sv002-self-characterization-001.json")
        self.assertEqual(reg["tasks"][0]["authorized_policy_version"],"sv002-self-characterization-v0.2")
        self.assertEqual(reg["authority_effect"],"NONE_REGISTRATION_ONLY")
        self.assertFalse(req["request_granted_authority"])
        self.assertEqual(req["authority_effect"],"NONE_REQUEST_ONLY")

    def test_worker_preserves_transition_effect_artifact(self):
        s=(ROOT/"workers/sv002_self_characterization_worker.py").read_text(encoding="utf-8")
        self.assertIn('"transition_effects_path"',s)
        self.assertIn('"DERIVED_FROM_APPLICABLE_TRANSITION_ELEMENTS"',s)
        self.assertIn('"NOT_APPLICABLE_NO_PRINCIPAL_TRANSITION"',s)

if __name__=="__main__":
    unittest.main()
