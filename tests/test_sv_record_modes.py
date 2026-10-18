"""Record modes (NATIVE | MIGRATED_HISTORICAL) and schema fixes SF-1..SF-10 from Lane D's migration fixtures."""
from __future__ import annotations

import copy
import hashlib
import json
import unittest

from tests import test_sv_native_work_items as base

wi, fx, ss = base.wi, base.fx, base.ss
mg = base._load("sv_migration", "resident-runtime/sv_migration.py")
U, EPOCH, SESSION = wi.UNKNOWN, base.EPOCH, base.SESSION
ROOT = base.ROOT
ISSUE_SCHEMA = json.loads((ROOT / "schemas/sv-issue.v1.schema.json").read_text())
CHANGE_SCHEMA = json.loads((ROOT / "schemas/sv-change.v1.schema.json").read_text())
ITEMS_SCHEMA = json.loads((ROOT / "schemas/canonical-task-work-items.v1.schema.json").read_text())
code = base.code


def migrated_issue(**over):
    rec = {k: v for k, v in copy.deepcopy(base.ISSUES[0]).items() if k not in ("issue_id", "issue_sha256")}
    rec.update(over)
    return mg.finish_issue(rec)


def migrated_change(**over):
    rec = copy.deepcopy(base.CHANGES[2])
    rec.update(over)
    return mg.finish_change(rec)


def both(rec, schema, validator):
    """(schema errors, validator code) so each rule is checked by the schema and by the validator."""
    return ss.validate(rec, schema), code(validator, rec)


class RecordModeTests(unittest.TestCase):
    def test_fixtures_are_migrated_and_list_every_unknown(self):
        for r in base.ISSUES + base.CHANGES:
            self.assertEqual(r["record_mode"], "MIGRATED_HISTORICAL")
            self.assertEqual(sorted(r["unknown_fields"]), sorted(wi.sentinel_pointers(r)))
            self.assertIn("/hb_epoch", r["unknown_fields"])

    def test_mode_must_be_declared(self):
        rec = {k: v for k, v in base.ISSUES[0].items() if k != "record_mode"}
        errs, c = both(base.reseal_issue(rec), ISSUE_SCHEMA, wi.validate_issue)
        self.assertIn(("/record_mode", "required"), errs)
        self.assertEqual(c, "RECORD_MODE_INVALID")

    def test_unknown_only_where_listed(self):
        rec = dict(base.ISSUES[0], unknown_fields=[p for p in base.ISSUES[0]["unknown_fields"] if p != "/hb_epoch"])
        self.assertEqual(code(wi.validate_issue, base.reseal_issue(rec)), "UNKNOWN_FIELDS_NOT_DECLARED")
        rec = migrated_issue()
        rec = dict(rec, violated_invariant={**rec["violated_invariant"], "rule_id": U})
        rec["unknown_fields"] = sorted(wi.sentinel_pointers(rec))
        errs, c = both(base.reseal_issue(rec), ISSUE_SCHEMA, wi.validate_issue)
        self.assertEqual(c, "UNKNOWN_FIELD_NOT_PERMITTED")
        self.assertTrue(errs)

    def test_native_rejects_any_unknown_and_any_migration_field(self):
        n = base.nativize_issue(base.ISSUES[0])
        self.assertEqual(both(n, ISSUE_SCHEMA, wi.validate_issue), ([], "ALLOW"))
        for over in ({"hb_epoch": U}, {"resolution_class": U}, {"owning_goal": U}, {"surface": U}):
            errs, c = both(base.nativize_issue(base.ISSUES[0], **over), ISSUE_SCHEMA, wi.validate_issue)
            self.assertEqual(c, "UNKNOWN_IN_NATIVE_RECORD", over)
            self.assertTrue(errs, over)
        withprov = base.reseal_issue(dict(n, migration_provenance=mg.provenance(n["observed_base"])))
        self.assertEqual(code(wi.validate_issue, withprov), "MIGRATION_FIELDS_ON_NATIVE_RECORD")

    def test_migrated_record_is_never_admitted(self):
        ch = dict(base.CHANGES[2], lifecycle_state="FAIL_CLOSED")
        ch = mg.finish_change(ch)
        ctx = {"current_base": ch["base_ref"], "predicate_digest": "sha256:" + "c" * 64, "corpus_head": "sha256:" + "d" * 64,
               "evaluator": lambda obs, **k: {"disposition": "ALLOW", "failed_predicate": None}}
        out = wi.transition("SV_CHANGE_ADMIT", ch, hb_epoch=EPOCH, context=ctx)
        self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                         ("FAIL_CLOSED", "HISTORICAL_RECORD_NOT_ADMISSIBLE", "ADMITTED_RECORDS_ARE_NATIVE"))
        for f in wi.SIX_FIELDS:
            self.assertTrue(out[f], f)
        self.assertEqual(out["record"]["lifecycle_state"], "FAIL_CLOSED")
        self.assertEqual(wi.admit(wi.admission_inputs(ch, ch["base_ref"]))["failure_code"], "HISTORICAL_RECORD_NOT_ADMISSIBLE")

    def test_no_in_place_promotion_to_native(self):
        flipped = dict(base.ISSUES[0], record_mode="NATIVE")
        self.assertEqual(code(wi.validate_issue, flipped), "UNKNOWN_IN_NATIVE_RECORD")
        ch = dict(base.CHANGES[2], record_mode="NATIVE")
        self.assertIn(code(wi.validate_change, ch), ("UNKNOWN_IN_NATIVE_RECORD", "MIGRATION_FIELDS_ON_NATIVE_RECORD"))
        clean = {k: v for k, v in ch.items() if k not in base.MIGRATION_KEYS}
        clean["hb_epoch"] = EPOCH
        self.assertEqual(code(wi.validate_change, clean), "REQUEST_DIGEST_MISMATCH")

    def test_native_only_through_superseding_record(self):
        old = base.ISSUES[0]
        succ = base.nativize_issue(old, supersedes=old["issue_sha256"])
        out = wi.transition("SV_ISSUE_SUPERSEDE", old, hb_epoch=EPOCH, context={"successor": succ})
        self.assertEqual((out["disposition"], out["record"]["lifecycle_state"], out["record"]["superseded_by"]),
                         ("ALLOW", "SUPERSEDED", succ["issue_sha256"]))
        self.assertEqual(wi.transition("SV_ISSUE_SUPERSEDE", old, hb_epoch=EPOCH)["failure_code"], "SUCCESSOR_NOT_RECORDED")
        unnamed = base.nativize_issue(old)
        self.assertEqual(wi.transition("SV_ISSUE_SUPERSEDE", old, hb_epoch=EPOCH, context={"successor": unnamed})["failure_code"],
                         "SUCCESSOR_DOES_NOT_NAME_PREDECESSOR")
        still_unknown = base.nativize_issue(old, supersedes=old["issue_sha256"], owning_goal=U)
        self.assertEqual(wi.transition("SV_ISSUE_SUPERSEDE", old, hb_epoch=EPOCH, context={"successor": still_unknown})["failure_code"],
                         "UNKNOWN_IN_NATIVE_RECORD")
        ch = base.CHANGES[2]
        nsucc = base.nativize_change(ch, supersedes=ch["request_digest"])
        out = wi.transition("SV_CHANGE_SUPERSEDE", ch, hb_epoch=EPOCH, context={"successor": nsucc})
        self.assertEqual((out["disposition"], out["record"]["superseded_by"]), ("ALLOW", nsucc["request_digest"]))
        self.assertEqual(code(wi.validate_change, out["record"]), "ALLOW")


