"""SV_CHANGE_ADMIT derives the branch writer from the sv-push-receipt chain (Lane C alignment, TVC#531 manifest v2).

PR_AUTHOR_SESSION_DECLARED is retired: no PR body line, commit trailer or declared_session grants or refuses anything.
BRANCH_WRITER_IS_BRANCH_OWNER is kept, evaluated over the chain; a gap is six-field FAIL_CLOSED BRANCH_WRITER_UNOBSERVED.
Every SV_CHANGE / SV_ISSUE predicate and invariant declares its lowest mode and its degraded form down to E0.
Owning goal StegVerse-org/.github#163.
"""
from __future__ import annotations

import copy
import json
import re
import unittest

from tests import test_sv_native_work_items as base

wi, fx, al = base.wi, base.fx, base.al
ROOT, EPOCH, SESSION = base.ROOT, base.EPOCH, base.SESSION
GOAL163 = "StegVerse-org/.github#163"
LIFECYCLE = json.loads((ROOT / "data/sv-work-items/lifecycle-transitions.json").read_text())
INVARIANTS = json.loads((ROOT / "data/sv-work-items/invariants.json").read_text())
RUNGS = ("E0", "E1", "E2", "E3")
# provider or model names never appear in a mode declaration (a rung is a count of available LLMs, not a vendor)
PROVIDER = re.compile(r"\b(openai|anthropic|claude|gpt|gemini|grok|llama|mistral|copilot|codex)\b", re.I)


def refusal(fn, *a, **k):
    try:
        return fn(*a, **k)
    except wi.Refusal as r:
        return r.record


def six(rec):
    return all(isinstance(rec.get(f), str) and rec[f] for f in wi.SIX_FIELDS) and rec["owning_existing_goal"].startswith(GOAL163)


def admitted_obs(ch=None, **kw):
    ch = ch or fx.known_good_change(fx.SURFACE_PATH["transition"])
    return ch, fx.observe(ch, fx.LABS_BASE, fx.signoff_receipts_for(ch), fx.fixture_base_state_readback(), fx.fixture_resolved_issues(ch), **kw)


class DeriveBranchWriterTests(unittest.TestCase):
    CH = fx.known_good_change(fx.SURFACE_PATH["transition"])
    CC = fx.FIXTURE_CHANGE_COMMITS

    def derive(self, receipts, cc=None, **k):
        return refusal(wi.derive_branch_writer, receipts, cc or self.CC, target_repository=self.CH["target_repository"],
                       change_id=self.CH["change_id"], **k)

    def test_session_is_the_head_receipts_pusher(self):
        out = self.derive(fx.fixture_push_receipts(self.CH))
        self.assertEqual((out["session"], out["pushers"], out["head_commit"]), (SESSION, [SESSION], self.CC["head_commit"]))
        self.assertEqual(len(out["chain"]), 2)

    def gap(self, receipts, want_gap, cc=None, code="BRANCH_WRITER_UNOBSERVED"):
        out = self.derive(receipts, cc)
        self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                         ("FAIL_CLOSED", code, "BRANCH_WRITER_IS_BRANCH_OWNER"), want_gap)
        self.assertEqual(out["writer_evidence"], want_gap)
        self.assertTrue(six(out), want_gap)
        self.assertIn("sv_push_receipt.py::emit", out["retry_entrypoint"])
        self.assertIn("#3255", out["retry_entrypoint"])
        return out

    def test_every_chain_gap_is_six_field_fail_closed_never_deny(self):
        r1, r2 = fx.fixture_push_receipts(self.CH)
        other_repo = fx.push_receipt(self.CH, self.CC["base_commit"], fx.FIXTURE_MID_COMMIT, [fx.FIXTURE_MID_COMMIT], repository="x/y")
        other_ref = fx.push_receipt(self.CH, fx.FIXTURE_MID_COMMIT, self.CC["head_commit"], [self.CC["head_commit"]], ref="refs/heads/other")
        other_change = fx.push_receipt(self.CH, self.CC["base_commit"], self.CC["head_commit"], [self.CC["head_commit"]],
                                       change_id="svc:" + "e" * 64)
        fork = fx.push_receipt(self.CH, self.CC["base_commit"], self.CC["head_commit"], [self.CC["head_commit"]])
        unsealed = dict(r2, pusher_session="someone else")  # edited after sealing
        cases = [
            (None, "NO_PUSH_RECEIPT"), ([], "NO_PUSH_RECEIPT"),
            ([r1, unsealed], "PUSH_RECEIPT_INVALID"),
            ([other_repo, r2], "PUSH_RECEIPT_OTHER_REPOSITORY"),
            ([r1, other_ref], "PUSH_RECEIPT_REFS_DIFFER"),
            ([other_change], "PUSH_RECEIPT_OTHER_CHANGE"),
            ([r1, fork], "PUSH_RECEIPT_CHAIN_FORKS"),
            ([r2], "PUSH_RECEIPT_CHAIN_NOT_AT_BASE"),
        ]
        for receipts, want in cases:
            self.gap(receipts, want)
        stray = fx.push_receipt(self.CH, "d" * 40, "e" * 40, ["e" * 40])
        self.gap([r1, r2, stray], "PUSH_RECEIPT_CHAIN_GAP")
        self.gap(fx.fixture_push_receipts(self.CH), "CHANGE_COMMITS_UNOBSERVED", cc={"base_commit": None, "head_commit": None})

    def test_chain_not_at_head_is_writer_evidence_not_at_head(self):
        r1, _ = fx.fixture_push_receipts(self.CH)
        out = self.gap([r1], "WRITER_EVIDENCE_NOT_AT_HEAD", code="WRITER_EVIDENCE_NOT_AT_HEAD")
        self.assertEqual((out["chain_tip"], out["head_commit"]), (fx.FIXTURE_MID_COMMIT, self.CC["head_commit"]))


