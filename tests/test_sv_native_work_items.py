"""NWI-S0: SV_ISSUE / SV_CHANGE schemas, validators, lifecycle, migration fixtures and the admission corpus."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, rel):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


wi = _load("sv_work_items", "resident-runtime/sv_work_items.py")
al = _load("admission_learning", "resident-runtime/admission_learning.py")
fx = _load("build_sv_native_fixtures", "scripts/build_sv_native_fixtures.py")
ss = _load("schema_subset", "resident-runtime/schema_subset.py")
EPOCH = "1024"
SESSION = fx.SESSION
BASE = dict(fx.LABS_BASE)


def jsonl(rel):
    return [json.loads(l) for l in (ROOT / rel).read_text().splitlines() if l.strip()]


ISSUES = jsonl("data/sv-work-items/migration/sv-issues.jsonl")
CHANGES = jsonl("data/sv-work-items/migration/sv-changes.jsonl")


MIGRATION_KEYS = ("unknown_fields", "migration_provenance", "migration_flags")


def nativize_issue(rec, **over):
    """Synthetic NATIVE successor of a migrated fixture (test data: every value set explicitly here)."""
    rec = {k: v for k, v in copy.deepcopy(rec).items() if k not in MIGRATION_KEYS}
    rec.update(record_mode="NATIVE", hb_epoch=EPOCH, resolution_class="B", owning_goal="StegVerse-org/.github#163",
               surface={"kind": "transition", "path": "resident-runtime/example_transition.py"},
               source_receipt={"kind": "ORGANIZATION_LEDGER_RECEIPT", "ledger_ref": wi.LEDGER_REF, "receipt_sha256": "sha256:" + "5" * 64})
    rec["disposition"] = {**rec["disposition"], "owning_existing_goal": "StegVerse-org/.github#163"}
    rec.update(over)
    return reseal_issue(rec)


def nativize_change(rec, **over):
    rec = {k: v for k, v in copy.deepcopy(rec).items() if k not in MIGRATION_KEYS}
    rec.update(record_mode="NATIVE", hb_epoch=EPOCH)
    rec.update(over)
    return reseal_change(rec)


def reseal_issue(rec):
    rec = {k: v for k, v in rec.items() if k != "issue_sha256"}
    rec["issue_id"] = wi.issue_identity(rec)
    return wi.seal(rec, "issue_sha256")


def reseal_change(rec):
    rec = dict(rec)
    try:
        rec["head"] = {"change_digest": wi.change_digest(rec)}
    except wi.Refusal:
        pass
    rec["touched_paths"] = [c["path"] for c in rec["content"]]
    try:
        rec["change_id"] = wi.change_identity(rec)
    except wi.Refusal:
        pass  # an unbound base has no identity; the validator refuses it
    rec["request_digest"] = wi.request_digest(rec)
    return rec


def code(fn, rec):
    try:
        fn(rec)
    except wi.Refusal as r:
        for f in wi.SIX_FIELDS:
            assert r.record.get(f), f
        return r.record["failure_code"]
    return "ALLOW"


def worker_registry(task_id, worker=SESSION, claim="claim-1", fence=7):
    return {"tasks": [{"task_id": task_id, "worker_id": worker, "claim_id": claim, "assignment_timer": {"fencing_token": fence}, "state": "CLAIMED"}]}


class MigrationFixtureTests(unittest.TestCase):
    def test_fixtures_are_derived_deterministically(self):
        for path, text in fx.build().items():
            self.assertEqual(path.read_text(), text, str(path))

    def test_every_issue_fixture_validates(self):
        self.assertGreaterEqual(len(ISSUES), 15)
        for rec in ISSUES:
            self.assertEqual(wi.validate_issue(rec)["issue_id"], rec["issue_id"])

    def test_189_binder_and_p1_fail_closed_entries_are_issues(self):
        codes = {r["disposition"]["failure_code"] for r in ISSUES}
        for c in ("CLOCK_DERIVED_EPOCH_ADMITTED_BY_ORG_APPEND", "HB_EPOCH_CLI_COERCED", "HB_EPOCH_REFUSAL_NOT_SIX_FIELD_AT_CLI",
                  "MERGE_CONFLICT_WITH_40a5d235", "SHARED_LEDGER_COMPONENT_NOT_PUBLISHED", "ECOSYSTEM_CAPABILITY_ABSENT"):
            self.assertIn(c, codes)

    def test_every_change_fixture_validates_and_resolves_known_issues(self):
        ids = {r["issue_id"] for r in ISSUES}
        prs = set()
        for ch in CHANGES:
            wi.validate_change(ch)
            self.assertTrue(set(ch["resolves"]) <= ids)
            prs.add(ch["projection"]["pr"])
        self.assertEqual(prs, {3225, 3226, 3234, None})

    def test_migrated_changes_are_never_verified_or_admitted(self):
        for ch in CHANGES:
            self.assertEqual(ch["record_mode"], "MIGRATED_HISTORICAL")
            out = wi.transition("SV_CHANGE_VERIFY", ch, hb_epoch=EPOCH)
            self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "HISTORICAL_RECORD_NOT_ADMISSIBLE"))
            # as NATIVE with the same observed content, GitHub CI is still not a receipt
            out = wi.transition("SV_CHANGE_VERIFY", nativize_change(ch), hb_epoch=EPOCH)
            self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "CHECK_SKIPPED_OR_UNOBSERVED"))

    def test_work_items_projection_is_native_keyed_without_approval_flag(self):
        rec = wi.work_items_record(ISSUES + CHANGES)
        items = rec["work_items"]
        self.assertEqual(len(items), len(ISSUES) + len(CHANGES))
        schema = json.loads((ROOT / "schemas/canonical-task-work-items.v1.schema.json").read_text())
        self.assertEqual(ss.validate(rec, schema), [])
        self.assertEqual(sorted(i for ids in rec["goal_index"].values() for i in ids), sorted(w["work_item_id"] for w in items))
        allowed = set(schema["properties"]["work_items"]["items"]["properties"])
        for w in items:
            self.assertTrue(w["work_item_id"].startswith(("svi:", "svc:")))
            self.assertLessEqual(set(w), allowed)
            self.assertNotIn("owner_approval", json.dumps(w))

    def test_schema_required_fields_match_fixtures(self):
        for name, recs in (("sv-issue.v1", ISSUES), ("sv-change.v1", CHANGES)):
            schema = json.loads((ROOT / f"schemas/{name}.schema.json").read_text())
            for r in recs:
                self.assertEqual(ss.validate(r, schema), [], name)


class IssueNegativeTests(unittest.TestCase):
    def mut(self, f):
        rec = nativize_issue(ISSUES[0]); f(rec); return reseal_issue(rec)

    def test_negatives(self):
        cases = {
            "SV_ISSUE_BODY_NOT_NON_ALLOW": lambda r: r["disposition"].update(disposition="ALLOW"),
            "SV_ISSUE_SIX_FIELDS_INCOMPLETE": lambda r: r["disposition"].update(next_attempt=""),
            "SV_ISSUE_INVARIANT_UNNAMED": lambda r: r.update(violated_invariant={}),
            "SV_ISSUE_SOURCE_RECEIPT_ABSENT": lambda r: r.update(source_receipt={"kind": "ORGANIZATION_LEDGER_RECEIPT"}),
            "SV_ISSUE_CLASS_INVALID": lambda r: r.update(resolution_class="E"),
            "SV_ISSUE_STATE_INVALID": lambda r: r.update(lifecycle_state="MERGED"),
            "SV_ISSUE_BASE_UNBOUND": lambda r: r.update(observed_base={"registry_generation": 319}),
            "AUTHOR_SESSION_NOT_DECLARED": lambda r: r.update(opened_by_session=" "),
        }
        for want, f in cases.items():
            self.assertEqual(code(wi.validate_issue, self.mut(f)), want, want)

    def test_identity_and_digest(self):
        self.assertEqual(code(wi.validate_issue, nativize_issue(ISSUES[0])), "ALLOW")
        rec = dict(ISSUES[0], issue_id="svi:" + "0" * 64)
        self.assertEqual(code(wi.validate_issue, wi.seal({k: v for k, v in rec.items() if k != "issue_sha256"}, "issue_sha256")),
                         "SV_ISSUE_IDENTITY_MISMATCH")
        self.assertEqual(code(wi.validate_issue, dict(ISSUES[0], issue_sha256="sha256:" + "0" * 64)), "SV_ISSUE_DIGEST_MISMATCH")

    def test_epoch_negatives(self):
        for bad, want in (("+33", "HB_EPOCH_INVALID"), (" 33", "HB_EPOCH_INVALID"), ("3_3", "HB_EPOCH_INVALID"),
                          ("31", "HB_EPOCH_INVALID"), ("0", "HB_EPOCH_INVALID"), (None, "HB_EPOCH_NOT_SUPPLIED")):
            self.assertEqual(code(wi.validate_issue, nativize_issue(ISSUES[0], hb_epoch=bad)), want, repr(bad))


class ChangeNegativeTests(unittest.TestCase):
    def mut(self, f, reseal=True):
        rec = nativize_change(CHANGES[2]); f(rec); return reseal_change(rec) if reseal else rec

    def test_negatives(self):
        cases = {
            "AUTHOR_SESSION_NOT_DECLARED": lambda r: r.update(declared_session=""),
            "SV_CHANGE_RESOLVES_NOTHING": lambda r: r.update(resolves=[]),
            "SV_CHANGE_BASE_UNBOUND": lambda r: r.update(base_ref={"registry_generation": "319", "ledger_head": "x"}),
            "SV_CHANGE_CONTENT_ENTRY_INVALID": lambda r: r["content"][0].update(blob_digest="e29493af"),
            "SV_CHANGE_RESOLVES_INVALID": lambda r: r.update(resolves=["3234"]),
            "SV_CHANGE_CONTENT_DUPLICATE_PATH": lambda r: r["content"].append(dict(r["content"][0])),
            "SV_CHANGE_STATE_INVALID": lambda r: r.update(lifecycle_state="MERGED"),
            "REQUIRED_CHECKS_ROW_ABSENT": lambda r: r.update(required_checks_ref={"file": "x"}),
        }
        for want, f in cases.items():
            self.assertEqual(code(wi.validate_change, self.mut(f)), want, want)

    def test_digest_negatives(self):
        self.assertEqual(code(wi.validate_change, self.mut(lambda r: r.update(change_id="svc:" + "3" * 64), reseal=False)),
                         "SV_CHANGE_IDENTITY_INVALID")
        self.assertEqual(code(wi.validate_change, self.mut(lambda r: r["content"][0].update(blob_digest="sha256:" + "b" * 64), reseal=False)
                              | {"change_id": None}), "SV_CHANGE_IDENTITY_INVALID")
        moved = self.mut(lambda r: r["content"][0].update(blob_digest="sha256:" + "b" * 64), reseal=False)
        moved["change_id"] = wi.change_identity(moved)
        self.assertEqual(code(wi.validate_change, moved), "SV_CHANGE_DIGEST_MISMATCH")
        self.assertEqual(code(wi.validate_change, self.mut(lambda r: r.update(owning_goal="other"), reseal=False)), "REQUEST_DIGEST_MISMATCH")
        self.assertEqual(code(wi.validate_change, self.mut(lambda r: r.update(touched_paths=["x"]), reseal=False)),
                         "SV_CHANGE_TOUCHED_PATHS_MISMATCH")


class LifecycleTests(unittest.TestCase):
    def test_open_claim_via_workercoordinator_propose_admit_apply_resolve(self):
        issue = nativize_issue(ISSUES[0])
        self.assertEqual(wi.transition("SV_ISSUE_OPEN", issue, hb_epoch=EPOCH)["disposition"], "ALLOW")
        no_claim = wi.transition("SV_ISSUE_CLAIM", issue, hb_epoch=EPOCH, context={"observed_generation": 319, "current_base": BASE})
        self.assertEqual(no_claim["failure_code"], "WORKERCOORDINATOR_CLAIM_ABSENT")
        stale = wi.transition("SV_ISSUE_CLAIM", issue, hb_epoch=EPOCH,
                              context={"observed_generation": 318, "current_base": BASE, "worker_registry": worker_registry(issue["issue_id"])})
        self.assertEqual(stale["failure_code"], "STOP_STALE_COORDINATION")
        claimed = wi.transition("SV_ISSUE_CLAIM", issue, hb_epoch=EPOCH,
                                context={"observed_generation": 319, "current_base": BASE, "worker_registry": worker_registry(issue["issue_id"])})
        self.assertEqual(claimed["disposition"], "ALLOW")
        claimed = claimed["record"]
        self.assertEqual((claimed["lifecycle_state"], claimed["claim"]["fence_ref"], claimed["claim"]["projection_only"]), ("CLAIMED", 7, True))
        held = wi.transition("SV_ISSUE_RELEASE", claimed, hb_epoch=EPOCH, context={"worker_registry": worker_registry(issue["issue_id"])})
        self.assertEqual(held["failure_code"], "WORKERCOORDINATOR_CLAIM_STILL_HELD")

        good = al_known_good_change(issue["issue_id"])
        unclaimed = wi.transition("SV_CHANGE_PROPOSE", good, hb_epoch=EPOCH, context={"issues": [issue]})
        self.assertEqual(unclaimed["failure_code"], "RESOLVED_ISSUE_NOT_CLAIMED_BY_AUTHOR")
        prop = wi.transition("SV_CHANGE_PROPOSE", good, hb_epoch=EPOCH, context={"issues": [claimed]})
        self.assertEqual(prop["disposition"], "ALLOW")
        ver = wi.transition("SV_CHANGE_VERIFY", prop["record"], hb_epoch=EPOCH)
        self.assertEqual(ver["disposition"], "ALLOW", ver)
        noprov = wi.transition("SV_CHANGE_ADMIT", ver["record"], hb_epoch=EPOCH, context={"current_base": BASE})
        self.assertEqual(noprov["failure_code"], "ADMISSION_PROVENANCE_ABSENT")
        ctx = {"current_base": BASE, "predicate_digest": "sha256:" + "c" * 64, "corpus_head": "sha256:" + "d" * 64,
               "actor_session": "AI Entity (by manifest)", "covered_kinds": ["transition"]}
        moved = wi.transition("SV_CHANGE_ADMIT", ver["record"], hb_epoch=EPOCH, context={**ctx, "current_base": {**BASE, "registry_generation": 320}})
        self.assertEqual((moved["disposition"], moved["failure_code"], moved["record"]["lifecycle_state"]), ("DENY", "BASE_STALE", "DENIED"))
        uncovered = wi.transition("SV_CHANGE_ADMIT", ver["record"], hb_epoch=EPOCH, context={**ctx, "covered_kinds": []})
        self.assertEqual((uncovered["failure_code"], uncovered["record"]["lifecycle_state"]), ("NO_SCENARIO_COVERAGE_FOR_SURFACE", "FAIL_CLOSED"))
        adm = wi.transition("SV_CHANGE_ADMIT", ver["record"], hb_epoch=EPOCH, context=ctx)
        self.assertEqual((adm["disposition"], adm["record"]["lifecycle_state"], adm["corpus_head"]), ("ALLOW", "ADMITTED", ctx["corpus_head"]))
        app = wi.transition("SV_CHANGE_APPLY", adm["record"], hb_epoch=EPOCH, context={"current_base": BASE})
        self.assertEqual((app["record"]["lifecycle_state"], app["record"]["applied"]["registry_generation"]), ("APPLIED", 320))
        res = wi.transition("SV_ISSUE_RESOLVE", claimed, hb_epoch=EPOCH, context={"resolving_change": app["record"]})
        self.assertEqual(res["record"]["lifecycle_state"], "RESOLVED")
        skip = wi.transition("SV_CHANGE_APPLY", ver["record"], hb_epoch=EPOCH, context={"current_base": BASE})
        self.assertEqual(skip["failure_code"], "LIFECYCLE_STATE_NOT_ADMISSIBLE")
        proj = wi.transition("SV_CHANGE_PROJECT_GITHUB", app["record"], hb_epoch=EPOCH, context={"projection": {"repo": "x/y", "pr": 1}})
        self.assertEqual(proj["record"]["projection"]["authority_effect"], "NONE")

    def test_foreign_writer_refused_at_propose(self):
        issue = dict(nativize_issue(ISSUES[0]), lifecycle_state="CLAIMED", claim={"session": SESSION})
        ch = al_known_good_change(issue["issue_id"])
        ch["content"][0]["writer_session"] = {"session": "Claude (session 017WHFu1)", "evidence_class": "OBSERVED_COMMIT_TRAILER"}
        ch = reseal_change(ch)
        self.assertEqual(wi.transition("SV_CHANGE_PROPOSE", ch, hb_epoch=EPOCH, context={"issues": [issue]})["failure_code"], "BRANCH_HAS_FOREIGN_WRITER")
        ch["co_author_grants"] = [{"session": "Claude (session 017WHFu1)", "receipt_ref": "receipt:grant"}]
        ch = reseal_change(ch)
        self.assertEqual(wi.transition("SV_CHANGE_PROPOSE", ch, hb_epoch=EPOCH, context={"issues": [issue]})["disposition"], "ALLOW")

    def test_undeclared_transition_and_bad_epoch(self):
        self.assertEqual(wi.transition("SV_CHANGE_MERGE", CHANGES[0], hb_epoch=EPOCH)["failure_code"], "TRANSITION_UNDECLARED")
        self.assertEqual(wi.transition("SV_ISSUE_OPEN", ISSUES[0], hb_epoch="+33")["failure_code"], "HB_EPOCH_INVALID")
        self.assertEqual(wi.transition("SV_ISSUE_OPEN", ISSUES[0], hb_epoch=wi.UNKNOWN)["failure_code"], "HB_EPOCH_INVALID")

    def test_record_uses_existing_emitter_with_supplied_epoch(self):
        emit = _load("labs_emit", ".stegverse/transition-ledger/emit.py")
        with tempfile.TemporaryDirectory() as d:
            store = emit.ledger_store.PosixLedgerStore(Path(d))
            out = wi.transition("SV_ISSUE_OPEN", ISSUES[0], hb_epoch=EPOCH)
            rc = wi.record(out, None, hb_epoch=EPOCH, append=lambda *a, **k: emit.append(*a, store=store, **k))
            self.assertEqual(rc["schema"], "stegverse.repo-transition-receipt/v1")
            self.assertEqual(rc["transition_class"], "SV_ISSUE_OPEN")
            self.assertIs(rc["hb_reference"]["derived_from_clock"], False)
            self.assertEqual(rc["hb_reference"]["epoch"], 1024)
            refused = wi.transition("SV_ISSUE_OPEN", nativize_issue(ISSUES[0], hb_epoch="3_3"), hb_epoch=EPOCH)
            rc2 = wi.record(refused, None, hb_epoch=EPOCH, append=lambda *a, **k: emit.append(*a, store=store, **k))
            self.assertEqual(rc2["evidence"]["failure_code"], "HB_EPOCH_INVALID")
            self.assertEqual(rc2["previous_receipt_sha256"], rc["receipt_sha256"])
            with self.assertRaises(wi.Refusal):
                wi.record(out, None, hb_epoch=None, append=lambda *a, **k: self.fail("appended without an epoch"))


def al_known_good_change(issue_id):
    path = "resident-runtime/example_transition.py"
    content = [{"path": path, "blob_digest": "sha256:" + "a" * 64, "writer_session": {"session": SESSION, "evidence_class": "DECLARED"}}]
    digest = wi.change_digest({"target_repository": "StegVerse-Labs/.github", "base_ref": dict(BASE), "content": content})
    checks, _ = wi.required_for([path])
    ch = {"schema": wi.CHANGE_SCHEMA, "record_mode": "NATIVE", "target_repository": "StegVerse-Labs/.github", "resolves": [issue_id],
          "owning_goal": "StegVerse-org/.github#163", "declared_session": SESSION, "base_ref": dict(BASE), "head": {"change_digest": digest},
          "content": content, "touched_paths": [path], "lifecycle_state": "PROPOSED",
          "required_checks_ref": {"file": "data/sv-work-items/required-checks.json", "blob_sha": "WORKTREE", "row_id": "SV-CHANGE-REQUIRED-CHECKS-001"},
          "validation_receipts": [fx.ledger_receipt(c, digest) for c in checks],
          "signoffs": [], "hb_epoch": EPOCH}
    return reseal_change(ch)


class CorpusTests(unittest.TestCase):
    CLASSES = jsonl("data/admission-scenarios/classes.jsonl")
    SCEN = jsonl("data/admission-scenarios/corpus.jsonl")

    def test_seed_corpus_loads_and_covers_seed_fixtures(self):
        latest = al.latest_classes(self.CLASSES)
        self.assertEqual(len(latest), 10)
        origins = json.dumps([c["provenance"] for c in latest.values()])
        for ref in ("#3241", "#3244", "#3245", "SDK#533", "SDK#546", "TVC#526", "#3246", ".github#189"):
            self.assertIn(ref, origins)
        self.assertEqual(al.covered_kinds(latest), ["ledger_writer", "registry", "schema", "transition", "workflow"])
        for s in self.SCEN:
            al.verify_line(s, "scenario_sha256", "t")
            self.assertIn(s["scenario_class"], latest)
            out = wi.admit(s["observed_inputs"])
            self.assertEqual((out["disposition"], out.get("failure_code")), (s["expected_disposition"], s["expected_failure_code"]), s["scenario_id"])

    def test_same_class_rule_merges_3245_and_sdk533(self):
        c = al.latest_classes(self.CLASSES)["ASC-BRANCH_WRITER_IS_BRANCH_OWNER@transition"]
        self.assertEqual(len(c["provenance"]["origin_scenarios"]), 2)

    def _cls(self, pred, surface, **kw):
        return al.generalize({"failed_predicate": pred}, surface=surface, origin_scenarios=["test"], rule_refs=[fx.REFS["ST019"]],
                             declared_by_session=SESSION, harvest_receipt_ref=None, hb_epoch=EPOCH, **kw)

    def test_class_that_never_fires_is_denied(self):
        cls = self._cls("REQUIRED_SIGNOFF_RECORDED", "transition")   # transitions require no sign-off, so it cannot fire
        gen = al.generate(cls, fx.known_good(fx.SURFACE_PATH["transition"]), hb_epoch=EPOCH)
        out = al.corpus_append([], [], cls, gen, hb_epoch=EPOCH)
        self.assertEqual((out["disposition"], out["failure_code"]), ("DENY", "CLASS_NEVER_FIRES"))

    def test_class_refusing_known_good_is_denied(self):
        cls = self._cls("BASE_IS_CURRENT", "transition")
        gen = al.generate(cls, fx.known_good(fx.SURFACE_PATH["transition"]), hb_epoch=EPOCH)
        bad_good = fx.known_good(fx.SURFACE_PATH["transition"]); bad_good["validation_receipts"] = []
        out = al.corpus_append([], [], cls, gen, hb_epoch=EPOCH, known_good=[bad_good])
        self.assertEqual((out["disposition"], out["failure_code"]), ("DENY", "CLASS_REFUSES_KNOWN_GOOD"))
        strict = lambda obs, **k: (_ for _ in ()).throw(wi._fail("X", "Y", "z", "t"))
        out = al.corpus_append([], [], cls, gen, hb_epoch=EPOCH, evaluator=strict)
        self.assertEqual(out["failure_code"], "CLASS_NEVER_FIRES")

    def test_axis_without_negative_and_missing_control(self):
        cls = self._cls("BASE_IS_CURRENT", "transition")
        gen = al.generate(cls, fx.known_good(fx.SURFACE_PATH["transition"]), hb_epoch=EPOCH)
        self.assertEqual(al.corpus_append([], [], cls, gen[:-1], hb_epoch=EPOCH)["failure_code"], "CLASS_AXIS_WITHOUT_NEGATIVE")
        self.assertEqual(al.corpus_append([], [], cls, gen[1:], hb_epoch=EPOCH)["failure_code"], "CLASS_POSITIVE_CONTROL_ABSENT")

    def test_append_faults_fail_closed(self):
        cls = self._cls("BASE_IS_CURRENT", "transition")
        gen = al.generate(cls, fx.known_good(fx.SURFACE_PATH["transition"]), hb_epoch=EPOCH)
        self.assertEqual(al.corpus_append([], [], cls, gen, hb_epoch=None)["failure_code"], "HB_EPOCH_NOT_SUPPLIED")
        self.assertEqual(al.corpus_append([], [], dict(cls, class_sha256="sha256:" + "0" * 64), gen, hb_epoch=EPOCH)["failure_code"],
                         "CORPUS_LINE_DIGEST_MISMATCH")
        noprov = wi.seal({**{k: v for k, v in cls.items() if k != "class_sha256"}, "provenance": {}}, "class_sha256")
        self.assertEqual(al.corpus_append([], [], noprov, gen, hb_epoch=EPOCH)["failure_code"], "CLASS_PROVENANCE_ABSENT")
        orphan = [wi.seal({**{k: v for k, v in s.items() if k != "scenario_sha256"}, "scenario_class": "ASC-UNKNOWN@transition"}, "scenario_sha256") for s in gen]
        self.assertEqual(al.corpus_append([], [], cls, orphan, hb_epoch=EPOCH)["failure_code"], "SCENARIO_CLASS_UNKNOWN")
        unbound = wi.seal({**{k: v for k, v in gen[0].items() if k != "scenario_sha256"}, "hb_epoch": "+33"}, "scenario_sha256")
        self.assertEqual(al.corpus_append([], [], cls, [unbound] + gen[1:], hb_epoch=EPOCH)["failure_code"], "HB_EPOCH_INVALID")
        fresh = self._cls("BASE_IS_CURRENT", "workflow")
        fgen = al.generate(fresh, fx.known_good(fx.SURFACE_PATH["workflow"]), hb_epoch=EPOCH)
        self.assertEqual(al.corpus_append(self.CLASSES, self.SCEN, fresh, fgen, hb_epoch=EPOCH)["disposition"], "ALLOW")
        dup = al.corpus_append(self.CLASSES, self.SCEN, self._cls("BASE_IS_CURRENT", "workflow"), [self.SCEN[0]], hb_epoch=EPOCH)
        self.assertEqual(dup["failure_code"], "SCENARIO_ID_EXISTS")

    def test_supersede_chain(self):
        v1 = self._cls("BASE_IS_CURRENT", "transition")
        v2 = self._cls("BASE_IS_CURRENT", "transition", class_version=2, supersedes=v1["class_sha256"])
        self.assertEqual(al.latest_classes([v1, v2])["ASC-BASE_IS_CURRENT@transition"]["class_version"], 2)
        broken = self._cls("BASE_IS_CURRENT", "transition", class_version=2, supersedes="sha256:" + "0" * 64)
        fork = self._cls("BASE_IS_CURRENT", "workflow"); fork2 = dict(fork)
        for lines, want in (([v1, broken], "CLASS_SUPERSEDE_CHAIN_BROKEN"), ([v1, v1], "CLASS_SUPERSEDE_CHAIN_FORKED"),
                            ([v2], "CLASS_SUPERSEDE_CHAIN_BROKEN"), ([fork, fork2], "CLASS_SUPERSEDE_CHAIN_FORKED")):
            with self.assertRaises(wi.Refusal) as cm:
                al.latest_classes(lines)
            self.assertEqual(cm.exception.record["failure_code"], want)
        same = self._cls("BASE_IS_CURRENT", "transition", class_version=2, supersedes=v1["class_sha256"])
        gen = al.generate(same, fx.known_good(fx.SURFACE_PATH["transition"]), hb_epoch=EPOCH)
        self.assertEqual(al.corpus_append([v1], [], same, gen, hb_epoch=EPOCH)["failure_code"], "CLASS_VERSION_UNCHANGED")

    def test_undeclared_predicate_fails_closed(self):
        with self.assertRaises(wi.Refusal) as cm:
            self._cls("SOME_NEW_PREDICATE", "transition")
        self.assertEqual(cm.exception.record["failure_code"], "PREDICATE_BINDING_UNDECLARED")

    def test_harvest_and_miss_feedback(self):
        cands = al.harvest(ISSUES + [{"evidence": {"disposition": "ALLOW"}}, {"evidence": {"disposition": "DENY", "failure_code": "BASE_STALE",
                                                                                              "failed_predicate": "BASE_IS_CURRENT"}, "receipt_sha256": "sha256:" + "9" * 64}])
        self.assertEqual(len(cands), len(ISSUES) + 1)
        self.assertEqual(cands, al.harvest(list(reversed(ISSUES)) + [{"evidence": {"disposition": "DENY", "failure_code": "BASE_STALE",
                                                                                     "failed_predicate": "BASE_IS_CURRENT"}, "receipt_sha256": "sha256:" + "9" * 64}]))
        applied = dict(al_known_good_change(ISSUES[0]["issue_id"]), lifecycle_state="APPLIED")
        miss = al.admission_miss(applied, admission_receipt_ref="receipt:admit", correcting_ref="receipt:revert", miss_kind="REVERT",
                                 predicate_gap="BASE_IS_CURRENT", class_ids=["ASC-BASE_IS_CURRENT@transition"], hb_epoch=EPOCH)
        self.assertEqual(al.miss_counts([miss, miss]), {"ASC-BASE_IS_CURRENT@transition": 2})
        self.assertEqual(al.harvest([miss])[0]["origin"], "ADMISSION_MISS")
        with self.assertRaises(wi.Refusal):
            al.admission_miss(dict(applied, lifecycle_state="ADMITTED"), admission_receipt_ref="r", correcting_ref="c", miss_kind="REVERT",
                              predicate_gap=None, class_ids=[], hb_epoch=EPOCH)
        with self.assertRaises(wi.Refusal):
            al.miss_counts([dict(miss, class_ids=["other"])])


if __name__ == "__main__":
    unittest.main()
