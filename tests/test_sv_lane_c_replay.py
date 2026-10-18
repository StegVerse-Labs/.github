"""Lane C (TVC#519 head 28699422) replay round 2: pinned row blob, replay rebinding, fixture sign-off receipts,
DENY/FAIL_CLOSED check split, and the validation-receipt -> ledger-receipt digest binding."""
from __future__ import annotations

import json
import subprocess
import unittest

from tests import test_sv_native_work_items as base
from tests import test_sv_record_modes as rm

wi, fx, ss, mg, al = base.wi, base.fx, base.ss, rm.mg, base.al
ROOT, U = base.ROOT, base.wi.UNKNOWN
SCN = "data/admission-scenarios/"
GOAL163 = "StegVerse-org/.github#163"
SIGNOFF_SCHEMA = json.loads((ROOT / "schemas/sv-change-signoff-receipt.v0.1.schema.json").read_text())
CHANGE_SCHEMA = json.loads((ROOT / "schemas/sv-change.v1.schema.json").read_text())


def refusal(fn, *a, **k):
    try:
        out = fn(*a, **k)
    except wi.Refusal as r:
        return r.record
    return out


def six(rec):
    return all(isinstance(rec.get(f), str) and rec[f] for f in wi.SIX_FIELDS) and rec["owning_existing_goal"].startswith(GOAL163)


class PinnedRowBlobTests(unittest.TestCase):
    def test_blob_is_the_committed_row_file_blob(self):
        blob = mg.git_blob((ROOT / fx.REQUIRED_CHECKS_FILE).read_bytes())
        self.assertRegex(blob, r"^[0-9a-f]{40}$")
        self.assertEqual(fx.REQUIRED_CHECKS_BLOB, blob)
        for ch in base.jsonl(SCN + "tvc-replay/sv-changes.jsonl"):
            self.assertEqual(ch["required_checks_ref"]["blob_sha"], blob)
            self.assertEqual(ch["request_digest"], wi.request_digest(ch))

    def test_guard_rejects_placeholders_everywhere(self):
        self.assertEqual(fx.pin_violations(fx.build()), [])
        p = ROOT / SCN / "tvc-replay/sv-changes.jsonl"
        ch = fx.known_good_change(fx.SURFACE_PATH["transition"])
        for bad in ("WORKTREE", "ACBE", "", None, "a" * 39, U):
            rec = dict(ch, required_checks_ref={**ch["required_checks_ref"], "blob_sha": bad})
            self.assertTrue(fx.pin_violations({p: json.dumps(rec) + "\n"}), bad)
        mig = dict(ch, record_mode="MIGRATED_HISTORICAL", required_checks_ref={**ch["required_checks_ref"], "blob_sha": U})
        self.assertEqual(fx.pin_violations({p: json.dumps(mig) + "\n"}), [])
        self.assertTrue(fx.pin_violations({p: json.dumps({"note": "WORKTREE"}) + "\n"}))

    def test_validator_refuses_non_hex_blob_with_six_fields(self):
        ch = fx.known_good_change(fx.SURFACE_PATH["transition"])
        for bad in ("WORKTREE", "acbe8061"):
            rec = base.reseal_change(dict(ch, required_checks_ref={**ch["required_checks_ref"], "blob_sha": bad}))
            out = refusal(wi.validate_change, rec)
            self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                             ("FAIL_CLOSED", "REQUIRED_CHECKS_ROW_NOT_PINNED", "REQUIRED_CHECKS_ROW_RESOLVES"))
            self.assertTrue(six(out))
            self.assertTrue(ss.validate(rec, CHANGE_SCHEMA))

    def test_migrated_placeholder_becomes_unknown_and_is_listed(self):
        for ch in base.jsonl("data/sv-work-items/migration/sv-changes.jsonl"):
            self.assertEqual(ch["required_checks_ref"]["blob_sha"], U)
            self.assertIn("/required_checks_ref/blob_sha", ch["unknown_fields"])
            self.assertEqual(rm.both(ch, CHANGE_SCHEMA, wi.validate_change), ([], "ALLOW"))


