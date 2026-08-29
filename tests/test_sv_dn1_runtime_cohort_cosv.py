from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VECTORS={
    "SV-DN1-INTR-RUNTIME-001":"50000000102000",
    "SV-DN1-SDK-FIRST-ROUND-001":"50000000103000",
}
FRAGMENTS={
    "SV-DN1-INTR-RUNTIME-001":"control/worker-registry.d/sv-dn1-intr-runtime-001.json",
    "SV-DN1-SDK-FIRST-ROUND-001":"control/worker-registry.d/sv-dn1-sdk-first-round-001.json",
}
HANDOFFS={
    "SV-DN1-INTR-RUNTIME-001":"handoffs/SV-DN1-INTR-RUNTIME-001.json",
    "SV-DN1-SDK-FIRST-ROUND-001":"handoffs/SV-DN1-SDK-FIRST-ROUND-001.json",
}
RESIDENT="SV-DN1-RESIDENT-OBSERVER-001"

spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)

class SVDN1RuntimeCohortCOSVTests(unittest.TestCase):
    def test_clean_cohort_vectors_recompute_and_match_blockers(self):
        for task_id,expected in VECTORS.items():
            record=json.loads((ROOT/f"control/task-vectors/{task_id}.json").read_text(encoding="utf-8"))
            fragment=json.loads((ROOT/FRAGMENTS[task_id]).read_text(encoding="utf-8"))
            task=fragment["tasks"][0]
            handoff=json.loads((ROOT/HANDOFFS[task_id]).read_text(encoding="utf-8"))
            self.assertTrue(cosv.validate_record(record))
            self.assertEqual(cosv.encode_task(record["exact_metrics"]),expected)
            self.assertEqual(record["vector"],expected)
            self.assertEqual(record["exact_metrics"]["blocker_count"],len(task["admissible_existence"]["blockers"]))
            self.assertEqual(task["admissible_existence"]["blockers"],handoff["admissible_existence"]["blockers"])
            self.assertEqual(task["source_state_vector_ref"],f"control/task-vectors/{task_id}.json")
            self.assertEqual(handoff["source_state_vector_ref"],task["source_state_vector_ref"])
            self.assertFalse(handoff["task"]["manual_execution_allowed"])
            self.assertIsNone(task["admissible_existence"]["activation_proof_ref"])
            self.assertFalse(record["exact_metrics"]["evidence_complete"])
            self.assertFalse(record["exact_metrics"]["activated"])
            self.assertFalse(record["exact_metrics"]["propagated"])

    def test_resident_observer_conflict_remains_fail_closed(self):
        self.assertFalse((ROOT/f"control/task-vectors/{RESIDENT}.json").exists())
        coverage=json.loads((ROOT/"control/cosv-global-registry-coverage.json").read_text(encoding="utf-8"))
        self.assertIn(RESIDENT,coverage["active_worker_task_ids_missing_canonical_cosv"])
        conflict=coverage["sv_dn1_resident_observer_conflict"]
        self.assertEqual(conflict["task_id"],RESIDENT)
        self.assertFalse(conflict["vector_emission_allowed"])
        frag=json.loads((ROOT/"control/worker-registry.d/sv-dn1-resident-observer-001.json").read_text(encoding="utf-8"))
        hand=json.loads((ROOT/"handoffs/SV-DN1-RESIDENT-OBSERVER-001.json").read_text(encoding="utf-8"))
        self.assertNotEqual(frag["tasks"][0]["admissible_existence"]["blockers"],hand["admissible_existence"]["blockers"])

if __name__=="__main__":
    unittest.main()
