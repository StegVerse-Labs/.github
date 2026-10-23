"""Operating-mode declaration (StegVerse-org/.github#160 issuecomment-6354238464, #163 issuecomment-6354245549)."""
from __future__ import annotations

import contextlib
import copy
import io
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("sv_operating_modes", ROOT / "resident-runtime/sv_operating_modes.py")
om = importlib.util.module_from_spec(_s)
sys.modules["sv_operating_modes"] = om
_s.loader.exec_module(om)

DOC = json.loads(om.DECLARATION.read_text())
STAGES = om.load_stage_predicates()
CLOSED = ["NWI-S2:SV_LLM_VERDICT_AGREEMENT_RATE", "NWI-S3:W05_TV_TVC_HELD_INVOCATION_ADMITTED", "sv_llm_paths:ENTITY_RESPOND"]
CLASS_B_RECORD = {"disposition": "FAIL_CLOSED", "failure_code": "OPERATING_MODE_E0_TERMINAL_MISSING",
                  "failed_predicate": "E0_TERMINAL_OR_CLASS_B", "required_evidence_or_repair": "build the E0 terminal",
                  "retry_entrypoint": "resident-runtime/sv_operating_modes.py::validate",
                  "owning_existing_goal": "StegVerse-org/.github#163", "next_attempt": "re-run validate"}


def doc():
    return copy.deepcopy(DOC)


def resolved():
    return doc()


def find(d, item):
    where, _, iid = item.partition(":")
    pool = d["sv_llm_paths"] if where == "sv_llm_paths" else next(s for s in d["stages"] if s["stage_id"] == where)["predicates"]
    return next(p for p in pool if p["id"] == iid)


def gapped(*items):
    """The declaration with the named items reverted to class B gaps (no E0 terminal)."""
    d = doc()
    for name in items:
        it = find(d, name)
        it.update(e0_terminal=None, lowest_supported_mode="NONE", class_b=dict(CLASS_B_RECORD))
        if ":" in name and not name.startswith("sv_llm_paths"):
            next(s for s in d["stages"] if s["stage_id"] == name.split(":")[0])["exit_passable_at_e0"] = False
    return d


def six(r):
    return all(isinstance(r.get(k), str) and r[k] for k in om.SIX)


