from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001"
VECTOR_REF = f"control/task-vectors/{TASK_ID}.json"

spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)


class TVCRepositoryBrokerValidationCOSVTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = json.loads((ROOT / VECTOR_REF).read_text(encoding="utf-8"))
        fragment = json.loads((ROOT / "control/worker-registry.d/tvc-repository-broker-validation-001.json").read_text(encoding="utf-8"))
        self.task = next(x for x in fragment["tasks"] if x["task_id"] == TASK_ID)
        self.handoff = json.loads((ROOT / "handoffs/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json").read_text(encoding="utf-8"))

    def test_vector_recomputes_from_exact_metrics(self) -> None:
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]), self.record["vector"])
        self.assertEqual(self.record["vector"], "50000000101000")
        self.assertEqual(self.record["exact_metrics"]["blocker_count"], len(self.task["admissible_existence"]["blockers"]))

    def test_source_binding_is_single_and_authority_neutral(self) -> None:
        self.assertEqual(self.task["source_state_vector_ref"], VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"], VECTOR_REF)
        embedded = self.task["machine_readable_state"]["cosv"]
        self.assertEqual(embedded["vector"], self.record["vector"])
        self.assertEqual(embedded["authority_effect"], "NONE")
        self.assertEqual(self.handoff["machine_readable_state"]["cosv"]["vector"], self.record["vector"])

    def test_vector_does_not_promote_unobserved_validation_or_activation(self) -> None:
        m = self.record["exact_metrics"]
        self.assertFalse(m["evidence_complete"])
        self.assertFalse(m["activated"])
        self.assertFalse(m["propagated"])
        self.assertEqual(self.task["state"], "HANDOFF_READY")
        self.assertIsNone(self.task["admissible_existence"]["activation_proof_ref"])


if __name__ == "__main__":
    unittest.main()