class SchemaFixTests(unittest.TestCase):
    def test_sf1_epoch_unknown_only_migrated(self):
        self.assertEqual(both(base.ISSUES[0], ISSUE_SCHEMA, wi.validate_issue), ([], "ALLOW"))
        self.assertEqual(both(base.CHANGES[0], CHANGE_SCHEMA, wi.validate_change), ([], "ALLOW"))
        errs, c = both(base.nativize_change(base.CHANGES[0], hb_epoch=U), CHANGE_SCHEMA, wi.validate_change)
        self.assertEqual(c, "UNKNOWN_IN_NATIVE_RECORD")
        self.assertTrue(errs)
        self.assertEqual(code(wi.validate_issue, migrated_issue(hb_epoch="+33")), "HB_EPOCH_INVALID")

    def test_sf2_change_id_derivation_is_published_and_reproducible(self):
        self.assertIn("change_identity", CHANGE_SCHEMA["properties"]["change_id"]["x-derivation"])
        for ch in base.CHANGES:
            content = sorted(({"path": c["path"], "blob_digest": c["blob_digest"], "deleted": bool(c.get("deleted", False))}
                              for c in ch["content"]), key=lambda c: c["path"])
            raw = json.dumps({"target_repository": ch["target_repository"], "base_ref": ch["base_ref"], "content": content},
                             sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
            self.assertEqual(ch["change_id"], "svc:" + hashlib.sha256(raw).hexdigest())
        ch = base.CHANGES[2]
        other_writer = copy.deepcopy(ch)
        other_writer["content"][0]["writer_session"] = {"session": None, "evidence_class": U}
        self.assertEqual(wi.change_identity(other_writer), ch["change_id"])
        deleted = copy.deepcopy(ch); deleted["content"][0]["deleted"] = True
        self.assertNotEqual(wi.change_identity(deleted), ch["change_id"])
        rebased = dict(ch, base_ref={**ch["base_ref"], "registry_generation": 320})
        self.assertNotEqual(wi.change_identity(rebased), ch["change_id"])

    def test_sf3_resolution_class_never_defaulted(self):
        self.assertEqual(fx.resolution_class("no table here", "X_CODE"), U)
        self.assertEqual(fx.resolution_class("| X_CODE | **D** |", "X_CODE"), "D")
        self.assertIn(U, {r["resolution_class"] for r in base.ISSUES})
        self.assertEqual(code(wi.validate_issue, base.nativize_issue(base.ISSUES[0], resolution_class=U)), "UNKNOWN_IN_NATIVE_RECORD")

    def test_sf4_resolves(self):
        errs, c = both(base.nativize_change(base.CHANGES[2], resolves=[]), CHANGE_SCHEMA, wi.validate_change)
        self.assertEqual(c, "SV_CHANGE_RESOLVES_NOTHING")
        self.assertIn(("/resolves", "minItems"), errs)
        empty = migrated_change(resolves=[])
        self.assertEqual(empty["migration_flags"], [wi.MIGRATION_FLAG_RESOLVES])
        self.assertEqual(both(empty, CHANGE_SCHEMA, wi.validate_change), ([], "ALLOW"))
        unflagged = {k: v for k, v in empty.items() if k != "migration_flags"}
        unflagged["request_digest"] = wi.request_digest(unflagged)
        errs, c = both(unflagged, CHANGE_SCHEMA, wi.validate_change)
        self.assertEqual(c, "MIGRATION_FLAG_MISMATCH")
        self.assertTrue(errs)

    def test_sf5_only_ledger_receipts_count(self):
        ch = base.al_known_good_change("svi:" + "1" * 64)
        obs = wi.admission_inputs(ch, ch["base_ref"])
        self.assertEqual(wi.admit({**obs, "required_signoff_roles": []})["disposition"], "ALLOW")
        art = base.reseal_change(dict(ch, validation_receipts=[
            {**v, "evidence_class": "OBSERVED_ARTIFACT", "ref": "docs/lane-file.md#L57"} for v in ch["validation_receipts"]]))
        self.assertEqual(both(art, CHANGE_SCHEMA, wi.validate_change), ([], "ALLOW"))
        out = wi.admit(wi.admission_inputs(art, art["base_ref"]))
        self.assertEqual((out["failure_code"], out["artifact_only"]), ("CHECK_SKIPPED_OR_UNOBSERVED", sorted(c for c in out["unobserved"])))
        bad = base.reseal_change(dict(ch, validation_receipts=[{**ch["validation_receipts"][0], "ref": "receipt:x"}]))
        errs, c = both(bad, CHANGE_SCHEMA, wi.validate_change)
        self.assertEqual(c, "VALIDATION_RECEIPT_INVALID")
        self.assertTrue(errs)

    def test_sf6_unknown_writer_fails_branch_writer_is_branch_owner(self):
        issue = dict(base.nativize_issue(base.ISSUES[0]), lifecycle_state="CLAIMED", claim={"session": SESSION})
        ch = base.al_known_good_change(issue["issue_id"])
        ch["content"][0]["writer_session"] = {"session": None, "evidence_class": U}
        ch = base.reseal_change(ch)
        self.assertEqual(both(ch, CHANGE_SCHEMA, wi.validate_change), ([], "ALLOW"))
        out = wi.transition("SV_CHANGE_PROPOSE", ch, hb_epoch=EPOCH, context={"issues": [issue]})
        self.assertEqual((out["failure_code"], out["failed_predicate"]), ("BRANCH_WRITER_UNOBSERVED", "BRANCH_WRITER_IS_BRANCH_OWNER"))
        self.assertEqual(wi.admit(wi.admission_inputs(ch, ch["base_ref"]))["failure_code"], "BRANCH_WRITER_UNOBSERVED")
        for w in ({"session": None, "evidence_class": "DECLARED"}, {"session": "x", "evidence_class": U}, "P1"):
            bad = copy.deepcopy(ch); bad["content"][0]["writer_session"] = w
            errs, c = both(base.reseal_change(bad), CHANGE_SCHEMA, wi.validate_change)
            self.assertEqual(c, "SV_CHANGE_CONTENT_ENTRY_INVALID", w)
            self.assertTrue(errs, w)

    def test_sf7_identity_ignores_free_text_and_dedupes_reworded_duplicates(self):
        a = migrated_issue()
        d = a["disposition"]
        reworded = migrated_issue(disposition={**d, "required_evidence_or_repair": "reworded: " + d["required_evidence_or_repair"],
                                               "next_attempt": "later, differently worded", "owning_existing_goal": U,
                                               "failure_code": d["failure_code"] + "_RESTATED"})
        self.assertEqual(reworded["issue_id"], a["issue_id"])
        merged, _ = mg.merge_issues([a, reworded])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["restatements"][0]["failure_code"], d["failure_code"] + "_RESTATED")
        self.assertEqual(code(wi.validate_issue, merged[0]), "ALLOW")
        for over in ({"surface": {"kind": "workflow", "path": ".github/workflows/x.yml"}},
                     {"disposition": {**d, "failed_predicate": "OTHER_PREDICATE"}},
                     {"violated_invariant": {**a["violated_invariant"], "rule_id": "OTHER_RULE"}},
                     {"source_receipt": {**a["source_receipt"], "evidence_sha256": "sha256:" + "9" * 64}}):
            self.assertNotEqual(migrated_issue(**over)["issue_id"], a["issue_id"], over)
        self.assertEqual(set(wi.issue_identity_inputs(a)), {"violated_invariant", "failed_predicate", "owning_goal", "surface", "source_receipt_ref"})

    def test_sf8_owning_goal_unknown_only_migrated(self):
        m = migrated_issue(owning_goal=U)
        self.assertIn("/owning_goal", m["unknown_fields"])
        self.assertEqual(both(m, ISSUE_SCHEMA, wi.validate_issue), ([], "ALLOW"))
        self.assertEqual(both(migrated_change(owning_goal=U), CHANGE_SCHEMA, wi.validate_change), ([], "ALLOW"))
        self.assertEqual(code(wi.validate_change, base.nativize_change(base.CHANGES[2], owning_goal=U)), "UNKNOWN_IN_NATIVE_RECORD")

    def test_sf9_multi_goal_index_lives_on_the_coordination_task_record(self):
        recs = base.ISSUES + base.CHANGES + [migrated_change(owning_goal=U)]
        rec = wi.work_items_record(recs)
        self.assertEqual(ss.validate(rec, ITEMS_SCHEMA), [])
        self.assertEqual(rec["coordination_task_id"], "STEGVERSE-CANONICAL-WORK-COORDINATION-001")
        self.assertIn(U, rec["goal_index"])
        self.assertGreater(len(rec["goal_index"]), 1)
        self.assertIn("goal_index", ITEMS_SCHEMA["x-carrier"])

    def test_sf10_migration_provenance(self):
        good = base.ISSUES[0]["migration_provenance"]
        self.assertEqual((good["original_base_observed"], good["original_base_ref"]), (False, None))
        for mp in ({**good, "original_base_ref": good["migrated_at_base"]},
                   {**good, "original_base_observed": True},
                   {**good, "migrated_at_base": {**good["migrated_at_base"], "registry_generation": 1}},
                   {k: v for k, v in good.items() if k != "migrated_at_base"}):
            rec = base.reseal_issue(dict(base.ISSUES[0], migration_provenance=mp))
            errs, c = both(rec, ISSUE_SCHEMA, wi.validate_issue)
            self.assertEqual(c, "MIGRATION_PROVENANCE_INVALID", mp)
        observed = base.reseal_issue(dict(base.ISSUES[0], migration_provenance={**good, "original_base_observed": True,
                                                                              "original_base_ref": {"registry_generation": 300, "ledger_head": "a" * 40}}))
        self.assertEqual(both(observed, ISSUE_SCHEMA, wi.validate_issue), ([], "ALLOW"))
        self.assertEqual(code(wi.validate_issue, base.reseal_issue({k: v for k, v in base.ISSUES[0].items() if k != "migration_provenance"})),
                         "MIGRATION_PROVENANCE_INVALID")