class AdmissionTests(unittest.TestCase):
    def test_known_good_admits_from_the_chain(self):
        _, obs = admitted_obs()
        self.assertEqual(wi.admit(obs, fixture_mode=True)["disposition"], "ALLOW")
        self.assertNotIn("declared_session", obs)
        self.assertNotIn("declared_session_matches_writers", obs)

    def test_no_pr_body_declaration_is_needed_and_none_grants_or_refuses(self):
        # declared_session is an attribution label only: any non-empty value admits identically; the writer is derived
        for label in ("anything at all", "P9 Some Other Lane", fx.FOREIGN_SESSION):
            ch = base.reseal_change(dict(fx.known_good_change(fx.SURFACE_PATH["transition"]), declared_session=label))
            _, obs = admitted_obs(ch)
            out = wi.admit(obs, fixture_mode=True)
            self.assertEqual(out["disposition"], "ALLOW", (label, out))
        # and a matching declaration never rescues a missing chain
        _, obs = admitted_obs(push_receipts=None)
        out = wi.admit(obs, fixture_mode=True)
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "BRANCH_WRITER_UNOBSERVED"))
        self.assertTrue(six(out))

    def test_chain_gap_fail_closes_admission_in_both_modes(self):
        ch = fx.known_good_change(fx.SURFACE_PATH["transition"])
        r1, _ = fx.fixture_push_receipts(ch)
        for receipts, want in ((None, "BRANCH_WRITER_UNOBSERVED"), ([r1], "WRITER_EVIDENCE_NOT_AT_HEAD")):
            _, obs = admitted_obs(ch, push_receipts=receipts)
            for fixture_mode in (False, True):
                out = wi.admit(obs, fixture_mode=fixture_mode)
                self.assertNotEqual(out["disposition"], "ALLOW")
            out = wi.admit(obs, fixture_mode=True)
            self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                             ("FAIL_CLOSED", want, "BRANCH_WRITER_IS_BRANCH_OWNER"))
            self.assertTrue(six(out))

    def test_foreign_pusher_is_fail_closed_unless_granted(self):
        ch = fx.known_good_change(fx.SURFACE_PATH["transition"])
        cc = fx.FIXTURE_CHANGE_COMMITS
        mixed = [fx.push_receipt(ch, cc["base_commit"], fx.FIXTURE_MID_COMMIT, [fx.FIXTURE_MID_COMMIT], session=fx.FOREIGN_SESSION),
                 fx.push_receipt(ch, fx.FIXTURE_MID_COMMIT, cc["head_commit"], [cc["head_commit"]])]
        _, obs = admitted_obs(ch, push_receipts=mixed)
        out = wi.admit(obs, fixture_mode=True)
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "BRANCH_HAS_FOREIGN_WRITER"))
        self.assertEqual((out["derived_session"], out["foreign_writers"]), (SESSION, [fx.FOREIGN_SESSION]))
        self.assertTrue(six(out))

    def test_propose_checks_claims_against_the_derived_session(self):
        issue = dict(base.nativize_issue(base.ISSUES[0]), lifecycle_state="CLAIMED", claim={"session": SESSION})
        ch = base.al_known_good_change(issue["issue_id"])
        ok = wi.transition("SV_CHANGE_PROPOSE", ch, hb_epoch=EPOCH, context={**fx.writer_context(ch), "issues": [issue]})
        self.assertEqual(ok["disposition"], "ALLOW", ok)
        # the chain names another session as the head pusher: the issue is not claimed by the branch writer
        other = fx.writer_context(ch, session=fx.FOREIGN_SESSION)
        ch2 = copy.deepcopy(ch); ch2["content"][0]["writer_session"] = {"session": fx.FOREIGN_SESSION, "evidence_class": "DECLARED"}
        out = wi.transition("SV_CHANGE_PROPOSE", base.reseal_change(ch2), hb_epoch=EPOCH, context={**other, "issues": [issue]})
        self.assertEqual(out["failure_code"], "RESOLVED_ISSUE_NOT_CLAIMED_BY_AUTHOR")
        none = wi.transition("SV_CHANGE_PROPOSE", ch, hb_epoch=EPOCH, context={"issues": [issue]})
        self.assertEqual((none["disposition"], none["failure_code"]), ("FAIL_CLOSED", "BRANCH_WRITER_UNOBSERVED"))

    def test_pr_author_predicate_is_retired_everywhere_it_decided(self):
        preds = {p for t in LIFECYCLE["transitions"] for p in t["predicates"]}
        self.assertNotIn("PR_AUTHOR_SESSION_DECLARED", preds)
        src = (ROOT / "resident-runtime/sv_work_items.py").read_text()
        self.assertNotIn("AUTHOR_SESSION_NOT_DECLARED", src)
        self.assertNotIn('"PR_AUTHOR_SESSION_DECLARED"', src)
        # the frozen corpus class keeps its id; its axis now fires BRANCH_WRITER_UNOBSERVED
        corpus = base.jsonl("data/admission-scenarios/corpus.jsonl")
        neg = [s for s in corpus if s["scenario_id"] == "ASC-PR_AUTHOR_SESSION_DECLARED@schema/declared_session"]
        self.assertEqual(len(neg), 1)
        self.assertEqual((neg[0]["expected_disposition"], neg[0]["expected_failure_code"]), ("FAIL_CLOSED", "BRANCH_WRITER_UNOBSERVED"))
        self.assertEqual(wi.admit(neg[0]["observed_inputs"], fixture_mode=True)["failure_code"], "BRANCH_WRITER_UNOBSERVED")


