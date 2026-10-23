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
CLASS_B = ["NWI-S2:SV_LLM_VERDICT_AGREEMENT_RATE", "NWI-S3:W05_TV_TVC_HELD_INVOCATION_ADMITTED", "sv_llm_paths:ENTITY_RESPOND"]
E0T = {"dispositions": ["ALLOW", "FAIL_CLOSED"], "by": "a deterministic component"}


def doc():
    return copy.deepcopy(DOC)


def find(d, item):
    where, _, iid = item.partition(":")
    pool = d["sv_llm_paths"] if where == "sv_llm_paths" else next(s for s in d["stages"] if s["stage_id"] == where)["predicates"]
    return next(p for p in pool if p["id"] == iid)


def resolved():
    """The declaration with every class B item given an E0 terminal: what it looks like once the gaps are built."""
    d = doc()
    for name in CLASS_B:
        it = find(d, name)
        it.pop("class_b")
        it["e0_terminal"] = dict(E0T)
        it["lowest_supported_mode"] = "E0"
        if it["requires_llms"] == 1:
            it["lowest_supported_mode"] = "E1"
            it["degraded_forms"] = {"E0": "resolved from invariants and receipts, else a six-field FAIL_CLOSED"}
        if it["requires_llms"] == om.UNKNOWN:
            it["requires_llms"] = 0
    for s in d["stages"]:
        s["exit_passable_at_e0"] = True
    return d


def six(r):
    return all(isinstance(r.get(k), str) and r[k] for k in om.SIX)


class DeclarationTests(unittest.TestCase):
    def test_every_stage_and_gate_predicate_is_declared(self):
        self.assertEqual(sorted(STAGES), ["NWI-S0", "NWI-S1", "NWI-S2", "NWI-S3", "NWI-S4"])
        for s in DOC["stages"]:
            self.assertEqual(sorted(p["id"] for p in s["predicates"]), sorted(STAGES[s["stage_id"]]))
            self.assertIn(s["lowest_supported_mode"], om.MODES)

    def test_real_declaration_reports_exactly_the_class_b_gaps(self):
        out = om.validate(DOC, STAGES)
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "OPERATING_MODE_E0_TERMINAL_MISSING"))
        self.assertTrue(six(out))
        self.assertEqual([g["item"] for g in out["class_b"]], CLASS_B)
        for g in out["class_b"]:
            self.assertTrue(six(g["class_b"]))
            self.assertEqual(g["class_b"]["owning_existing_goal"], "StegVerse-org/.github#163")
            self.assertEqual(g["class_b"]["disposition"], "FAIL_CLOSED")

    def test_stage_exit_passability_matches_the_gaps(self):
        flags = {s["stage_id"]: s["exit_passable_at_e0"] for s in DOC["stages"]}
        self.assertEqual(flags, {"NWI-S0": True, "NWI-S1": True, "NWI-S2": False, "NWI-S3": False, "NWI-S4": True})

    def test_every_sv_llm_path_names_its_source(self):
        for p in DOC["sv_llm_paths"]:
            self.assertTrue(p["source"])

    def test_resolved_declaration_is_allow(self):
        self.assertEqual(om.validate(resolved(), STAGES)["disposition"], "ALLOW")

    def test_main_exits_zero_on_declared_gaps(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(om.main(), 0)


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
        d = doc()
        find(d, CLASS_B[2]).pop("class_b")
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "CLASS_B_RECORD_INCOMPLETE"))

    def test_class_b_record_missing_a_field(self):
        d = doc()
        del find(d, CLASS_B[0])["class_b"]["next_attempt"]
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "CLASS_B_RECORD_INCOMPLETE"))

    def test_class_b_kept_after_resolution(self):
        d = resolved()
        find(d, CLASS_B[0])["class_b"] = find(DOC, CLASS_B[0])["class_b"]
        self.assertEqual(self.code(d), ("FAIL_CLOSED", "OPERATING_MODE_INCONSISTENT"))

    def test_exit_passability_must_be_derived(self):
        d = doc()
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