class LiftTests(unittest.TestCase):
    """Records written against the 1673cb5f draft (Lane D's shape) lift by the published rules only."""

    def v0_change(self):
        ch = copy.deepcopy(base.CHANGES[2])
        for k in ("record_mode", "unknown_fields", "migration_provenance", "migration_flags"):
            ch.pop(k, None)
        ch.update(change_id=U, resolves=[], owning_goal=U)
        ch["content"] = [{**c, "writer_session": U} for c in ch["content"]]
        return ch

    def test_lift_v0_change_validates_without_inventing(self):
        out = mg.lift_v0_change(self.v0_change(), {})
        self.assertEqual(both(out, CHANGE_SCHEMA, wi.validate_change), ([], "ALLOW"))
        self.assertEqual(out["unknown_fields"], ["/hb_epoch", "/owning_goal"])
        self.assertTrue(all(c["writer_session"] == {"session": None, "evidence_class": U} for c in out["content"]))
        self.assertEqual(out["migration_flags"], [wi.MIGRATION_FLAG_RESOLVES])

    def test_v0_receipt_without_digest_stays_a_gap(self):
        ch = self.v0_change()
        ch["validation_receipts"] = [{"check_id": "BRANCH_WRITER_IS_BRANCH_OWNER", "disposition": "FAIL_CLOSED",
                                      "change_digest": ch["head"]["change_digest"], "receipt_ref": U}]
        out = mg.lift_v0_change(ch, {})
        self.assertEqual(code(wi.validate_change, out), "UNKNOWN_FIELD_NOT_PERMITTED")

    def test_lift_v0_issue_rederives_identity(self):
        v0 = {k: v for k, v in base.ISSUES[0].items() if k not in ("record_mode", "unknown_fields", "migration_provenance", "surface")}
        v0["issue_id"] = "svi:" + "4" * 64
        out = mg.lift_v0_issue(v0)
        self.assertEqual(out.pop("_old_id"), "svi:" + "4" * 64)
        self.assertEqual(both(out, ISSUE_SCHEMA, wi.validate_issue), ([], "ALLOW"))
        self.assertEqual(out["surface"], mg.derive_surface(v0["disposition"]["retry_entrypoint"]))
        self.assertEqual(mg.derive_surface("on merge"), U)