class ReplayEvaluationTests(unittest.TestCase):
    CORPUS = {s["scenario_id"]: s for s in base.jsonl(SCN + "corpus.jsonl")}
    CH = {c["change_id"]: c for c in base.jsonl(SCN + "tvc-replay/sv-changes.jsonl")}
    MAP = base.jsonl(SCN + "tvc-replay/replay-map.jsonl")
    SIGN = {r["receipt_sha256"]: r for r in base.jsonl(SCN + "tvc-replay/signoff-receipts.jsonl")}

    def evaluate(self, m, rebind=True):
        mut = m["mutation"] if rebind or m["mutation"] is None else {**m["mutation"], "rebind_request_digest": False}
        ch = fx.apply_replay_mutation(self.CH[m["sv_change_id"]], mut)
        obs = wi.admission_inputs(ch, m["current_base"], [self.SIGN[k] for k in m["signoff_receipts"]])
        out = wi.admit(obs, fixture_mode=True)
        return out["disposition"], out.get("failure_code")

    def test_every_scenario_evaluates_to_its_expected_code(self):
        self.assertEqual(len(self.MAP), len(self.CORPUS))
        for m in self.MAP:
            sc = self.CORPUS[m["scenario_id"]]
            self.assertEqual(self.evaluate(m), (sc["expected_disposition"], sc["expected_failure_code"]), m["scenario_id"])

    def test_rebind_flag_is_set_unless_the_target_is_the_request_digest(self):
        for m in self.MAP:
            mut = m["mutation"]
            if mut is None:
                continue
            if mut["applies_to"] == "SV_CHANGE":
                self.assertEqual(mut["rebind_request_digest"], mut["pointer"] != "/request_digest", m["scenario_id"])
                self.assertIn("value", mut)
                if mut["axis"] != "validation_receipts[required_check_ids[0]]":  # a drop needs no value
                    self.assertIsNotNone(mut["value"], m["scenario_id"])
            else:
                self.assertFalse(mut["rebind_request_digest"])

    def test_foreign_writer_needs_the_rebind(self):
        m = next(m for m in self.MAP if m["scenario_id"].startswith("ASC-BRANCH_WRITER_IS_BRANCH_OWNER@transition/writer_sessions"))
        sc = self.CORPUS[m["scenario_id"]]
        self.assertEqual(sc["expected_failure_code"], "BRANCH_HAS_FOREIGN_WRITER")
        self.assertEqual(self.evaluate(m), (sc["expected_disposition"], "BRANCH_HAS_FOREIGN_WRITER"))
        self.assertEqual(self.evaluate(m, rebind=False)[1], "REQUEST_DIGEST_MISMATCH")

    def test_fixture_receipts_never_count_on_the_real_path(self):
        for m in self.MAP:
            if m["mutation"] is None:
                obs = self.CORPUS[m["scenario_id"]]["observed_inputs"]
                self.assertNotEqual(wi.admit(obs)["disposition"], "ALLOW", m["scenario_id"])


