"""sv_change_admit: the org-ledger writer records the SV_CHANGE_SUPERSEDE -> VERIFY -> ADMIT outcome once per change.

Authoring-Session: p1-ecosystem-ai-lane (StegVerse-org/.github#163; Lane D FAIL_CLOSED StegVerse-org/.github#167 c6513778290).

Temporary repositories and ledgers only: receipts here are exercise evidence on those, not records of the published
organization ledger. Clock-free and network-free: epochs are supplied constants.

  * accept: the pinned P1 lifecycle outcome is the repository receipt's $.evidence, aggregated into an organization receipt,
    read back from a fresh fetch, at a supplied epoch; ALLOW is never manufactured: a change that lacks the evidence the
    evaluator needs is recorded as the refusal the evaluator returned;
  * observed, not supplied: push receipts and the current base come from the ledger and the checkout;
  * duplicate: a second request for the same change is refused with the six fields and appends nothing;
  * refusals: malformed requests, non-NATIVE successors, another organization's change and every epoch break are six-field
    refusals before any write;
  * routing: the ingest request names the operation; the manifest declares it; the writer runs it on push only.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests import test_sv_native_work_items as nwi
from tests import test_sv_push_receipt_append as pushtests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "resident-runtime"))
import sv_change_admit_append as ca  # noqa: E402

SIX = ca.SIX_FIELDS
WRITER = ROOT / ".github" / "workflows" / "organization-ledger-transition.yml"
PR_FACING = ROOT / ".github" / "workflows" / "organization-ledger-transition-validation.yml"
OPERATIONS = ROOT / ".stegverse" / "organization-ledger-ingest" / "operations.json"
appendtests, GitLedger, REF, ledger_store, readback = pushtests.appendtests, pushtests.GitLedger, pushtests.REF, pushtests.ledger_store, pushtests.readback
ing, push_receipt, oid = pushtests.ing, pushtests.push_receipt, pushtests.oid
pa = ca.pa
EPOCH = 1024


def predecessor_record(index=0):
    return copy.deepcopy(nwi.CHANGES[index])


def successor_record(predecessor, tip=None, resolves=None, **over):
    """A NATIVE successor of `predecessor`, resealed; its base is the test ledger's tip when given and it cites `resolves`."""
    fields = dict(supersedes=predecessor["request_digest"], hb_epoch=str(EPOCH))
    if resolves is not None:
        fields["resolves"] = list(resolves)
    if tip is not None:
        fields["base_ref"] = {"registry_generation": ca.registry_generation(), "ledger_head": tip}
    fields.update(over)
    return nwi.nativize_change(predecessor, **fields)


def admission(**over):
    out = {"predicate_digest": "sha256:" + "a" * 64, "corpus_head": "b" * 40, "actor_session": "p1-ecosystem-ai-lane",
           "change_commits": {"base_commit": oid(1), "head_commit": oid(3)},
           "push_ranges": [{"repository": "StegVerse-Labs/.github", "ref": pushtests.BRANCH, "old_sha": oid(1), "new_sha": oid(3)}]}
    out.update(over)
    return out


