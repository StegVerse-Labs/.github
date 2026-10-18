"""GATE_RECEIPT_PAIR_RESOLVES_GATE_DERIVED_ISSUE and GATE_MANIFEST_IS_THE_CONTRACT_PINNED_MANIFEST over Lane B's minted pair
(SV-LLM/.github#46 @b9942dc8, verifier_ref SV-LLM/.github#46:sha256:9bc988fc), carried byte-for-byte in
tests/fixtures/laneB-46-b9942dc8: base 978b8880 FAIL_CLOSED STAGE_REGRESSION (receipt sha256 4a2cd463), head 7898cedb ALLOW
(gate receipt sha256 2d887e0b). The org append is SIMULATED (tests/sv_ledger_fixtures.py at ledger commit 000...0, as Lane B
did); nothing here is on a real ledger. Pure; no clock, no network."""
from __future__ import annotations

import copy
import hashlib
import json
import unittest

from tests import test_sv_stage_gate_issue as sgi
from tests import sv_ledger_fixtures as lf

wi, fx, base = sgi.wi, sgi.fx, sgi.base
ROOT = sgi.ROOT
D = ROOT / "tests/fixtures/laneB-46-b9942dc8"
SIM = "0" * 40  # Lane B's simulated ledger commit
EPOCH = 469411750  # the receipts' own hb_epoch
LANE_B_BASE = {"ledger_head": "a5bb54d81893b392a3ce28182986fc39857807e1", "registry_generation": 319}
BASE_COMMIT, HEAD_COMMIT = "978b8880d238dc3e3a8b690c0675d8bb0e9d6985", "7898cedba1400c8545cebcb463fd26deb25f7d5a"
ISSUE_ID = "svi:2dc786afabce2f55c3f0c625d0accbc9e8bc16f08b8c4cc2e0334ca857ebd04b"
ISSUE_SHA = "sha256:f4aa0945825e1e853828d5772a6dda1a52cf2d35106c3b2ea2a0c55c615287aa"
PINNED_BLOB = "20b37917e1454ec788e8f1b8c75d1562ba76d1b3"
CONTRACT_PINS = {"files": {"data/sv-work-items/stages/NWI-S0.json": {
    "blob": PINNED_BLOB, "sha256": "sha256:f92387e4cd2af861411da101f694eda9cd306833f9857d577573fae3eeace56a"}}}  # @7898cedb


def load(name):
    return json.loads((D / name).read_text())


def refusal(fn, *a, **k):
    try:
        return fn(*a, **k)
    except wi.Refusal as r:
        return r.record


def ledger(receipt, commit=SIM):
    repo = lf.repo_receipt(receipt, EPOCH)
    org = lf.org_receipt(repo, EPOCH, boundary_evidence=lf.boundary())
    return lf.ledger_objects(commit, org, repo), lf.org_ref(commit, org)


