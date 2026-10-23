"""Class B owner-assignment transition: ALLOW only on a read-back receipted lineage chain."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import owner_assignment_transition as T  # noqa: E402

REPO = "Example-Org/example"
GOAL = "EXAMPLE-GOAL-001"
OTHER = "OTHER-GOAL-002"
SIX = T.SIX
CLOSURE = os.path.join(ROOT, "control", "owner-assignment", "GITHUB-UNIVERSAL-GOVERNANCE-PRODUCT-001-closure")


def git(cwd, *args, git_dir=None):
    base = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false"]
    if git_dir:
        base += ["--git-dir", git_dir]
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": cwd, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z"}
    return subprocess.run(base + list(args), cwd=cwd, check=True, capture_output=True, env=env).stdout.decode().strip()


class Fixture:
    def __init__(self, tmp):
        self.tmp = tmp
        self.src = os.path.join(tmp, "src")
        os.makedirs(os.path.join(self.src, "pkg"))
        git(self.src, "init", "-q")
        with open(os.path.join(self.src, "pkg", "f.py"), "w") as fh:
            fh.write("A = 1\n")
        git(self.src, "add", ".")
        git(self.src, "commit", "-q", "-m", "add")
        self.intro = git(self.src, "rev-parse", "HEAD")
        with open(os.path.join(self.src, "pkg", "f.py"), "a") as fh:
            fh.write("B = 2\n")
        git(self.src, "commit", "-q", "-am", "modify")
        self.mod = git(self.src, "rev-parse", "HEAD")
        with open(os.path.join(self.src, "pkg", "f.py"), "rb") as fh:
            self.digest = "sha256:" + hashlib.sha256(fh.read()).hexdigest()
        self.registry = {"tasks": [{"task_id": GOAL, "targets": {"repositories": [REPO]}},
                                   {"task_id": "NARROW-001", "targets": {"repositories": ["Else/where"]}}]}
        self.records = os.path.join(tmp, "records")
        os.makedirs(self.records)

    def request(self, goal=GOAL, digest=None, names_goal=None, **entry):
        lin = {"names_goal": names_goal} if names_goal else {}
        return {"schema": T.REQUEST_SCHEMA, "request_id": "R-1", "source_repository": REPO,
                "pinned_commit": self.mod, "candidate_goal": goal,
                "files": [{"path": "pkg/f.py", "sha256": digest or self.digest, "observed_non_receipted_lineage": lin,
                           **entry}]}

    def sources(self, texts):
        exports = []
        for n, body in texts.items():
            p = os.path.join(self.tmp, f"x{n}.json")
            with open(p, "w") as fh:
                json.dump({"number": n, "body": body, "comments": [
                    {"url": f"https://x/{n}#issuecomment-{n}0", "body": "see " + body}]}, fh)
            exports.append(p)
        return T.sources_snapshot(exports, REPO)

    def history(self, req):
        return T.history(os.path.join(self.src, ".git"), REPO, req["pinned_commit"], [f["path"] for f in req["files"]])

    def ledger(self, evidences, tamper=False, orphan=None):
        """Bare copy at <tmp>/ledgers/Example-Org.git with a chained receipt list."""
        work = os.path.join(self.tmp, "lw")
        os.makedirs(os.path.join(work, "receipts"), exist_ok=True)
        prev = None
        for ev in evidences:
            body = {"schema": "stegverse.repo-transition-receipt/v1", "evidence": ev, "previous_receipt_sha256": prev}
            r = {**body, "receipt_sha256": T.sha(body)}
            if tamper:
                r["evidence"] = {**ev, "tampered": True}
            with open(os.path.join(work, "receipts", r["receipt_sha256"].split(":")[1] + ".json"), "w") as fh:
                json.dump(r, fh)
            prev = r["receipt_sha256"]
        if orphan is not None:
            body = {"schema": "x", "evidence": orphan, "previous_receipt_sha256": None}
            r = {**body, "receipt_sha256": T.sha(body)}
            with open(os.path.join(work, "receipts", r["receipt_sha256"].split(":")[1] + ".json"), "w") as fh:
                json.dump(r, fh)
        with open(os.path.join(work, "HEAD.json"), "w") as fh:
            json.dump({"receipt_sha256": prev}, fh)
        git(work, "init", "-q")
        git(work, "add", ".")
        git(work, "commit", "-q", "-m", "ledger")
        copies = os.path.join(self.tmp, "ledgers")
        os.makedirs(copies, exist_ok=True)
        bare = os.path.join(copies, "Example-Org.git")
        git(self.tmp, "clone", "-q", "--bare", work, bare)
        git(self.tmp, "update-ref", T.LEDGER_REF, "HEAD", git_dir=bare)
        return copies

    def run(self, req, copies=None, history=None, sources=None):
        hist = history or self.history(req)
        return T.evaluate(req, hist, T.read_ledgers(copies), self.registry, self.records, "sha256:req", "sha256:reg",
                          sources)


def landed(commit):
    return {"repository": REPO, "merge_commit": commit}


class OwnerAssignmentTransitionTests(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.f = Fixture(self._t.name)

    def tearDown(self):
        self._t.cleanup()

    def only(self, run):
        self.assertEqual(len(run["records"]), 1)
        return run["records"][0]

    def assert_six(self, rec, predicate):
        self.assertEqual(rec["disposition"], "FAIL_CLOSED")
        for k in SIX:
            self.assertTrue(rec.get(k), k)
        self.assertEqual(rec["failure_code"], "LINEAGE_INSUFFICIENT")
        self.assertIn(predicate, [m["failed_predicate"] for m in rec["unmet_predicates"]])

    def test_allow_only_with_fully_receipted_lineage(self):
        copies = self.f.ledger([landed(self.f.intro), {**landed(self.f.intro), "task_id": GOAL}, landed(self.f.mod)])
        rec = self.only(self.f.run(self.f.request(), copies))
        self.assertEqual(rec["disposition"], "ALLOW")
        self.assertEqual(rec["assigned_owner"], GOAL)
        self.assertEqual(rec["record_kind"], "OWNER_ASSIGNMENT")
        self.assertNotIn("custody", rec)
        self.assertNotIn("failure_code", rec)
        links = rec["lineage_chain"]["links_oldest_first"]
        self.assertEqual([l["commit"] for l in links], [self.f.intro, self.f.mod])
        self.assertTrue(links[0]["goal_binding_receipts"])

    def test_unreceipted_modification_fails_closed(self):
        copies = self.f.ledger([{**landed(self.f.intro), "task_id": GOAL}])
        rec = self.only(self.f.run(self.f.request(), copies))
        self.assert_six(rec, "EVERY_HISTORY_COMMIT_HAS_A_READ_BACK_LANDING_RECEIPT")
        self.assertIn(self.f.mod, rec["required_evidence_or_repair"])

    def test_receipt_binding_another_goal_does_not_assign(self):
        copies = self.f.ledger([{**landed(self.f.intro), "task_id": OTHER}, landed(self.f.mod)])
        rec = self.only(self.f.run(self.f.request(names_goal=OTHER), copies))
        self.assert_six(rec, "INTRODUCING_COMMIT_BOUND_TO_CANDIDATE_GOAL_BY_RECEIPT")
        self.assertIn(OTHER, rec["contradicting_observation"])

    def test_off_chain_receipt_is_not_read_back(self):
        copies = self.f.ledger([landed(self.f.mod)], orphan={**landed(self.f.intro), "task_id": GOAL})
        rec = self.only(self.f.run(self.f.request(), copies))
        self.assert_six(rec, "INTRODUCING_COMMIT_BOUND_TO_CANDIDATE_GOAL_BY_RECEIPT")

    def test_tampered_receipt_breaks_chain_and_fails_closed(self):
        copies = self.f.ledger([landed(self.f.intro), {**landed(self.f.intro), "task_id": GOAL}, landed(self.f.mod)], tamper=True)
        led = T.read_ledgers(copies)
        self.assertTrue(led["copies"][0]["chains"][0]["chain_break"].startswith("receipt_does_not_hash_to_address"))
        rec = self.only(self.f.run(self.f.request(), copies))
        self.assert_six(rec, "EVERY_HISTORY_COMMIT_HAS_A_READ_BACK_LANDING_RECEIPT")

    def test_goal_targets_must_cover_repository(self):
        copies = self.f.ledger([{**landed(self.f.intro), "task_id": "NARROW-001"}, landed(self.f.mod)])
        rec = self.only(self.f.run(self.f.request(goal="NARROW-001"), copies))
        self.assert_six(rec, "GOAL_TARGETS_COVER_FILE_REPOSITORY")
        self.assertEqual(rec["failed_predicate"], "GOAL_TARGETS_COVER_FILE_REPOSITORY")

    def test_unregistered_goal_fails_closed(self):
        rec = self.only(self.f.run(self.f.request(goal="NOT-REGISTERED-001")))
        self.assert_six(rec, "CANDIDATE_GOAL_REGISTERED")

    def test_declared_sha256_must_match_pinned_bytes(self):
        rec = self.only(self.f.run(self.f.request(digest="sha256:" + "0" * 64)))
        self.assert_six(rec, "FILE_BYTES_AT_PIN_MATCH_DECLARED_SHA256")

    def test_no_ledger_copies_never_allows_and_is_deterministic(self):
        req = self.f.request()
        a, b = self.f.run(req), self.f.run(req)
        self.assertEqual(T.canon(a), T.canon(b))
        self.assert_six(self.only(a), "INTRODUCING_COMMIT_BOUND_TO_CANDIDATE_GOAL_BY_RECEIPT")
        self.assertEqual(a["tally"], {"FAIL_CLOSED": 1})
        self.assertFalse(a["llm_required"])
        self.assertTrue(a["e0_terminal"])

    def test_tampered_history_snapshot_refused(self):
        req = self.f.request()
        hist = self.f.history(req)
        hist["files"]["pkg/f.py"]["introducing_commit"] = self.f.mod
        with self.assertRaises(SystemExit):
            self.f.run(req, history=hist)

    def test_no_registered_derived_candidate_is_a_custody_record_not_ownership(self):
        src = self.f.sources({61: "tracked in UNREGISTERED-TASK-010", 70: "slice of #61"})
        req = self.f.request(goal=None, derive_candidates_from=[61, 70])
        rec = self.only(self.f.run(req, sources=src))
        self.assertEqual(rec["record_kind"], "CUSTODY")
        self.assertIsNone(rec["candidate_owner"])
        self.assertIsNone(rec["assigned_owner"])
        self.assertEqual(rec["failure_code"], "NO_REGISTERED_CANDIDATE_OWNER")
        for k in SIX:
            self.assertTrue(rec.get(k), k)
        self.assertEqual(rec["custody"]["custodian"], "STEGVERSE-CANONICAL-WORK-COORDINATION-001")
        self.assertEqual(rec["custody"]["owner_status"], "UNOWNED_NOT_OBSERVED")
        self.assertTrue(rec["custody"]["custody_is_not_ownership"])
        refs = rec["candidate_derivation"]["references"]
        self.assertEqual([(r["goal_id"], r["registered"]) for r in refs], [("UNREGISTERED-TASK-010", False)])
        self.assertIn("UNREGISTERED-TASK-010", rec["required_evidence_or_repair"])

    def test_registered_derived_candidate_still_needs_receipts(self):
        src = self.f.sources({61: f"owned by {GOAL}"})
        req = self.f.request(goal=None, derive_candidates_from=[61])
        rec = self.only(self.f.run(req, sources=src))
        self.assertEqual(rec["record_kind"], "OWNER_ASSIGNMENT")
        self.assertEqual(rec["candidate_owner"]["goal_id"], GOAL)
        self.assertEqual(rec["candidate_owner"]["selected_by"], "DERIVED_FROM_GOAL_REFERENCES")
        self.assert_six(rec, "INTRODUCING_COMMIT_BOUND_TO_CANDIDATE_GOAL_BY_RECEIPT")
        copies = self.f.ledger([{**landed(self.f.intro), "task_id": GOAL}, landed(self.f.mod)])
        self.assertEqual(self.only(self.f.run(req, copies, sources=src))["assigned_owner"], GOAL)

    def test_excluded_candidate_is_never_derived_or_selected(self):
        src = self.f.sources({61: f"owned by {GOAL}"})
        excl = [{"goal_id": GOAL, "reason": "ruling"}]
        rec = self.only(self.f.run(self.f.request(goal=None, derive_candidates_from=[61], excluded_candidates=excl),
                                   sources=src))
        self.assertEqual(rec["record_kind"], "CUSTODY")
        self.assertEqual(rec["excluded_candidates"], excl)
        rec = self.only(self.f.run(self.f.request(goal=GOAL, excluded_candidates=excl)))
        self.assertEqual(rec["record_kind"], "CUSTODY")
        rec = self.only(self.f.run(self.f.request(candidate_owner={"goal_id": GOAL, "basis": []},
                                                  excluded_candidates=excl)))
        self.assertEqual(rec["failure_code"], "CANDIDATE_IS_EXCLUDED")

    def test_two_registered_candidates_are_ambiguous(self):
        self.f.registry["tasks"].append({"task_id": OTHER, "targets": {"repositories": [REPO]}})
        src = self.f.sources({61: f"{GOAL} and {OTHER}"})
        rec = self.only(self.f.run(self.f.request(goal=None, derive_candidates_from=[61]), sources=src))
        self.assertEqual(rec["failure_code"], "CANDIDATE_OWNER_AMBIGUOUS")
        self.assertEqual(rec["record_kind"], "CUSTODY")

    def test_explicit_candidate_owner_is_separate_from_assigned_owner(self):
        rec = self.only(self.f.run(self.f.request(goal=None, candidate_owner={"goal_id": GOAL, "basis": ["PR body"]})))
        self.assertEqual(rec["candidate_owner"]["goal_id"], GOAL)
        self.assertIsNone(rec["assigned_owner"])
        self.assertEqual(rec["disposition"], "FAIL_CLOSED")

    def test_sources_missing_or_tampered_fail_closed(self):
        rec = self.only(self.f.run(self.f.request(goal=None, derive_candidates_from=[61])))
        self.assertEqual(rec["failure_code"], "GOAL_REFERENCE_SOURCES_UNAVAILABLE")
        src = self.f.sources({61: "x"})
        src["sources"][0]["text"] = "UNREGISTERED-TASK-010"
        with self.assertRaises(SystemExit):
            self.f.run(self.f.request(goal=None, derive_candidates_from=[61]), sources=src)

    def test_no_network_clock_or_randomness_imports(self):
        with open(os.path.join(ROOT, "scripts", "owner_assignment_transition.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
                 for a in (n.names if isinstance(n, ast.Import) else [ast.alias(n.module or "")])}
        self.assertFalse(names & {"socket", "urllib", "http", "requests", "time", "datetime", "random", "secrets"})


class CommittedClosureRunTests(unittest.TestCase):
    """The committed run over the five unowned closure files replays offline."""

    def load(self, suffix):
        with open(f"{CLOSURE}.{suffix}.json", "rb") as fh:
            raw = fh.read()
        return json.loads(raw), "sha256:" + hashlib.sha256(raw).hexdigest()

    def test_committed_run_is_sealed_and_bound_to_its_inputs(self):
        run, _ = self.load("run")
        req, req_sha = self.load("request")
        hist, _ = self.load("git-history")
        self.assertEqual(run["run_sha256"], T.sha({k: v for k, v in run.items() if k != "run_sha256"}))
        self.assertEqual(run["request_sha256"], req_sha)
        self.assertEqual(run["history_snapshot_sha256"], hist["snapshot_sha256"])
        for rec in run["records"]:
            self.assertEqual(rec["record_sha256"], T.sha({k: v for k, v in rec.items() if k != "record_sha256"}))

    def test_all_five_fail_closed_with_six_fields_per_coordination_rulings(self):
        run, _ = self.load("run")
        self.assertEqual(run["tally"], {"FAIL_CLOSED": 5})
        self.assertEqual(run["record_kinds"], {"CUSTODY": 4, "OWNER_ASSIGNMENT": 1})
        interlock = "INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001"
        for rec in run["records"]:
            for k in SIX:
                self.assertTrue(rec.get(k), (rec["path"], k))
            self.assertIsNone(rec["assigned_owner"])
            self.assertIn(interlock, [e["goal_id"] for e in rec["excluded_candidates"]])
            self.assertEqual(rec["custody"]["custodian"], "STEGVERSE-CANONICAL-WORK-COORDINATION-001")
        names = {r["path"]: r for r in run["records"]}
        orn = names.pop("stegverse/organization_record_names.py")
        self.assertEqual(orn["record_kind"], "OWNER_ASSIGNMENT")
        self.assertEqual(orn["failure_code"], "LINEAGE_INSUFFICIENT")
        self.assertEqual(orn["candidate_owner"]["goal_id"], "MASTER-RECORDS-BULK-SEMANTIC-REMEDIATION-002")
        self.assertEqual({m["failed_predicate"] for m in orn["unmet_predicates"]},
                         {"EVERY_HISTORY_COMMIT_HAS_A_READ_BACK_LANDING_RECEIPT",
                          "INTRODUCING_COMMIT_BOUND_TO_CANDIDATE_GOAL_BY_RECEIPT"})
        self.assertEqual(len(names), 4)
        for rec in names.values():
            self.assertEqual(rec["record_kind"], "CUSTODY")
            self.assertEqual(rec["failure_code"], "NO_REGISTERED_CANDIDATE_OWNER")
            self.assertEqual(rec["custody"]["owner_status"], "UNOWNED_NOT_OBSERVED")
            self.assertEqual(rec["candidate_derivation"]["source_numbers"], [61, 65, 66, 67, 69, 70])
            self.assertEqual(rec["candidate_derivation"]["registered"], [])

    def test_records_replay_from_committed_inputs_without_ledger_copies(self):
        run, _ = self.load("run")
        req, req_sha = self.load("request")
        hist, _ = self.load("git-history")
        src, _ = self.load("goal-reference-sources")
        self.assertEqual(req["goal_reference_sources_sha256"], src["snapshot_sha256"])
        with open(os.path.join(ROOT, "data", "canonical-task-registry.json"), encoding="utf-8") as fh:
            registry = json.load(fh)
        replay = T.evaluate(req, hist, T.read_ledgers(None), registry,
                            os.path.join(ROOT, "data", "canonical-task-records"), req_sha, run["registry_sha256"], src)
        # no supplied ledger copy held a matching receipt, so the records are identical with none supplied
        self.assertEqual(T.canon(replay["records"]), T.canon(run["records"]))


if __name__ == "__main__":
    unittest.main()
