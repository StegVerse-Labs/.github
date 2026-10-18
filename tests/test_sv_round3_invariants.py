"""Round 3: undeclared-command receipts, NATIVE_RECORD_HB_EPOCH_IS_BASE_LEDGER_HEAD_EPOCH (decided in round 5, JD-P4-3 partial) and
CHECK_DERIVED_ISSUES_ARE_DERIVED_FROM_THE_LEDGERED_FAILING_RECEIPT. Pure functions over supplied bytes; no clock, no network."""
from __future__ import annotations

import json
import unittest
from unittest import mock

from tests import test_sv_native_work_items as base
from tests import test_sv_record_modes as rm
from tests import sv_ledger_fixtures as lf

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


UNKNOWN_ENTRY = {"appender": "org-ledger-writer (Labs#3255)", "command_paths": [], "expected": U,
                 "minter": "NWI-S1-verifier (SV-LLM/.github#46)", "offline_command": U}


class UndeclaredCommandReceiptTests(unittest.TestCase):
    """The undeclared-command receipt rule stays generic for any future UNKNOWN command: simulated here by setting a
    declared id's row entry to UNKNOWN (no check in the committed row is in that state)."""
    CID = "supplied-epoch-binder-check"

    def setUp(self):
        p = mock.patch.dict(wi.REQUIRED_CHECKS["checks"], {self.CID: UNKNOWN_ENTRY})
        p.start()
        self.addCleanup(p.stop)

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
        return wi.admit(wi.admission_inputs(ch, fx.LABS_BASE, fx.signoff_receipts_for(ch), resolved_issues=fx.fixture_resolved_issues(ch)),
                        fixture_mode=True)

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


def ledger_at(commit, epoch=None, *, hb_reference=None, **kw):
    """The org ledger at `commit`: HEAD.json -> a sealed organization-transition receipt (real layout)."""
    repo = lf.repo_receipt({"note": "head fixture"}, 1024)
    org = lf.org_receipt(repo, epoch if epoch is not None else 1024, boundary_evidence=lf.boundary(), hb_reference=hb_reference, **kw)
    return lf.ledger_objects(commit, org, repo), org


