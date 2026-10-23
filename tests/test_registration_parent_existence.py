"""REGISTRATION_PARENT_EXISTENCE_NOT_CHECKED: the planner refuses a child of an unregistered parent.

StegVerse-Labs/.github#3195: ``canonical_task_registration_transition.py plan``
returned ALLOW (generation 320 -> 321 at main 86382e60) for the proposed child
SKAP-UNDECLARED-CRYPTOGRAPHY-001 whose parent and root, KV-SKAP-VAULT-FUNCTIONAL-001,
is not on the canonical Registry. scripts/registration_parent_existence.py is the
predicate; the planner's derivation calls it (readability first, then the parent check
after its own generation and uniqueness predicates).
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "canonical_task_registration_transition.py"
MODULE = ROOT / "scripts" / "registration_parent_existence.py"
FIXTURE = ROOT / "tests" / "fixtures" / "canonical_task_registration" / "fixture.request.json"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")
# Predecessor-tree inputs later planner revisions read (the collision check-in, #3324's stack);
# copied into the scratch base when this tree carries them, so the ALLOW path stays reachable.
PREDECESSOR_INPUTS = ("scripts/check_registry_collision_checkin.py", "scripts/evaluate_task_registry_collision_checkin.py",
                      "scripts/task_registry_checkin_event_history.py",
                      "scripts/validate_task_registration_substrate_resolution.py",
                      "data/task-registry-global-invariants.json", "data/task-registry-general-checkin-caller-policy.json")
PARENT = "KV-SKAP-VAULT-FUNCTIONAL-001"
CHILD = "SKAP-UNDECLARED-CRYPTOGRAPHY-001"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


crt = _load("crt_for_parent_existence", SCRIPT)
rpe = _load("registration_parent_existence_under_test", MODULE)


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def child_request(generation: int) -> dict:
    """The #3195 child: SKAP-UNDECLARED-CRYPTOGRAPHY-001 under KV-SKAP-VAULT-FUNCTIONAL-001."""
    request = json.loads(FIXTURE.read_text(encoding="utf-8"))
    old = request["task_id"]
    request = json.loads(json.dumps(request).replace(old, CHILD))
    request["request_id"] = "test-skap-undeclared-cryptography-child"
    request["observed_registry_generation"] = generation
    request["record"]["parent_task_id"] = PARENT
    request["record"]["root_correlation_id"] = PARENT
    return request


class Base(unittest.TestCase):
    GENERATION = 320

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.base = self.tmp / "base"
        (self.base / "schemas").mkdir(parents=True)
        shutil.copy(ROOT / crt.RECORD_SCHEMA_PATH, self.base / crt.RECORD_SCHEMA_PATH)
        for rel in PREDECESSOR_INPUTS:
            if (ROOT / rel).is_file():
                (self.base / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ROOT / rel, self.base / rel)
        self.set_registry(["EXISTING-001"])
        self.request = child_request(self.GENERATION)

    def set_registry(self, task_ids) -> None:
        write(self.base / crt.REGISTRY, {"schema": "fixture", "generation": self.GENERATION,
                                         "tasks": [{"task_id": t} for t in task_ids]})

    def plan(self, request=None, mode="plan", base=None, head=None):
        path = self.tmp / "req.json"
        write(path, self.request if request is None else request)
        return crt.run(mode, path, base or self.base, head)

    def assert_refused(self, body, predicate):
        self.assertEqual(body["disposition"], "FAIL_CLOSED", body)
        self.assertEqual(body["failure_code"], predicate, body)
        self.assertEqual(body["failed_predicate"], predicate, body)
        for field in SIX:
            self.assertTrue(body.get(field), f"{field} missing in {body}")
        self.assertFalse(body["consequence_committed"])
        self.assertNotIn("evidence", body)
        self.assertNotIn("derived_files", body)
        self.assertNotIn("poll", json.dumps(body).lower())