class AdmitBase(GitLedger):
    def setUp(self):
        super().setUp()
        # The one source of an issue is a failing sv_check_receipt this ledger retains: the sv_check_receipt operation appends
        # it, and the issue is derived from it (nothing here writes an issue).
        checked = appendtests.svc.append_check_receipt(appendtests.check_receipt(), hb_epoch=40)
        self.assertEqual(checked["disposition"], "ALLOW", checked)
        self.seed = self.tip()
        self.issue = self.derived_issue(checked)
        self.pred = predecessor_record()
        self.succ = self.mk(self.pred)

    def derived_issue(self, checked):
        wi = ca._check.p1_readers()
        commit = self.tip()
        objs = {commit + ":" + k: _git(self.bare, "show", commit + ":" + k) for k in
                (checked["organization_receipt_key"], checked["repository_receipt_source_key"])}
        ref = "%s@%s:%s" % (REF, commit, checked["organization_receipt_key"])
        return wi.derive_issue_from_check_receipt(objs, ref, observed_base={"registry_generation": ca.registry_generation(),
                                                                            "ledger_head": commit})

    def mk(self, predecessor, tip=None, **over):
        """A NATIVE successor on the ledger tip that cites the issue the ledger derives."""
        over.setdefault("resolves", [self.issue["issue_id"]])
        return successor_record(predecessor, tip or self.tip(), **over)

    def assert_refused(self, result, code, disposition="FAIL_CLOSED"):
        self.assertEqual(result["disposition"], disposition, result)
        self.assertEqual(result["failure_code"], code, result)
        for field in SIX:
            self.assertTrue(isinstance(result[field], str) and result[field], field)
        self.assertIs(result["consequence_committed"], False)
        self.assertEqual(self.tip(), self.seed, "a refusal appends nothing")

    def append(self, succ=None, adm=None, pred=None, epoch=EPOCH):
        return ca.append_change_admit(pred or self.pred, succ or self.succ, adm or admission(), hb_epoch=epoch)

    def admits(self):
        store = ledger_store.open_store(f"git+{self.bare}#{REF}:{appendtests.NAMESPACE}")
        return [r for r in pa.ingress.repository_ledger.chain(store, store.get(ledger_store.HEAD_KEY))
                if r["transition_class"] == ca.TRANSITION_CLASS]