class DeclarationTests(unittest.TestCase):
    def test_every_stage_and_gate_predicate_is_declared(self):
        self.assertEqual(sorted(STAGES), ["NWI-S0", "NWI-S1", "NWI-S2", "NWI-S3", "NWI-S4"])
        for s in DOC["stages"]:
            self.assertEqual(sorted(p["id"] for p in s["predicates"]), sorted(STAGES[s["stage_id"]]))
            self.assertIn(s["lowest_supported_mode"], om.MODES)

    def test_real_declaration_is_allow_at_e0_by_exercise(self):
        out = om.validate(DOC, STAGES)
        self.assertEqual(out["disposition"], "ALLOW", out)
        self.assertEqual(out["mode"], "E0")
        exercised = {w["item"]: w for w in out["exercised"]}
        for name in CLOSED + ["NWI-S3:ADMISSION_MISS_RATE"]:
            self.assertIn(name, exercised)
            self.assertTrue(any(o["disposition"] != "ALLOW" for o in exercised[name]["outcomes"]))
        for sid in ("NWI-S0", "NWI-S1", "NWI-S2", "NWI-S3"):
            self.assertIn(sid + ":STAGE_GATE", exercised)

    def test_no_class_b_record_remains(self):
        for s in DOC["stages"]:
            for p in s["predicates"]:
                self.assertNotIn("class_b", p)
        for p in DOC["sv_llm_paths"]:
            self.assertNotIn("class_b", p)

    def test_closed_items_declare_witnesses(self):
        for name in CLOSED:
            it = find(DOC, name)
            self.assertIn("witness", it["e0_terminal"])
        self.assertEqual(find(DOC, CLOSED[0])["requires_llms"], 0)
        w05 = find(DOC, CLOSED[1])
        self.assertEqual((w05["requires_llms"], w05["lowest_supported_mode"]), (1, "E1"))
        self.assertIn("E0", w05["degraded_forms"])

    def test_gaps_are_still_reported_as_class_b(self):
        out = om.validate(gapped(*CLOSED), STAGES)
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "OPERATING_MODE_E0_TERMINAL_MISSING"))
        self.assertTrue(six(out))
        self.assertEqual([g["item"] for g in out["class_b"]], CLOSED)

    def test_stage_exit_passability_matches_the_gaps(self):
        flags = {s["stage_id"]: s["exit_passable_at_e0"] for s in DOC["stages"]}
        self.assertEqual(flags, {"NWI-S0": True, "NWI-S1": True, "NWI-S2": True, "NWI-S3": True, "NWI-S4": True})

    def test_every_sv_llm_path_names_its_source(self):
        for p in DOC["sv_llm_paths"]:
            self.assertTrue(p["source"])

    def test_sandbox_pins_are_the_e0_terminal_head(self):
        text = json.dumps(DOC)
        self.assertNotIn("5e65e7a8b0cdf81a277845bf8082efd64626535d", text)
        self.assertIn("SV-LLM/sandbox@5814d5c1626f87fd6d62ffee1a851072cb5d114a", text)

    def test_resolved_declaration_is_allow(self):
        self.assertEqual(om.validate(resolved(), STAGES)["disposition"], "ALLOW")

    def test_shape_only_validation_skips_exercise(self):
        out = om.validate(DOC, STAGES, exercise=False)
        self.assertEqual(out["disposition"], "ALLOW")
        self.assertNotIn("exercised", out)

    def test_main_exits_zero_on_allow(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(om.main(), 0)
        self.assertEqual(json.loads(buf.getvalue())["disposition"], "ALLOW")


class WitnessRefusalTests(unittest.TestCase):
    def code(self, d):
        out = om.validate(d, STAGES)
        self.assertNotEqual(out["disposition"], "ALLOW")
        self.assertTrue(six(out))
        return out["disposition"], out["failure_code"]

    def test_flag_without_witness_or_pin_is_unproven(self):
        d = doc()
        find(d, CLOSED[0])["e0_terminal"].pop("witness")
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_E0_TERMINAL_UNPROVEN"))

    def test_unpinned_external_component_is_unproven(self):
        d = doc()
        it = find(d, "sv_llm_paths:PROVIDER_LAYER_TRANSITION")
        it["e0_terminal"]["by"] = "no admitted provider transition"
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_E0_TERMINAL_UNPROVEN"))

    def test_cases_digest_mismatch(self):
        d = doc()
        find(d, CLOSED[2])["e0_terminal"]["witness"]["cases_sha256"] = "sha256:" + "0" * 64
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_UNBOUND"))

    def test_cases_file_absent(self):
        d = doc()
        find(d, CLOSED[1])["e0_terminal"]["witness"]["cases"] = "data/sv-work-items/e0-witnesses/absent.json"
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_UNBOUND"))

    def test_entrypoint_outside_resident_runtime(self):
        d = doc()
        find(d, CLOSED[1])["e0_terminal"]["witness"]["entrypoint"] = "../tmp/x.py::f"
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_UNBOUND"))

    def test_entrypoint_that_does_not_exist(self):
        d = doc()
        find(d, CLOSED[1])["e0_terminal"]["witness"]["entrypoint"] = "resident-runtime/sv_e0_terminals.py::no_such_fn"
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_UNBOUND"))

    def test_wrong_entrypoint_fails_the_cases(self):
        d = doc()
        find(d, CLOSED[0])["e0_terminal"]["witness"]["entrypoint"] = "resident-runtime/sv_e0_terminals.py::witness_bounded_solving"
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_FAILED"))

    def test_undeclared_disposition_fails(self):
        d = doc()
        find(d, CLOSED[1])["e0_terminal"]["dispositions"] = ["ALLOW", "FAIL_CLOSED"]  # a case DENYs
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_FAILED"))

    def test_undeclared_non_allow_code_fails(self):
        d = doc()
        find(d, CLOSED[2])["e0_terminal"]["non_allow_codes"] = ["ENTITY_SURFACE_NOT_SUPPLIED"]
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_FAILED"))

    def test_stage_gate_codes_must_be_declared(self):
        d = doc()
        d["stages"][0]["e0_terminal"]["non_allow_codes"] = ["STAGE_REGRESSION"]
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_FAILED"))


class WitnessCasesFileTests(unittest.TestCase):
    """Corrupted cases files are refused: written to a temporary root, never into the repository."""

    def run_with(self, mutate):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as tmp:
            root = Path(tmp)
            (root / "resident-runtime").mkdir()
            for f in ("sv_e0_terminals.py", "sv_work_items.py", "stage_gate.py"):
                shutil.copy(ROOT / "resident-runtime" / f, root / "resident-runtime" / f)
            src = ROOT / "data/sv-work-items/e0-witnesses/nwi-s3-bounded-solving.json"
            (root / "data/sv-work-items/e0-witnesses").mkdir(parents=True)
            cases = json.loads(src.read_text())
            mutate(cases)
            raw = json.dumps(cases).encode()
            dst = root / "data/sv-work-items/e0-witnesses/nwi-s3-bounded-solving.json"
            dst.write_bytes(raw)
            import hashlib
            e0 = copy.deepcopy(find(DOC, CLOSED[1])["e0_terminal"])
            e0["witness"]["cases_sha256"] = "sha256:" + hashlib.sha256(raw).hexdigest()
            return om.exercise_witness(CLOSED[1], e0, root)

    def test_unmodified_cases_pass(self):
        bad, summary = self.run_with(lambda c: None)
        self.assertEqual(bad, [])
        self.assertEqual(summary["cases"], 6)

    def test_wrong_expectation_fails(self):
        def m(c):
            c["cases"][4]["expect"]["disposition"] = "ALLOW"
        bad, _ = self.run_with(m)
        self.assertEqual(bad[0]["failure_code"], "OPERATING_MODE_E0_WITNESS_FAILED")

    def test_only_allow_cases_is_not_proof_of_the_fail_closed_path(self):
        def m(c):
            c["cases"] = [x for x in c["cases"] if x["expect"]["disposition"] == "ALLOW"]
        bad, _ = self.run_with(m)
        self.assertEqual(bad[0]["failure_code"], "OPERATING_MODE_E0_WITNESS_FAILED")

    def test_cases_for_another_item(self):
        def m(c):
            c["item"] = "NWI-S2:SV_LLM_VERDICT_AGREEMENT_RATE"
        bad, _ = self.run_with(m)
        self.assertEqual(bad[0]["failure_code"], "OPERATING_MODE_E0_WITNESS_UNBOUND")

    def test_empty_cases(self):
        def m(c):
            c["cases"] = []
        bad, _ = self.run_with(m)
        self.assertEqual(bad[0]["failure_code"], "OPERATING_MODE_E0_WITNESS_UNBOUND")


class RefusalTests(unittest.TestCase):
    def code(self, d):
        out = om.validate(d, STAGES)
        self.assertNotEqual(out["disposition"], "ALLOW")
        self.assertTrue(six(out))
        return out["disposition"], out["failure_code"]

    def test_missing_stage(self):
        d = resolved()
        d["stages"] = [s for s in d["stages"] if s["stage_id"] != "NWI-S4"]
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_STAGE_COVERAGE"))

    def test_uncovered_predicate(self):
        d = resolved()
        d["stages"][1]["predicates"].pop()
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_PREDICATE_COVERAGE"))

    def test_two_llm_requirement_is_denied(self):
        d = resolved()
        it = d["sv_llm_paths"][0]
        it.update(requires_llms=2, lowest_supported_mode="E2", degraded_forms={"E0": "x", "E1": "y"})
        self.assertEqual(self.code(d), ("DENY", "OPERATING_MODE_REQUIRES_MORE_THAN_ONE_LLM"))

    def test_missing_degraded_rung(self):
        d = resolved()
        it = find(d, "sv_llm_paths:STEGBROWSER_LLM_V1_TOOL")
        it["degraded_forms"] = {}
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_DEGRADED_FORM_MISSING"))

    def test_specific_provider_requirement_is_denied(self):
        d = resolved()
        find(d, "sv_llm_paths:STEGBROWSER_LLM_V1_TOOL")["degraded_forms"]["E0"] = "ask Claude instead"
        self.assertEqual(self.code(d), ("DENY", "OPERATING_MODE_REQUIRES_SPECIFIC_PROVIDER"))

    def test_owner_must_act_is_denied(self):
        d = resolved()
        d["sv_llm_paths"][0]["e0_terminal"]["by"] = "FAIL_CLOSED until the owner must act"
        self.assertEqual(self.code(d), ("DENY", "OPERATING_MODE_OWNER_MUST_ACT"))

    def test_unknown_mode(self):
        d = resolved()
        d["sv_llm_paths"][0]["lowest_supported_mode"] = "E9"
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_UNDECLARED"))

    def test_gap_without_class_b_record(self):
        d = gapped(CLOSED[2])
        find(d, CLOSED[2]).pop("class_b")
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "CLASS_B_RECORD_INCOMPLETE"))

    def test_class_b_record_missing_a_field(self):
        d = gapped(CLOSED[0])
        del find(d, CLOSED[0])["class_b"]["next_attempt"]
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "CLASS_B_RECORD_INCOMPLETE"))

    def test_class_b_kept_after_resolution(self):
        d = resolved()
        find(d, CLOSED[0])["class_b"] = dict(CLASS_B_RECORD)
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_INCONSISTENT"))

    def test_exit_passability_must_be_derived(self):
        d = gapped(CLOSED[0])
        next(s for s in d["stages"] if s["stage_id"] == "NWI-S2")["exit_passable_at_e0"] = True
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_INCONSISTENT"))

    def test_malformed_e0_terminal(self):
        d = resolved()
        d["sv_llm_paths"][0]["e0_terminal"] = {"dispositions": ["OUTSTANDING"], "by": "x"}
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_E0_TERMINAL_MALFORMED"))

    def test_ladder_and_schema(self):
        d = resolved()
        d["ladder"] = d["ladder"][::-1]
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_LADDER_MALFORMED"))
        d = resolved()
        d["schema"] = "x"
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_DECLARATION_MALFORMED"))

    def test_bool_is_not_a_count(self):
        d = resolved()
        d["sv_llm_paths"][0]["requires_llms"] = True
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_REQUIREMENT_MALFORMED"))


if __name__ == "__main__":
    unittest.main()
