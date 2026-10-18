"""Round 3: undeclared-command receipts, NATIVE_RECORD_HB_EPOCH_IS_BASE_LEDGER_HEAD_EPOCH (provisional, JD-P4-3) and
CHECK_DERIVED_ISSUES_ARE_DERIVED_FROM_THE_LEDGERED_FAILING_RECEIPT. Pure functions over supplied bytes; no clock, no network."""
from __future__ import annotations

import json
import unittest

from tests import test_sv_native_work_items as base
from tests import test_sv_record_modes as rm

wi, fx, ss = base.wi, base.fx, base.ss
ROOT, U = base.ROOT, base.wi.UNKNOWN
GOAL163 = "StegVerse-org/.github#163"
CHECK_SCHEMA = json.loads((ROOT / "schemas/sv-check-receipt.v1.schema.json").read_text())
ISSUE_SCHEMA = json.loads((ROOT / "schemas/sv-issue.v1.schema.json").read_text())
CHANGE_SCHEMA = json.loads((ROOT / "schemas/sv-change.v1.schema.json").read_text())
LEDGER_COMMIT = "e" * 40


def refusal(fn, *a, **k):
    try:
        return fn(*a, **k)
    except wi.Refusal as r:
        return r.record


def six(rec):
    return all(isinstance(rec.get(f), str) and rec[f] for f in wi.SIX_FIELDS) and GOAL163 in rec["owning_existing_goal"]


def check_receipt(check_id, disposition="FAIL_CLOSED", code=None, digest="sha256:" + "a" * 64, **extra):
    r = {"schema": wi.CHECK_RECEIPT_SCHEMA, "check_id": check_id, "disposition": disposition, "change_digest": digest,
         "head_sha": "b" * 40, "hb_epoch": base.EPOCH, "verifier_ref": "SV-LLM/.github#46@f8f72487"}
    if disposition != "ALLOW":
        r.update({"failure_code": code or "CHECK_COMMAND_UNDECLARED", "failed_predicate": "CHECK_HAS_OFFLINE_COMMAND",
                  "required_evidence_or_repair": "declare an offline command for the check in the required-checks row",
                  "retry_entrypoint": "NWI-S1 verifier", "owning_existing_goal": GOAL163,
                  "next_attempt": "after the row declares the command"})
    r.update(extra)
    return r


class UndeclaredCommandReceiptTests(unittest.TestCase):
    CID = "supplied-epoch-binder-check"

    def test_explicit_fail_closed_receipt_is_accepted(self):
        r = check_receipt(self.CID)
        self.assertEqual(ss.validate(r, CHECK_SCHEMA), [])
        self.assertEqual(wi.validate_check_receipt(r)["failure_code"], "CHECK_COMMAND_UNDECLARED")

    def test_allow_or_other_outcome_refused(self):
        for r in (check_receipt(self.CID, "ALLOW"), check_receipt(self.CID, "DENY"),
                  check_receipt(self.CID, "FAIL_CLOSED", code="CHECK_SKIPPED_OR_UNOBSERVED")):
            out = refusal(wi.validate_check_receipt, r)
            self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                             ("FAIL_CLOSED", "CHECK_COMMAND_UNDECLARED", "CHECK_HAS_OFFLINE_COMMAND"), r["disposition"])
            self.assertTrue(six(out))

    def test_undeclared_id_stays_check_id_undeclared(self):
        self.assertEqual(refusal(wi.validate_check_receipt, check_receipt("epoch-binder"))["failure_code"], "CHECK_ID_UNDECLARED")

    def test_declared_command_check_unaffected(self):
        self.assertEqual(wi.validate_check_receipt(check_receipt("schema-validate", code="CHECK_SKIPPED_OR_UNOBSERVED"))["disposition"],
                         "FAIL_CLOSED")
        self.assertEqual(wi.validate_check_receipt(check_receipt("schema-validate", "ALLOW"))["disposition"], "ALLOW")

    def admission(self, check_id):
        ch = fx.known_good_change(fx.SURFACE_PATH["ledger_writer"])
        ch["validation_receipts"] = [fx.ledger_receipt(v["check_id"], ch["head"]["change_digest"],
                                                       "FAIL_CLOSED" if v["check_id"] == check_id else "ALLOW")
                                     for v in ch["validation_receipts"]]
        ch = base.reseal_change(ch)
        return wi.admit(wi.admission_inputs(ch, fx.LABS_BASE, fx.signoff_receipts_for(ch)), fixture_mode=True)

    def test_admission_names_check_command_undeclared(self):
        out = self.admission(self.CID)
        self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                         ("FAIL_CLOSED", "CHECK_COMMAND_UNDECLARED", "CHECK_HAS_OFFLINE_COMMAND"))
        self.assertTrue(six(out))
        other = self.admission("mutation-negative-suite")
        self.assertEqual((other["failure_code"], other["failed_predicate"]), ("CHECK_SKIPPED_OR_UNOBSERVED", "CHECK_RECEIPT_DISPOSITION_IS_ALLOW"))

    def test_fence_base_field_not_accepted_by_the_pinned_receipt_shape(self):
        r = check_receipt("registry-generation-fence", "ALLOW", base_commit="725d0f65cd5e7b81684c045c6f5d047f95fa946b")
        self.assertTrue(ss.validate(r, CHECK_SCHEMA))  # additionalProperties: false
        self.assertEqual(refusal(wi.validate_check_receipt, r)["failure_code"], "SV_CHECK_RECEIPT_INVALID")