KAT_RECORD = {
    "target_repository": "StegVerse-Labs/.github",
    "base_ref": {"registry_generation": 319, "ledger_head": "a5bb54d81893b392a3ce28182986fc39857807e1"},
    "content": [
        {"path": "schemas/\u00e9.json", "blob_digest": "sha256:" + "b" * 64,
         "writer_session": {"session": "P1", "evidence_class": "DECLARED"}},
        {"path": "docs/old.md", "blob_digest": None, "deleted": True,
         "writer_session": {"session": None, "evidence_class": "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"}},
    ],
}
KAT_BYTES = ('{"base_ref":{"ledger_head":"a5bb54d81893b392a3ce28182986fc39857807e1","registry_generation":319},'
             '"content":[{"blob_digest":null,"deleted":true,"path":"docs/old.md"},'
             '{"blob_digest":"sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","deleted":false,"path":"schemas/\u00e9.json"}],'
             '"target_repository":"StegVerse-Labs/.github"}').encode("utf-8")
KAT_CHANGE_ID = "svc:b1f56ebe998a4a0896e8f3f18ef76abe65f6f6bd0c613fa04e50291025300239"


class ChangeIdCanonicalTests(unittest.TestCase):
    """Lane C amendment: pinned canonical serialization, deleted entries, base_ref, OBSERVED_ARTIFACT never passes."""

    def test_change_id_known_answer(self):
        self.assertEqual(wi.canon(wi.change_identity_input(KAT_RECORD)), KAT_BYTES)
        self.assertEqual(len(KAT_BYTES), 342)
        self.assertFalse(KAT_BYTES.endswith(b"\n"))
        self.assertIn("\u00e9".encode("utf-8"), KAT_BYTES)  # ensure_ascii false: raw UTF-8, no \\u escape
        self.assertEqual("svc:" + hashlib.sha256(KAT_BYTES).hexdigest(), KAT_CHANGE_ID)
        self.assertEqual(wi.change_identity(KAT_RECORD), KAT_CHANGE_ID)

    def test_serialization_is_pinned_in_schema_and_code(self):
        pinned = CHANGE_SCHEMA["properties"]["change_id"]["x-canonical-serialization"]
        self.assertEqual(pinned, {"format": "JSON", "sort_keys": True, "separators": [",", ":"], "encoding": "UTF-8",
                                  "ensure_ascii": False, "trailing_newline": False})
        self.assertEqual(pinned, wi.CANONICAL_SERIALIZATION)
        v = {"b": "\u00e9", "a": [1, None]}
        self.assertEqual(wi.canon(v), json.dumps(v, sort_keys=pinned["sort_keys"], separators=tuple(pinned["separators"]),
                                                 ensure_ascii=pinned["ensure_ascii"]).encode(pinned["encoding"].lower().replace("-", "")))

    def test_deleted_entry_hashes_null_blob_digest(self):
        hashed = wi.change_identity_input(KAT_RECORD)["content"][0]
        self.assertEqual(hashed, {"path": "docs/old.md", "blob_digest": None, "deleted": True})
        other = copy.deepcopy(KAT_RECORD); other["content"][1]["blob_digest"] = "sha256:" + "0" * 64
        self.assertEqual(wi.change_identity(other), KAT_CHANGE_ID)  # hashed form is null either way; the validator refuses it (below)
        undeleted = copy.deepcopy(KAT_RECORD); undeleted["content"][1]["deleted"] = False
        self.assertNotEqual(wi.change_identity(undeleted), KAT_CHANGE_ID)
        truthy = copy.deepcopy(KAT_RECORD); truthy["content"][1]["deleted"] = "yes"
        self.assertEqual(wi.change_identity_input(truthy)["content"][0]["deleted"], False)  # only boolean true deletes

    def test_base_ref_keeps_registry_generation_and_ledger_head(self):
        self.assertEqual(set(wi.change_identity_input(KAT_RECORD)["base_ref"]), {"registry_generation", "ledger_head"})
        for drop in ("registry_generation", "ledger_head"):
            rec = copy.deepcopy(KAT_RECORD); del rec["base_ref"][drop]
            self.assertEqual(code(wi.change_identity, rec), "SV_CHANGE_BASE_UNBOUND", drop)
            ch = copy.deepcopy(base.nativize_change(base.CHANGES[2])); del ch["base_ref"][drop]
            self.assertEqual(code(wi.validate_change, ch), "SV_CHANGE_BASE_UNBOUND", drop)
        for k, v in (("registry_generation", 320), ("ledger_head", "f" * 40)):
            rec = copy.deepcopy(KAT_RECORD); rec["base_ref"][k] = v
            self.assertNotEqual(wi.change_identity(rec), KAT_CHANGE_ID, k)

    def test_observed_artifact_is_unknown_for_verified_never_a_pass(self):
        ch = base.al_known_good_change("svi:" + "1" * 64)
        first = ch["validation_receipts"][0]["check_id"]
        art = base.reseal_change(dict(ch, validation_receipts=[
            {**v, "evidence_class": "OBSERVED_ARTIFACT", "ref": "docs/evidence.md"} if v["check_id"] == first else v
            for v in ch["validation_receipts"]]))
        out = wi.transition("SV_CHANGE_VERIFY", art, hb_epoch=EPOCH)
        self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                         ("FAIL_CLOSED", "CHECK_SKIPPED_OR_UNOBSERVED", "MERGE_READY_REQUIRES_EVERY_JOB_RAN_AND_PASSED"))
        self.assertEqual(out["record"]["lifecycle_state"], art["lifecycle_state"])
        res = wi.admit(wi.admission_inputs(art, art["base_ref"]))
        self.assertEqual((res["unobserved"], res["artifact_only"]), ([first], [first]))
        # an artifact never upgrades or overrides: alongside a ledger DENY it does not hide the refusal
        mixed = base.reseal_change(dict(ch, validation_receipts=[
            {**v, "disposition": "DENY"} if v["check_id"] == first else v for v in ch["validation_receipts"]] +
            [{**ch["validation_receipts"][0], "evidence_class": "OBSERVED_ARTIFACT", "ref": "docs/evidence.md"}]))
        self.assertEqual(wi.admit({**wi.admission_inputs(mixed, mixed["base_ref"]), "required_signoff_roles": []})["failure_code"],
                         "CHECK_NOT_PASSING")


