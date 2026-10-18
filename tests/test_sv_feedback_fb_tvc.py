"""NWI-S0 follow-ups: Lane D FB-1..FB-3 (#3265 @d1a00300) and Lane C TVC#519 alignment, plus the check-receipt invariant."""
from __future__ import annotations

import copy
import json
import unittest

from tests import test_sv_native_work_items as base
from tests import test_sv_record_modes as rm

wi, fx, ss, mg = base.wi, base.fx, base.ss, rm.mg
al = base.al
U, ROOT, code = wi.UNKNOWN, base.ROOT, base.code
SCHEMAS = {n: json.loads((ROOT / ("schemas/%s.schema.json" % n)).read_text())
           for n in ("sv-issue.v1", "sv-change.v1", "sv-check-receipt.v1", "sv-surface-aliases.v1")}
SIX = wi.SIX_FIELDS
GOAL163 = "StegVerse-org/.github#163"


def fx_admit(obs, **kw):
    """Fixture context: fixture validation refs and fixture_only sign-off receipts count (never on the real path)."""
    return wi.admit(obs, fixture_mode=True, **kw)


def refusal(fn, *a, **k):
    try:
        fn(*a, **k)
    except wi.Refusal as r:
        return r.record
    raise AssertionError("no refusal")


def six_complete(rec):
    return all(isinstance(rec.get(f), str) and rec[f].strip() for f in SIX)


class FB1AliasTests(unittest.TestCase):
    def setUp(self):
        self.table = mg.load_aliases()

    def test_table_conforms_to_minimal_schema_and_is_pinned(self):
        self.assertEqual(ss.validate(self.table, SCHEMAS["sv-surface-aliases.v1"]), [])
        self.assertEqual(mg.git_blob(mg.SURFACE_ALIASES_PATH.read_bytes()), mg.SURFACE_ALIASES_BLOB)

    def test_new_aliases_resolve_to_verified_base_objects(self):
        by = {e["alias"]: e for e in self.table["lane_aliases"]}
        for alias, path, blob in (("SPPA", "scripts/authorize_site_production_promotion.py", "0538784f657f5e58cf1f7c975710e64ead3a4e00"),
                                  ("that script", "scripts/project_worker_claim_into_canonical_task.py", "9573c5bb963d7c19f64a08173f7397f427ba32dd")):
            e = by[alias]
            self.assertEqual((e["path"], e["verified"]["object_sha"], e["verified"]["commit"]),
                             (path, blob, "978b8880d238dc3e3a8b690c0675d8bb0e9d6985"))
            self.assertTrue((ROOT / path).is_file(), path)  # also present on this branch
            self.assertEqual(mg.alias_disposition(alias)["disposition"], "ALLOW")
            self.assertEqual(mg.alias_disposition(alias)["surface"], {"kind": "transition", "path": path})

    def test_pr_head_only_workflows_never_allow(self):
        un = {e["alias"]: e for e in self.table["unresolved_declarations"]}
        self.assertEqual(set(un), {"#3235 verify workflow", "allocator workflow"})
        heads = {"#3235 verify workflow": "5052569970dc05f3932ad640f9ea296b555d038a", "allocator workflow": "e5ba67b26403bef2207638161fcc9cc28e7d8036"}
        for alias, e in un.items():
            self.assertEqual(e["path"], U)
            self.assertFalse(e["evidence"]["on_base"])
            self.assertEqual(e["evidence"]["commit"], heads[alias])
            self.assertFalse((ROOT / e["candidate_path"]).exists(), e["candidate_path"])  # not on our base/branch
            d = mg.alias_disposition("retry " + alias)
            self.assertEqual((d["disposition"], d["failure_code"], d["owning_existing_goal"]),
                             ("FAIL_CLOSED", "SURFACE_ALIAS_TARGET_NOT_ON_BASE", GOAL163))
            self.assertTrue(six_complete(d))
            self.assertEqual(mg.resolve_surface("retry " + alias), U)
        bad = copy.deepcopy(self.table)
        bad["unresolved_declarations"][0]["disposition"] = "ALLOW"
        self.assertTrue(ss.validate(bad, SCHEMAS["sv-surface-aliases.v1"]))
        bad = copy.deepcopy(self.table)
        bad["unresolved_declarations"][0]["path"] = bad["unresolved_declarations"][0]["candidate_path"]
        self.assertTrue(ss.validate(bad, SCHEMAS["sv-surface-aliases.v1"]))

    def test_undeclared_alias_fails_closed(self):
        d = mg.alias_disposition("NOT-AN-ALIAS")
        self.assertEqual((d["disposition"], d["failure_code"]), ("FAIL_CLOSED", "SURFACE_ALIAS_UNRESOLVED"))
        self.assertTrue(six_complete(d))
        self.assertEqual(mg.alias_disposition("patches/D14-*.json-patch.json")["disposition"], "FAIL_CLOSED")


