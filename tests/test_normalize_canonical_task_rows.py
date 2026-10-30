"""Fixture tests for scripts/normalize_canonical_task_rows.py --check (read-only, stdlib)."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "normalize_canonical_task_rows.py"
spec = importlib.util.spec_from_file_location("normalize_canonical_task_rows", SCRIPT)
norm = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(norm)

SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")
GOOD_CLAIM = {"authority": "WORKERCOORDINATOR", "claim_ref": None, "fence_ref": None, "projection_only": True}
GOOD_REQ = {"capabilities": [], "mutation_required": False, "deployment_required": False,
            "current_observation_required": False}
GOOD_RES = {"map_ref": "control/runtime-profile-map.json", "map_generation": 2, "candidate_profile_ids": ["P1"],
            "resolved_at": None, "projection_only": True, "selection_grants_authority": False}


def task(task_id, **changes):
    row = {"task_id": task_id, "correlation_id": task_id, "worker_claim": copy.deepcopy(GOOD_CLAIM),
           "runtime_requirements": copy.deepcopy(GOOD_REQ), "runtime_resolution": None}
    for key, value in changes.items():
        if value is ...:
            row.pop(key, None)
        else:
            row[key] = value
    return row


class NormalizeCheckTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.schema = self.dir / "schema.json"
        self.schema.write_text(norm.TASK_SCHEMA.read_text(encoding="utf-8"), encoding="utf-8")
        self.map = self.dir / "map.json"
        self.map.write_text(json.dumps({"generation": 2, "profiles": [{"profile_id": "P1"}]}), encoding="utf-8")
        self.registry = self.dir / "registry.json"

    def write(self, tasks):
        self.registry.write_text(json.dumps({"generation": 7, "tasks": tasks}), encoding="utf-8")

    def run_main(self, *extra):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = norm.main(["--check", "--registry", str(self.registry), "--schema", str(self.schema),
                              "--runtime-map", str(self.map), *extra])
        return code, out.getvalue(), err.getvalue()

    def report(self, tasks):
        self.write(tasks)
        return norm.build_report(self.registry, self.schema, self.map)

    def test_conforming_rows_are_out_of_scope_and_pass(self):
        rep = self.report([task("A"), task("B", runtime_resolution=copy.deepcopy(GOOD_RES))])
        self.assertEqual(rep["summary"]["rows_in_scope"], 0)
        self.assertEqual(norm.six_fields(rep, None)["disposition"], "PASS")

    def test_worker_claim_target_comes_from_schema_and_invariant(self):
        rep = self.report([task("A", worker_claim=...)])
        self.assertEqual(rep["worker_claim_target"], GOOD_CLAIM)
        row = rep["rows"][0]
        self.assertEqual(row["worker_claim"]["kind"], "ABSENT")
        self.assertEqual(row["worker_claim"]["target"], GOOD_CLAIM)
        self.assertIn("dfcb305f", row["worker_claim"]["basis"])
        self.assertIn("L46-L53", row["worker_claim"]["basis"])

    def test_worker_claim_kinds(self):
        rep = self.report([
            task("SESSION", worker_claim={"authority": "CURRENT_SESSION", "claim_ref": "c-1", "fence_ref": None,
                                          "projection_only": False}),
            task("STRING", worker_claim="CURRENT_SESSION"),
            task("NOFENCE", worker_claim={"authority": "WORKERCOORDINATOR", "claim_ref": None, "projection_only": True}),
        ])
        kinds = {r["task_id"]: r["worker_claim"]["kind"] for r in rep["rows"]}
        self.assertEqual(kinds["SESSION"], "AUTHORITY_DRIFT+PROJECTION_ONLY_DRIFT+NONNULL_REF_REQUIRES_OBSERVED_CLAIM_CHECK")
        self.assertEqual(kinds["STRING"], "NOT_OBJECT")
        self.assertEqual(kinds["NOFENCE"], "MISSING_KEYS")
        session = next(r for r in rep["rows"] if r["task_id"] == "SESSION")
        self.assertEqual(session["worker_claim"]["target"]["claim_ref"], "c-1")  # kept, flagged, not nulled
        self.assertEqual(session["worker_claim"]["changes"], ["authority", "projection_only"])

    def test_runtime_resolution_delta(self):
        stale = dict(GOOD_RES, map_generation=1)
        extra = {"authority_basis": "x", "current_executor": "y"}
        rep = self.report([task("STALE", runtime_resolution=stale), task("EXTRA", runtime_resolution=extra),
                           task("OK", runtime_resolution=copy.deepcopy(GOOD_RES))])
        rows = {r["task_id"]: r for r in rep["rows"]}
        self.assertNotIn("OK", rows)
        self.assertEqual(rows["STALE"]["runtime_resolution"]["violations"], ["STALE_OR_MISSING_MAP_GENERATION"])
        self.assertIsNone(rows["STALE"]["runtime_resolution"]["target"])
        self.assertEqual(rows["EXTRA"]["runtime_resolution"]["non_schema_keys"], ["authority_basis", "current_executor"])
        self.assertEqual(rows["EXTRA"]["runtime_resolution"]["non_schema_key_destination"], "UNDECIDED_Q-R-j")
        self.assertEqual(rep["summary"]["rows_runtime_resolution_only"], 2)

    def test_runtime_requirements_reported_not_normalized(self):
        rep = self.report([task("A", runtime_requirements=...), task("B", runtime_requirements={"capabilities": []})])
        statuses = {r["task_id"]: r["runtime_requirements"] for r in rep["rows"]}
        self.assertEqual(statuses["A"], {"status": "ABSENT", "disposition": "NOT_NORMALIZED_PENDING_Q-R-k"})
        self.assertEqual(statuses["B"]["status"], "FLAG_NOT_BOOLEAN")
        self.assertNotIn("target", statuses["A"])

    def test_check_never_writes_sources_and_is_deterministic(self):
        self.write([task("A", worker_claim=...), task("B", runtime_resolution={"x": 1})])
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.registry, self.schema, self.map)}
        first = self.run_main()
        second = self.run_main()
        after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.registry, self.schema, self.map)}
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        code, out, _ = first
        self.assertEqual(code, 0)
        report_text, summary_text = out.split("\ndisposition: ", 1)
        report = json.loads(report_text)
        self.assertFalse(report["writes_performed"])
        for field in SIX:
            self.assertIn(f"\n{field}: ", "\n" + summary_text)
        self.assertTrue(summary_text.startswith("FAIL_CLOSED"))

    def test_enforce_and_check_required(self):
        self.write([task("A", worker_claim=...)])
        self.assertEqual(self.run_main("--enforce")[0], 1)
        out = io.StringIO()
        with contextlib.redirect_stderr(out):
            self.assertEqual(norm.main(["--registry", str(self.registry)]), 1)
        self.assertIn("only --check is supported", out.getvalue())

    def test_unreadable_sources_fail_closed(self):
        cases = {
            "missing": None,
            "bad json": "{",
            "tasks not array": json.dumps({"tasks": {}}),
            "row not object": json.dumps({"tasks": [1]}),
        }
        for name, content in cases.items():
            with self.subTest(case=name):
                if content is None:
                    self.registry.unlink(missing_ok=True)
                else:
                    self.registry.write_text(content, encoding="utf-8")
                code, out, _ = self.run_main()
                self.assertEqual(code, 1)
                self.assertIn("CANONICAL_TASK_ROW_NORMALIZATION_CHECK_SOURCE_UNREADABLE", out)
                for field in SIX:
                    self.assertIn(f"{field}: ", out)

    def test_report_path_cannot_target_a_source(self):
        self.write([task("A", worker_claim=...)])
        before = self.registry.read_bytes()
        code, _, err = self.run_main("--report", str(self.registry))
        self.assertEqual(code, 1)
        self.assertIn("must not point at a source file", err)
        self.assertEqual(self.registry.read_bytes(), before)

    def test_live_registry_counts_91_plus_3(self):
        rep = norm.build_report(norm.REGISTRY, norm.TASK_SCHEMA, norm.RUNTIME_MAP)
        summary = rep["summary"]
        self.assertEqual(summary["rows_in_scope"],
                         summary["rows_worker_claim_or_runtime_requirements"] + summary["rows_runtime_resolution_only"])


if __name__ == "__main__":
    unittest.main()