class FixtureSignoffReceiptTests(unittest.TestCase):
    RECEIPTS = base.jsonl(SCN + "tvc-replay/signoff-receipts.jsonl")

    def test_receipts_valid_sealed_and_flagged(self):
        self.assertTrue(self.RECEIPTS)
        self.assertIn("ledger-component-owner", {r["role"] for r in self.RECEIPTS})
        for r in self.RECEIPTS:
            self.assertEqual(ss.validate(r, SIGNOFF_SCHEMA), [])
            self.assertEqual(r["receipt_sha256"], wi.sha({k: v for k, v in r.items() if k != "receipt_sha256"}))
            self.assertIs(r["fixture_only"], True)
            self.assertEqual(sorted(r["unobserved_fields"]), ["disposition", "session"])

    def test_ledger_writer_controls_resolve_only_in_fixture_mode(self):
        kg = fx.known_good(fx.SURFACE_PATH["ledger_writer"])
        self.assertEqual(wi.admit(kg, fixture_mode=True)["disposition"], "ALLOW")
        no_rcpt = wi.admit({**kg, "signoff_receipts": []}, fixture_mode=True)
        self.assertEqual((no_rcpt["failure_code"], no_rcpt["failed_predicate"]), ("SIGNOFF_RECEIPT_ABSENT", "REQUIRED_SIGNOFF_RECORDED"))
        so, r = kg["signoffs"][0], kg["signoff_receipts"][0]
        d = kg["head_change_digest"]
        self.assertTrue(wi.signoff_resolves(so, [r], d, fixture_mode=True))
        self.assertFalse(wi.signoff_resolves(so, [r], d))  # fixture_only never counts outside fixtures
        real = wi.seal({k: v for k, v in r.items() if k not in ("receipt_sha256", "fixture_only", "unobserved_fields")}, "receipt_sha256")
        self.assertTrue(wi.signoff_resolves(dict(so, receipt_ref=real["receipt_sha256"]), [real], d))
        tampered = dict(r, session="someone-else")
        self.assertFalse(wi.signoff_resolves(so, [tampered], d, fixture_mode=True))
        self.assertFalse(wi.signoff_resolves(so, [r], "sha256:" + "0" * 64, fixture_mode=True))
        self.assertFalse(wi.signoff_resolves(so, [wi.seal(dict({k: v for k, v in r.items() if k != "receipt_sha256"},
                                                                disposition="DENY"), "receipt_sha256")], d, fixture_mode=True))

    def test_positive_controls_that_name_the_role_are_backed(self):
        sign = {r["receipt_sha256"] for r in self.RECEIPTS}
        for ch in base.jsonl(SCN + "tvc-replay/sv-changes.jsonl"):
            for so in ch["signoffs"]:
                self.assertIn(so["receipt_ref"], sign)
                self.assertNotIn("fixture:signoff:", so["receipt_ref"])


class CheckDispositionSplitTests(unittest.TestCase):
    def obs(self, disposition):
        ch = fx.known_good_change(fx.SURFACE_PATH["transition"])
        ch["validation_receipts"][0] = fx.ledger_receipt(ch["validation_receipts"][0]["check_id"], ch["head"]["change_digest"], disposition)
        return wi.admission_inputs(base.reseal_change(ch), fx.LABS_BASE)

    def test_deny_and_fail_closed_codes(self):
        d = wi.admit(self.obs("DENY"), fixture_mode=True)
        self.assertEqual((d["disposition"], d["failure_code"], d["failed_predicate"]), ("DENY", "REQUIRED_CHECK_DENIED", "CHECK_PASSES"))
        f = wi.admit(self.obs("FAIL_CLOSED"), fixture_mode=True)
        self.assertEqual((f["disposition"], f["failure_code"], f["failed_predicate"]),
                         ("FAIL_CLOSED", "CHECK_SKIPPED_OR_UNOBSERVED", "CHECK_RECEIPT_DISPOSITION_IS_ALLOW"))
        self.assertTrue(six(d) and six(f))

    def test_bindings_follow_the_split(self):
        self.assertEqual(al.PREDICATE_BINDINGS["CHECK_PASSES"][0], "REQUIRED_CHECK_DENIED")
        self.assertEqual(al.PREDICATE_BINDINGS["CHECK_RECEIPT_DISPOSITION_IS_ALLOW"][0], "CHECK_SKIPPED_OR_UNOBSERVED")

    def test_old_code_is_gone(self):
        old = "CHECK_NOT" + "_PASSING"
        hits = subprocess.run(["git", "grep", "-l", old], cwd=ROOT, capture_output=True, text=True).stdout.split()
        self.assertEqual(hits, [])


