"""canonical-work-projection-trigger: request -> fence -> projection -> receipts.

Every case runs against a temporary registry and temporary ledgers; the real
data/canonical-task-registry.json is never written.
"""
from __future__ import annotations

import difflib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "canonical_work_projection_trigger.py"
PROJECTION = ROOT / "scripts" / "apply_admitted_canonical_work_projection.py"
WORKFLOW = ROOT / ".github" / "workflows" / "canonical-work-projection-trigger.yml"
EVALUATE_WORKFLOW = ROOT / ".github" / "workflows" / "canonical-work-projection-trigger-evaluate.yml"
GOVERNANCE = ROOT / ".github" / "workflows" / "organization-governance-decision.yml"
MAIN_REGISTRY = ROOT / "data" / "canonical-task-registry.json"

_spec = importlib.util.spec_from_file_location("canonical_work_projection_trigger", SCRIPT)
trigger = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(trigger)

TASK_ID = "TASK-FIXTURE-PROJECTION-001"
CORRELATION = "corr-fixture-projection-001"
MAT = "INTR-MAT-" + "0" * 24


def ingress(**overrides):
    value = {"schema": trigger.projection.INGRESS_SCHEMA, "state": "INGRESS_ADMITTED",
             "authority_effect": "INGRESS_TRANSITION_ONLY", "claim_or_fence_minted": False,
             "credential_authority": "TV/TVC", "github_token_runtime_authority": "NONE",
             "materialization_id": MAT, "request_hash": "sha256:" + "1" * 64,
             "payload_hash": "sha256:" + "2" * 64, "operation_id": "op-fixture"}
    value.update(overrides)
    return value


def consumption(**overrides):
    value = {"schema": trigger.projection.CONSUMPTION_SCHEMA, "state": "INGRESS_BOUND_COORDINATION_PROJECTED",
             "claim_or_fence_minted": False, "materialization_id": MAT,
             "request_hash": "sha256:" + "1" * 64, "payload_hash": "sha256:" + "2" * 64,
             "operation_id": "op-fixture", "task_id": TASK_ID, "correlation_id": CORRELATION,
             "ingress_receipt_ref": "runtime://receipts/canonical-work-intr-ingress/" + MAT}
    value.update(overrides)
    return value


def request(request_id="cwp-fixture-001", generation=7, **overrides):
    value = {"schema": trigger.REQUEST_SCHEMA, "request_id": request_id, "task_id": TASK_ID,
             "observed_registry_generation": generation, "hb_epoch": "33",
             "ingress_receipt": ingress(), "consumption_receipt": consumption(),
             "authority_effect": "NONE_REQUEST_ONLY"}
    value.update(overrides)
    return value