class FB2ClassColumnTests(unittest.TestCase):
    def test_fallback_runs_only_on_unknown_and_is_flagged(self):
        s, f = mg.derive_surface_with_class_column("Labs#3211 new head", "**B** apply_admitted_canonical_work_projection.py")
        self.assertEqual(s, {"kind": "transition", "path": "scripts/apply_admitted_canonical_work_projection.py"})
        self.assertEqual(f, ["SURFACE_DERIVED_FROM_CLASS_COLUMN"])
        s, f = mg.derive_surface_with_class_column("CONS::consume", "**B** apply_admitted_canonical_work_projection.py")
        self.assertEqual((s["path"], f), ("scripts/consume_org_claim_allocator_request.py", []))  # entrypoint wins
        self.assertEqual(mg.derive_surface_with_class_column("Labs#3211", "**C** no path"), (U, []))
        self.assertEqual(mg.derive_surface_with_class_column("Labs#3211", None), (U, []))

    def test_flagged_record_validates_and_flag_is_not_identity(self):
        s, f = mg.derive_surface_with_class_column("Labs#3211 new head", "apply_admitted_canonical_work_projection.py")
        flagged = rm.migrated_issue(surface=s, migration_flags=f)
        plain = rm.migrated_issue(surface=s)
        self.assertEqual(flagged["migration_flags"], ["SURFACE_DERIVED_FROM_CLASS_COLUMN"])
        self.assertEqual(rm.both(flagged, SCHEMAS["sv-issue.v1"], wi.validate_issue), ([], "ALLOW"))
        self.assertEqual(flagged["issue_id"], plain["issue_id"])
        self.assertNotEqual(flagged["issue_sha256"], plain["issue_sha256"])

    def test_flag_misuse_refused(self):
        errs, c = rm.both(rm.migrated_issue(surface=U, migration_flags=["SURFACE_DERIVED_FROM_CLASS_COLUMN"]), SCHEMAS["sv-issue.v1"], wi.validate_issue)
        self.assertEqual(c, "MIGRATION_FLAG_MISMATCH")
        errs, c = rm.both(rm.migrated_issue(migration_flags=["OBSERVED"]), SCHEMAS["sv-issue.v1"], wi.validate_issue)
        self.assertTrue(errs); self.assertEqual(c, "MIGRATION_FLAG_MISMATCH")
        native = base.nativize_issue(base.ISSUES[0]); native["migration_flags"] = ["SURFACE_DERIVED_FROM_CLASS_COLUMN"]
        self.assertEqual(code(wi.validate_issue, base.reseal_issue(native)), "MIGRATION_FIELDS_ON_NATIVE_RECORD")

    def test_lane_d_builder_no_longer_needs_its_own_fallback(self):
        src = (ROOT / "resident-runtime/sv_migration.py").read_text()
        self.assertIn("def derive_surface_with_class_column", src)