class LedgerReceiptBindingTests(unittest.TestCase):
    COMMIT = "c" * 40

    def stored(self):
        body = {"check_id": "unit-tests", "disposition": "ALLOW", "change_digest": "sha256:" + "a" * 64}
        rec = wi.seal(body, "receipt_sha256")
        path = "receipts/%s.json" % rec["receipt_sha256"].split(":", 1)[1]
        raw = json.dumps(rec, indent=2).encode()  # stored bytes need not be canonical; the digest is over canon(object)
        return rec, path, raw

    def test_allow_mismatch_unresolved(self):
        rec, path, raw = self.stored()
        ref = "refs/stegverse/organization-ledger@%s:%s" % (self.COMMIT, path)
        objs = {self.COMMIT + ":" + path: raw}
        digest = "sha256:" + wi.hashlib.sha256(wi.canon(rec)).hexdigest()
        self.assertEqual(wi.ledger_receipt_digest(raw), digest)
        ok = wi.verify_ledger_receipt_binding({"ref": ref, "digest": digest}, objs)
        self.assertEqual((ok["disposition"], ok["digest"]), ("ALLOW", digest))
        mis = refusal(wi.verify_ledger_receipt_binding, {"ref": ref, "digest": "sha256:" + "0" * 64}, objs)
        self.assertEqual((mis["disposition"], mis["failure_code"], mis["failed_predicate"]),
                         ("FAIL_CLOSED", "LEDGER_RECEIPT_DIGEST_MISMATCH", "VALIDATION_RECEIPT_DIGEST_BINDS_LEDGER_RECEIPT"))
        self.assertTrue(six(mis))
        other = "receipts/%s.json" % ("e" * 64)
        cases = [({"ref": "docs/evidence.md", "digest": digest}, objs),
                 ({"ref": wi.LEDGER_REF + "#fixture:unit-tests", "digest": digest}, objs),
                 ({"ref": ref.replace(self.COMMIT, "d" * 40), "digest": digest}, objs),
                 ({"ref": ref, "digest": digest}, {self.COMMIT + ":" + path: b"\xff not json"}),
                 ({"ref": ref, "digest": digest}, {self.COMMIT + ":" + path: b"[1,2]"}),
                 ({"ref": "refs/stegverse/organization-ledger@%s:%s" % (self.COMMIT, other), "digest": digest},
                  {self.COMMIT + ":" + other: raw}),
                 ({"digest": digest}, objs)]
        for receipt, store in cases:
            out = refusal(wi.verify_ledger_receipt_binding, receipt, store)
            self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                             ("FAIL_CLOSED", "LEDGER_RECEIPT_UNRESOLVED", "VALIDATION_RECEIPT_REF_RESOLVES_ON_ORGANIZATION_LEDGER"), receipt)
            self.assertTrue(six(out))

    def test_addressing_matches_ledger_store(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("ledger_store_t", ROOT / "resident-runtime/ledger_store.py")
        ls = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ls)
        rec, path, _ = self.stored()
        self.assertEqual(ls.receipt_key(rec["receipt_sha256"]), path)


