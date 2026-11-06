"""GOAL_SCOPE_SEALED: registration seals a Goal's scope; the read-only PR check freezes it."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")


def _module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gss = _module("goal_scope_seal_under_test", "scripts/goal_scope_seal.py")
crt = _module("crt_for_scope_seal", "scripts/canonical_task_registration_transition.py")
FIXTURE = ROOT / "tests" / "fixtures" / "canonical_task_registration" / "fixture.request.json"
CHECKIN_FILES = ("scripts/check_registry_collision_checkin.py", "scripts/evaluate_task_registry_collision_checkin.py",
                 "scripts/task_registry_checkin_event_history.py",
                 "scripts/validate_task_registration_substrate_resolution.py",
                 "data/task-registry-global-invariants.json", "data/task-registry-general-checkin-caller-policy.json")


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def reseal(request: dict) -> dict:
    scope = gss.scope_of(request["record"], request["sealed_scope"]["scope"]["finish_point"])
    request["sealed_scope"]["scope"] = scope
    request["sealed_scope"]["scope_digest"] = gss.digest(scope)
    return request


class Registration(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.base = self.tmp / "base"
        (self.base / "schemas").mkdir(parents=True)
        shutil.copy(ROOT / crt.RECORD_SCHEMA_PATH, self.base / crt.RECORD_SCHEMA_PATH)
        write(self.base / crt.REGISTRY, {"schema": "fixture", "generation": 7, "tasks": []})
        for rel in CHECKIN_FILES:
            (self.base / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, self.base / rel)
        self.request = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.request["observed_registry_generation"] = 7

    def plan(self, request=None):
        path = self.tmp / "req.json"
        write(path, self.request if request is None else request)
        return crt.run("plan", path, self.base)

    def refused(self, body, code):
        self.assertEqual(body["disposition"], "FAIL_CLOSED", body)
        self.assertEqual(body["failed_predicate"], "GOAL_SCOPE_SEALED", body)
        self.assertEqual(body["failure_code"], code, body)
        for field in SIX:
            self.assertTrue(body.get(field), field)
        self.assertFalse(body["consequence_committed"])

    def test_sealed_request_derives_the_seal_and_reports_the_digest(self):
        body = self.plan()
        self.assertEqual(body["disposition"], "ALLOW", body)
        tid = self.request["task_id"]
        self.assertIn(f"{crt.SEALS}/{tid}.json", body["derived_files"])
        self.assertEqual(body["evidence"]["scope_digest"], self.request["sealed_scope"]["scope_digest"])
        self.assertEqual(body["evidence"]["scope_digest"], gss.digest(self.request["sealed_scope"]["scope"]))
        self.assertEqual(body["evidence"]["finish_point"], self.request["sealed_scope"]["scope"]["finish_point"])

    def test_new_identity_without_a_seal_is_refused(self):
        request = copy.deepcopy(self.request)
        del request["sealed_scope"]
        self.refused(self.plan(request), "GOAL_SCOPE_NOT_SEALED")

    def test_wrong_digest_is_refused(self):
        request = copy.deepcopy(self.request)
        request["sealed_scope"]["scope_digest"] = "sha256:" + "0" * 64
        self.refused(self.plan(request), "GOAL_SCOPE_DIGEST_MISMATCH")

    def test_scope_that_is_not_the_record_is_refused(self):
        request = copy.deepcopy(self.request)
        request["sealed_scope"]["scope"]["goal"] = "a narrower goal than the record"
        request["sealed_scope"]["scope_digest"] = gss.digest(request["sealed_scope"]["scope"])
        self.refused(self.plan(request), "GOAL_SCOPE_DIVERGES_FROM_RECORD")

    def test_finish_point_must_name_a_test_and_a_predicate(self):
        for missing in gss.FINISH_POINT_FIELDS:
            request = copy.deepcopy(self.request)
            request["sealed_scope"]["scope"]["finish_point"][missing] = ""
            body = self.plan(reseal(request))  # the request schema refuses first; the seal module is the floor
            self.assertEqual(body["disposition"], "FAIL_CLOSED", body)
            self.assertIn(body["failed_predicate"], ("REGISTRATION_REQUEST_SCHEMA_INVALID", "GOAL_SCOPE_SEALED"))
            with self.assertRaises(gss.ScopeRefusal) as caught:
                gss.validate_sealed_scope(request["sealed_scope"], request["task_id"], request["record"], new_identity=True)
            self.assertEqual(caught.exception.code, "GOAL_FINISH_POINT_NOT_TESTABLE")

    def test_new_identity_supersedes_nothing(self):
        request = copy.deepcopy(self.request)
        request["sealed_scope"]["supersedes_scope_digest"] = "sha256:" + "1" * 64
        self.refused(self.plan(request), "GOAL_SCOPE_SUPERSEDE_ON_NEW_IDENTITY")

    def test_an_existing_seal_is_an_identity_collision(self):
        write(self.base / crt.SEALS / f"{self.request['task_id']}.json", {"schema": gss.SEAL_SCHEMA})
        body = self.plan()
        self.assertEqual(body["failed_predicate"], "TASK_IDENTITY_NOT_UNIQUE", body)


class Freeze(unittest.TestCase):
    """The scope-freeze PR check over base -> head trees."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.base, self.head = self.tmp / "base", self.tmp / "head"
        request = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.tid = request["task_id"]
        self.record = request["record"]
        self.seal = gss.validate_sealed_scope(request["sealed_scope"], self.tid, self.record, new_identity=True)
        for root in (self.base, self.head):
            write(root / gss.RECORDS / f"{self.tid}.json", self.record)
            write(root / gss.REGISTRY, {"generation": 1, "tasks": [copy.deepcopy(self.record)]})
            write(root / gss.SEALS / f"{self.tid}.json", self.seal)

    def refused(self, code):
        body = gss.check(self.base, self.head)
        self.assertEqual(body["disposition"], "FAIL_CLOSED", body)
        self.assertEqual(body["failed_predicate"], "GOAL_SCOPE_SEALED")
        self.assertIn(code, [f["failure_code"] for f in body["failures"]], body)
        for field in SIX:
            self.assertTrue(body.get(field), field)
        return body

    def test_unchanged_sealed_goal_is_allowed(self):
        body = gss.check(self.base, self.head)
        self.assertEqual(body["disposition"], "ALLOW", body)
        self.assertEqual(body["sealed_goals_on_head"], [self.tid])

    def test_expanding_the_record_goal_is_refused(self):
        record = copy.deepcopy(self.record)
        record["goal"] += " Also build an unrelated thing."
        write(self.head / gss.RECORDS / f"{self.tid}.json", record)
        self.refused("GOAL_SCOPE_EXPANDED_WITHOUT_SUPERSEDE")

    def test_adding_a_target_or_predicate_is_refused(self):
        record = copy.deepcopy(self.record)
        record["targets"]["components"] = record["targets"]["components"] + ["scope-creep"]
        write(self.head / gss.REGISTRY, {"generation": 2, "tasks": [record]})
        self.refused("GOAL_SCOPE_EXPANDED_WITHOUT_SUPERSEDE")
        record = copy.deepcopy(self.record)
        record["expected_evidence_predicates"] = record["expected_evidence_predicates"] + ["NEW_PREDICATE"]
        write(self.head / gss.RECORDS / f"{self.tid}.json", record)
        self.refused("GOAL_SCOPE_EXPANDED_WITHOUT_SUPERSEDE")

    def _new_scope(self):
        record = copy.deepcopy(self.record)
        record["goal"] += " Superseded scope."
        scope = gss.scope_of(record, self.seal["scope"]["finish_point"])
        seal = dict(self.seal, scope=scope, scope_digest=gss.digest(scope), supersedes_scope_digest=self.seal["scope_digest"])
        write(self.head / gss.RECORDS / f"{self.tid}.json", record)
        write(self.head / gss.REGISTRY, {"generation": 2, "tasks": [record]})
        write(self.head / gss.SEALS / f"{self.tid}.json", seal)
        return seal

    def test_resealing_without_a_supersede_request_is_refused(self):
        self._new_scope()
        self.refused("GOAL_SCOPE_CHANGED_WITHOUT_SUPERSEDE")

    def test_resealing_with_a_supersede_request_is_allowed(self):
        seal = self._new_scope()
        write(self.head / gss.SUPERSEDE_REQUESTS / "fixture-supersede.json", {
            "schema": gss.SUPERSEDE_SCHEMA, "task_id": self.tid, "prior_scope_digest": self.seal["scope_digest"],
            "successor_scope_digest": seal["scope_digest"], "reason": "fixture", "authority_effect": "NONE_REQUEST_ONLY"})
        self.assertEqual(gss.check(self.base, self.head)["disposition"], "ALLOW")

    def test_editing_the_seal_in_place_is_refused(self):
        seal = copy.deepcopy(self.seal)
        seal["scope"]["goal"] = "edited"
        write(self.head / gss.SEALS / f"{self.tid}.json", seal)
        self.refused("GOAL_SCOPE_DIGEST_MISMATCH")

    def test_removing_the_seal_is_refused(self):
        (self.head / gss.SEALS / f"{self.tid}.json").unlink()
        self.refused("GOAL_SCOPE_SEAL_REMOVED")

    def test_cli_exit_codes_and_receipt(self):
        out = self.tmp / "receipt.json"
        ok = subprocess.run([sys.executable, str(ROOT / "scripts/goal_scope_seal.py"), "check", "--base", str(self.base),
                             "--head", str(self.head), "--receipt-out", str(out)], capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertEqual(json.loads(out.read_text())["disposition"], "ALLOW")
        (self.head / gss.SEALS / f"{self.tid}.json").unlink()
        bad = subprocess.run([sys.executable, str(ROOT / "scripts/goal_scope_seal.py"), "check", "--base", str(self.base),
                              "--head", str(self.head)], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)

    def test_live_repository_holds_no_unsealed_drift(self):
        self.assertEqual(gss.check(ROOT, ROOT)["disposition"], "ALLOW")


class Surface(unittest.TestCase):
    def test_workflow_runs_the_freeze_read_only_on_pull_request(self):
        text = (ROOT / crt.WORKFLOW).read_text()
        self.assertIn("scripts/goal_scope_seal.py check", text)
        self.assertIn("tests.test_goal_scope_seal", text)
        for path in ("control/goal-scope-seals/**", "control/goal-scope-supersede-requests/**",
                     "data/canonical-task-records/**", "data/canonical-task-registry.json"):
            self.assertIn(f"'{path}'", text)
        self.assertIn("contents: read", text)
        for forbidden in ("contents: write", "workflow_dispatch", "git push", "schedule:"):
            self.assertNotIn(forbidden, text)

    def test_contract_names_the_seal(self):
        contract = json.loads((ROOT / "contracts/canonical-task-registration-transition.v1.json").read_text())
        self.assertIn("GOAL_SCOPE_SEALED", contract["predicates"])
        self.assertIn("control/goal-scope-seals/<task_id>.json", contract["transition"]["derived_paths"])
        self.assertEqual(contract["registration_modes"]["scope_seal"]["module"], "scripts/goal_scope_seal.py")


if __name__ == "__main__":
    unittest.main()