class FB3CollisionTests(unittest.TestCase):
    def loc(self, l):
        return {**base.ISSUES[0]["source_receipt"], "evidence_locator": l}

    def test_known_goal_identity_unchanged(self):
        for r in base.ISSUES:
            self.assertNotIn("source_locator", wi.issue_identity_inputs(r))
            self.assertEqual(wi.issue_identity(r), r["issue_id"])
        with_loc = rm.migrated_issue(source_receipt=self.loc("L5"))
        self.assertEqual(with_loc["issue_id"], rm.migrated_issue()["issue_id"])  # a locator never moves a known-goal id

    def test_set_validator_refuses_duplicates(self):
        a = rm.migrated_issue()
        r = refusal(wi.validate_issue_set, [a, copy.deepcopy(a)])
        self.assertEqual((r["disposition"], r["failure_code"], r["failed_predicate"]), ("FAIL_CLOSED", "SV_ISSUE_ID_COLLISION", "ISSUE_ID_IS_UNIQUE_IN_RECORD_SET"))
        self.assertTrue(six_complete(r)); self.assertIn("#163", r["owning_existing_goal"])
        self.assertEqual(r["collisions"], {a["issue_id"]: [0, 1]})
        self.assertEqual(len(wi.validate_issue_set(base.ISSUES)), len(base.ISSUES))

    def test_unknown_goal_requires_locator(self):
        r = refusal(wi.validate_issue, rm.migrated_issue(owning_goal=U))
        self.assertEqual((r["disposition"], r["failure_code"]), ("FAIL_CLOSED", "SV_ISSUE_UNKNOWN_GOAL_UNLOCATED"))
        self.assertTrue(ss.validate(rm.migrated_issue(owning_goal=U), SCHEMAS["sv-issue.v1"]))

    def test_old_collision_is_removed_deterministically(self):
        # the pre-FB-3 collision: same file, predicate, surface, goal UNKNOWN, different rows
        x = rm.migrated_issue(owning_goal=U, source_receipt=self.loc("L586"))
        y = rm.migrated_issue(owning_goal=U, source_receipt=self.loc("L898"),
                              disposition={**base.ISSUES[0]["disposition"], "next_attempt": "a different row"})
        self.assertNotEqual(x["issue_id"], y["issue_id"])
        self.assertEqual(rm.migrated_issue(owning_goal=U, source_receipt=self.loc("L586"))["issue_id"], x["issue_id"])  # stable
        self.assertEqual(len(wi.validate_issue_set([x, y])), 2)
        merged, _ = mg.merge_issues([x, y])
        self.assertEqual(len(merged), 2)

    def test_merge_never_folds_two_unknown_goal_bodies(self):
        x = rm.migrated_issue(owning_goal=U, source_receipt=self.loc("L1"))
        y = dict(x, disposition={**x["disposition"], "next_attempt": "different body"})
        r = refusal(mg.merge_issues, [x, y])
        self.assertEqual(r["failure_code"], "SV_ISSUE_ID_COLLISION")
        merged, _ = mg.merge_issues([rm.migrated_issue(), rm.migrated_issue(disposition={**base.ISSUES[0]["disposition"], "next_attempt": "reworded"})])
        self.assertEqual(len(merged), 1)  # known-goal restatements still merge
        self.assertEqual(len(merged[0]["restatements"]), 1)