class LaneBPair(unittest.TestCase):
    def setUp(self):
        self.br, self.hr = load("base-978b8880.nwi-s0-exit-gate.json"), load("head-7898cedb.nwi-s0-exit-gate.json")
        self.bs, self.hs = load("base-978b8880.subject.json"), load("head-7898cedb.subject.json")
        bo, self.bref = ledger(self.br)
        ho, self.href = ledger(self.hr)
        self.objs = {**bo, **ho}
        self.iss = wi.derive_issue_from_check_receipt(self.objs, self.bref, observed_base=LANE_B_BASE)
        ch = sgi.resolving_change([self.iss["issue_id"]])
        self.change = base.reseal_change(dict(ch, base_ref={**ch["base_ref"], "ledger_head": SIM}))
        self.evals = [{"subject": self.bs, "receipt_ref": self.bref}, {"subject": self.hs, "receipt_ref": self.href}]
        self.commits = {"base_commit": BASE_COMMIT, "head_commit": HEAD_COMMIT}

    def facts(self, **k):
        kw = dict(evaluations=self.evals, change_commits=self.commits, contract_pins=CONTRACT_PINS)
        kw.update(k)
        return wi.derive_resolved_issue_facts(self.objs, "refs/stegverse/organization-ledger@" + SIM, self.change, [self.iss], **kw)

    def obs(self, facts, change=None):
        ch = change or self.change
        o = wi.admission_inputs(ch, fx.LABS_BASE, fx.signoff_receipts_for(ch), fx.fixture_base_state_readback(), facts)
        return o

    def test_lane_b_files_are_byte_identical(self):
        self.assertEqual(hashlib.sha256((D / "base-978b8880.nwi-s0-exit-gate.json").read_bytes()).hexdigest()[:8], "4a2cd463")
        self.assertEqual(hashlib.sha256((D / "head-7898cedb.nwi-s0-exit-gate.json").read_bytes()).hexdigest()[:8], "2d887e0b")
        self.assertEqual(wi.stage_evaluation_digest(self.bs), self.br["change_digest"])
        self.assertEqual(wi.stage_evaluation_digest(self.hs), self.hr["change_digest"])
        self.assertEqual((self.br["disposition"], self.br["failure_code"], self.hr["disposition"]), ("FAIL_CLOSED", "STAGE_REGRESSION", "ALLOW"))

    def test_the_pair_derives_exactly_one_fact(self):
        self.assertEqual((self.iss["issue_id"], self.iss["issue_sha256"]), (ISSUE_ID, ISSUE_SHA))
        f, = self.facts()
        self.assertEqual((f["issue_id"], f["check_id"], f["fixture_only"]), (ISSUE_ID, "nwi-s0-exit-gate", False))
        self.assertEqual(f["derived_issue_ids_from_receipt"], [ISSUE_ID])
        out = wi.verify_resolution_pair(f["resolution_pair"], "nwi-s0-exit-gate")
        self.assertEqual((out["disposition"], out["pinned_manifest_blob"], out["base_receipt"], out["head_receipt"]),
                         ("ALLOW", PINNED_BLOB, self.bref, self.href))
        self.assertEqual(f["resolution_pair"]["manifest_source"], "CONTRACT_PINS")
        self.assertEqual(wi.verify_resolutions(self.obs([f]))["disposition"], "ALLOW")
        # the head receipt is ALLOW: it derives nothing itself
        self.assertEqual(refusal(wi.derive_issue_from_check_receipt, self.objs, self.href)["failure_code"], "CHECK_RECEIPT_NOT_FAILING")

    def test_pure(self):
        self.assertEqual(wi.canon(self.facts()), wi.canon(self.facts()))

    def code(self, facts, change=None):
        out = refusal(wi.verify_resolutions, self.obs(facts, change))
        return out["disposition"], out["failure_code"]

    def pair_code(self, pair):
        out = refusal(wi.verify_resolution_pair, pair, "nwi-s0-exit-gate")
        if out["disposition"] == "ALLOW":
            return "ALLOW", None
        for k in ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint", "owning_existing_goal", "next_attempt"):
            self.assertTrue(out.get(k), k)  # all six fields
        self.assertIn("StegVerse-org/.github#163", out["owning_existing_goal"])
        return out["disposition"], out["failure_code"]

    def test_each_failure_has_its_own_code(self):
        f, = self.facts()
        p = f["resolution_pair"]
        def mut(fn):
            q = copy.deepcopy(p); fn(q); return self.pair_code(q)
        def rebind(side):
            side["subject_digest"] = wi.stage_evaluation_digest(side["subject"]); side["receipt"]["change_digest"] = side["subject_digest"]
            side["receipt"]["head_sha"] = side["subject"]["evaluated_commit"]
        self.assertEqual(mut(lambda q: q.update(change_commits={"base_commit": None, "head_commit": HEAD_COMMIT})),
                         ("FAIL_CLOSED", "GATE_PAIR_CHANGE_COMMITS_UNOBSERVED"))
        self.assertEqual(mut(lambda q: q["base"]["receipt"].update(ledgered_at_base=False)), ("FAIL_CLOSED", "GATE_PAIR_BASE_RECEIPT_MISSING"))
        self.assertEqual(mut(lambda q: q.update(head=None)), ("FAIL_CLOSED", "GATE_PAIR_HEAD_RECEIPT_MISSING"))
        self.assertEqual(mut(lambda q: q["head"]["receipt"].update(change_digest="sha256:" + "9" * 64)),
                         ("DENY", "GATE_PAIR_SUBJECT_NOT_BOUND_BY_RECEIPT"))
        self.assertEqual(mut(lambda q: q["head"]["receipt"].update(disposition="FAIL_CLOSED")), ("DENY", "GATE_PAIR_HEAD_RECEIPT_NOT_ALLOW"))
        def other_repo(q):
            q["head"]["subject"]["repository"] = "StegVerse-Labs/other"; rebind(q["head"])
        self.assertEqual(mut(other_repo), ("DENY", "GATE_PAIR_REPOSITORY_MISMATCH"))
        def other_manifest(q):
            q["head"]["subject"]["manifest_blob"] = "f" * 40; rebind(q["head"])
        self.assertEqual(mut(other_manifest), ("DENY", "GATE_PAIR_MANIFEST_MISMATCH"))
        self.assertEqual(mut(lambda q: q.update(pinned_manifest=None)), ("FAIL_CLOSED", "GATE_PAIR_PINNED_MANIFEST_UNOBSERVED"))
        def wrong_commit(q):
            q["change_commits"] = {"base_commit": "a" * 40, "head_commit": HEAD_COMMIT}
        self.assertEqual(mut(wrong_commit), ("DENY", "GATE_PAIR_SUBJECT_COMMIT_WRONG"))
        # without contract-pins the derived pair is unobserved, never ALLOW
        g, = self.facts(contract_pins=None)
        self.assertEqual(self.pair_code(g["resolution_pair"]), ("FAIL_CLOSED", "GATE_PAIR_PINNED_MANIFEST_UNOBSERVED"))

    def test_a_manifest_read_from_the_subject_is_deny(self):
        # a subject that binds the blob at its own evaluated_commit, not the contract-pinned blob
        other_pins = {"files": {"data/sv-work-items/stages/NWI-S0.json": {"blob": "e" * 40, "sha256": None}}}
        f, = self.facts(contract_pins=other_pins)
        self.assertEqual(self.pair_code(f["resolution_pair"]), ("DENY", "GATE_MANIFEST_READ_FROM_SUBJECT"))
        out = refusal(wi.verify_resolution_pair, f["resolution_pair"], "nwi-s0-exit-gate")
        self.assertEqual(out["failed_predicate"], "GATE_MANIFEST_IS_THE_CONTRACT_PINNED_MANIFEST")
        self.assertEqual(self.code([f]), ("DENY", "GATE_MANIFEST_READ_FROM_SUBJECT"))
        # the receipt-level check: validate_gate_receipt(..., contract_pins=)
        rb = fx.fixture_base_state_readback()
        subj = dict(self.hs, base_ref=dict(fx.LABS_BASE))
        rc = dict(self.hr, change_digest=wi.stage_evaluation_digest(subj))
        out = refusal(wi.validate_gate_receipt, rc, subj, rb, fixture_mode=True, contract_pins=other_pins)
        self.assertEqual((out["disposition"], out["failure_code"]), ("DENY", "GATE_MANIFEST_READ_FROM_SUBJECT"))

    def test_self_sourced_head_receipt_is_deny(self):
        f, = self.facts()
        hp = f["resolution_pair"]["head"]["receipt"]["receipt_ledger_paths"][0]
        ch = sgi.resolving_change([ISSUE_ID], extra_content=[
            {"path": hp, "blob_digest": "sha256:" + "d" * 64, "deleted": False, "writer_session": {"session": fx.SESSION, "evidence_class": "DECLARED"}}])
        ch = base.reseal_change(dict(ch, base_ref={**ch["base_ref"], "ledger_head": SIM}))
        self.assertEqual(self.code([f], ch), ("DENY", "SV_CHANGE_SELF_SOURCED_ISSUE"))

    def test_resolved_once_still_applies(self):
        resolved = wi.seal({**{k: v for k, v in self.iss.items() if k != "issue_sha256"}, "lifecycle_state": "RESOLVED",
                            "resolved_by": "svc:" + "1" * 64}, "issue_sha256")
        f, = wi.derive_resolved_issue_facts(self.objs, "refs/stegverse/organization-ledger@" + SIM, self.change, [resolved],
                                            evaluations=self.evals, change_commits=self.commits, contract_pins=CONTRACT_PINS)
        self.assertEqual(self.code([f]), ("DENY", "SV_ISSUE_ALREADY_RESOLVED"))

    def test_3264_stays_resolves_nothing_at_its_real_base(self):
        # at the real base a5bb54d8 nothing is appended: no fact, and the real record cites nothing
        real = sgi.resolving_change([ISSUE_ID])
        facts = wi.derive_resolved_issue_facts({}, "refs/stegverse/organization-ledger@" + LANE_B_BASE["ledger_head"], real, [self.iss],
                                               evaluations=self.evals, change_commits=self.commits, contract_pins=CONTRACT_PINS)
        self.assertEqual(facts, [])
        self.assertEqual(self.code(facts, real), ("DENY", "SV_CHANGE_RESOLVES_NOTHING"))
        self.assertEqual(self.code([], sgi.resolving_change([])), ("DENY", "SV_CHANGE_RESOLVES_NOTHING"))

    def test_contract_pins_is_the_manifest_source(self):
        m = json.loads((ROOT / "data/sv-work-items/stages/NWI-S0.json").read_text())["exit_gate_check"]
        self.assertEqual((m["evaluation_subject"]["manifest_source"], m["receipt_form"]["manifest_source"]), ("CONTRACT_PINS", "CONTRACT_PINS"))
        cp = (ROOT / "data/sv-work-items/contract-pins.json").read_bytes()
        pin = wi.pinned_gate_manifest(cp, "NWI-S0")
        self.assertEqual(pin["contract_pins_sha256"], "sha256:" + hashlib.sha256(cp).hexdigest())
        inv = {i["invariant_id"]: i for i in json.loads((ROOT / "data/sv-work-items/invariants.json").read_text())["invariants"]}
        self.assertIn("GATE_MANIFEST_READ_FROM_SUBJECT", inv["GATE_MANIFEST_IS_THE_CONTRACT_PINNED_MANIFEST"]["codes"])
        self.assertNotIn("GATE_PAIR_MANIFEST_EQUIVALENCE_UNOBSERVED", inv["GATE_RECEIPT_PAIR_RESOLVES_GATE_DERIVED_ISSUE"]["codes"])