class HarvestedWriterEvidenceLostTests(unittest.TestCase):
    CID = "ASC-BRANCH_WRITER_IS_BRANCH_OWNER@transition"
    SID = CID + "/harvested/WRITER_EVIDENCE_LOST_BY_SNAPSHOT_RESTORE@StegVerse-org/.github#192@f108ed0a"
    CORPUS = base.jsonl(SCN + "corpus.jsonl")
    CLASSES = base.jsonl(SCN + "classes.jsonl")

    def test_maps_onto_existing_class_as_alias_not_duplicate(self):
        latest = al.latest_classes(self.CLASSES)
        self.assertEqual(len(latest), 10)
        self.assertNotIn("ASC-WRITER_EVIDENCE_LOST_BY_SNAPSHOT_RESTORE@transition", latest)
        c = latest[self.CID]
        self.assertEqual((c["class_version"], c["predicate"]), (2, "BRANCH_WRITER_IS_BRANCH_OWNER"))
        self.assertEqual(c["supersedes"], next(x for x in self.CLASSES if x["class_id"] == self.CID and x["class_version"] == 1)["class_sha256"])
        self.assertEqual(c["provenance"]["class_aliases"], ["WRITER_EVIDENCE_LOST_BY_SNAPSHOT_RESTORE"])
        self.assertEqual(al.CLASS_ALIASES["WRITER_EVIDENCE_LOST_BY_SNAPSHOT_RESTORE"], self.CID)
        self.assertEqual(c["provenance"]["harvest_receipt_ref"], fx.HARVEST_LOCATOR)
        self.assertEqual(c["provenance"]["unobserved_fields"], ["harvest_receipt_ref"])

    def test_harvested_scenario_and_flags(self):
        sc = next(s for s in self.CORPUS if s["scenario_id"] == self.SID)
        self.assertEqual((sc["origin"], sc["expected_disposition"], sc["expected_failure_code"]),
                         ("HARVESTED", "FAIL_CLOSED", "BRANCH_WRITER_UNOBSERVED"))
        src = sc["source"]
        self.assertEqual(src["source_receipt_ref"], "orchestrator:2026-10-18T14:31Z:org#192@f108ed0a")
        self.assertIn("source_receipt_ref", src["unobserved_fields"])
        self.assertIsNone(src["receipt_sha256"])  # no ledger receipt is held for the report
        self.assertEqual(src["observed_case"]["writer_session"], {"session": None, "evidence_class": U})
        self.assertIs(src["observed_case"]["reflog_reconstructed"], False)
        for fixture_mode in (False, True):
            out = wi.admit(sc["observed_inputs"], fixture_mode=fixture_mode)
            self.assertNotEqual(out["disposition"], "ALLOW")
        out = wi.admit(sc["observed_inputs"], fixture_mode=True)
        self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                         ("FAIL_CLOSED", "BRANCH_WRITER_UNOBSERVED", "BRANCH_WRITER_IS_BRANCH_OWNER"))
        h = fx.HARVESTED[0]
        self.assertTrue(h["required_evidence_or_repair"].startswith("a durable push-time writer receipt (sv-push-receipt"))
        self.assertEqual(h["owning_existing_goal"], GOAL163)

    def test_appended_through_the_gate(self):
        classes, scenarios, receipts = fx.corpus()
        self.assertEqual(receipts[-1]["class_id"], self.CID)
        self.assertEqual(receipts[-1]["disposition"], "ALLOW")
        self.assertEqual([s["scenario_id"] for s in scenarios], [s["scenario_id"] for s in self.CORPUS])
        # the gate refuses the harvest when the harvested scenario expects the wrong code
        pre_c, pre_s = classes[:-1], [s for s in scenarios if s["scenario_class"] != self.CID or "content[*]" not in s["scenario_id"]]
        bad = [wi.seal({**{k: v for k, v in s.items() if k != "scenario_sha256"}, "expected_failure_code": "BRANCH_HAS_FOREIGN_WRITER"},
                       "scenario_sha256") for s in scenarios if s["scenario_class"] == self.CID and "content[*]" in s["scenario_id"]]
        out = al.corpus_append(pre_c, pre_s, classes[-1], bad, hb_epoch=fx.FIXTURE_HB_EPOCH)
        self.assertEqual(out["failure_code"], "CLASS_NEVER_FIRES")

    def unknown_writer_change(self, session):
        """Tree verified (head digest recomputed from the content), base current, writer evidence UNKNOWN."""
        ch = fx.known_good_change("resident-runtime/admission_predicate.py")
        ch["content"] = [{**c, "writer_session": {"session": session, "evidence_class": U}} for c in ch["content"]]
        ch = base.reseal_change(ch)
        self.assertEqual(ch["head"]["change_digest"], wi.change_digest(ch))
        return ch

    def test_negative_tree_verified_refetch_is_not_writer_evidence(self):
        for session in (None, fx.SESSION):  # lost, or filled from the commit author / range base
            ch = self.unknown_writer_change(session)
            obs = wi.admission_inputs(ch, ch["base_ref"], fx.signoff_receipts_for(ch))
            self.assertEqual(obs["current_base"], obs["base_ref"])  # the range base is exactly current
            for fixture_mode in (False, True):
                out = wi.admit(obs, fixture_mode=fixture_mode)
                self.assertNotEqual(out["disposition"], "ALLOW", session)
            out = wi.admit(obs, fixture_mode=True)
            self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "BRANCH_WRITER_UNOBSERVED"), session)
            self.assertTrue(six(out))

    def test_negative_range_base_writer_claim_never_overrides(self):
        ch = self.unknown_writer_change(None)
        obs = wi.admission_inputs(ch, ch["base_ref"], fx.signoff_receipts_for(ch))
        forged = {**obs, "writer_sessions": [fx.SESSION], "declared_session_matches_writers": True}
        out = wi.admit(forged, fixture_mode=True)
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "BRANCH_WRITER_UNOBSERVED"))
        prop = wi.transition("SV_CHANGE_PROPOSE", ch, hb_epoch=base.EPOCH, context={"issues": []})
        self.assertNotEqual(prop["disposition"], "ALLOW")