class NativeHbEpochTests(unittest.TestCase):
    def change(self):
        return fx.known_good_change(fx.SURFACE_PATH["transition"])

    def assert_unobserved(self, ch, objs):
        out = refusal(wi.validate_change, ch, objs)
        self.assertEqual({f: out[f] for f in ("disposition", "failure_code", "failed_predicate", "required_evidence_or_repair",
                                               "retry_entrypoint", "next_attempt")},
                         {"disposition": "FAIL_CLOSED", "failure_code": "HB_EPOCH_SOURCE_UNOBSERVED",
                          "failed_predicate": "NATIVE_RECORD_HB_EPOCH_IS_BASE_LEDGER_HEAD_EPOCH",
                          "required_evidence_or_repair": "bind base_ref.ledger_head to an org-ledger receipt carrying hb_epoch",
                          "retry_entrypoint": "native record re-derivation",
                          "next_attempt": "after the org writer appends at that head"})
        self.assertTrue(six(out))

    def test_match_by_integer_value(self):
        ch = self.change()
        head = ch["base_ref"]["ledger_head"]
        objs, org = ledger_at(head, int(ch["hb_epoch"]))
        self.assertIsInstance(org["hb_reference"]["epoch"], int)
        self.assertNotIn("hb_epoch", org)
        self.assertEqual(wi.validate_change(ch, objs)["hb_epoch"], ch["hb_epoch"])
        self.assertEqual(wi.verify_native_hb_epoch(ch, objs)["hb_epoch"], "1024")

    def test_mismatch_is_deny(self):
        ch = self.change()
        objs, _ = ledger_at(ch["base_ref"]["ledger_head"], 2048)
        out = refusal(wi.validate_change, ch, objs)
        self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                         ("DENY", "HB_EPOCH_MISMATCH", "NATIVE_RECORD_HB_EPOCH_IS_BASE_LEDGER_HEAD_EPOCH"))
        self.assertEqual(out["expected"], "2048")

    def test_unobserved_cases(self):
        ch = self.change()
        head = ch["base_ref"]["ledger_head"]
        good, org = ledger_at(head, 1024)
        rkey = head + ":" + lf.ledger_store.receipt_key(org["receipt_sha256"])
        hb = dict(org["hb_reference"])

        def resealed(**changes):
            body = {k: v for k, v in org.items() if k != "receipt_sha256"}
            body.update(changes)
            o = {**body, "receipt_sha256": lf.sha(body)}
            return lf.ledger_objects(head, o)

        cases = [{}, {k: v for k, v in good.items() if not k.endswith("HEAD.json")},     # no HEAD
                 {k: v for k, v in good.items() if k != rkey},                              # HEAD names an absent receipt
                 {**good, rkey: json.dumps({**org, "authority_effect": "TAMPERED"}).encode()},  # broken seal
                 {**good, rkey: b"\xff"},
                 ledger_at("d" * 40, 1024)[0],                                              # another commit
                 resealed(hb_reference={k: v for k, v in hb.items() if k != "epoch"}),       # no epoch
                 resealed(hb_reference={**hb, "epoch": "1024"}),                            # string: no coercion
                 resealed(hb_reference={**hb, "epoch": 1024.0}),                            # float: no coercion
                 resealed(hb_reference={**hb, "epoch": True}),                              # bool is not an int here
                 resealed(hb_reference={**hb, "epoch": 31}),                                # below the hb32 anchor
                 resealed(hb_reference={**hb, "derived_from_clock": True}),                 # a clock reading
                 resealed(hb_reference=None),
                 resealed(hb_epoch="1024", hb_reference=None),                              # a top-level hb_epoch is not the source
                 resealed(schema="stegverse.repo-transition-receipt/v1")]
        for objs in cases:
            self.assert_unobserved(ch, objs)

    def test_record_epoch_must_be_ascii_digits(self):
        ch = self.change()
        objs, _ = ledger_at(ch["base_ref"]["ledger_head"], 1024)
        for bad in ("01024x", " 1024"):
            self.assertEqual(wi.verify_native_hb_epoch(dict(ch, hb_epoch="1024"), objs)["disposition"], "ALLOW")
            self.assertEqual(refusal(wi.verify_native_hb_epoch, dict(ch, hb_epoch=bad), objs)["failure_code"],
                             "HB_EPOCH_MISMATCH")
        self.assertEqual(wi.verify_native_hb_epoch(dict(ch, hb_epoch="01024"), objs)["disposition"], "ALLOW")  # integer value

    def test_without_ledger_bytes_behavior_unchanged(self):
        ch = self.change()
        self.assertEqual(wi.validate_change(ch)["change_id"], ch["change_id"])
        unk = base.reseal_change(dict(ch, hb_epoch=U))
        out = refusal(wi.validate_change, unk)
        # orchestrator decision UNKNOWN_IN_NATIVE_RECORD: FAIL_CLOSED, never DENY
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "UNKNOWN_IN_NATIVE_RECORD"))
        self.assertTrue(six(out))

    def test_migrated_records_not_bound(self):
        mig = base.jsonl("data/sv-work-items/migration/sv-changes.jsonl")[0]
        self.assertEqual(wi.validate_change(mig, {})["change_id"], mig["change_id"])