class RemainingFeedbackTests(unittest.TestCase):
    """Lane D RF-1..RF-3 (laned/s0-lane-d-migration-fixtures @1b53fb05)."""

    def test_rf1_same_predicate_under_two_goals_stays_two_issues(self):
        a = migrated_issue(owning_goal="STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001")
        b = migrated_issue(owning_goal="STEGOPS-CAMPAIGN-CRM-PROJECTION-001")
        self.assertNotEqual(a["issue_id"], b["issue_id"])
        merged, _ = mg.merge_issues([a, b])
        self.assertEqual(len(merged), 2)
        idx = wi.work_items_record(merged)["goal_index"]
        self.assertEqual(set(idx), {"STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001", "STEGOPS-CAMPAIGN-CRM-PROJECTION-001"})
        self.assertEqual(migrated_issue(owning_goal=" STEGOPS-CAMPAIGN-CRM-PROJECTION-001 ")["issue_id"], b["issue_id"])  # stripped

    def test_rf1_known_limit_unknown_goals_still_collide(self):
        x = migrated_issue(owning_goal=U)
        y = migrated_issue(owning_goal=U, disposition={**base.ISSUES[0]["disposition"], "next_attempt": "another goal's row"})
        self.assertEqual(x["issue_id"], y["issue_id"])
        self.assertIn("known limit", ISSUE_SCHEMA["properties"]["issue_id"]["x-derivation"])

    def test_rf2_alias_table_is_pinned_by_blob(self):
        raw = mg.SURFACE_ALIASES_PATH.read_bytes()
        self.assertEqual(mg.git_blob(raw), mg.SURFACE_ALIASES_BLOB)
        table = mg.load_aliases()
        self.assertEqual(table["schema"], "stegverse.sv-surface-aliases/v1")
        import tempfile, pathlib
        with tempfile.TemporaryDirectory() as d:
            alt = pathlib.Path(d) / "aliases.json"
            alt.write_bytes(raw.replace(b'"CONS"', b'"CONZ"'))
            with self.assertRaises(wi.Refusal) as cm:
                mg.load_aliases(alt)
            self.assertEqual(cm.exception.record["failure_code"], "SURFACE_ALIAS_TABLE_UNPINNED")

    def test_rf2_every_resolved_alias_names_a_verified_object(self):
        table = mg.load_aliases()
        repos = {r["repository"]: r["commit"] for r in table["repositories"]}
        for group in ("lane_aliases", "bare_names", "patch_entrypoints"):
            for e in table[group]:
                if e["path"] in (U, wi.NON_REPOSITORY_EVIDENCE):
                    self.assertTrue(e.get("reason"), e)
                    self.assertNotIn("verified", e)
                    continue
                v = e["verified"]
                self.assertEqual(repos[v["repository"]], v["commit"], e)
                self.assertRegex(v["object_sha"], r"^[0-9a-f]{40}$")
                self.assertFalse(wi.is_box_local(e["path"]), e)

    def test_rf2_resolution(self):
        r = mg.resolve_surface
        self.assertEqual(r("CONS::consume"), {"kind": "transition", "path": "scripts/consume_org_claim_allocator_request.py"})
        self.assertEqual(r("re CONS"), {"kind": "transition", "path": "scripts/consume_org_claim_allocator_request.py"})
        self.assertEqual(r("CONSOLE output"), U)  # whole token only
        self.assertEqual(r("Site data/session-work-claims.d"), {"kind": "doc", "path": "data/session-work-claims.d"})
        self.assertEqual(r("projection in apply_admitted_canonical_work_projection.py"),
                         {"kind": "transition", "path": "scripts/apply_admitted_canonical_work_projection.py"})
        self.assertEqual(r("patches/D4-canonical-task-record-schema.diff"), {"kind": "schema", "path": "schemas/canonical-task-record.schema.json"})
        self.assertEqual(r("patches/D13-r6-rebased-on-site-b6ebfee0.diff"),
                         {"kind": "workflow", "path": ".github/workflows/workspace-kv-binding-validation.yml"})
        self.assertEqual(r("patches/STEGOPS-CRM-registry-row.json-patch.json"), {"kind": "registry", "path": "data/canonical-task-registry.json"})
        self.assertEqual(r("patches/D14-*.json-patch.json"), U)  # ambiguous glob, declared UNKNOWN
        self.assertEqual(r("SPPA (18.3) in retro-classification mode"), U)  # alias without a declared path
        self.assertEqual(r("that script"), U)
        self.assertEqual(r("Labs#3211 new head"), U)

    def test_rf3_box_local_paths_are_non_repository_evidence(self):
        r, N = mg.resolve_surface, wi.NON_REPOSITORY_EVIDENCE
        for text, path in (("patches/H46-fence-floor-repair.diff", "patches/H46-fence-floor-repair.diff"),
                           ("/workspace/lane-d/wu2-wu3-plan.md", "/workspace/lane-d/wu2-wu3-plan.md"),
                           ("/tmp/b189/repair/org-kernel/kernel.py", "/tmp/b189/repair/org-kernel/kernel.py"),
                           ("wu1-wu5-readiness.md WU1", "wu1-wu5-readiness.md"), ("wu2-wu3-plan.md", "wu2-wu3-plan.md")):
            self.assertEqual(r(text), {"kind": N, "path": path}, text)
        tree = {"scripts/real.py"}
        self.assertEqual(r("scripts/real.py", repo_paths=tree), {"kind": "transition", "path": "scripts/real.py"})
        self.assertEqual(r("scripts/not_in_tree.py", repo_paths=tree), {"kind": N, "path": "scripts/not_in_tree.py"})
        self.assertEqual(mg.recheck_surface({"kind": "doc", "path": "patches/WU4-restated-registry-entry.json"}),
                         {"kind": "registry", "path": "data/canonical-task-records/STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001.json"})
        self.assertEqual(mg.recheck_surface({"kind": "doc", "path": "patches/local-only.json"}), {"kind": N, "path": "patches/local-only.json"})

    def test_rf3_non_repository_surface_is_never_admissible(self):
        N = wi.NON_REPOSITORY_EVIDENCE
        m = migrated_issue(surface={"kind": N, "path": "patches/x.diff"})
        self.assertEqual(both(m, ISSUE_SCHEMA, wi.validate_issue), ([], "ALLOW"))  # classified history only
        errs, c = both(base.nativize_issue(base.ISSUES[0], surface={"kind": N, "path": "patches/x.diff"}), ISSUE_SCHEMA, wi.validate_issue)
        self.assertEqual(c, "SURFACE_NOT_IN_REPOSITORY_TREE")
        self.assertTrue(errs)
        disguised = migrated_issue(surface={"kind": "doc", "path": "patches/x.diff"})
        self.assertEqual(code(wi.validate_issue, disguised), "SURFACE_NOT_IN_REPOSITORY_TREE")
        for p in ("/workspace/a.py", "/tmp/a.py", "/abs/a.py"):
            self.assertEqual(code(wi.validate_issue, migrated_issue(surface={"kind": "transition", "path": p})), "SURFACE_NOT_IN_REPOSITORY_TREE", p)
        self.assertNotEqual(migrated_issue(surface={"kind": N, "path": "wu1-wu5-readiness.md"})["issue_id"],
                            migrated_issue(surface={"kind": N, "path": "wu2-wu3-plan.md"})["issue_id"])