class IntegerEpochTests(unittest.TestCase):
    """NATIVE_RECORD_HB_EPOCH_IS_A_STRING: validate_change agrees with admission (an integer hb_epoch is DENY HB_EPOCH_MISMATCH)."""

    def test_integer_epoch_is_deny_in_validate_change(self):
        ok = fx.known_good_change(fx.SURFACE_PATH["transition"])
        for bad in (1024, 469411750, 1024.0, True, ["1024"], {"e": "1024"}):
            ch = base.reseal_change(dict(ok, hb_epoch=bad))
            out = refusal(wi.validate_change, ch)
            self.assertEqual((out["disposition"], out["failure_code"], out.get("rule")),
                             ("DENY", "HB_EPOCH_MISMATCH", "NATIVE_RECORD_HB_EPOCH_IS_A_STRING"), repr(bad))
            for k in ("failed_predicate", "required_evidence_or_repair", "retry_entrypoint", "owning_existing_goal", "next_attempt"):
                self.assertTrue(out.get(k), k)
        # the string form is not refused by this rule
        out = refusal(wi.validate_change, base.reseal_change(dict(ok, hb_epoch=str(ok.get("hb_epoch") or "1024"))))
        self.assertNotEqual(out.get("rule"), "NATIVE_RECORD_HB_EPOCH_IS_A_STRING")


if __name__ == "__main__":
    unittest.main()