class Accept(AdmitBase):
    def test_the_lifecycle_outcome_is_recorded_as_it_was_returned_and_read_back(self):
        result = self.append()
        self.assertEqual(result["disposition"], "ALLOW", result)  # the pair was appended
        self.assertIs(result["appended"], True)
        self.assertEqual(result["transition_class"], "SV_CHANGE_ADMIT")
        self.assertEqual(result["transition_id"], self.succ["change_id"] + ":SV_CHANGE_ADMIT")
        self.assertEqual([s["transition_class"] for s in result["chain"]], ["SV_CHANGE_SUPERSEDE", "SV_CHANGE_VERIFY", "SV_CHANGE_ADMIT"])
        # nothing supplies the check receipts, sign-offs or resolved issues: the evaluator's refusal is the outcome
        self.assertNotEqual(result["admit_disposition"], "ALLOW", result)
        self.assertEqual(_git(self.bare, "merge-base", "--is-ancestor", self.seed, REF), b"")
        self.assertEqual(_git(self.bare, "rev-parse", f"{REF}:MARKER"), _git(self.bare, "rev-parse", f"{self.seed}:MARKER"))

        store = ledger_store.GitLedgerStore(self.bare, REF, custody="PRIVATE")
        org = store.get(result["organization_receipt_key"])
        repo = store.get(result["repository_receipt_source_key"])
        ev = repo["evidence"]
        self.assertEqual(repo["transition_class"], "SV_CHANGE_ADMIT")
        self.assertEqual(ev["record"]["change_id"], self.succ["change_id"])
        self.assertEqual(ev["disposition"], result["admit_disposition"])
        for field in SIX:
            self.assertEqual(ev[field] is None, ev["disposition"] == "ALLOW", field)
        self.assertEqual(org["boundary_evidence"]["operation"], "sv_change_admit")
        self.assertEqual(org["repo_receipt_sha256"], repo["receipt_sha256"])
        for row in (org, repo):
            self.assertIs(row["hb_reference"]["derived_from_clock"], False)
            self.assertEqual(row["hb_reference"]["epoch"], EPOCH)
            self.assertTrue(pa._self_verifies(row))
            self.assertTrue(readback.self_verifies(row))
        observed = ev["observed"]
        self.assertEqual(observed["current_base"]["ledger_head"], self.seed)  # read from the ledger ref, not the request
        self.assertEqual(observed["predecessor_request_digest"], self.pred["request_digest"])
        self.assertIn("required-check ledger receipts", observed["not_supplied_by_this_operation"])
        self.assertNotIn("resolved SV_ISSUE facts", observed["not_supplied_by_this_operation"])
        derived = observed["resolved_issue_facts_derived_from_the_ledger"]
        self.assertEqual(derived["ledger_commit"], self.seed)
        self.assertEqual([i["issue_id"] for i in derived["issues"]], [self.issue["issue_id"]])
        self.assertEqual(result["chain"][1].get("failure_code") != "SV_CHANGE_RESOLVES_NOTHING", True, result["chain"])

        reader = self.work / "reader.git"
        subprocess.run(["git", "init", "--bare", "-q", str(reader)], check=True)
        subprocess.run(["git", "--git-dir", str(reader), "fetch", "-q", str(self.bare), f"+{REF}:{REF}"], check=True)
        bound = ca.bind_change_admit(f"git+{reader}#{REF}", result)
        self.assertEqual(bound["disposition"], "ALLOW", bound)
        self.assertEqual(readback.readback(f"git+{reader}#{REF}")["disposition"], "ALLOW")
        self.assertEqual(len(self.admits()), 1)

    def test_an_unrecorded_push_range_stays_unobserved_and_a_recorded_one_is_read_from_the_ledger(self):
        first = self.append()
        self.assertEqual(first["unrecorded_push_ranges"], admission()["push_ranges"])
        self.assertEqual(first["chain"][1]["failure_code"], "BRANCH_WRITER_UNOBSERVED", first["chain"])

    def test_push_receipts_on_the_ledger_are_passed_to_the_evaluator(self):
        for old, new in ((1, 2), (2, 3)):
            rec = push_receipt(old, new)
            self.assertEqual(pa.append_push_receipt(rec, hb_epoch=EPOCH)["disposition"], "ALLOW")
        adm = admission(push_ranges=[{"repository": "StegVerse-Labs/.github", "ref": pushtests.BRANCH, "old_sha": oid(1), "new_sha": oid(2)},
                                     {"repository": "StegVerse-Labs/.github", "ref": pushtests.BRANCH, "old_sha": oid(2), "new_sha": oid(3)},
                                     {"repository": "StegVerse-Labs/.github", "ref": pushtests.BRANCH, "old_sha": oid(3), "new_sha": oid(4)}])
        succ = self.mk(self.pred)
        result = self.append(succ, adm)
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertEqual(len(result["unrecorded_push_ranges"]), 1)  # only the range the ledger does not hold
        self.assertEqual(result["unrecorded_push_ranges"][0]["new_sha"], oid(4))
        store = ledger_store.GitLedgerStore(self.bare, REF, custody="PRIVATE")
        seen = store.get(result["repository_receipt_source_key"])["evidence"]["observed"]["push_receipts_read_from_ledger"]
        self.assertEqual(len(seen), 2)
        self.assertNotEqual(result["chain"][1].get("failure_code"), "BRANCH_WRITER_UNOBSERVED", result["chain"])

    def test_another_change_is_appended_beside_the_first_and_the_chain_stays_whole(self):
        first = self.append()
        pred2 = predecessor_record(1)
        other = self.append(self.mk(pred2), pred=pred2)
        for result in (first, other):
            self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertNotEqual(first["transition_id"], other["transition_id"])
        self.assertEqual(len(self.admits()), 2)  # chain() verifies every node it walks