class ModeDeclarationTests(unittest.TestCase):
    PM = LIFECYCLE["predicate_modes"]

    def check(self, name, m):
        self.assertEqual(m["lowest_supported_mode"], "E0", name)
        for r in RUNGS:
            self.assertTrue(isinstance(m.get(r), str) and m[r], (name, r))
        self.assertTrue(isinstance(m.get("llm_inputs"), str) and m["llm_inputs"], name)
        self.assertFalse(PROVIDER.search(json.dumps(m)), name)

    def test_every_lifecycle_predicate_declares_modes(self):
        names = {p for t in LIFECYCLE["transitions"] if t["transition_class"].startswith(("SV_ISSUE_", "SV_CHANGE_"))
                 for p in t["predicates"]}
        self.assertTrue(names)
        self.assertLessEqual(names, set(self.PM["predicates"]))
        for n, m in self.PM["predicates"].items():
            self.check(n, m)

    def test_every_runtime_refusal_and_corpus_predicate_declares_modes(self):
        src = (ROOT / "resident-runtime/sv_work_items.py").read_text()
        runtime = set(re.findall(r'_(?:fail|deny)\(\s*"[A-Z0-9_]+",\s*"([A-Za-z0-9_.]+)"', src))
        runtime = {p for p in runtime if not p.endswith("_")}  # "RECORD_SCHEMA_IS_" + schema: the expanded names are listed
        runtime |= {"BRANCH_WRITER_IS_BRANCH_OWNER", "RECORD_SCHEMA_IS_stegverse.sv_change.v1", "RECORD_SCHEMA_IS_stegverse.sv_issue.v1"}
        runtime -= {"RECORD_SCHEMA_IS_stegverse.sv_check_receipt.v1"}  # the check receipt is not an SV_CHANGE / SV_ISSUE record
        self.assertLessEqual(runtime, set(self.PM["predicates"]), sorted(runtime - set(self.PM["predicates"])))
        self.assertLessEqual(set(al.PREDICATE_BINDINGS), set(self.PM["predicates"]))
        classes = base.jsonl("data/admission-scenarios/classes.jsonl")
        self.assertLessEqual({c["predicate"] for c in classes}, set(self.PM["predicates"]))

    def test_every_invariant_declares_modes(self):
        for i in INVARIANTS["invariants"]:
            self.check(i["invariant_id"], i["modes"])

    def test_ladder_is_referenced_not_duplicated(self):
        self.assertIn("#3308", self.PM["ladder"])
        self.assertIn("operating-modes.json", self.PM["ladder"])
        self.assertNotIn("ladder", {k for k in self.PM if isinstance(self.PM[k], list)})

    def test_writer_predicate_e0_form_is_the_chain_and_its_terminal(self):
        m = self.PM["predicates"]["BRANCH_WRITER_IS_BRANCH_OWNER"]
        self.assertIn("derive_branch_writer", m["E0"])
        self.assertIn("BRANCH_WRITER_UNOBSERVED", m["unavailable"])
        new = next(i for i in INVARIANTS["invariants"] if i["invariant_id"] == "BRANCH_WRITER_IS_DERIVED_FROM_THE_PUSH_RECEIPT_CHAIN")
        self.assertIn("PR_AUTHOR_SESSION_DECLARED", new["retires"])
        self.assertEqual(new["owning_goal"], GOAL163)


if __name__ == "__main__":
    unittest.main()