class TVCSchemaTests(unittest.TestCase):
    def test_deleted_required_and_closed_shapes(self):
        ch = rm.sealed()
        self.assertEqual(rm.both(ch, SCHEMAS["sv-change.v1"], wi.validate_change), ([], "ALLOW"))
        missing = copy.deepcopy(ch); del missing["content"][0]["deleted"]
        errs, c = rm.both(missing, SCHEMAS["sv-change.v1"], wi.validate_change)
        self.assertIn(("/content/0/deleted", "required"), errs); self.assertEqual(c, "SV_CHANGE_CONTENT_ENTRY_INVALID")
        extra = copy.deepcopy(ch); extra["content"][0]["note"] = "x"
        errs, c = rm.both(extra, SCHEMAS["sv-change.v1"], wi.validate_change)
        self.assertTrue(errs); self.assertEqual(c, "SV_CHANGE_CONTENT_ENTRY_INVALID")
        head = copy.deepcopy(ch); head["head"]["extra"] = "x"
        errs, c = rm.both(head, SCHEMAS["sv-change.v1"], wi.validate_change)
        self.assertTrue(errs); self.assertEqual(c, "SV_CHANGE_HEAD_INVALID")

    def test_touched_paths_equal_content_path_set(self):
        ch = rm.sealed()
        for tp in ([], ch["touched_paths"] * 2, ch["touched_paths"] + ["other.py"]):
            bad = dict(ch, touched_paths=tp); bad["request_digest"] = wi.request_digest(bad)
            self.assertEqual(code(wi.validate_change, bad), "SV_CHANGE_TOUCHED_PATHS_MISMATCH", tp)

    def test_fixtures_valid_under_tightened_schema(self):
        for ch in base.CHANGES:
            self.assertEqual(rm.both(ch, SCHEMAS["sv-change.v1"], wi.validate_change), ([], "ALLOW"))
            self.assertTrue(all(c["deleted"] is (c["blob_digest"] is None) for c in ch["content"]))

    def test_migration_derives_deleted_from_null_blob(self):
        self.assertFalse(mg.content_entry({"path": "a", "blob_digest": "sha256:" + "1" * 64, "writer_session": None})["deleted"])
        self.assertTrue(mg.content_entry({"path": "a", "blob_digest": None, "writer_session": None})["deleted"])
        self.assertTrue(mg.content_entry({"path": "a", "blob_digest": "x", "deleted": True, "writer_session": None})["deleted"])  # recorded wins


class TVCCodeTests(unittest.TestCase):
    def test_renamed_codes_and_predicate(self):
        self.assertEqual(al.PREDICATE_BINDINGS["RECEIPT_CHANGE_DIGEST_EQUALS_HEAD"][0], "CHECK_SKIPPED_OR_UNOBSERVED")
        self.assertEqual(al.PREDICATE_BINDINGS["REQUIRED_SIGNOFF_RECORDED"][0], "SIGNOFF_RECEIPT_ABSENT")
        self.assertNotIn("CHECK_SKIPPED_OR_UNOBSERVED", al.FAILURE_CODE_TO_PREDICATE)  # ambiguous code: predicate required
        for rel in ("data/admission-scenarios/corpus.jsonl", "data/admission-scenarios/classes.jsonl", "data/admission-scenarios/seed-append-outcomes.jsonl",
                    "data/sv-work-items/lifecycle-transitions.json", "resident-runtime/sv_work_items.py", "resident-runtime/admission_learning.py",
                    "schemas/sv-change.v1.schema.json", "data/admission-scenarios/tvc-replay/replay-map.jsonl"):
            t = (ROOT / rel).read_text()
            for old in ("VALIDATION_NOT_AT_EXACT_HEAD", "SIGNOFF_ABSENT", "VALIDATION_RECEIPT_BINDS_EXACT_HEAD"):
                self.assertNotIn(old, t, rel)

    def test_signoff_code(self):
        kg = fx.known_good(fx.SURFACE_PATH["ledger_writer"])
        out = fx_admit({**kg, "signoffs": []})
        self.assertEqual((out["failure_code"], out["failed_predicate"]), ("SIGNOFF_RECEIPT_ABSENT", "REQUIRED_SIGNOFF_RECORDED"))

    def test_code_only_candidate_with_shared_code_fails_closed(self):
        r = refusal(al.generalize, {"failure_code": "CHECK_SKIPPED_OR_UNOBSERVED"}, surface="transition", origin_scenarios=[], rule_refs=[],
                    declared_by_session=fx.SESSION, harvest_receipt_ref=None, hb_epoch="1024")
        self.assertEqual(r["failure_code"], "PREDICATE_BINDING_UNDECLARED")


def receipt(**over):
    ch = rm.sealed()
    r = {"schema": "stegverse.sv_check_receipt.v1", "check_id": "unit-tests", "disposition": "ALLOW",
         "change_digest": ch["head"]["change_digest"], "head_sha": "c" * 40, "hb_epoch": "1024", "verifier_ref": "SV-LLM/.github#46:run-1"}
    r.update(over)
    return r, ch