class CheckCommandRowTests(unittest.TestCase):
    ROW = json.loads((ROOT / "data/sv-work-items/required-checks.json").read_text())
    HEAD_PATHS = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()

    def test_every_check_declares_a_command_or_fails_closed(self):
        for cid, c in self.ROW["checks"].items():
            self.assertIn("offline_command", c)
            if c["offline_command"] == U:
                st = c["command_status"]
                self.assertEqual((st["disposition"], st["failure_code"]), ("FAIL_CLOSED", "CHECK_COMMAND_UNDECLARED"))
                self.assertTrue(six(st))
                out = refusal(wi.check_command, cid, self.HEAD_PATHS)
                self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "CHECK_COMMAND_UNDECLARED"))
                self.assertTrue(six(out))
            else:
                self.assertIsInstance(c["offline_command"], list)
                self.assertEqual(c["offline_command"][0], "python3")
                self.assertIn("exit_code", c["expected"])
                for p in c["command_paths"]:
                    self.assertTrue((ROOT / p).is_file(), p)
                self.assertEqual(wi.check_command(cid, self.HEAD_PATHS)["disposition"], "ALLOW")
        self.assertEqual(self.ROW["checks"]["supplied-epoch-binder-check"]["offline_command"], U)

    def test_command_absent_at_older_heads(self):
        for pr, head in (("#3225", "e6ba9601933c1c9d58f6b704c2a119544d21cb4d"), ("#3226", "f82c0324aa4b6ac74adc44a3541ac98b33826447")):
            ls = subprocess.run(["git", "ls-tree", "-r", "--name-only", head], cwd=ROOT, capture_output=True, text=True)
            if ls.returncode != 0:
                self.skipTest("head %s not in the local clone" % head)
            paths = ls.stdout.split()
            for cid in ("schema-validate", "unit-tests", "mutation-negative-suite"):
                out = refusal(wi.check_command, cid, paths)
                self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                                 ("FAIL_CLOSED", "CHECK_COMMAND_ABSENT_AT_HEAD", "CHECK_COMMAND_PATHS_PRESENT_AT_HEAD"), (pr, cid))
                self.assertTrue(six(out) and out["absent"])
        self.assertEqual(refusal(wi.check_command, "not-a-check", self.HEAD_PATHS)["failure_code"], "CHECK_ID_UNDECLARED")

    def test_outcome_matching(self):
        exp = self.ROW["checks"]["schema-validate"]["expected"]
        self.assertTrue(wi.check_outcome_matches(exp, 0, '{"disposition": "ALLOW", "stale": []}\n', ""))
        self.assertFalse(wi.check_outcome_matches(exp, 0, '{"disposition": "FAIL_CLOSED", "stale": ["x"]}', ""))
        self.assertFalse(wi.check_outcome_matches(exp, 1, '{"disposition": "ALLOW", "stale": []}', ""))
        self.assertFalse(wi.check_outcome_matches(exp, 0, "not json", ""))
        ut = self.ROW["checks"]["unit-tests"]["expected"]
        self.assertTrue(wi.check_outcome_matches(ut, 0, "", "....\nRan 4 tests in 0.1s\n\nOK\n"))
        self.assertFalse(wi.check_outcome_matches(ut, 0, "", "Ran 4 tests\n\nFAILED (failures=1)\n"))

    def test_no_receipt_for_an_undeclared_command(self):
        ch = fx.known_good_change(fx.SURFACE_PATH["ledger_writer"])
        r = {"schema": wi.CHECK_RECEIPT_SCHEMA, "check_id": "supplied-epoch-binder-check", "disposition": "ALLOW",
             "change_digest": ch["head"]["change_digest"], "head_sha": "b" * 40, "hb_epoch": str(base.EPOCH), "verifier_ref": "fixture"}
        out = refusal(wi.validate_check_receipt, r, ch)
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "CHECK_COMMAND_UNDECLARED"))


if __name__ == "__main__":
    unittest.main()