def ledger_at(commit, body):
    rec = wi.seal(body, "receipt_sha256")
    head = {"organization": "StegVerse-org", "receipt_sha256": rec["receipt_sha256"]}
    return {commit + ":HEAD.json": json.dumps(head).encode(),
            commit + ":receipts/%s.json" % rec["receipt_sha256"].split(":", 1)[1]: json.dumps(rec, indent=2).encode()}


class NativeHbEpochTests(unittest.TestCase):
    def change(self):
        return fx.known_good_change(fx.SURFACE_PATH["transition"])

    def test_match_mismatch_and_unobserved(self):
        ch = self.change()
        head = ch["base_ref"]["ledger_head"]
        self.assertEqual(wi.validate_change(ch, ledger_at(head, {"hb_epoch": ch["hb_epoch"], "previous_receipt_sha256": None}))["hb_epoch"],
                         ch["hb_epoch"])
        out = refusal(wi.validate_change, ch, ledger_at(head, {"hb_epoch": "2048"}))
        self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                         ("DENY", "HB_EPOCH_NOT_BASE_LEDGER_EPOCH", "NATIVE_RECORD_HB_EPOCH_IS_BASE_LEDGER_HEAD_EPOCH"))
        good = ledger_at(head, {"hb_epoch": ch["hb_epoch"]})
        receipt_key = next(k for k in good if "receipts/" in k)
        unsealed = dict(good); unsealed[receipt_key] = json.dumps({"hb_epoch": ch["hb_epoch"], "receipt_sha256": "sha256:" + "0" * 64}).encode()
        for objs in ({}, ledger_at(head, {"note": "no epoch"}), ledger_at("d" * 40, {"hb_epoch": ch["hb_epoch"]}),
                     {k: v for k, v in good.items() if "HEAD" in k}, unsealed, {**good, receipt_key: b"\xff"}):
            out = refusal(wi.validate_change, ch, objs)
            self.assertEqual({f: out[f] for f in ("disposition", "failure_code", "failed_predicate", "required_evidence_or_repair",
                                                   "retry_entrypoint", "next_attempt")},
                             {"disposition": "FAIL_CLOSED", "failure_code": "HB_EPOCH_SOURCE_UNOBSERVED",
                              "failed_predicate": "NATIVE_RECORD_HB_EPOCH_IS_BASE_LEDGER_HEAD_EPOCH",
                              "required_evidence_or_repair": "bind base_ref.ledger_head to an org-ledger receipt carrying hb_epoch",
                              "retry_entrypoint": "native record re-derivation",
                              "next_attempt": "after the org writer appends at that head"})
            self.assertTrue(six(out))

    def test_without_ledger_bytes_behavior_unchanged(self):
        ch = self.change()
        self.assertEqual(wi.validate_change(ch)["change_id"], ch["change_id"])
        unk = base.reseal_change(dict(ch, hb_epoch=U))
        out = refusal(wi.validate_change, unk)
        self.assertEqual((out["disposition"], out["failure_code"]), ("DENY", "UNKNOWN_IN_NATIVE_RECORD"))

    def test_migrated_records_not_bound(self):
        mig = base.jsonl("data/sv-work-items/migration/sv-changes.jsonl")[0]
        self.assertEqual(wi.validate_change(mig, {})["change_id"], mig["change_id"])

    def test_pure_reader(self):
        head = "c" * 40
        self.assertEqual(wi.base_ledger_head_epoch(head, ledger_at(head, {"hb_epoch": "77"})), "77")
        self.assertIsNone(wi.base_ledger_head_epoch(head, ledger_at(head, {"hb_epoch": 77})))
        self.assertIsNone(wi.base_ledger_head_epoch("not-a-sha", ledger_at(head, {"hb_epoch": "77"})))