class CheckReceiptInvariantTests(unittest.TestCase):
    ROW = wi.REQUIRED_CHECKS

    def test_invariant_recorded_with_minter_and_appender(self):
        inv = self.ROW["check_receipt_invariant"]
        self.assertEqual(inv["invariant_id"], "REQUIRED_CHECK_RECEIPTS_ARE_S1_VERIFIER_OUTPUTS_APPENDED_BY_ORG_WRITER")
        ids = sorted({c for v in self.ROW["surface_kinds"].values() for c in v["checks"]})
        self.assertEqual(sorted(self.ROW["checks"]), ids)
        for e in self.ROW["checks"].values():
            self.assertEqual({k: e[k] for k in ("minter", "appender")},
                             {"minter": "NWI-S1-verifier (SV-LLM/.github#46)", "appender": "org-ledger-writer (Labs#3255)"})
        self.assertIn("REQUIRED_CHECK_RECEIPTS_ARE_S1_VERIFIER_OUTPUTS_APPENDED_BY_ORG_WRITER",
                      (ROOT / "docs/NWI_S0_NATIVE_WORK_ITEMS_MIRROR_HANDOFF.md").read_text())
        # the receipt schema's closed enum: the row's checks plus each stage manifest's exit_gate_check (STAGE_GATE_RECEIPT_DERIVES_NATIVE_ISSUE)
        self.assertEqual(SCHEMAS["sv-check-receipt.v1"]["properties"]["check_id"]["enum"], sorted(ids + list(wi.GATE_CHECKS)))
        self.assertEqual(wi.declared_check_ids(), sorted(ids + list(wi.GATE_CHECKS)))

    def test_real_row_fails_closed_until_appended(self):
        st = wi.row_receipt_status()
        self.assertEqual((st["disposition"], st["failure_code"], st["failed_predicate"]),
                         ("FAIL_CLOSED", "CHECK_RECEIPT_ABSENT_FROM_LEDGER", "REQUIRED_CHECK_HAS_LEDGER_RECEIPT"))
        self.assertEqual(st["required_evidence_or_repair"], "NWI-S1 verifier emits the check id at the exact head and the org writer appends it")
        self.assertEqual(st["owning_existing_goal"], GOAL163)
        self.assertIn("JD-P4-3", st["next_attempt"])
        self.assertTrue(six_complete(st))
        art = [{"check_id": c, "evidence_class": "OBSERVED_ARTIFACT", "ref": "x"} for c in self.ROW["checks"]]
        self.assertEqual(wi.row_receipt_status(art)["disposition"], "FAIL_CLOSED")  # artifacts never count
        led = [{"check_id": c, "evidence_class": "LEDGER_RECEIPT", "ref": wi.LEDGER_REF + "#x"} for c in self.ROW["checks"]]
        self.assertEqual(wi.row_receipt_status(led)["disposition"], "ALLOW")
        self.assertEqual(wi.row_receipt_status(led[1:])["missing_check_ids"], [sorted(self.ROW["checks"])[0]])

    def test_undeclared_check_id_refused_everywhere(self):
        ch = rm.sealed()
        bad = copy.deepcopy(ch); bad["validation_receipts"].append(fx.ledger_receipt("ci-green", ch["head"]["change_digest"]))
        bad["request_digest"] = wi.request_digest(bad)
        errs, c = rm.both(bad, SCHEMAS["sv-change.v1"], wi.validate_change)
        self.assertTrue(errs); self.assertEqual(c, "CHECK_ID_UNDECLARED")
        obs = wi.admission_inputs(ch, ch["base_ref"], resolved_issues=fx.fixture_resolved_issues(ch))
        obs["validation_receipts"].append(fx.ledger_receipt("ci-green", ch["head"]["change_digest"]))
        out = fx_admit(obs)
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "CHECK_ID_UNDECLARED"))
        self.assertTrue(six_complete(out))
        r, _ = receipt(check_id="ci-green")
        self.assertEqual(refusal(wi.validate_check_receipt, r)["failure_code"], "CHECK_ID_UNDECLARED")
        self.assertTrue(ss.validate(r, SCHEMAS["sv-check-receipt.v1"]))

    def test_check_receipt_shape(self):
        r, ch = receipt()
        self.assertEqual(ss.validate(r, SCHEMAS["sv-check-receipt.v1"]), [])
        self.assertEqual(wi.validate_check_receipt(r, ch, "c" * 40)["check_id"], "unit-tests")
        for over, want in (({"hb_epoch": "31"}, "HB_EPOCH"), ({"hb_epoch": "1o24"}, "HB_EPOCH")):
            bad, _ = receipt(**over)
            self.assertTrue(ss.validate(bad, SCHEMAS["sv-check-receipt.v1"]), over)
            self.assertIn(want, refusal(wi.validate_check_receipt, bad)["failure_code"])
        off, ch = receipt(change_digest="sha256:" + "0" * 64)
        rr = refusal(wi.validate_check_receipt, off, ch)
        self.assertEqual((rr["failure_code"], rr["failed_predicate"]), ("CHECK_SKIPPED_OR_UNOBSERVED", "RECEIPT_CHANGE_DIGEST_EQUALS_HEAD"))
        self.assertEqual(refusal(wi.validate_check_receipt, receipt()[0], None, "d" * 40)["failure_code"], "CHECK_SKIPPED_OR_UNOBSERVED")
        deny, _ = receipt(disposition="DENY")
        self.assertTrue(ss.validate(deny, SCHEMAS["sv-check-receipt.v1"]))
        self.assertEqual(refusal(wi.validate_check_receipt, deny)["failure_code"], "SV_CHECK_RECEIPT_SIX_FIELDS_INCOMPLETE")
        full, _ = receipt(disposition="DENY", **{f: "x" for f in SIX})
        self.assertEqual(ss.validate(full, SCHEMAS["sv-check-receipt.v1"]), [])
        self.assertEqual(wi.validate_check_receipt(full)["disposition"], "DENY")
        extra, _ = receipt(ledger_ref="refs/x")
        self.assertTrue(ss.validate(extra, SCHEMAS["sv-check-receipt.v1"]))
        self.assertEqual(refusal(wi.validate_check_receipt, extra)["failure_code"], "SV_CHECK_RECEIPT_INVALID")