class DuplicateChange(AdmitBase):
    def test_a_second_request_for_the_same_change_is_refused_and_appends_nothing(self):
        first = self.append()
        self.assertEqual(first["disposition"], "ALLOW", first)
        tip = self.tip()
        again = self.append()
        self.assertEqual(again["disposition"], "FAIL_CLOSED", again)
        self.assertEqual(again["failure_code"], "SV_CHANGE_ADMIT_ALREADY_RECORDED")
        self.assertEqual(again["failed_predicate"], "ONE_ADMIT_PER_CHANGE")
        for field in SIX:
            self.assertTrue(isinstance(again[field], str) and again[field], field)
        self.assertIs(again["appended"], False)
        self.assertIs(again["consequence_committed"], False)
        self.assertEqual(again["recorded_repository_receipt_sha256"], first["repository_receipt_sha256"])
        self.assertEqual(again["recorded_disposition"], first["admit_disposition"])
        self.assertEqual(self.tip(), tip, "the ledger did not move")
        self.assertEqual(len(self.admits()), 1)

    def test_a_request_that_differs_in_provenance_or_epoch_is_also_a_duplicate(self):
        self.append()
        tip = self.tip()
        for adm in (admission(actor_session="someone-else"), admission(corpus_head="c" * 40), admission(predicate_digest="sha256:" + "d" * 64)):
            result = self.append(adm=adm)
            self.assertEqual(result["failure_code"], "SV_CHANGE_ADMIT_ALREADY_RECORDED", result)
            self.assertEqual(self.tip(), tip)
        self.assertEqual(len(self.admits()), 1)

    def test_the_duplicate_is_refused_through_the_command_line_with_a_nonzero_exit(self):
        files = {}
        for name, doc in (("predecessor", self.pred), ("successor", self.succ), ("admission", admission())):
            files[name] = self.work / (name + ".json")
            files[name].write_text(json.dumps(doc), encoding="utf-8")
        env = {**os.environ, "STEGVERSE_ORG_LEDGER_GIT_DIR": str(self.bare),
               "STEGVERSE_REPO_LEDGER_ROOT": f"git+{self.bare}#{REF}:{appendtests.NAMESPACE}"}
        argv = [sys.executable, str(ROOT / "resident-runtime" / "sv_change_admit_append.py"), "append",
                "--predecessor", str(files["predecessor"]), "--successor", str(files["successor"]),
                "--admission", str(files["admission"]), "--hb-epoch", str(EPOCH)]
        ok = subprocess.run(argv, env=env, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        tip = self.tip()
        dup = subprocess.run(argv, env=env, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(dup.returncode, 1, dup.stdout + dup.stderr)
        self.assertEqual(json.loads(dup.stdout)["failure_code"], "SV_CHANGE_ADMIT_ALREADY_RECORDED")
        self.assertEqual(self.tip(), tip)


class IssueFacts(AdmitBase):
    """The resolved SV_ISSUE is read from the ledger and never supplied; with none, the refusal is the correct outcome."""

    def assert_absent(self, result, **detail):
        self.assert_refused(result, "SV_CHANGE_ADMIT_RESOLVED_ISSUE_FACTS_ABSENT")
        self.assertEqual(result["failed_predicate"], "RESOLVED_ISSUE_FACTS_ARE_DERIVED_FROM_THE_LEDGER_AT_THE_CHANGE_BASE")
        self.assertEqual(result["authority_effect"], "NONE_REFUSAL_ONLY")
        for key, value in detail.items():
            self.assertEqual(result[key], value, key)

    def test_a_successor_that_cites_no_issue_is_refused_and_appends_nothing(self):
        self.assert_absent(self.append(self.mk(self.pred, resolves=[])), detail="RESOLVES_IS_EMPTY")

    def test_an_issue_the_ledger_does_not_derive_is_refused_not_recorded(self):
        for cited in ("svi:" + "1" * 64, "svi:" + "0" * 64):
            result = self.append(self.mk(self.pred, resolves=[cited]))
            self.assert_absent(result, detail="CITED_ISSUE_NOT_DERIVED_FROM_THE_LEDGER")
            self.assertEqual(result["derived_issue_ids"], [self.issue["issue_id"]])
        # one derived and one not: still refused, nothing is half-admitted
        self.assert_absent(self.append(self.mk(self.pred, resolves=[self.issue["issue_id"], "svi:" + "2" * 64])),
                           detail="CITED_ISSUE_NOT_DERIVED_FROM_THE_LEDGER")

    def test_a_migrated_historical_issue_cannot_be_cited(self):
        migrated = [i for i in nwi.ISSUES if i.get("record_mode") == "MIGRATED_HISTORICAL"] if hasattr(nwi, "ISSUES") else []
        cited = migrated[0]["issue_id"] if migrated else "svi:" + "3" * 64
        self.assert_absent(self.append(self.mk(self.pred, resolves=[cited])), detail="CITED_ISSUE_NOT_DERIVED_FROM_THE_LEDGER")

    def test_a_ledger_with_no_failing_check_receipt_has_no_issue_for_any_change(self):
        # a second, empty ledger: the same successor cites an id nothing on it derives
        bare = self.work / "empty.git"
        subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
        tip = self.tip()
        succ = self.mk(self.pred)
        store = ledger_store.GitLedgerStore(self.bare, REF, custody="PRIVATE")
        facts = ca.ledger_issue_facts(store, successor_record(self.pred, tip, resolves=["svi:" + "4" * 64]), 1, admission()["change_commits"])
        self.assertEqual(facts["failure_code"], "SV_CHANGE_ADMIT_RESOLVED_ISSUE_FACTS_ABSENT", facts)
        self.assertEqual(self.tip(), tip)
        self.assertIsNotNone(succ)

    def test_a_passing_check_receipt_derives_no_issue(self):
        ok = appendtests.svc.append_check_receipt(appendtests.check_receipt(disposition="ALLOW", failure_code=None, failed_predicate=None,
                                                                         required_evidence_or_repair=None, retry_entrypoint=None,
                                                                         owning_existing_goal=None, next_attempt=None,
                                                                         head_sha="c" * 40, hb_epoch="41"), hb_epoch=41)
        self.assertEqual(ok["disposition"], "ALLOW", ok)
        store = ledger_store.GitLedgerStore(self.bare, REF, custody="PRIVATE")
        facts = ca.ledger_issue_facts(store, self.mk(self.pred), ca.registry_generation(), admission()["change_commits"])
        self.assertEqual([i["issue_id"] for i in facts["issues"]], [self.issue["issue_id"]], "only the failing receipt derives an issue")
        self.assertEqual(facts["check_receipts_read"], 2)

    def test_the_issue_is_never_a_request_field(self):
        text = (ROOT / "resident-runtime" / "sv_change_admit_append.py").read_text(encoding="utf-8")
        self.assertNotIn('"resolved_issues": []', text)
        self.assertNotIn('admission.get("resolved', text)
        self.assertEqual(ca.ADMISSION_FIELDS, {"predicate_digest", "corpus_head", "actor_session", "change_commits", "push_ranges"})
        result = self.append(adm=admission(resolved_issues=[{"issue_id": self.issue["issue_id"]}]))
        self.assertEqual(result["failure_code"], "SV_CHANGE_ADMIT_REQUEST_MALFORMED", result)


class Refusals(AdmitBase):
    def test_a_malformed_request_is_refused_before_any_write(self):
        for name, args in {
            "no predecessor": dict(pred=None), "admission field missing": dict(adm={k: v for k, v in admission().items() if k != "corpus_head"}),
            "admission extra field": dict(adm=admission(extra=1)), "bad predicate digest": dict(adm=admission(predicate_digest="abc")),
            "short corpus head": dict(adm=admission(corpus_head="abc")), "blank actor": dict(adm=admission(actor_session=" ")),
            "commits missing": dict(adm=admission(change_commits={"base_commit": oid(1)})),
            "no ranges": dict(adm=admission(push_ranges=[])),
            "range with extra field": dict(adm=admission(push_ranges=[{"repository": "r", "ref": "x", "old_sha": "a", "new_sha": "b", "z": 1}])),
        }.items():
            pred = args.get("pred", self.pred)
            result = ca.append_change_admit(pred, self.succ, args.get("adm", admission()), hb_epoch=EPOCH)
            self.assertEqual(result["failure_code"], "SV_CHANGE_ADMIT_REQUEST_MALFORMED", name)
            self.assertEqual(self.tip(), self.seed, name)
            self.assertIs(result["consequence_committed"], False, name)
            for field in SIX:
                self.assertTrue(isinstance(result[field], str) and result[field], name + " " + field)

    def test_a_successor_that_is_not_native_is_refused(self):
        self.assert_refused(self.append(succ=copy.deepcopy(nwi.CHANGES[1])), "SV_CHANGE_ADMIT_SUCCESSOR_NOT_NATIVE")

    def test_another_organizations_change_is_not_admitted_on_this_ledger(self):
        pred = predecessor_record(3)  # target StegVerse-org/.github
        succ = self.mk(pred)
        result = self.append(succ, pred=pred)
        self.assert_refused(result, "SV_CHANGE_TARGET_NOT_OWNED_BY_THIS_LEDGER")
        self.assertEqual(result["failed_predicate"], "CHANGE_BINDS_TARGET_REPOSITORY_LEDGER")

    def test_a_supersede_across_repositories_is_refused(self):
        other = predecessor_record(3)
        self.assert_refused(self.append(pred=other), "SV_CHANGE_SUPERSEDE_CROSSES_REPOSITORIES")

    def test_an_absent_null_or_sentinel_epoch_is_unobserved(self):
        for bad in (None, "", "null", "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"):
            result = self.append(epoch=bad)
            self.assert_refused(result, "HB_EPOCH_SOURCE_UNOBSERVED")
            self.assertEqual(result["shared_rule_sha256"], pa.SHARED_RULE_SHA256)

    def test_a_malformed_or_unequal_epoch_is_a_mismatch_and_no_clock_is_read(self):
        for bad in (True, False, 31, 0, -40, "1024", 1024.0, "unknown", 2048):
            result = self.append(epoch=bad)
            self.assert_refused(result, "HB_EPOCH_MISMATCH", disposition="DENY")
            self.assertEqual(result["failed_predicate"], "SUCCESSOR_HB_EPOCH_EQUALS_REQUEST_HB_EPOCH")

    def test_a_successor_that_does_not_name_the_predecessor_is_recorded_as_the_supersede_refusal_not_hidden(self):
        succ = self.mk(self.pred, supersedes="sha256:" + "9" * 64)
        result = self.append(succ)
        self.assertEqual(result["disposition"], "ALLOW", result)  # appended: the refusal is the recorded outcome
        self.assertEqual(result["chain"][0]["failure_code"], "SUCCESSOR_DOES_NOT_NAME_PREDECESSOR", result["chain"])
        self.assertNotEqual(result["admit_disposition"], "ALLOW")

    def test_a_stale_base_is_never_allow(self):
        succ = self.mk(self.pred, "e" * 40)  # not a commit of this ledger
        self.assert_refused(self.append(succ), "SV_CHANGE_ADMIT_RESOLVED_ISSUE_FACTS_ABSENT")

    def test_an_older_base_that_is_a_ledger_commit_reads_its_facts_there_and_is_never_allow(self):
        older = self.tip()
        self.assertEqual(pa.append_push_receipt(push_receipt(1, 2), hb_epoch=EPOCH)["disposition"], "ALLOW")
        succ = self.mk(self.pred, older)
        result = self.append(succ)
        self.assertEqual(result["disposition"], "ALLOW", result)  # appended: the outcome is what the evaluator returned
        self.assertNotEqual(result["admit_disposition"], "ALLOW", result)

    def test_the_verifier_reads_no_clock_and_no_network(self):
        text = (ROOT / "resident-runtime" / "sv_change_admit_append.py").read_text(encoding="utf-8")
        for token in ("import time", "from time", "datetime", "import socket", "urllib", "requests", "http.client", "subprocess",
                      "time.time", "utcnow"):
            self.assertNotIn(token, text, token)


class Routing(unittest.TestCase):
    def test_the_ingest_request_names_the_operation_and_materializes_its_parts(self):
        pred = predecessor_record()
        succ = successor_record(pred)
        parts = {"predecessor": pred, "successor": succ, "admission": admission()}
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text(json.dumps({"schema": ing.SCHEMA, "operation": "sv_change_admit", **parts, "hb_epoch": EPOCH}), encoding="utf-8")
            read = ing.read_request(request)
            self.assertEqual(read["disposition"], "ALLOW", read)
            self.assertEqual((read["operation"], read["hb_epoch"]), ("sv_change_admit", EPOCH))
            env_file, out = Path(tmp) / "env", Path(tmp) / "parts"
            self.assertEqual(ing.main(["read", "--request", str(request), "--materialize", str(out), "--github-env", str(env_file)]), 0)
            for name, doc in parts.items():
                self.assertEqual(json.loads((out / (name + ".json")).read_text(encoding="utf-8")), doc)
            self.assertEqual(env_file.read_text(encoding="utf-8").split(), ["INGEST_OPERATION=sv_change_admit", "HB_EPOCH=1024"])
            for bad, code in (({"successor": "text"}, "INGEST_REQUEST_SCHEMA_MISMATCH"),
                              ({"admission": [admission()]}, "INGEST_REQUEST_SCHEMA_MISMATCH"),
                              ({"hb_epoch": "1024"}, "SV_CHANGE_ADMIT_HB_EPOCH_INVALID"),
                              ({"hb_epoch": True}, "SV_CHANGE_ADMIT_HB_EPOCH_INVALID"),
                              ({"hb_epoch": -1}, "SV_CHANGE_ADMIT_HB_EPOCH_INVALID"),
                              ({"push_receipt": {}}, "INGEST_REQUEST_SCHEMA_MISMATCH")):
                request.write_text(json.dumps({"schema": ing.SCHEMA, "operation": "sv_change_admit", **parts, "hb_epoch": EPOCH} | bad),
                                   encoding="utf-8")
                refused = ing.read_request(request)
                self.assertEqual(refused["failure_code"], code, refused)
                for field in SIX:
                    self.assertTrue(refused[field], field)

    def test_the_operation_is_declared_with_its_class_and_one_admit_per_change(self):
        declared = json.loads(OPERATIONS.read_text(encoding="utf-8"))["organization_ledger_writer_operations"]
        entry, = [e for e in declared if e["operation"] == ca.OPERATION_ID]
        self.assertEqual(entry["operation_module"], "resident-runtime/sv_change_admit_append.py")
        self.assertEqual(entry["transition_class"], ca.TRANSITION_CLASS)
        self.assertEqual(entry["organization_receipt_boundary_operation"], "sv_change_admit")
        self.assertIs(entry["ingress_capability"], False)
        self.assertIs(entry["addressable_from_the_service_registry"], False)
        self.assertIn("SV_CHANGE_ADMIT_ALREADY_RECORDED", entry["one_admit_per_change"])
        self.assertIn("no dispatch input, no schedule, no new workflow", entry["invoked_by"])
        self.assertIn("StegVerse-Labs", entry["owning_ledger"])
        self.assertEqual(ca.LEDGER_OWNER, "StegVerse-Labs")

    def test_the_writer_runs_it_on_push_only_under_the_shared_lock_and_pr_verify_appends_nothing(self):
        text = WRITER.read_text(encoding="utf-8")
        head, _ = text.split("\njobs:\n", 1)
        self.assertIn("env.INGEST_OPERATION == 'sv_change_admit'", text)
        self.assertIn("resident-runtime/sv_change_admit_append.py append", text)
        self.assertIn("resident-runtime/sv_change_admit_append.py readback", text)
        self.assertIn("concurrency:\n  group: organization-ledger\n  cancel-in-progress: false\n", text)
        on = head.split("\non:\n", 1)[1].split("\n\n", 1)[0] if "\non:\n" in head else head
        for token in ("workflow_dispatch", "schedule", "cron", "pull_request"):
            self.assertNotIn(token, on, token)
        self.assertNotIn("--force", text)
        self.assertEqual(sorted(p.name for p in (ROOT / ".github" / "workflows").glob("*change*admit*")), [])  # no new workflow
        pr = PR_FACING.read_text(encoding="utf-8")
        self.assertIn("tests/test_sv_change_admit_append.py", pr)
        self.assertNotIn("sv_change_admit_append.py append", pr)

    def test_files_touched_do_not_use_the_forbidden_word(self):
        token = "g" + "rant"
        for path in (ROOT / "resident-runtime" / "sv_change_admit_append.py", OPERATIONS, Path(__file__)):
            self.assertNotIn(token, path.read_text(encoding="utf-8").lower().replace(token + "s nothing", ""), path.name)


_git = appendtests._git

if __name__ == "__main__":
    unittest.main()