class CheckDerivedIssueTests(unittest.TestCase):
    OBS = {"registry_generation": 319, "ledger_head": "a5bb54d81893b392a3ce28182986fc39857807e1"}

    def ledgered(self, receipt, commit=LEDGER_COMMIT, indent=None):
        env = wi.seal({"evidence": receipt, "previous_receipt_sha256": None}, "receipt_sha256")
        ref = "refs/stegverse/organization-ledger@%s:receipts/%s.json" % (commit, env["receipt_sha256"].split(":", 1)[1])
        return json.dumps(env, indent=indent).encode(), ref

    def test_derivation_fields_and_validity(self):
        r = check_receipt("schema-validate", code="CHECK_SKIPPED_OR_UNOBSERVED")
        raw, ref = self.ledgered(r)
        iss = wi.derive_issue_from_check_receipt(raw, ref, observed_base=self.OBS)
        self.assertEqual(ss.validate(iss, ISSUE_SCHEMA), [])
        self.assertEqual(wi.validate_issue(iss)["issue_id"], iss["issue_id"])
        self.assertEqual(iss["record_mode"], "NATIVE")
        self.assertEqual(iss["source_receipt"], {"kind": "ORGANIZATION_LEDGER_RECEIPT", "ledger_ref": ref,
                                                 "receipt_sha256": json.loads(raw)["receipt_sha256"]})
        self.assertEqual(iss["disposition"]["failed_predicate"], r["failed_predicate"])
        self.assertEqual(iss["surface"], {"kind": "transition", "path": "scripts/build_sv_native_fixtures.py"})
        self.assertEqual(iss["owning_goal"], GOAL163)
        self.assertEqual(iss["owning_goal"], fx.wi.REQUIRED_CHECKS["owning_goal"])
        self.assertEqual(iss["violated_invariant"]["rule_id"], "SV-CHANGE-REQUIRED-CHECKS-001#checks.schema-validate")
        self.assertEqual(iss["opened_by_session"], wi.ISSUE_DERIVATION_SESSION)
        self.assertEqual(iss["hb_epoch"], r["hb_epoch"])

    def test_idempotent_and_runner_independent(self):
        r = check_receipt("unit-tests", code="CHECK_SKIPPED_OR_UNOBSERVED")
        raw, ref = self.ledgered(r)
        raw2, ref2 = self.ledgered(json.loads(json.dumps(r)), indent=2)  # other bytes, same receipt object
        a = wi.derive_issue_from_check_receipt(raw, ref, observed_base=self.OBS)
        b = wi.derive_issue_from_check_receipt(raw, ref, observed_base=self.OBS)
        c = wi.derive_issue_from_check_receipt(raw2, ref2, observed_base={**self.OBS, "registry_generation": 320})
        self.assertEqual(a, b)
        self.assertEqual(ref, ref2)
        self.assertEqual(a["issue_id"], c["issue_id"])  # observed_base is not identity
        self.assertEqual(a["surface"]["path"], "tests/test_sv_native_work_items.py")
        other, oref = self.ledgered(r, commit="f" * 40)  # the same receipt read at another ledger commit is another source ref
        self.assertNotEqual(wi.derive_issue_from_check_receipt(other, oref, observed_base=self.OBS)["issue_id"], a["issue_id"])

    def test_undeclared_command_issue_surface_is_the_row(self):
        raw, ref = self.ledgered(check_receipt("supplied-epoch-binder-check"))
        iss = wi.derive_issue_from_check_receipt(raw, ref, observed_base=self.OBS)
        self.assertEqual(iss["surface"], {"kind": "doc", "path": "data/sv-work-items/required-checks.json"})
        self.assertEqual(iss["disposition"]["failure_code"], "CHECK_COMMAND_UNDECLARED")

    def test_not_ledgered_fails_closed(self):
        r = check_receipt("schema-validate", code="CHECK_SKIPPED_OR_UNOBSERVED")
        raw, ref = self.ledgered(r)
        env = json.loads(raw)
        cases = [(json.dumps(r).encode(), ref),                                              # bare verifier receipt
                 (raw, ref.replace(ref.rsplit("/", 1)[1], "0" * 64 + ".json")),             # not at that path
                 (raw, "refs/heads/main:receipts/x.json"),                                  # not an org-ledger ref
                 (json.dumps({**env, "previous_receipt_sha256": "sha256:" + "1" * 64}).encode(), ref),  # unsealed
                 (b"\xff", ref)]
        for b, rf in cases:
            out = refusal(wi.derive_issue_from_check_receipt, b, rf, observed_base=self.OBS)
            self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                             ("FAIL_CLOSED", "SOURCE_RECEIPT_NOT_LEDGERED", "CHECK_DERIVED_ISSUES_ARE_DERIVED_FROM_THE_LEDGERED_FAILING_RECEIPT"))
            self.assertTrue(six(out))

    def test_allow_receipt_derives_nothing_and_base_required(self):
        raw, ref = self.ledgered(check_receipt("schema-validate", "ALLOW"))
        self.assertEqual(refusal(wi.derive_issue_from_check_receipt, raw, ref, observed_base=self.OBS)["failure_code"],
                         "CHECK_RECEIPT_NOT_FAILING")
        raw, ref = self.ledgered(check_receipt("schema-validate", code="CHECK_SKIPPED_OR_UNOBSERVED"))
        self.assertEqual(refusal(wi.derive_issue_from_check_receipt, raw, ref)["failure_code"], "ISSUE_OBSERVED_BASE_UNSUPPLIED")
        raw, ref = self.ledgered(check_receipt("epoch-binder"))
        self.assertEqual(refusal(wi.derive_issue_from_check_receipt, raw, ref, observed_base=self.OBS)["failure_code"], "CHECK_ID_UNDECLARED")

    def test_invariants_recorded(self):
        inv = json.loads((ROOT / "data/sv-work-items/invariants.json").read_text())
        ids = {i["invariant_id"]: i for i in inv["invariants"]}
        self.assertEqual(ids["NATIVE_RECORD_HB_EPOCH_IS_BASE_LEDGER_HEAD_EPOCH"]["status"], "PROVISIONAL_UNTIL_JD-P4-3")
        self.assertIn("CHECK_DERIVED_ISSUES_ARE_DERIVED_FROM_THE_LEDGERED_FAILING_RECEIPT", ids)
        doc = (ROOT / "docs/NWI_S0_NATIVE_WORK_ITEMS_MIRROR_HANDOFF.md").read_text()
        for i in ids:
            self.assertIn(i, doc)


if __name__ == "__main__":
    unittest.main()