class TVCReplayTests(unittest.TestCase):
    CORPUS = base.jsonl("data/admission-scenarios/corpus.jsonl")
    CH = {c["change_id"]: c for c in base.jsonl("data/admission-scenarios/tvc-replay/sv-changes.jsonl")}
    MAP = base.jsonl("data/admission-scenarios/tvc-replay/replay-map.jsonl")

    def test_every_scenario_mapped_to_a_valid_full_change(self):
        self.assertEqual([m["scenario_id"] for m in self.MAP], [s["scenario_id"] for s in self.CORPUS])
        for ch in self.CH.values():
            self.assertEqual(rm.both(ch, SCHEMAS["sv-change.v1"], wi.validate_change), ([], "ALLOW"))
        by = {s["scenario_id"]: s for s in self.CORPUS}
        for m in self.MAP:
            sc = by[m["scenario_id"]]
            self.assertEqual(m["scenario_sha256"], sc["scenario_sha256"])
            ch = self.CH[m["sv_change_id"]]
            self.assertEqual(m["expected_failure_code"], sc["expected_failure_code"])
            if m["mutation"] is None:
                rcpts = {r["receipt_sha256"]: r for r in base.jsonl("data/admission-scenarios/tvc-replay/signoff-receipts.jsonl")}
                self.assertEqual(wi.admission_inputs(ch, m["current_base"], [rcpts[k] for k in m["signoff_receipts"]], m["hb_epoch_readback"],
                                                    m["resolved_issues"]),
                                 sc["observed_inputs"])
                self.assertEqual(fx_admit(sc["observed_inputs"])["disposition"], "ALLOW")
            else:
                self.assertEqual(m["mutation"]["axis"], sc["generated_from"]["axis"])
                self.assertIn(m["mutation"]["applies_to"], ("SV_CHANGE", "REPLAY_INPUT"))
                self.assertEqual(sc["observed_inputs"]["current_base"], m["current_base"])


if __name__ == "__main__":
    unittest.main()