class Workspace(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.registry = self.dir / "registry.json"
        self.shards = self.dir / "shards"
        self.shards.mkdir()
        self.registry.write_text(json.dumps({
            "generation": 7, "status": "FIXTURE", "nonclaims": [], "human_actions": [],
            "tasks": [{"task_id": TASK_ID, "correlation_id": CORRELATION, "coordination_state": "PROPOSED"}],
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.requests = self.dir / "requests"
        self.requests.mkdir()

    def write_request(self, value, name=None):
        path = self.requests / f"{name or value.get('request_id', 'unnamed')}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def decide(self, paths, apply=False):
        return trigger.evaluate(paths, registry_path=self.registry, task_shards=self.shards, apply=apply)

    def assertRefused(self, result, code):
        self.assertEqual(result["disposition"], "FAIL_CLOSED", result)
        self.assertEqual(result["failure_code"], code, result)
        for key in trigger.SIX_FIELDS:
            self.assertTrue(isinstance(result.get(key), str) and result[key], key)
        self.assertIs(result["consequence_committed"], False)


class DecisionTests(Workspace):
    def test_plan_allows_and_writes_nothing(self):
        before = self.registry.read_bytes()
        result = self.decide([self.write_request(request())])
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertEqual(result["projected_generation"], 8)
        self.assertEqual(result["generation_fence"]["disposition"], "ALLOW")
        self.assertIs(result["written"], False)
        self.assertEqual(self.registry.read_bytes(), before)

    def test_apply_writes_exactly_what_the_projection_script_writes(self):
        path = self.write_request(request())
        req = json.loads(path.read_text())
        (self.dir / "i.json").write_text(json.dumps(req["ingress_receipt"]))
        (self.dir / "c.json").write_text(json.dumps(req["consumption_receipt"]))
        expected = self.dir / "expected.json"
        subprocess.run([sys.executable, str(PROJECTION), "--registry", str(self.registry),
                        "--task-shards", str(self.shards), "--ingress-receipt", str(self.dir / "i.json"),
                        "--consumption-receipt", str(self.dir / "c.json"), "--output", str(expected)],
                       check=True)
        result = self.decide([path], apply=True)
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertEqual(self.registry.read_bytes(), expected.read_bytes())
        self.assertEqual(json.loads(self.registry.read_text())["generation"], 8)
        self.assertEqual(result["generation_set_by"], "apply_admitted_canonical_work_projection.project")

    def test_a_replay_of_an_applied_request_is_not_projected_twice(self):
        path = self.write_request(request())
        self.decide([path], apply=True)
        applied = self.registry.read_bytes()
        result = self.decide([path], apply=True)
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertEqual(result["applicability"], "REPLAY_ALREADY_PROJECTED")
        self.assertEqual(self.registry.read_bytes(), applied)

    def test_a_stale_generation_is_a_fence_mismatch(self):
        result = self.decide([self.write_request(request(generation=6))])
        self.assertRefused(result, "REGISTRY_GENERATION_FENCE_MISMATCH")
        self.assertIn("session_mutation_generation_fence", result["evidence"])

    def test_unadmitted_work_is_refused(self):
        for bad in (ingress(state="INGRESS_PENDING"), ingress(claim_or_fence_minted=True),
                    ingress(credential_authority="GITHUB_TOKEN")):
            result = self.decide([self.write_request(request(ingress_receipt=bad))])
            self.assertRefused(result, "CANONICAL_WORK_PROJECTION_NOT_ADMITTED")

    def test_an_unknown_task_is_refused(self):
        result = self.decide([self.write_request(request(
            task_id="TASK-ABSENT-001", consumption_receipt=consumption(task_id="TASK-ABSENT-001")))])
        self.assertRefused(result, "CANONICAL_WORK_PROJECTION_NOT_ADMITTED")

    def test_a_missing_manifest_is_refused(self):
        self.assertRefused(self.decide([]), "CANONICAL_WORK_PROJECTION_MANIFEST_ABSENT")
        self.assertRefused(self.decide([self.requests / "gone.json"]), "CANONICAL_WORK_PROJECTION_MANIFEST_ABSENT")

    def test_more_than_one_request_per_push_is_refused(self):
        a = self.write_request(request("cwp-a-001"))
        b = self.write_request(request("cwp-b-001"))
        self.assertRefused(self.decide([a, b]), "CANONICAL_WORK_PROJECTION_BATCH_NOT_SINGULAR")

    def test_malformed_requests_are_refused(self):
        cases = [request(schema="other/v1"), request(authority_effect="EXECUTE"),
                 request(observed_registry_generation="7"), request(ingress_receipt=None),
                 request(consumption_receipt=consumption(task_id="OTHER"))]
        for value in cases:
            self.assertRefused(self.decide([self.write_request(value)]), "CANONICAL_WORK_PROJECTION_REQUEST_INVALID")
        self.assertRefused(self.decide([self.write_request(request(), name="mismatched-name")]),
                           "CANONICAL_WORK_PROJECTION_REQUEST_INVALID")
        broken = self.requests / "broken.json"
        broken.write_text("{not json", encoding="utf-8")
        self.assertRefused(self.decide([broken]), "CANONICAL_WORK_PROJECTION_REQUEST_INVALID")

    def test_the_epoch_is_supplied_never_read_from_a_clock(self):
        value = request()
        del value["hb_epoch"]
        self.assertRefused(self.decide([self.write_request(value)]), "HB_EPOCH_NOT_SUPPLIED")
        for bad in ("31", "0", "+33", 33.0, True):
            result = self.decide([self.write_request(request(hb_epoch=bad))])
            self.assertRefused(result, "HB_EPOCH_INVALID")
            self.assertIs(result["derived_from_clock"], False)
        self.assertEqual(self.decide([self.write_request(request(hb_epoch="32"))])["disposition"], "ALLOW")

    def test_a_layout_it_cannot_reproduce_is_refused_and_never_rewritten(self):
        value = json.loads(self.registry.read_text())
        self.registry.write_text(json.dumps(value, indent=2).replace('"status": "FIXTURE"', '"status":  "FIXTURE"') + "\n",
                                 encoding="utf-8")
        before = self.registry.read_bytes()
        result = self.decide([self.write_request(request())], apply=True)
        self.assertRefused(result, "REGISTRY_LAYOUT_NOT_PRESERVABLE")
        self.assertIn("own fenced registry generation", result["required_evidence_or_repair"])
        self.assertEqual(self.registry.read_bytes(), before)

    def test_an_unsorted_non_ascii_layout_is_preserved(self):
        value = {"tasks": [{"task_id": TASK_ID, "coordination_state": "PROPOSED", "correlation_id": CORRELATION,
                            "goal": "caf\u00e9 \u2014 fixture"}],
                 "generation": 7, "status": "FIXTURE", "nonclaims": []}
        self.registry.write_text(json.dumps(value, indent=4, ensure_ascii=False), encoding="utf-8")
        result = self.decide([self.write_request(request())], apply=True)
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertEqual(result["layout"]["indent"], 4)
        self.assertIs(result["layout"]["sort_keys"], False)
        text = self.registry.read_text(encoding="utf-8")
        self.assertIn("caf\u00e9 \u2014 fixture", text)
        self.assertTrue(text.startswith('{\n    "tasks": [\n'))
        self.assertFalse(text.endswith("\n"))
        self.assertEqual(json.loads(text)["generation"], 8)

    def test_a_row_projection_against_the_main_registry_changes_only_that_row(self):
        main_raw = MAIN_REGISTRY.read_text(encoding="utf-8")
        main = json.loads(main_raw)
        ids = [t.get("task_id") for t in main["tasks"]]
        row = next((t for t in main["tasks"] if t.get("coordination_state") == "PROPOSED"
                    and ids.count(t.get("task_id")) == 1 and t.get("correlation_id")), None)
        if row is None:
            self.skipTest("main has no projectable PROPOSED row")
        shutil.copyfile(MAIN_REGISTRY, self.registry)
        task_id = row["task_id"]
        value = request(task_id=task_id, generation=main["generation"],
                        consumption_receipt=consumption(task_id=task_id, correlation_id=row["correlation_id"]))
        result = self.decide([self.write_request(value)], apply=True)
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertEqual(result["projected_generation"], main["generation"] + 1)
        new_raw = self.registry.read_text(encoding="utf-8")
        # Content is exactly what project() returns.
        _, expected, _ = trigger.projection.project(main, value["ingress_receipt"], value["consumption_receipt"],
                                                    task_shards=self.shards)
        self.assertEqual(json.loads(new_raw), expected)
        old_lines, new_lines = main_raw.splitlines(), new_raw.splitlines()

        def row_span(lines):
            at = lines.index(f'      "task_id": {json.dumps(task_id, ensure_ascii=False)},')
            start = max(i for i in range(at) if lines[i] == "    {")
            end = next(i for i in range(at, len(lines)) if lines[i] in ("    }", "    },"))
            return range(start, end + 1)

        def block_span(lines, key):
            start = lines.index(f'  "{key}": [')
            end = next(i for i in range(start, len(lines)) if lines[i] in ("  ]", "  ],"))
            return range(start, end + 1)

        def header(lines, key):
            return {i for i, line in enumerate(lines) if line.startswith(f'  "{key}": ')}

        allowed_old = set(row_span(old_lines)) | set(block_span(old_lines, "nonclaims")) | header(old_lines, "generation") | header(old_lines, "status")
        allowed_new = set(row_span(new_lines)) | set(block_span(new_lines, "nonclaims")) | header(new_lines, "generation") | header(new_lines, "status")
        changed_old, changed_new = set(), set()
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False).get_opcodes():
            if tag != "equal":
                changed_old.update(range(i1, i2))
                changed_new.update(range(j1, j2))
        self.assertTrue(changed_old or changed_new)
        self.assertLessEqual(changed_old, allowed_old)
        self.assertLessEqual(changed_new, allowed_new)
        # Outside the row: only the header fields project() itself sets.
        outside = (changed_old - set(row_span(old_lines))) | {i for i in changed_new - set(row_span(new_lines))}
        self.assertLessEqual(len(outside), 2 * 2 + len(block_span(new_lines, "nonclaims")))
        self.assertLess(len(changed_old) + len(changed_new), 100, "a row projection must not rewrite the layout")

    def test_the_cli_exits_nonzero_with_the_six_fields_on_stderr(self):
        path = self.write_request(request(generation=5))
        done = subprocess.run([sys.executable, str(SCRIPT), "evaluate", "--mode", "plan", "--request", str(path),
                               "--registry", str(self.registry), "--task-shards", str(self.shards)],
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 1)
        for key in trigger.SIX_FIELDS:
            self.assertIn(key + "=", done.stderr)
        none = subprocess.run([sys.executable, str(SCRIPT), "evaluate", "--mode", "plan", "--allow-none"],
                              capture_output=True, text=True)
        self.assertEqual(none.returncode, 0, none.stderr)
        self.assertEqual(json.loads(none.stdout)["applicability"], "NOT_APPLICABLE")


class LedgerTests(Workspace):
    def setUp(self):
        super().setUp()
        names = ("STEGVERSE_REPO_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_ROOT")
        previous = {n: os.environ.get(n) for n in names}
        for n in names:
            os.environ[n] = str(self.dir / n.lower())

        def restore():
            for n, v in previous.items():
                os.environ.pop(n, None) if v is None else os.environ.__setitem__(n, v)
        self.addCleanup(restore)

    def receipts(self, variable, schema):
        return [r for r in (json.loads(p.read_text()) for p in Path(os.environ[variable]).rglob("*.json"))
                if r.get("schema") == schema]

    def test_an_allow_and_a_refusal_are_each_recorded_at_both_levels(self):
        refused = self.decide([self.write_request(request("cwp-stale-001", generation=1))])
        allowed = self.decide([self.write_request(request())], apply=True)
        for result, cls in ((allowed, trigger.APPLIED_CLASS), (refused, trigger.REFUSED_CLASS)):
            recorded = trigger.record(result, "33")
            self.assertEqual(recorded["transition_class"], cls)
            self.assertIs(recorded["organization_receipt_preserves_repository_receipt"], True)
        repo = self.receipts("STEGVERSE_REPO_LEDGER_ROOT", "stegverse.repo-transition-receipt/v1")
        org = self.receipts("STEGVERSE_ORG_LEDGER_ROOT", "stegverse.organization-transition-receipt/v1")
        self.assertEqual(sorted(r["transition_class"] for r in repo), sorted([trigger.APPLIED_CLASS, trigger.REFUSED_CLASS]))
        self.assertEqual(len(org), 2)
        stale, = [r for r in repo if r["transition_class"] == trigger.REFUSED_CLASS]
        for key in trigger.SIX_FIELDS:
            self.assertIn(key, stale["evidence"])
        self.assertEqual(stale["hb_reference"]["epoch"], 33)

    def test_recording_the_same_decision_twice_mints_one_receipt(self):
        result = self.decide([self.write_request(request())])
        first, second = trigger.record(result, "33"), trigger.record(result, "40")
        self.assertEqual(first["repository_receipt_sha256"], second["repository_receipt_sha256"])

    def child_env(self):
        # The child interpreter declares the POSIX ledger locus the way
        # tests/posix_ledger_locus documents for a child given a POSIX root.
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(ROOT / "tests" / "posix_ledger_locus"),
                                                          env.get("PYTHONPATH")]))
        return env

    def refusal_receipt(self, request_id):
        repo = self.receipts("STEGVERSE_REPO_LEDGER_ROOT", "stegverse.repo-transition-receipt/v1")
        found = [r for r in repo if r["transition_id"] == trigger.REFUSED_CLASS + ":" + request_id]
        self.assertEqual(len(found), 1, [r["transition_id"] for r in repo])
        return found[0]

    def test_a_refusal_without_a_supplied_epoch_is_recorded_at_the_ledger_head_epoch(self):
        trigger.record(self.decide([self.write_request(request())], apply=True), "41")
        missing = request("cwp-no-epoch-001")
        del missing["hb_epoch"]
        cases = (("cwp-no-epoch-001", missing, "HB_EPOCH_NOT_SUPPLIED", None),
                 ("cwp-low-epoch-001", request("cwp-low-epoch-001", hb_epoch="31"), "HB_EPOCH_INVALID", "31"),
                 ("cwp-coerced-epoch-001", request("cwp-coerced-epoch-001", hb_epoch="+33"), "HB_EPOCH_INVALID", "+33"))
        for request_id, value, code, supplied in cases:
            result = self.decide([self.write_request(value)])
            self.assertRefused(result, code)
            self.assertEqual(result["failed_predicate"], "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH")
            recorded = trigger.record(result, supplied)
            self.assertEqual(recorded["transition_class"], trigger.REFUSED_CLASS)
            self.assertEqual(recorded["hb_epoch_source"], "ORGANIZATION_LEDGER_HEAD_RECEIPT")
            self.assertIs(recorded["organization_receipt_preserves_repository_receipt"], True)
            receipt = self.refusal_receipt(request_id)
            for key in trigger.SIX_FIELDS:
                self.assertTrue(receipt["evidence"][key], key)
            self.assertEqual(receipt["evidence"]["failure_code"], code)
            self.assertEqual(receipt["evidence"]["request_hb_epoch_failure"], code)
            self.assertIs(receipt["evidence"]["derived_from_clock"], False)
            self.assertIs(receipt["hb_reference"]["derived_from_clock"], False)
            self.assertEqual(receipt["hb_reference"]["epoch"], 41)

    def test_an_unreadable_request_refusal_is_recorded_through_the_cli(self):
        trigger.record(self.decide([self.write_request(request())], apply=True), "35")
        broken = self.requests / "broken.json"
        broken.write_text("{not json", encoding="utf-8")
        decision = self.dir / "decision.json"
        decision.write_text(json.dumps(self.decide([broken])), encoding="utf-8")
        done = subprocess.run([sys.executable, str(SCRIPT), "record", "--result", str(decision),
                               "--request", str(broken)], capture_output=True, text=True, env=self.child_env())
        self.assertEqual(done.returncode, 0, done.stderr)
        out = json.loads(done.stdout)
        self.assertEqual(out["decision_disposition"], "FAIL_CLOSED")
        self.assertEqual(out["hb_epoch"], 35)
        self.assertEqual(out["hb_epoch_source"], "ORGANIZATION_LEDGER_HEAD_RECEIPT")
        receipt = self.refusal_receipt(out["request_id"])
        self.assertTrue(out["request_id"].startswith("unidentified-broken-"))
        self.assertEqual(receipt["evidence"]["failure_code"], "CANONICAL_WORK_PROJECTION_REQUEST_INVALID")

    def test_with_no_supplied_epoch_anywhere_the_refusal_says_it_was_not_recorded(self):
        value = request()
        del value["hb_epoch"]
        path = self.write_request(value)
        result = self.decide([path])
        with self.assertRaises(trigger.RefusalEpochUnavailable):
            trigger.record(result, None)
        decision = self.dir / "decision.json"
        decision.write_text(json.dumps(result), encoding="utf-8")
        done = subprocess.run([sys.executable, str(SCRIPT), "record", "--result", str(decision),
                               "--request", str(path)], capture_output=True, text=True, env=self.child_env())
        self.assertEqual(done.returncode, 1)
        out = json.loads(done.stdout)
        self.assertEqual(out["failure_code"], "PROPAGATION_REFUSAL_NOT_RECORDED")
        for key in trigger.SIX_FIELDS:
            self.assertIn(key + "=", done.stderr)
        self.assertEqual(self.receipts("STEGVERSE_REPO_LEDGER_ROOT", "stegverse.repo-transition-receipt/v1"), [])

    def test_record_refuses_without_a_supplied_epoch(self):
        result = self.decide([self.write_request(request())])
        with self.assertRaises(ValueError):
            trigger.record(result, None)


