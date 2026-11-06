"""E0 terminal forms closing the #163 class B items (resident-runtime/sv_e0_terminals.py)."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("sv_e0_terminals", ROOT / "resident-runtime/sv_e0_terminals.py")
e0 = sys.modules.get("sv_e0_terminals") or importlib.util.module_from_spec(_s)
if "sv_e0_terminals" not in sys.modules:
    sys.modules["sv_e0_terminals"] = e0
    _s.loader.exec_module(e0)
wi, sg = e0.wi, e0.sg
WITNESSES = ROOT / "data/sv-work-items/e0-witnesses"


def cases(name):
    return {c["case_id"]: c["input"] for c in json.loads((WITNESSES / name).read_text())["cases"]}


S2 = cases("nwi-s2-verdict-agreement.json")
RESPOND = cases("sv-llm-entity-respond.json")
EVALS = S2["verifier-verdicts-vs-admission"]["evaluations"]


def six(r):
    return r["disposition"] != "ALLOW" and all(isinstance(r.get(k), str) and r[k] for k in e0.SIX)


def reseal(receipts):
    """Recompute every receipt hash and chain link, as a forger with no key would."""
    prev = receipts[0]["previous_receipt_sha256"]
    for r in receipts:
        r["previous_receipt_sha256"] = prev
        r["receipt_sha256"] = wi.sha({k: v for k, v in r.items() if k != "receipt_sha256"})
        prev = r["receipt_sha256"]
    return receipts


class VerdictAgreementTests(unittest.TestCase):
    def test_agreement_is_verifier_verdict_vs_admission(self):
        out = e0.verdict_agreement_e0(EVALS, fixture_mode=True)
        self.assertEqual((out["disposition"], out["mode"], out["agreed"], out["evaluated"]), ("ALLOW", "E0", 2, 3))
        self.assertAlmostEqual(out["agreement_rate"], 2 / 3)
        by = {v["change_digest"]: v for v in out["record"]["verdicts"]}
        self.assertEqual(by[EVALS[1]["change_digest"]]["verifier_verdict"], "DENY")
        self.assertFalse(by[EVALS[1]["change_digest"]]["agrees"])
        rec = out["record"]
        self.assertEqual(rec["record_digest"], wi.sha({k: v for k, v in rec.items() if k != "record_digest"}))
        self.assertEqual(out["gate_evidence"]["SV_LLM_VERDICT_AGREEMENT_RATE"]["verdict_record_digest"], rec["record_digest"])

    def test_ecosystem_verdict_precedence(self):
        self.assertEqual(e0.ecosystem_verdict(["ALLOW", "DENY", "FAIL_CLOSED"]), "FAIL_CLOSED")
        self.assertEqual(e0.ecosystem_verdict(["ALLOW", "DENY"]), "DENY")
        self.assertEqual(e0.ecosystem_verdict(["ALLOW"]), "ALLOW")

    def test_llm_verdicts_are_additive_only(self):
        base = e0.verdict_agreement_e0(EVALS, fixture_mode=True)
        llm = [{"mode": m, "change_digest": EVALS[0]["change_digest"], "disposition": "DENY"} for m in ("E1", "E2", "E3")]
        llm.append({"mode": "E0", "change_digest": EVALS[0]["change_digest"], "disposition": "DENY"})  # not an LLM rung
        out = e0.verdict_agreement_e0(EVALS, llm_verdicts=llm, fixture_mode=True)
        self.assertEqual((out["agreed"], out["evaluated"], out["agreement_rate"]), (base["agreed"], base["evaluated"], base["agreement_rate"]))
        self.assertEqual(out["record"]["additive_llm_layers"]["llm_verdicts"], 3)

    def test_no_evidence_fails_closed_with_six_fields(self):
        out = e0.verdict_agreement_e0([])
        self.assertTrue(six(out))
        self.assertEqual((out["failure_code"], out["mode"]), ("VERDICT_AGREEMENT_EVIDENCE_UNOBSERVED", "E0"))
        self.assertEqual(out["owning_existing_goal"], "StegVerse-org/.github#163")

    def test_fixture_refs_need_fixture_mode_and_ledger_refs_count(self):
        self.assertEqual(e0.verdict_agreement_e0(EVALS)["disposition"], "FAIL_CLOSED")
        ref = "refs/stegverse/organization-ledger@" + "a" * 40 + ":receipts/" + "b" * 64 + ".json"
        ev = copy.deepcopy(EVALS[:1])
        for c in ev[0]["check_receipts"]:
            c["receipt_ref"] = ref
        ev[0]["admission"]["receipt_ref"] = ref
        self.assertEqual(e0.verdict_agreement_e0(ev)["evaluated"], 1)

    def test_receipt_for_another_change_is_excluded(self):
        ev = copy.deepcopy(EVALS[:1])
        ev[0]["check_receipts"][0]["receipt"]["change_digest"] = EVALS[1]["change_digest"]
        out = e0.verdict_agreement_e0(ev, fixture_mode=True)
        self.assertEqual(out["failure_code"], "VERDICT_AGREEMENT_EVIDENCE_UNOBSERVED")
        self.assertEqual(out["excluded"][0]["reason"], "VERIFIER_RECEIPT_REFUSED")

    def test_admission_for_another_change_is_excluded(self):
        ev = copy.deepcopy(EVALS[:1])
        ev[0]["admission"]["change_digest"] = EVALS[1]["change_digest"]
        out = e0.verdict_agreement_e0(ev, fixture_mode=True)
        self.assertEqual(out["excluded"][0]["reason"], "ADMISSION_DISPOSITION_UNOBSERVED")

    def test_producer_evidence_passes_the_gate_once_a_threshold_is_declared(self):
        stages = sg.load_stages()
        for s in stages:
            if s["stage_id"] == "NWI-S2":
                s["exit_gate"][0]["threshold"]["value"] = 0.5
        out = e0.verdict_agreement_e0(EVALS, fixture_mode=True)
        evidence = {k: {**v, "receipt_ref": "x#fixture:record"} for k, v in out["gate_evidence"].items()}
        self.assertEqual(sg.evaluate_gate("NWI-S2", "NWI-S3", evidence, hb_epoch="32", stages=stages)["disposition"], "ALLOW")
        for s in stages:
            if s["stage_id"] == "NWI-S2":
                s["exit_gate"][0]["threshold"]["value"] = 0.9
        self.assertEqual(sg.evaluate_gate("NWI-S2", "NWI-S3", evidence, hb_epoch="32", stages=stages)["failure_code"], "STAGE_REGRESSION")

    def test_with_the_real_null_threshold_the_gate_terminates(self):
        out = e0.witness_verdict_agreement(S2["producer-evidence-through-the-nwi-s2-gate"])
        self.assertTrue(six(out))
        self.assertEqual(out["failure_code"], "STAGE_THRESHOLD_UNDECLARED")


class BoundedSolvingTests(unittest.TestCase):
    def test_each_e0_solver_resolves_at_e0(self):
        receipt = EVALS[0]["check_receipts"][0]["receipt"]
        items = {"SV_CHECK_RECEIPT_VALIDATION": {"receipt": receipt, "change_digest": receipt["change_digest"]},
                 "VERDICT_AGREEMENT": {"evaluations": EVALS, "fixture_mode": True},
                 "STAGE_GATE_EVALUATION": {"stage": "NWI-S1", "target": "NWI-S2", "evidence": {}, "hb_epoch": "32"}}
        self.assertEqual(sorted(items), sorted(e0.E0_SOLVERS))
        for cls, inp in items.items():
            out = e0.bounded_solve_e0({"work_item_id": "w-" + cls, "problem_class": cls, "input": inp})
            self.assertEqual((out["resolved_at_mode"], out["mode"]), ("E0", "E0"))
            self.assertEqual(out["solution_digest"], wi.sha(out["solution"]))
            if out["disposition"] != "ALLOW":
                self.assertTrue(six(out))

    def test_unsolvable_item_is_deferred_never_outstanding(self):
        item = {"work_item_id": "w-open", "problem_class": "OPEN_ENDED_DESIGN", "input": {"q": "x"}}
        out = e0.bounded_solve_e0(item)
        self.assertTrue(six(out))
        self.assertEqual(out["failure_code"], "PROVIDER_LAYER_NOT_ADMITTED")
        d = out["deferral"]
        self.assertEqual((d["deferred_to_mode"], d["e1_form"]), ("E1", "W05_TV_TVC_HELD_INVOCATION_ADMITTED"))
        self.assertIn("PROVIDER_LAYER_TRANSITION", d["resume_on"])
        self.assertEqual(d["deferral_digest"], wi.sha({k: v for k, v in d.items() if k != "deferral_digest"}))
        self.assertEqual(out, e0.bounded_solve_e0(copy.deepcopy(item)))  # deterministic

    def test_malformed_items(self):
        for item in (None, {}, {"work_item_id": "w", "problem_class": "VERDICT_AGREEMENT"}, {"work_item_id": " ", "problem_class": "X", "input": {}}):
            out = e0.bounded_solve_e0(item)
            self.assertEqual(out["failure_code"], "BOUNDED_SOLVING_ITEM_MALFORMED")
            self.assertTrue(six(out))

    def test_a_solver_that_returns_no_terminal_is_refused(self):
        saved = dict(e0.E0_SOLVERS)
        try:
            e0.E0_SOLVERS["BROKEN"] = lambda inp: {"disposition": "PENDING"}
            out = e0.bounded_solve_e0({"work_item_id": "w", "problem_class": "BROKEN", "input": {}})
            self.assertEqual(out["failure_code"], "E0_SOLVER_OUTCOME_NOT_TERMINAL")
        finally:
            e0.E0_SOLVERS.clear()
            e0.E0_SOLVERS.update(saved)


class RespondTerminalTests(unittest.TestCase):
    def test_both_passes_verify(self):
        for cid in ("e0-witness-respond-partial", "e0-witness-respond-none"):
            out = e0.verify_respond_terminal(RESPOND[cid])
            self.assertTrue(six(out))
            self.assertEqual((out["failure_code"], out["mode"], out["work_completed"]), ("ENTITY_SURFACE_NOT_SUPPLIED", "E0", True))
            self.assertEqual(out["entity_set_digest"], e0.entity_set_digest(RESPOND[cid]["supplied_entities"]))
        self.assertEqual(len(e0.verify_respond_terminal(RESPOND["e0-witness-respond-none"])["terminals"]), 2)
        self.assertEqual(len(e0.verify_respond_terminal(RESPOND["e0-witness-respond-partial"])["terminals"]), 1)

    def mutate(self, f, reseal_after=True):
        case = copy.deepcopy(RESPOND["e0-witness-respond-partial"])
        f(case["receipts"])
        if reseal_after:
            reseal(case["receipts"])
        return e0.verify_respond_terminal(case)

    def term_index(self, rs):
        return next(i for i, r in enumerate(rs) if r["evidence"].get("e0_terminal"))

    def test_resealed_forgeries_are_still_caught(self):
        def bad_id(rs):
            ev = rs[self.term_index(rs)]["evidence"]
            ev["contribution_id"] = ev["envelope"]["contribution_id"] = "surface-not-supplied:" + "0" * 64
        def bad_digest(rs):
            ev = rs[self.term_index(rs)]["evidence"]
            ev["envelope"]["non_success_status_record"]["uncertainty"] = "made up"
            ev["envelope"]["uncertainty"] = "made up"
        def five_fields(rs):
            del rs[self.term_index(rs)]["evidence"]["e0_terminal"]["next_attempt"]
        def no_completion(rs):
            del rs[-1]
        for f, check in ((bad_id, "CONTRIBUTION_ID_RECOMPUTES"), (bad_digest, "CONTENT_DIGEST_RECOMPUTES"),
                         (five_fields, "SIX_FIELD_FAIL_CLOSED_RECORDED"), (no_completion, "WORK_COMPLETED_AFTER_THE_TERMINALS")):
            out = self.mutate(f)
            self.assertEqual((out["failure_code"], out["failed_check"]), ("RESPOND_E0_TERMINAL_NOT_EVIDENCED", check), check)
            self.assertTrue(six(out))

    def test_chain_and_origin(self):
        def unlink(rs):
            rs[3]["previous_receipt_sha256"] = "sha256:" + "0" * 64
            rs[3]["receipt_sha256"] = wi.sha({k: v for k, v in rs[3].items() if k != "receipt_sha256"})
        self.assertEqual(self.mutate(unlink, reseal_after=False)["failed_check"], "RECEIPT_CHAIN_LINKS")
        def elsewhere(rs):
            rs[0]["repository"] = "SV-LLM/other"
        self.assertEqual(self.mutate(elsewhere)["failed_check"], "RECEIPT_IS_A_SANDBOX_REPO_RECEIPT")

    def test_all_surfaces_supplied_is_not_this_terminal(self):
        case = copy.deepcopy(RESPOND["e0-witness-respond-partial"])
        case["supplied_entities"] = sorted({r["evidence"]["entity"] for r in case["receipts"] if r["transition_class"] == "CONTRIBUTION_REQUESTED"})
        self.assertEqual(e0.verify_respond_terminal(case)["failed_check"], "A_REQUEST_WITH_NO_SUPPLIED_SURFACE")

    def test_mirrors_match_the_recorded_values(self):
        case = RESPOND["e0-witness-respond-none"]
        r = next(r for r in case["receipts"] if r["evidence"].get("e0_terminal"))["evidence"]
        d = e0.entity_set_digest([])
        self.assertEqual(r["envelope"]["evidence_refs"], ["entity-set:" + d])
        self.assertEqual(r["contribution_id"], e0.unsupplied_contribution_id(r["work_id"], r["entity"], r["envelope"]["capability"], d))


if __name__ == "__main__":
    unittest.main()
