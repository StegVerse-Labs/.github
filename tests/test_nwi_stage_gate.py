"""G5: STAGE_GATE transition (STAGE_GATES_ARE_ADMITTED_TRANSITIONS)."""
from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, rel):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


wi = _load("sv_work_items", "resident-runtime/sv_work_items.py")
sg = _load("stage_gate", "resident-runtime/stage_gate.py")
EPOCH = "1024"
OK = {"disposition": "ALLOW", "receipt_ref": "refs/stegverse/organization-ledger:receipt"}
S0_EVIDENCE = {"SV_WORK_ITEM_SCHEMAS_VALIDATE": OK, "EVERY_MIGRATION_FIXTURE_LOADS": OK}
S1_EVIDENCE = {g["predicate"]: OK for g in sg.load_stages()[1]["exit_gate"]}


def six(out):
    for f in wi.SIX_FIELDS:
        assert out.get(f), f
    return out["failure_code"]


class StageGateTests(unittest.TestCase):
    def test_manifests_are_contiguous_nwi_s0_to_s4(self):
        self.assertEqual([m["stage_id"] for m in sg.load_stages()], ["NWI-S0", "NWI-S1", "NWI-S2", "NWI-S3", "NWI-S4"])

    def test_s0_to_s1_admitted_with_receipted_evidence(self):
        out = sg.evaluate_gate("NWI-S0", "NWI-S1", S0_EVIDENCE, hb_epoch=EPOCH)
        self.assertEqual((out["disposition"], out["stage_after"], out["entry_transition"]), ("ALLOW", "NWI-S1", "STAGE_NWI_S1_ADMITTED"))
        req = sg.transition_request(out)
        self.assertEqual(req["schema"], "stegverse.organization-transition-request/v1")
        self.assertFalse(req["build_manifest"]["data"]["external_side_effect"])

    def test_no_skipping_and_no_backward_request(self):
        self.assertEqual(six(sg.evaluate_gate("NWI-S0", "NWI-S2", S0_EVIDENCE, hb_epoch=EPOCH)), "STAGE_SKIP")
        self.assertEqual(six(sg.evaluate_gate("NWI-S2", "NWI-S1", {}, hb_epoch=EPOCH)), "STAGE_NOT_FORWARD")
        self.assertEqual(six(sg.evaluate_gate("NWI-S1", "NWI-S1", S1_EVIDENCE, hb_epoch=EPOCH)), "STAGE_NOT_FORWARD")
        out = sg.evaluate_gate("NWI-S0", "NWI-S2", S0_EVIDENCE, hb_epoch=EPOCH)
        self.assertEqual((out["disposition"], out["stage_after"]), ("DENY", "NWI-S0"))

    def test_failed_gate_drops_back_one_stage(self):
        ev = dict(S1_EVIDENCE, W04_SANDBOX_RUNTIME_OBSERVED={"disposition": "FAIL_CLOSED", "receipt_ref": "r"})
        out = sg.evaluate_gate("NWI-S1", "NWI-S2", ev, hb_epoch=EPOCH)
        self.assertEqual((six(out), out["disposition"], out["stage_after"]), ("STAGE_REGRESSION", "FAIL_CLOSED", "NWI-S0"))
        self.assertEqual(out["failed"], ["W04_SANDBOX_RUNTIME_OBSERVED"])
        floor = sg.evaluate_gate("NWI-S0", "NWI-S1", dict(S0_EVIDENCE, EVERY_MIGRATION_FIXTURE_LOADS={"disposition": "DENY", "receipt_ref": "r"}),
                                 hb_epoch=EPOCH)
        self.assertEqual((floor["failure_code"], floor["stage_after"]), ("STAGE_REGRESSION", "NWI-S0"))

    def test_unobserved_evidence_does_not_pass_or_move(self):
        out = sg.evaluate_gate("NWI-S0", "NWI-S1", {"SV_WORK_ITEM_SCHEMAS_VALIDATE": OK,
                                                     "EVERY_MIGRATION_FIXTURE_LOADS": {"disposition": "ALLOW"}}, hb_epoch=EPOCH)
        self.assertEqual((six(out), out["stage_after"]), ("STAGE_EVIDENCE_UNOBSERVED", "NWI-S0"))

    def test_thresholds_come_only_from_the_manifest(self):
        ev = {"SV_LLM_VERDICT_AGREEMENT_RATE": {"receipt_ref": "r", "agreement_rate": 1.0}}
        out = sg.evaluate_gate("NWI-S2", "NWI-S3", ev, hb_epoch=EPOCH)
        self.assertEqual((six(out), out["stage_after"]), ("STAGE_THRESHOLD_UNDECLARED", "NWI-S2"))
        stages = copy.deepcopy(sg.load_stages())
        stages[2]["exit_gate"][0]["threshold"]["value"] = 0.95
        self.assertEqual(sg.evaluate_gate("NWI-S2", "NWI-S3", ev, hb_epoch=EPOCH, stages=stages)["disposition"], "ALLOW")
        low = {"SV_LLM_VERDICT_AGREEMENT_RATE": {"receipt_ref": "r", "agreement_rate": 0.5}}
        out = sg.evaluate_gate("NWI-S2", "NWI-S3", low, hb_epoch=EPOCH, stages=stages)
        self.assertEqual((out["failure_code"], out["stage_after"]), ("STAGE_REGRESSION", "NWI-S1"))
        missing = {"SV_LLM_VERDICT_AGREEMENT_RATE": {"receipt_ref": "r"}}
        self.assertEqual(sg.evaluate_gate("NWI-S2", "NWI-S3", missing, hb_epoch=EPOCH, stages=stages)["failure_code"], "STAGE_EVIDENCE_UNOBSERVED")
        self.assertEqual(six(sg.evaluate_gate("NWI-S3", "NWI-S4", {}, hb_epoch=EPOCH)), "STAGE_EVIDENCE_UNOBSERVED")

    def test_final_stage_and_unknown_stage(self):
        self.assertEqual(six(sg.evaluate_gate("NWI-S4", "NWI-S5", {}, hb_epoch=EPOCH)), "STAGE_MANIFEST_ABSENT")
        self.assertEqual(six(sg.evaluate_gate("S1", "S2", {}, hb_epoch=EPOCH)), "STAGE_MANIFEST_ABSENT")

    def test_epoch_rule(self):
        for bad, want in (("+33", "HB_EPOCH_INVALID"), (" 33", "HB_EPOCH_INVALID"), ("3_3", "HB_EPOCH_INVALID"), ("31", "HB_EPOCH_INVALID"),
                          (None, "HB_EPOCH_NOT_SUPPLIED")):
            self.assertEqual(six(sg.evaluate_gate("NWI-S0", "NWI-S1", S0_EVIDENCE, hb_epoch=bad)), want, repr(bad))

    def test_noncontiguous_manifests_fail_closed(self):
        import tempfile, json, shutil
        with tempfile.TemporaryDirectory() as d:
            for p in (ROOT / "data/sv-work-items/stages").glob("*.json"):
                if p.name != "NWI-S2.json":
                    shutil.copy(p, d)
            with self.assertRaises(wi.Refusal) as cm:
                sg.load_stages(Path(d))
            self.assertEqual(cm.exception.record["failure_code"], "STAGE_MANIFESTS_NOT_CONTIGUOUS")

    def test_source_has_no_clock_or_network(self):
        for rel in ("resident-runtime/stage_gate.py", "resident-runtime/sv_work_items.py", "resident-runtime/admission_learning.py",
                    "scripts/build_sv_native_fixtures.py", "resident-runtime/sv_migration.py", "resident-runtime/schema_subset.py",
                    "scripts/evaluate_migration_fixtures.py"):
            src = (ROOT / rel).read_text()
            for banned in ("datetime", "import time", "time.time", "urllib", "socket", "subprocess", "os.environ", "getenv", "import requests"):
                self.assertNotIn(banned, src, rel + ": " + banned)


if __name__ == "__main__":
    unittest.main()