class CheckDerivedIssueTests(unittest.TestCase):
    OBS = {"registry_generation": 319, "ledger_head": "a5bb54d81893b392a3ce28182986fc39857807e1"}

    def ledgered(self, evidence, commit=LEDGER_COMMIT, operation="sv_check_receipt", boundary=True, retain_repo=True):
        repo = lf.repo_receipt(evidence, 1024)
        org = lf.org_receipt(repo, 1024, boundary_evidence=lf.boundary(operation) if boundary else None)
        return lf.ledger_objects(commit, org, repo if retain_repo else None), lf.org_ref(commit, org), org, repo

    def test_derivation_fields_and_validity(self):
        r = check_receipt("schema-validate", code="CHECK_SKIPPED_OR_UNOBSERVED")
        objs, ref, org, repo = self.ledgered(r)
        self.assertNotIn("evidence", org)
        self.assertEqual(repo["evidence"], r)
        iss = wi.derive_issue_from_check_receipt(objs, ref, observed_base=self.OBS)
        self.assertEqual(ss.validate(iss, ISSUE_SCHEMA), [])
        self.assertEqual(wi.validate_issue(iss)["issue_id"], iss["issue_id"])
        self.assertEqual(iss["record_mode"], "NATIVE")
        self.assertEqual(iss["source_receipt"], {"kind": "ORGANIZATION_LEDGER_RECEIPT", "ledger_ref": ref, "receipt_sha256": org["receipt_sha256"]})
        self.assertEqual(iss["disposition"]["failed_predicate"], r["failed_predicate"])
        self.assertEqual(iss["surface"], {"kind": "transition", "path": "scripts/build_sv_native_fixtures.py"})
        self.assertEqual(iss["owning_goal"], GOAL163)
        self.assertEqual(iss["owning_goal"], wi.REQUIRED_CHECKS["owning_goal"])
        self.assertEqual(iss["violated_invariant"]["rule_id"], "SV-CHANGE-REQUIRED-CHECKS-001#checks.schema-validate")
        self.assertEqual(iss["opened_by_session"], wi.ISSUE_DERIVATION_SESSION)
        self.assertEqual(iss["hb_epoch"], r["hb_epoch"])

    def test_kind_marker_and_absent_boundary_operation(self):
        r = check_receipt("unit-tests", code="CHECK_SKIPPED_OR_UNOBSERVED")
        a = wi.derive_issue_from_check_receipt(*self.ledgered(r)[:2], observed_base=self.OBS)
        objs, ref, _, _ = self.ledgered({**r, "kind": "sv_check_receipt"}, boundary=False)
        b = wi.derive_issue_from_check_receipt(objs, ref, observed_base=self.OBS)
        self.assertEqual(a["disposition"], b["disposition"])
        self.assertEqual(b["surface"]["path"], "tests/test_sv_native_work_items.py")

    def test_idempotent_and_runner_independent(self):
        r = check_receipt("unit-tests", code="CHECK_SKIPPED_OR_UNOBSERVED")
        objs, ref, org, repo = self.ledgered(r)
        a = wi.derive_issue_from_check_receipt(objs, ref, observed_base=self.OBS)
        b = wi.derive_issue_from_check_receipt(dict(objs), ref, observed_base=self.OBS)
        respaced = {k: json.dumps(json.loads(v)).encode() for k, v in objs.items()}  # other bytes, same objects
        c = wi.derive_issue_from_check_receipt(respaced, ref, observed_base={**self.OBS, "registry_generation": 320})
        self.assertEqual(a, b)
        self.assertEqual(a["issue_id"], c["issue_id"])  # observed_base is not identity
        objs2, ref2, _, _ = self.ledgered(r, commit="f" * 40)  # the same receipt at another ledger commit is another source ref
        self.assertNotEqual(wi.derive_issue_from_check_receipt(objs2, ref2, observed_base=self.OBS)["issue_id"], a["issue_id"])

    def test_undeclared_command_issue_surface_is_the_row(self):
        objs, ref, _, _ = self.ledgered(check_receipt("supplied-epoch-binder-check"))
        iss = wi.derive_issue_from_check_receipt(objs, ref, observed_base=self.OBS)
        self.assertEqual(iss["surface"], {"kind": "doc", "path": "data/sv-work-items/required-checks.json"})
        self.assertEqual(iss["disposition"]["failure_code"], "CHECK_COMMAND_UNDECLARED")

    def assert_code(self, objs, ref, code):
        out = refusal(wi.derive_issue_from_check_receipt, objs, ref, observed_base=self.OBS)
        self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                         ("FAIL_CLOSED", code, "CHECK_DERIVED_ISSUES_ARE_DERIVED_FROM_THE_LEDGERED_FAILING_RECEIPT"), ref)
        self.assertTrue(six(out))

    def test_not_ledgered(self):
        r = check_receipt("schema-validate", code="CHECK_SKIPPED_OR_UNOBSERVED")
        objs, ref, org, repo = self.ledgered(r)
        okey = LEDGER_COMMIT + ":" + lf.ledger_store.receipt_key(org["receipt_sha256"])
        self.assert_code(self.ledgered(r, retain_repo=False)[0], ref, "SOURCE_RECEIPT_NOT_LEDGERED")        # repo receipt missing
        self.assert_code({}, ref, "SOURCE_RECEIPT_NOT_LEDGERED")                                             # nothing appended
        self.assert_code({LEDGER_COMMIT + ":verifier.json": json.dumps(r).encode()}, ref, "SOURCE_RECEIPT_NOT_LEDGERED")
        self.assert_code(objs, ref.replace(ref.rsplit("/", 1)[1], "0" * 64 + ".json"), "SOURCE_RECEIPT_NOT_LEDGERED")
        self.assert_code(objs, "refs/heads/main:receipts/x.json", "SOURCE_RECEIPT_NOT_LEDGERED")
        self.assert_code({**objs, okey: json.dumps({**org, "authority_effect": "TAMPERED"}).encode()}, ref,
                         "SOURCE_RECEIPT_NOT_LEDGERED")                                                      # org seal broken
        rkey = LEDGER_COMMIT + ":" + lf.ledger_store.source_key(repo["receipt_sha256"])
        self.assert_code({**objs, rkey: json.dumps({**repo, "transition_id": "TAMPERED"}).encode()}, ref,
                         "SOURCE_RECEIPT_NOT_LEDGERED")                                                      # repo seal broken

    def test_evidence_not_a_check_receipt(self):
        r = check_receipt("schema-validate", code="CHECK_SKIPPED_OR_UNOBSERVED")
        for ev in ({"note": "something else"}, {k: v for k, v in r.items() if k != "schema"}, {**r, "kind": "other"},
                   {**r, "schema": "stegverse.sv_check_receipt.v0"}, {**r, "extra": 1}, {}):
            objs, ref, _, _ = self.ledgered(ev)
            self.assert_code(objs, ref, "LEDGER_EVIDENCE_NOT_A_CHECK_RECEIPT")
        objs, ref, _, _ = self.ledgered(r, operation="org_writer_append")
        self.assert_code(objs, ref, "LEDGER_EVIDENCE_NOT_A_CHECK_RECEIPT")

    def test_allow_receipt_derives_nothing_and_base_required(self):
        objs, ref, _, _ = self.ledgered(check_receipt("schema-validate", "ALLOW"))
        self.assertEqual(refusal(wi.derive_issue_from_check_receipt, objs, ref, observed_base=self.OBS)["failure_code"],
                         "CHECK_RECEIPT_NOT_FAILING")
        objs, ref, _, _ = self.ledgered(check_receipt("schema-validate", code="CHECK_SKIPPED_OR_UNOBSERVED"))
        self.assertEqual(refusal(wi.derive_issue_from_check_receipt, objs, ref)["failure_code"], "ISSUE_OBSERVED_BASE_UNSUPPLIED")
        objs, ref, _, _ = self.ledgered(check_receipt("epoch-binder"))
        self.assertEqual(refusal(wi.derive_issue_from_check_receipt, objs, ref, observed_base=self.OBS)["failure_code"], "CHECK_ID_UNDECLARED")

    def test_invariants_recorded(self):
        inv = json.loads((ROOT / "data/sv-work-items/invariants.json").read_text())
        ids = {i["invariant_id"]: i for i in inv["invariants"]}
        nat, adm = ids["NATIVE_RECORD_HB_EPOCH_IS_BASE_LEDGER_HEAD_EPOCH"], ids["ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH"]
        self.assertNotIn("PROVISIONAL", nat["status"])
        self.assertEqual(nat["application_of"], "ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH")
        self.assertEqual(adm["native_record_application"], "NATIVE_RECORD_HB_EPOCH_IS_BASE_LEDGER_HEAD_EPOCH")
        self.assertEqual(adm["status"], "DECIDED_BY_INVARIANT (JD-P4-3, partial)")
        for i in (nat, adm):
            self.assertEqual((i["mismatch"]["disposition"], i["mismatch"]["failure_code"]), ("DENY", "HB_EPOCH_MISMATCH"))
        self.assertEqual(adm["unobserved"]["failure_code"], "HB_EPOCH_SOURCE_UNOBSERVED")
        self.assertTrue(six(adm["unobserved"]))
        self.assertNotIn("HB_EPOCH_NOT_BASE_LEDGER_EPOCH", json.dumps(inv))
        self.assertIn("$.hb_reference.epoch", ids["NATIVE_RECORD_HB_EPOCH_IS_BASE_LEDGER_HEAD_EPOCH"]["statement"])
        self.assertIn("repo_receipt_sha256", ids["CHECK_DERIVED_ISSUES_ARE_DERIVED_FROM_THE_LEDGERED_FAILING_RECEIPT"]["ledger_object_shape"])
        doc = (ROOT / "docs/NWI_S0_NATIVE_WORK_ITEMS_MIRROR_HANDOFF.md").read_text()
        for i in ids:
            self.assertIn(i, doc)


if __name__ == "__main__":
    unittest.main()