class WorkflowShapeTests(unittest.TestCase):
    def test_push_trigger_mirrors_the_governance_decision_trigger(self):
        text, governance = WORKFLOW.read_text(), GOVERNANCE.read_text()
        self.assertIn("  push:\n    branches: [main]\n    paths:\n      - '.stegverse/governance-decision-requests/**'", governance)
        self.assertIn("  push:\n    branches: [main]\n    paths:\n      - '.stegverse/canonical-work-projection-requests/*.json'", text)
        self.assertNotIn("workflow_dispatch", text)
        self.assertNotIn("--force", text)
        self.assertNotIn("secrets.", text)
        self.assertIn("check_registry_generation_fence.py --mode push", text)
        self.assertIn("group: ${{ github.event_name == 'push' && 'organization-ledger'", text)

    def test_the_workflow_is_registered(self):
        registry = json.loads((ROOT / "control" / "workflow-surface-registry.json").read_text())
        paths = {s["path"] for s in registry["surfaces"]}
        self.assertIn(".github/workflows/canonical-work-projection-trigger.yml", paths)
        self.assertIn(".github/workflows/canonical-work-projection-trigger-evaluate.yml", paths)

    def test_the_writer_is_push_only_so_no_job_is_skipped_on_a_pull_request(self):
        text = WORKFLOW.read_text()
        triggers = text[text.index("\non:\n"):text.index("\nconcurrency:")]
        self.assertNotIn("pull_request", triggers)
        self.assertNotIn("\n  validate:\n", text)

    def test_the_pull_request_apply_job_evaluates_and_writes_nothing(self):
        text = EVALUATE_WORKFLOW.read_text()
        triggers = text[text.index("\non:\n"):text.index("\nconcurrency:")]
        self.assertIn("  pull_request:\n", triggers)
        self.assertNotIn("push:", triggers)
        self.assertNotIn("workflow_dispatch", text)
        jobs = text[text.index("\njobs:\n"):]
        apply_job = jobs[jobs.index("\n  apply:\n"):]
        # Every job runs on every pull request: none is gated, so none is skipped.
        self.assertNotIn("\n    if:", jobs)
        self.assertNotIn("contents: write", text)
        self.assertNotIn("persist-credentials: true", text)
        self.assertEqual(text.count("persist-credentials: false"), 2)
        for forbidden in ("git push", "secrets.", " record ", "readback", "--force", "ledger_ref", "LEDGER_REF"):
            self.assertNotIn(forbidden, text)
        # The same fence and project() evaluation the writer runs, failing on FAIL_CLOSED.
        self.assertIn("check_registry_generation_fence.py --mode pull_request", apply_job)
        self.assertIn("check_registry_generation_fence.py --mode push", apply_job)
        self.assertIn("canonical_work_projection_trigger.py evaluate --mode plan --allow-none", apply_job)
        self.assertIn("set -euo pipefail", apply_job)
        # Not a no-op: the refusal path is proven live on every run.
        self.assertIn("CANONICAL_WORK_PROJECTION_MANIFEST_ABSENT", apply_job)
        self.assertIn('test "$status" -eq 1', apply_job)

    def test_the_evaluate_only_refusal_probe_fails_closed_with_six_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.txt"
            empty.write_text("")
            done = subprocess.run([sys.executable, str(ROOT / "scripts" / "canonical_work_projection_trigger.py"),
                                   "evaluate", "--mode", "plan", "--changed", str(empty)],
                                  capture_output=True, text=True)
            self.assertEqual(done.returncode, 1)
            out = json.loads(done.stdout)
            self.assertEqual(out["failure_code"], "CANONICAL_WORK_PROJECTION_MANIFEST_ABSENT")
            for key in trigger.SIX_FIELDS:
                self.assertTrue(out.get(key))
                self.assertIn(key + "=", done.stderr)
            allowed = subprocess.run([sys.executable, str(ROOT / "scripts" / "canonical_work_projection_trigger.py"),
                                      "evaluate", "--mode", "plan", "--allow-none", "--changed", str(empty)],
                                     capture_output=True, text=True)
            self.assertEqual(allowed.returncode, 0)
            self.assertEqual(json.loads(allowed.stdout)["applicability"], "NOT_APPLICABLE")
            self.assertFalse(json.loads(allowed.stdout)["written"])


if __name__ == "__main__":
    unittest.main()