if __name__ == "__main__":
    unittest.main()


def sealed(**over):
    """A NATIVE known-good change with overrides, resealed (change_id, head.change_digest, receipts at that head)."""
    ch = copy.deepcopy(base.al_known_good_change("svi:" + "1" * 64))
    ch.update(over)
    ch["touched_paths"] = sorted(c["path"] for c in ch["content"])
    ch = base.reseal_change(ch)
    ch["validation_receipts"] = [{**v, "change_digest": ch["head"]["change_digest"]} for v in ch["validation_receipts"]]
    return base.reseal_change(ch)


class ChangeDigestTests(unittest.TestCase):
    """head.change_digest is sha256 over the same canonical bytes as change_id; deleted entries store blob_digest null."""

    def test_change_digest_equals_change_id_hex(self):
        self.assertEqual(wi.change_digest(KAT_RECORD), "sha256:" + hashlib.sha256(KAT_BYTES).hexdigest())
        self.assertEqual(wi.change_digest(KAT_RECORD)[len("sha256:"):], KAT_CHANGE_ID[len("svc:"):])
        built = [json.loads(l) for l in (ROOT / "data/sv-work-items/migration/sv-changes.jsonl").read_text().splitlines() if l.strip()]
        for ch in built + [base.al_known_good_change("svi:" + "1" * 64)]:
            self.assertEqual(ch["head"]["change_digest"][7:], ch["change_id"][4:], ch["change_id"])
            self.assertEqual(ch["head"]["change_digest"], wi.change_digest(ch))

    def test_change_digest_moves_with_base_and_target(self):
        ch = base.al_known_good_change("svi:" + "1" * 64)
        for k, v in (("base_ref", dict(ch["base_ref"], registry_generation=ch["base_ref"]["registry_generation"] + 1)),
                     ("target_repository", "StegVerse-org/.github")):
            self.assertNotEqual(wi.change_digest(dict(ch, **{k: v})), ch["head"]["change_digest"], k)

    def test_stale_head_digest_refused_and_receipts_must_match(self):
        ch = base.al_known_good_change("svi:" + "1" * 64)
        legacy = mg.legacy_change_digest(ch["content"])
        bad = dict(ch, head={"change_digest": legacy})
        self.assertEqual(code(wi.validate_change, bad), "SV_CHANGE_DIGEST_MISMATCH")
        stale = base.reseal_change(dict(ch, validation_receipts=[dict(v, change_digest=legacy) for v in ch["validation_receipts"]]))
        out = wi.admit({**wi.admission_inputs(stale, stale["base_ref"]), "required_signoff_roles": []})
        self.assertEqual(out["failure_code"], "VALIDATION_NOT_AT_EXACT_HEAD")

    def test_lift_reexpresses_only_receipts_bound_to_same_content(self):
        src = copy.deepcopy(base.CHANGES[2])
        legacy = mg.legacy_change_digest(src["content"])
        src["head"] = {"change_digest": legacy}
        src["validation_receipts"] = [
            {"check_id": "a", "disposition": "ALLOW", "change_digest": legacy, "evidence_class": "OBSERVED_ARTIFACT", "ref": "x", "digest": None},
            {"check_id": "b", "disposition": "ALLOW", "change_digest": "sha256:" + "9" * 64, "evidence_class": "OBSERVED_ARTIFACT", "ref": "x", "digest": None}]
        out = mg.finish_change(src)
        self.assertEqual([v["change_digest"] for v in out["validation_receipts"]], [out["head"]["change_digest"], "sha256:" + "9" * 64])

    def test_deleted_entry_requires_null_blob_digest(self):
        ws = {"session": SESSION, "evidence_class": "DECLARED"}
        keep = base.al_known_good_change("svi:" + "1" * 64)["content"][0]
        good = sealed(content=[keep, {"path": "docs/old.md", "blob_digest": None, "deleted": True, "writer_session": ws}])
        self.assertEqual(both(good, CHANGE_SCHEMA, wi.validate_change), ([], "ALLOW"))
        bad = sealed(content=[keep, {"path": "docs/old.md", "blob_digest": "sha256:" + "0" * 64, "deleted": True, "writer_session": ws}])
        errs, c = both(bad, CHANGE_SCHEMA, wi.validate_change)
        self.assertTrue(errs); self.assertEqual(c, "SV_CHANGE_CONTENT_ENTRY_INVALID")
        live_null = sealed(content=[keep, {"path": "docs/new.md", "blob_digest": None, "writer_session": ws}])
        errs, c = both(live_null, CHANGE_SCHEMA, wi.validate_change)
        self.assertTrue(errs); self.assertEqual(c, "SV_CHANGE_CONTENT_ENTRY_INVALID")