class ParentMissingIsRefused(Base):
    def test_child_of_unregistered_kv_skap_vault_goal_is_refused(self):
        body = self.plan()
        self.assert_refused(body, "REGISTRATION_PARENT_NOT_REGISTERED")
        self.assertIn(f"parent_task_id='{PARENT}'", body["detail"])
        self.assertIn(f"root_correlation_id='{PARENT}'", body["detail"])
        self.assertIn("generation 320", body["detail"])

    def test_apply_and_verify_refuse_too_and_write_nothing(self):
        head = self.tmp / "head"
        head.mkdir()
        before = (self.base / crt.REGISTRY).read_bytes()
        self.assert_refused(self.plan(mode="apply", head=head), "REGISTRATION_PARENT_NOT_REGISTERED")
        self.assertEqual(list(head.rglob("*")), [])
        self.assert_refused(self.plan(mode="verify", head=head), "REGISTRATION_PARENT_NOT_REGISTERED")
        self.assertEqual((self.base / crt.REGISTRY).read_bytes(), before)

    def test_root_alone_unregistered_is_refused(self):
        self.set_registry(["EXISTING-001", PARENT])
        request = copy.deepcopy(self.request)
        request["record"]["root_correlation_id"] = "UNREGISTERED-ROOT-001"
        body = self.plan(request)
        self.assert_refused(body, "REGISTRATION_PARENT_NOT_REGISTERED")
        self.assertIn("root_correlation_id='UNREGISTERED-ROOT-001'", body["detail"])
        self.assertNotIn("parent_task_id", body["detail"])

    def test_a_task_cannot_be_its_own_parent(self):
        request = copy.deepcopy(self.request)
        request["record"]["parent_task_id"] = CHILD
        request["record"]["root_correlation_id"] = CHILD
        body = self.plan(request)
        self.assert_refused(body, "REGISTRATION_PARENT_NOT_REGISTERED")
        self.assertIn("names the task being registered", body["detail"])

    def test_non_string_parent_is_refused(self):
        request = copy.deepcopy(self.request)
        request["record"]["parent_task_id"] = ""
        self.assert_refused(self.plan(request), "REGISTRATION_PARENT_NOT_REGISTERED")

    def test_cli_exit_code_and_receipt_schema(self):
        path = self.tmp / "req.json"
        write(path, self.request)
        out = self.tmp / "receipt.json"
        proc = subprocess.run([sys.executable, str(SCRIPT), "plan", "--request", str(path), "--base", str(self.base),
                               "--receipt-out", str(out)], capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        body = json.loads(out.read_text())
        self.assert_refused(body, "REGISTRATION_PARENT_NOT_REGISTERED")
        schema = json.loads((ROOT / "schemas/canonical-task-registration-transition-receipt.schema.json").read_text())
        self.assertEqual(crt.schema_errors(body, schema), [], body)


class ParentPresentIsAllowed(Base):
    def test_child_of_registered_parent_is_allowed(self):
        self.set_registry(["EXISTING-001", PARENT])
        body = self.plan()
        self.assertEqual(body["disposition"], "ALLOW", body)
        self.assertEqual(body["evidence"]["successor_registry_generation"], self.GENERATION + 1)
        self.assertNotIn("failure_code", body)

    def test_root_goal_without_parent_is_allowed(self):
        request = copy.deepcopy(self.request)
        request["record"]["parent_task_id"] = None
        request["record"]["root_correlation_id"] = CHILD
        self.assertEqual(self.plan(request)["disposition"], "ALLOW")
        request["record"]["root_correlation_id"] = None
        self.assertEqual(self.plan(request)["disposition"], "ALLOW")

    def test_apply_writes_the_child_once_the_parent_is_registered(self):
        self.set_registry(["EXISTING-001", PARENT])
        head = self.tmp / "head"
        shutil.copytree(self.base, head)
        self.assertEqual(self.plan(mode="apply", head=head)["disposition"], "ALLOW")
        rows = json.loads((head / crt.REGISTRY).read_text())["tasks"]
        self.assertEqual([r["task_id"] for r in rows], ["EXISTING-001", PARENT, CHILD])
        self.assertEqual(self.plan(mode="verify", head=head)["disposition"], "ALLOW")


class RegistryUnreadableFailsClosed(Base):
    def assert_unreadable(self):
        self.assert_refused(self.plan(), "REGISTRATION_PARENT_REGISTRY_UNREADABLE")

    def test_missing_registry(self):
        (self.base / crt.REGISTRY).unlink()
        self.assert_unreadable()

    def test_registry_is_a_directory(self):
        (self.base / crt.REGISTRY).unlink()
        (self.base / crt.REGISTRY).mkdir()
        self.assert_unreadable()

    def test_registry_not_json(self):
        (self.base / crt.REGISTRY).write_text("{not json", encoding="utf-8")
        self.assert_unreadable()

    def test_registry_not_utf8(self):
        (self.base / crt.REGISTRY).write_bytes(b"\xff\xfe\x00")
        self.assert_unreadable()

    def test_registry_without_task_rows(self):
        for value in ([], {"generation": 320}, {"generation": 320, "tasks": {"x": 1}}):
            write(self.base / crt.REGISTRY, value)
            self.assert_unreadable()

    def test_unreadable_registry_refuses_even_a_root_goal(self):
        (self.base / crt.REGISTRY).write_text("", encoding="utf-8")
        request = copy.deepcopy(self.request)
        request["record"]["parent_task_id"] = None
        request["record"]["root_correlation_id"] = CHILD
        self.assert_refused(self.plan(request), "REGISTRATION_PARENT_REGISTRY_UNREADABLE")


class Module(unittest.TestCase):
    def test_module_is_read_only_stdlib_and_clock_free(self):
        source = MODULE.read_text(encoding="utf-8")
        for forbidden in ("write_text", "write_bytes", ".open(", "open(", "import time", "datetime", "subprocess",
                          "urllib", "socket", "requests", "sleep", "dispatch"):
            if forbidden == "dispatch":
                self.assertNotIn("workflow_dispatch", source)
                continue
            self.assertNotIn(forbidden, source, forbidden)
        imports = {line.split()[1].split(".")[0] for line in source.splitlines()
                   if line.startswith(("import ", "from ")) and not line.startswith("from __future__")}
        self.assertTrue(imports <= {"json", "pathlib", "typing"}, imports)

    def test_check_raises_its_own_refusal_without_a_planner(self):
        with self.assertRaises(rpe.ParentExistenceRefusal) as caught:
            rpe.check(Path(tempfile.gettempdir()) / "no-such-registry-root", child_request(1))
        self.assertEqual(caught.exception.predicate, rpe.REGISTRY_UNREADABLE)

    def test_planner_hook_order(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(source.count("_parent_existence().require_registry_readable(root, Refusal)"), 1)
        self.assertEqual(source.count("_parent_existence().check(root, request, Refusal)"), 1)
        derive = source[source.index("def derive("):source.index("def receipt(")]
        readable, read = derive.index("require_registry_readable("), derive.index("registry_path.read_bytes()")
        unique, check = derive.index('"TASK_IDENTITY_NOT_UNIQUE"'), derive.index("_parent_existence().check(")
        self.assertLess(readable, read)
        self.assertLess(derive.index('"REGISTRY_GENERATION_NOT_OBSERVED_TIP"'), check)
        self.assertLess(unique, check)

    def test_existing_predicates_keep_precedence(self):
        base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, base)
        (base / "schemas").mkdir()
        shutil.copy(ROOT / crt.RECORD_SCHEMA_PATH, base / crt.RECORD_SCHEMA_PATH)
        write(base / crt.REGISTRY, {"generation": 7, "tasks": [{"task_id": CHILD}]})
        path = base / "req.json"
        write(path, child_request(6))  # stale generation and unregistered parent
        self.assertEqual(crt.run("plan", path, base)["failure_code"], "REGISTRY_GENERATION_NOT_OBSERVED_TIP")
        write(path, child_request(7))  # duplicate identity and unregistered parent
        self.assertEqual(crt.run("plan", path, base)["failure_code"], "TASK_IDENTITY_NOT_UNIQUE")


class LiveRegistry(unittest.TestCase):
    """Against this tree's own data/canonical-task-registry.json (read only)."""

    def test_kv_child_against_the_live_registry(self):
        registry_path = ROOT / crt.REGISTRY
        before = hashlib.sha256(registry_path.read_bytes()).hexdigest()
        live = json.loads(registry_path.read_text(encoding="utf-8"))
        ids = {row.get("task_id") for row in live["tasks"]}
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        path = tmp / "req.json"
        write(path, child_request(live["generation"]))
        body = crt.run("plan", path, ROOT)
        if PARENT in ids:  # once the parent is registered the same child plans ALLOW
            self.assertEqual(body["disposition"], "ALLOW", body)
        else:
            self.assertEqual(body["disposition"], "FAIL_CLOSED", body)
            self.assertEqual(body["failure_code"], "REGISTRATION_PARENT_NOT_REGISTERED", body)
            for field in SIX:
                self.assertTrue(body.get(field), field)
        self.assertEqual(hashlib.sha256(registry_path.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main()
