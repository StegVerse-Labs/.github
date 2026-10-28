"""WRITE_ADMISSION (scripts/write_admission.py), E0: stdlib, temporary local git only, no clock, no network.

Every relationship is recomputed from a receipted body; each test changes the evidence (a body, its key, its seal,
the active-work set, the constraints) and checks that the recomputation, not any claim, decides.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


wa = _load("write_admission_under_test", "scripts/write_admission.py")
ar = wa.ar

REPO = "Org/fp"
WRITER = "SUBJ-001"
HEAD = "a" * 40
OTHER_HEAD = "b" * 40


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def surface(path="runtime/vault.py", repo=REPO):
    return {"kind": "file", "repository": repo, "path": path}


def work(task=WRITER, branch="laned/subj", head=HEAD, work_id="Org/fp#10", pr="Org/fp#10"):
    return {"schema": wa.WORK_ITEM_SCHEMA, "task_id": task, "work_id": work_id, "repository": REPO,
            "branch": branch, "head": head, "pull_request": pr}


def active(*items, source="test: open drafts and claims, listed by the fixture"):
    return {"schema": wa.ACTIVE_SCHEMA, "observed": {"source": source}, "items": list(items)}


def other_work(path="runtime/vault.py", head=OTHER_HEAD, work_id="Org/fp#11", branch="laneb/other"):
    return {"work_id": work_id, "task_id": "OTHER-001", "kind": "pull_request", "ref": work_id, "repository": REPO,
            "branch": branch, "head": head, "surfaces": [surface(path)]}


def record(task=WRITER, refs=(), components=("vault-module",)):
    return {"schema": wa.RECORD_SCHEMA, "task_id": task, "targets": {"repositories": [REPO], "components": list(components)},
            "source_refs": list(refs)}


def ruling(deps=(), protected=(), task=WRITER):
    body = {"schema": ar.SCHEMA, "task_id": task, "ruling_class": "D", "ruling": "ADJACENT_NOT_DUPLICATE",
            "ruled_by": "Coordination (test)", "subject": {"components": ["vault-module"], "finish_point": {
                "acceptance_test": f"{REPO}:tests/test_fp.py::test_x", "repository": REPO, "source_commit": HEAD}},
            "candidates": [], "consumes_dependencies": list(deps), "protected_paths": list(protected),
            "evidence_digest": ""}
    body["evidence_digest"] = ar.ruling_digest(body)
    return body


def pin(task, files, commit=HEAD):
    return {"task_id": task, "pinned_source": {"repository": REPO, "commit": commit, "files": files}}


def graph(*bodies):
    return wa.seal_graph(list(bodies))


class WriteAdmissionTests(unittest.TestCase):
    def allowed(self, verdict, *kinds):
        self.assertEqual(verdict["disposition"], "ALLOW", verdict)
        self.assertEqual(verdict[ar.SEAL], ar.seal(verdict)[ar.SEAL])
        self.assertEqual(verdict["ledger_status"], ar.SCRATCH)
        self.assertFalse(verdict["clock_read"] or verdict["network_used"] or verdict["llm_used"])
        self.assertEqual(sorted({r["kind"] for r in verdict["relationships"]}), sorted(kinds))
        return verdict

    def refused(self, verdict, code):
        self.assertEqual(verdict["disposition"], "FAIL_CLOSED", verdict)
        self.assertEqual(verdict["failure_code"], code, verdict)
        for field in SIX:
            self.assertTrue(verdict[field], field)
        self.assertNotIn(ar.SEAL, verdict)
        return verdict

    def repo(self, files):
        root = Path(tempfile.mkdtemp(prefix="wa-repo-"))
        self.addCleanup(shutil.rmtree, root, True)
        for rel, text in files.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text, encoding="utf-8")
        git(root, "init", "-q")
        git(root, "add", "-A")
        git(root, "commit", "-qm", "fixture")
        return root, git(root, "rev-parse", "HEAD")

    # -- ALLOW: one per relationship kind ---------------------------------------------------------------------
    def test_goal_target_by_source_ref_allows(self) -> None:
        v = wa.evaluate(surface(), work(), graph(record(refs=[f"{REPO}/runtime/vault.py"])), active())
        self.allowed(v, "GOAL_TARGET")

    def test_goal_target_by_component_module_allows(self) -> None:
        v = wa.evaluate(surface("runtime/vault_module.py"), work(), graph(record()), active())
        self.allowed(v, "GOAL_TARGET")

    def test_finish_test_closure_allows(self) -> None:
        receipt = {"schema": ar.RECEIPT_SCHEMA, "task_id": WRITER, "disposition": "ALLOW",
                   "finish_point": {"repository": REPO, "test": "tests/test_fp.py", "source_commit": HEAD,
                                    "closure": {"tests/test_fp.py": "sha256:x", "runtime/helper.py": "sha256:y"}}}
        self.allowed(wa.evaluate(surface("runtime/helper.py"), work(), graph(receipt), active()), "FINISH_TEST_CLOSURE")
        failed = dict(receipt, disposition="FAIL_CLOSED")
        self.refused(wa.evaluate(surface("runtime/helper.py"), work(), graph(failed), active()),
                     "WRITE_ADMISSION_RELATIONSHIP_UNRECEIPTED")

    def test_consumes_pin_allows_the_owner_and_routes_a_non_owner(self) -> None:
        protected = [{"repository": REPO, "paths": ["runtime/reg.py"], "owner_task_id": "CAND-A-001",
                      "on_modification": {"failure_code": "ADJACENCY_RULING_OWNER_OWNED_EDIT"}}]
        body = ruling([pin("CAND-A-001", {"runtime/reg.py": "c" * 64})], protected)
        v = self.refused(wa.evaluate(surface("runtime/reg.py"), work(), graph(body), active()),
                         "ADJACENCY_RULING_OWNER_OWNED_EDIT")
        self.assertEqual(v["owning_existing_goal"], "CAND-A-001")
        self.assertEqual(v["detail"]["routed_to"], "CAND-A-001")
        owner = work(task="CAND-A-001", branch="lanea/reg")
        self.allowed(wa.evaluate(surface("runtime/reg.py"), owner,
                                 graph(body, record("CAND-A-001", refs=[f"{REPO}:runtime/reg.py"])), active()),
                     "GOAL_TARGET")
        # the subject's read relationship to a consumed, unprotected file is a relationship
        free = ruling([pin("CAND-A-001", {"runtime/lib.py": "d" * 64})])
        self.allowed(wa.evaluate(surface("runtime/lib.py"), work(), graph(free), active()), "CONSUMES_PIN")

    def test_issue_and_pull_request_link_allows(self) -> None:
        issue = {"kind": "issue", "repository": "Org/hub", "number": 160}
        link = {"schema": wa.LINK_SCHEMA, "task_id": WRITER, "surface": issue, "links": ["Org/fp#10"]}
        self.allowed(wa.evaluate(issue, work(), graph(link), active()), "ISSUE_PR_LINK")
        pr = {"kind": "pull_request", "repository": "Org/fp", "number": 12}
        self.refused(wa.evaluate(pr, work(), graph(link), active()), "WRITE_ADMISSION_RELATIONSHIP_UNRECEIPTED")
        self.allowed(wa.evaluate(pr, work(), graph(record(refs=["https://github.com/Org/fp/pull/12"])), active()),
                     "GOAL_TARGET")

    # -- relationship missing / receipts not trusted ------------------------------------------------------------
    def test_no_relationship_fails_closed(self) -> None:
        v = self.refused(wa.evaluate(surface("docs/unrelated.md"), work(), graph(record()), active()),
                         "WRITE_ADMISSION_RELATIONSHIP_UNRECEIPTED")
        self.assertEqual(v["failed_predicate"], "WRITE_IS_RELATED_TO_THE_WRITERS_WORK")
        other = record("OTHER-001", refs=[f"{REPO}/docs/unrelated.md"])
        self.refused(wa.evaluate(surface("docs/unrelated.md"), work(), graph(other), active()),
                     "WRITE_ADMISSION_RELATIONSHIP_UNRECEIPTED")

    def test_receipts_that_do_not_re_derive_are_rejected(self) -> None:
        good = record(refs=[f"{REPO}/runtime/vault.py"])
        g = graph(good)
        key = next(iter(g["receipts"]))
        forged = {"schema": wa.GRAPH_SCHEMA, "receipts": {key: dict(good, task_id=WRITER, extra="edited")}}
        v = self.refused(wa.evaluate(surface(), work(), forged, active()), "WRITE_ADMISSION_RELATIONSHIP_UNRECEIPTED")
        self.assertEqual(v["detail"]["rejected_receipts"][0]["reason"], "KEY_IS_NOT_THE_CANONICAL_SHA256_OF_THE_BODY")
        bad_ruling = ruling([pin("CAND-A-001", {"runtime/vault.py": "c" * 64})])
        bad_ruling["ruled_by"] = "edited after the digest"
        v = self.refused(wa.evaluate(surface(), work(), graph(bad_ruling), active()),
                         "WRITE_ADMISSION_RELATIONSHIP_UNRECEIPTED")
        self.assertEqual(v["detail"]["rejected_receipts"][0]["reason"], "ADJACENCY_RULING_EVIDENCE_DIGEST_DOES_NOT_RE_DERIVE")
        sealed = ar.seal({"schema": wa.LINK_SCHEMA, "task_id": WRITER, "surface": surface(), "links": ["Org/fp#10"]})
        sealed["links"] = ["Org/fp#10", "x"]
        v = self.refused(wa.evaluate(surface(), work(), graph(sealed), active()), "WRITE_ADMISSION_RELATIONSHIP_UNRECEIPTED")
        self.assertEqual(v["detail"]["rejected_receipts"][0]["reason"], "RECEIPT_SHA256_DOES_NOT_RE_DERIVE")

    # -- inputs ---------------------------------------------------------------------------------------------
    def test_malformed_inputs_fail_closed(self) -> None:
        g, a = graph(record(refs=[f"{REPO}/runtime/vault.py"])), active()
        for name, args in {
            "absolute path": (surface("/etc/passwd"), work(), g, a),
            "parent path": (surface("../x.py"), work(), g, a),
            "issue number": ({"kind": "issue", "repository": REPO, "number": 0}, work(), g, a),
            "unknown task": (surface(), work(task=wa.UNKNOWN), g, a),
            "short head": (surface(), dict(work(), head="abc"), g, a),
            "graph schema": (surface(), work(), {"receipts": {}}, a),
            "constraints": (surface(), work(), g, a, {"rules": []}),
        }.items():
            with self.subTest(name):
                self.refused(wa.evaluate(*args), "WRITE_ADMISSION_INPUT_INVALID")

    def test_unobserved_active_work_fails_closed(self) -> None:
        g = graph(record(refs=[f"{REPO}/runtime/vault.py"]))
        for a in (None, active(source=wa.UNKNOWN), {"schema": wa.ACTIVE_SCHEMA, "items": []},
                  active({"task_id": "X"})):
            with self.subTest(a=a):
                v = self.refused(wa.evaluate(surface(), work(), g, a), "WRITE_ADMISSION_ACTIVE_WORK_NOT_OBSERVED")
                self.assertEqual(v["failed_predicate"], "ACTIVE_WORK_SET_OBSERVED")

    # -- constraints -------------------------------------------------------------------------------------------
    def test_constraints(self) -> None:
        g, a = graph(record(refs=[f"{REPO}/runtime/vault.py", f"{REPO}/ledger/entries.json"])), active()
        rules = {"schema": wa.CONSTRAINTS_SCHEMA, "rules": [
            {"id": "g8", "kind": "writer_branch_glob", "globs": ["laned/*"], "failure_code": "G8_BRANCH_NOT_OWNED"},
            {"id": "ledger", "kind": "deny_surface", "paths": ["ledger/*"]}]}
        v = self.allowed(wa.evaluate(surface(), work(), g, a, rules), "GOAL_TARGET")
        self.assertEqual([c["rule"] for c in v["constraints"]], ["g8", "ledger"])
        self.refused(wa.evaluate(surface(), work(branch="main"), g, a, rules), "G8_BRANCH_NOT_OWNED")
        self.refused(wa.evaluate(surface("ledger/entries.json"), work(), g, a, rules), "WRITE_ADMISSION_CONSTRAINT_VIOLATED")
        unknown = {"schema": wa.CONSTRAINTS_SCHEMA, "rules": [{"id": "x", "kind": "allow_everything"}]}
        self.refused(wa.evaluate(surface(), work(), g, a, unknown), "WRITE_ADMISSION_INPUT_INVALID")

    def test_shipped_lane_d_constraints_are_well_formed(self) -> None:
        for path in sorted((ROOT / "control" / "write-admission").glob("*.json")):
            with self.subTest(path.name):
                rules = json.loads(path.read_text(encoding="utf-8"))
                g = graph(record(refs=[f"{REPO}/runtime/vault.py"]))
                self.allowed(wa.evaluate(surface(), work(), g, active(), rules), "GOAL_TARGET")
                self.refused(wa.evaluate(surface(), work(branch="main"), g, active(), rules),
                             rules["rules"][0].get("failure_code") or "WRITE_ADMISSION_CONSTRAINT_VIOLATED")

    # -- active work ---------------------------------------------------------------------------------------
    def test_uncoordinated_active_work_conflicts(self) -> None:
        g = graph(record(refs=[f"{REPO}/runtime/vault.py"]))
        v = self.refused(wa.evaluate(surface(), work(), g, active(other_work())), "WRITE_ADMISSION_ACTIVE_WORK_CONFLICT")
        self.assertEqual(v["detail"]["active"][0]["work_id"], "Org/fp#11")
        self.assertIn("observe-stack", v["required_evidence_or_repair"])
        # other surfaces, and the writer's own work, are not conflicts
        self.allowed(wa.evaluate(surface(), work(), g, active(other_work("runtime/other.py"))), "GOAL_TARGET")
        self.allowed(wa.evaluate(surface(), work(), g, active(other_work(work_id="Org/fp#10"))), "GOAL_TARGET")

    def test_stacked_on_active_work_is_coordinated_and_a_relationship(self) -> None:
        root, base = self.repo({"runtime/vault.py": "V = 1\n"})
        git(root, "checkout", "-qb", "laneb/other")
        (root / "runtime" / "vault.py").write_text("V = 2\n", encoding="utf-8")
        git(root, "commit", "-qam", "other")
        other_head = git(root, "rev-parse", "HEAD")
        git(root, "checkout", "-qb", "laned/subj")
        (root / "runtime" / "vault.py").write_text("V = 3\n", encoding="utf-8")
        git(root, "commit", "-qam", "stacked")
        my_head = git(root, "rev-parse", "HEAD")
        git(root, "checkout", "-q", base)
        git(root, "checkout", "-qb", "laned/unstacked")
        (root / "README").write_text("x\n", encoding="utf-8")
        git(root, "add", "-A")
        git(root, "commit", "-qm", "unstacked")
        loose_head = git(root, "rev-parse", "HEAD")

        a = active(other_work(head=other_head))
        stack = wa.observe_stack(root, REPO, "laned/subj", my_head, [other_head])
        self.assertEqual(stack["contains"], [{"head": other_head}])
        v = self.allowed(wa.evaluate(surface(), work(head=my_head), graph(stack), a), "STACKED_BRANCH")
        self.assertEqual(v["active_work_coordinated"][0]["coordinated_by"], "STACKED_OR_REBASED_ONTO")
        loose = wa.observe_stack(root, REPO, "laned/unstacked", loose_head, [other_head])
        self.assertEqual(loose["not_contained"], [other_head])
        mine = record(refs=[f"{REPO}/runtime/vault.py"])
        self.refused(wa.evaluate(surface(), work(branch="laned/unstacked", head=loose_head), graph(loose, mine), a),
                     "WRITE_ADMISSION_ACTIVE_WORK_CONFLICT")
        # an observation of a different head does not carry over to the writer's current head
        self.refused(wa.evaluate(surface(), work(head=loose_head), graph(stack, mine), a),
                     "WRITE_ADMISSION_ACTIVE_WORK_CONFLICT")
        unseen = wa.observe_stack(root, REPO, "laned/subj", my_head, ["f" * 40])
        self.assertEqual(unseen["unobserved"], ["f" * 40])

    def test_write_coordination_resolves_the_conflict(self) -> None:
        mine = record(refs=[f"{REPO}/runtime/vault.py"])
        coord = {"schema": wa.COORDINATION_SCHEMA, "surface": surface(), "work_ids": ["Org/fp#10", "Org/fp#11"],
                 "ruled_by": "Coordination (test)"}
        v = self.allowed(wa.evaluate(surface(), work(), graph(mine, coord), active(other_work())), "GOAL_TARGET")
        self.assertEqual(v["active_work_coordinated"][0]["coordinated_by"], "WRITE_COORDINATION")
        partial = dict(coord, work_ids=["Org/fp#11", "Org/fp#12"])
        self.refused(wa.evaluate(surface(), work(), graph(mine, partial), active(other_work())),
                     "WRITE_ADMISSION_ACTIVE_WORK_CONFLICT")
        elsewhere = dict(coord, surface=surface("runtime/other.py"))
        self.refused(wa.evaluate(surface(), work(), graph(mine, elsewhere), active(other_work())),
                     "WRITE_ADMISSION_ACTIVE_WORK_CONFLICT")

    # -- an unowned consumed file: admitted when re-pinned and receipted -----------------------------------------
    def unowned_setup(self):
        root, pin_commit = self.repo({"gate/reader.py": "R = 1\n", "tests/test_fp.py": "X = 1\n"})
        old = hashlib.sha256(b"R = 1\n").hexdigest()
        (root / "gate" / "reader.py").write_text("R = 2\n", encoding="utf-8")
        git(root, "commit", "-qam", "edit the consumed file")
        head = git(root, "rev-parse", "HEAD")
        new = hashlib.sha256(b"R = 2\n").hexdigest()
        stale = ruling([pin(ar.UNOWNED, {"gate/reader.py": old}, pin_commit)])
        moved = ruling([pin(ar.UNOWNED, {"gate/reader.py": new}, head)])
        return root, pin_commit, head, stale, moved

    def test_unowned_consumed_edit_needs_a_consumes_edit_receipt(self) -> None:
        root, base, head, stale, moved = self.unowned_setup()
        s, w = surface("gate/reader.py"), work(head=head)
        v = self.refused(wa.evaluate(s, w, graph(stale), active()), "ADJACENCY_RULING_UNOWNED_CONSUMED_EDIT")
        self.assertIn("consumes-edit", v["retry_entrypoint"])
        self.refused(wa.evaluate(s, w, graph(moved), active()), "ADJACENCY_RULING_UNOWNED_CONSUMED_EDIT")
        edit = ar.consumes_edit(moved, root, base, head, "gate/reader.py", WRITER, "Org/fp#10")
        self.assertEqual(edit["disposition"], "ALLOW", edit)
        edit = dict(edit, repository=REPO)
        edit = ar.seal({k: v for k, v in edit.items() if k != ar.SEAL})
        v = self.allowed(wa.evaluate(s, w, graph(moved, edit), active()), "CONSUMES_EDIT")
        self.assertNotIn("CONSUMES_PIN", {r["kind"] for r in v["relationships"]})
        # a receipt does not admit the edit against a ruling whose pin it did not move
        self.refused(wa.evaluate(s, w, graph(stale, edit), active()), "ADJACENCY_RULING_UNOWNED_CONSUMED_EDIT")
        # nor when another receipted ruling still pins the old bytes
        other = ruling([pin(ar.UNOWNED, {"gate/reader.py": hashlib.sha256(b"R = 1\n").hexdigest()}, base)], task="OTHER-001")
        self.refused(wa.evaluate(s, w, graph(moved, edit, other), active()), "ADJACENCY_RULING_UNOWNED_CONSUMED_EDIT")
        # a refused consumes-edit (another writer) is not a relationship
        refused = ar.consumes_edit(moved, root, base, head, "gate/reader.py", "OTHER-001")
        self.assertEqual(refused["disposition"], "FAIL_CLOSED")
        self.refused(wa.evaluate(s, work(task="OTHER-001", head=head), graph(moved, refused), active()),
                     "ADJACENCY_RULING_UNOWNED_CONSUMED_EDIT")

    # -- determinism and the CLI -----------------------------------------------------------------------------
    def test_deterministic_and_cli(self) -> None:
        args = (surface(), work(), graph(record(refs=[f"{REPO}/runtime/vault.py"])), active())
        first, second = wa.evaluate(*copy.deepcopy(args)), wa.evaluate(*copy.deepcopy(args))
        self.assertEqual(first, second)
        tmp = Path(tempfile.mkdtemp(prefix="wa-cli-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        names = ("surface", "work-item", "graph", "active-work")
        for name, value in zip(names, args):
            (tmp / f"{name}.json").write_text(json.dumps(value), encoding="utf-8")
        (tmp / "rec.json").write_text(json.dumps(record(refs=[f"{REPO}/runtime/vault.py"])), encoding="utf-8")
        self.assertEqual(wa.main(["seal-graph", "--body", str(tmp / "rec.json"), "--out", str(tmp / "graph.json")]), 0)
        argv = ["evaluate"] + [x for n in names for x in (f"--{n}", str(tmp / f"{n}.json"))]
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(wa.main(argv + ["--receipt-out", str(tmp / "out.json")]), 0)
            self.assertEqual(json.loads((tmp / "out.json").read_text(encoding="utf-8")), first)
            (tmp / "active-work.json").write_text(json.dumps(active(other_work())), encoding="utf-8")
            self.assertEqual(wa.main(argv), 1)


if __name__ == "__main__":
    unittest.main()
