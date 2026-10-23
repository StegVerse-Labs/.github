"""Manifest-directed canonical Goal Task registration transition."""
from __future__ import annotations

import builtins
import copy
import datetime
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "canonical_task_registration_transition.py"
FIXTURE = ROOT / "tests" / "fixtures" / "canonical_task_registration" / "fixture.request.json"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")

spec = importlib.util.spec_from_file_location("canonical_task_registration_transition", SCRIPT)
crt = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(crt)
sys.path.insert(0, str(ROOT / "scripts"))
from cosv import encode_task  # noqa: E402


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.base = self.tmp / "base"
        (self.base / "schemas").mkdir(parents=True)
        shutil.copy(ROOT / crt.RECORD_SCHEMA_PATH, self.base / crt.RECORD_SCHEMA_PATH)
        write(self.base / crt.REGISTRY, {"schema": "fixture", "generation": 41,
                                         "tasks": [{"task_id": "EXISTING-001"}]})
        write(self.base / crt.INDEX, {"tasks": [{"task_id": "INDEXED-001"}]})
        self.request = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.request["observed_registry_generation"] = 41

    def manifest(self, request=None, name="req.json") -> Path:
        path = self.tmp / name
        write(path, self.request if request is None else request)
        return path

    def run_mode(self, mode="plan", request=None, head=None):
        return crt.run(mode, self.manifest(request), self.base, head)

    def assert_refused(self, body, predicate):
        self.assertEqual(body["disposition"], "FAIL_CLOSED", body)
        self.assertEqual(body["failed_predicate"], predicate, body)
        for field in SIX:
            self.assertTrue(body.get(field), f"{field} missing in {body}")
        self.assertFalse(body["consequence_committed"])
        self.assertNotIn("poll", json.dumps(body).lower())


class Allow(Base):
    def test_plan_derives_the_four_surfaces_from_the_manifest_alone(self):
        body = self.run_mode("plan")
        self.assertEqual(body["disposition"], "ALLOW", body)
        tid = self.request["task_id"]
        self.assertEqual(sorted(body["derived_files"]), sorted([
            crt.REGISTRY, f"{crt.RECORDS}/{tid}.json", f"{crt.VECTORS}/{tid}.json", f"{crt.INDEX_SHARDS}/{tid}.json"]))
        ev = body["evidence"]
        self.assertEqual((ev["predecessor_registry_generation"], ev["successor_registry_generation"]), (41, 42))
        self.assertEqual(ev["cosv_task_vector"], encode_task(self.request["vector"]["exact_metrics"]))
        self.assertFalse((self.base / f"{crt.RECORDS}/{tid}.json").exists(), "plan must not write")

    def test_apply_then_verify_and_row_equals_record(self):
        head = self.tmp / "head"
        shutil.copytree(self.base, head)
        self.assertEqual(crt.run("apply", self.manifest(), self.base, head)["disposition"], "ALLOW")
        tid = self.request["task_id"]
        registry = json.loads((head / crt.REGISTRY).read_text())
        record = json.loads((head / f"{crt.RECORDS}/{tid}.json").read_text())
        self.assertEqual(registry["generation"], 42)
        self.assertEqual(registry["tasks"][-1], record)
        self.assertEqual(registry["tasks"][:-1], [{"task_id": "EXISTING-001"}])
        self.assertEqual(record["source_state_vector_ref"], f"{crt.VECTORS}/{tid}.json")
        shard = json.loads((head / f"{crt.INDEX_SHARDS}/{tid}.json").read_text())
        self.assertEqual((shard["vector"], shard["vector_state"]), (record["cosv_task_vector"], "EMITTED"))
        self.assertEqual(crt.run("verify", self.manifest(), self.base, head)["disposition"], "ALLOW")

    def test_derivation_is_deterministic_and_reads_no_clock(self):
        boom = mock.Mock(side_effect=AssertionError("clock read"))
        with mock.patch.object(time, "time", boom), mock.patch.object(datetime, "datetime", mock.Mock(now=boom, utcnow=boom)):
            first, second = self.run_mode(), self.run_mode()
        self.assertEqual(first, second)
        self.assertFalse(first["clock_read"])

    def test_receipt_conforms_to_its_schema_and_mints_nothing(self):
        schema = json.loads((ROOT / "schemas/canonical-task-registration-transition-receipt.schema.json").read_text())
        allow = self.run_mode()
        refused = self.run_mode(request=dict(self.request, observed_registry_generation=40))
        for body in (allow, refused):
            self.assertEqual(crt.schema_errors(body, schema), [], body)
            self.assertEqual(body["authority_effect"], "NONE_REGISTRATION_ONLY")
            for key in ("workercoordinator_claim_or_fence_minted", "intr_admission_minted",
                        "execution_authority_minted", "organization_ledger_appended"):
                self.assertIs(body[key], False)

    def test_fixture_registers_against_the_live_repository_registry(self):
        live = json.loads((ROOT / crt.REGISTRY).read_text())
        request = dict(self.request, observed_registry_generation=live["generation"])
        body = crt.run("plan", self.manifest(request), ROOT)
        self.assertEqual(body["disposition"], "ALLOW", body)
        self.assertEqual(body["evidence"]["successor_registry_generation"], live["generation"] + 1)


class Refusals(Base):
    def test_stale_generation(self):
        self.assert_refused(self.run_mode(request=dict(self.request, observed_registry_generation=40)),
                            "REGISTRY_GENERATION_NOT_OBSERVED_TIP")

    def test_duplicate_identity_on_every_surface(self):
        for task_id in ("EXISTING-001", "INDEXED-001"):
            req = copy.deepcopy(self.request)
            req["task_id"] = req["record"]["task_id"] = task_id
            self.assert_refused(self.run_mode(request=req), "TASK_IDENTITY_NOT_UNIQUE")
        tid = self.request["task_id"]
        for rel in (f"{crt.RECORDS}/{tid}.json", f"{crt.VECTORS}/{tid}.json", f"{crt.INDEX_SHARDS}/{tid}.json"):
            write(self.base / rel, {})
            self.assert_refused(self.run_mode(), "TASK_IDENTITY_NOT_UNIQUE")
            (self.base / rel).unlink()

    def test_claim_or_fence_in_the_manifest(self):
        req = copy.deepcopy(self.request)
        req["record"]["worker_claim"]["fence_ref"] = "SHWP-X-G1"
        self.assert_refused(self.run_mode(request=req), "WORKER_CLAIM_NOT_PROJECTION_ONLY")

    def test_completion_claim(self):
        req = copy.deepcopy(self.request)
        req["record"]["completion"]["claimed"] = True
        self.assert_refused(self.run_mode(request=req), "UNQUALIFIED_COMPLETION_PROHIBITED")

    def test_manual_or_underivable_vector(self):
        req = copy.deepcopy(self.request)
        req["record"]["cosv_task_vector"] = "10500000110000"
        self.assert_refused(self.run_mode(request=req), "COSV_NOT_DERIVABLE")
        req = copy.deepcopy(self.request)
        del req["vector"]["exact_metrics"]["blocker_count"]
        self.assert_refused(self.run_mode(request=req), "COSV_NOT_DERIVABLE")

    def test_record_schema_and_initial_state(self):
        req = copy.deepcopy(self.request)
        req["record"]["unexpected"] = 1
        self.assert_refused(self.run_mode(request=req), "CANONICAL_RECORD_SCHEMA_INVALID")
        req = copy.deepcopy(self.request)
        req["record"]["coordination_state"] = "CLAIMED"
        self.assert_refused(self.run_mode(request=req), "CANONICAL_RECORD_SCHEMA_INVALID")

    def test_request_schema(self):
        self.assert_refused(self.run_mode(request=dict(self.request, authority_effect="ALLOW")),
                            "REGISTRATION_REQUEST_SCHEMA_INVALID")
        req = dict(self.request)
        del req["vector"]
        self.assert_refused(self.run_mode(request=req), "REGISTRATION_REQUEST_SCHEMA_INVALID")
        path = self.tmp / "bad.json"
        path.write_text("{", encoding="utf-8")
        self.assert_refused(crt.run("plan", path, self.base), "REGISTRATION_REQUEST_SCHEMA_INVALID")

    def test_verify_refuses_unapplied_and_hand_edited_successors(self):
        head = self.tmp / "head"
        shutil.copytree(self.base, head)
        self.assert_refused(self.run_mode("verify", head=head), "REGISTRATION_NOT_APPLIED")
        crt.run("apply", self.manifest(), self.base, head)
        record = head / f"{crt.RECORDS}/{self.request['task_id']}.json"
        record.write_text(record.read_text().replace('"PROPOSED"', '"CLAIMABLE"'), encoding="utf-8")
        self.assert_refused(self.run_mode("verify", head=head), "REGISTRATION_BYTES_DIVERGE")

    def test_cli_exit_codes(self):
        ok = subprocess.run([sys.executable, str(SCRIPT), "plan", "--request", str(self.manifest()),
                             "--base", str(self.base)], capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertEqual(json.loads(ok.stdout)["disposition"], "ALLOW")
        bad = subprocess.run([sys.executable, str(SCRIPT), "plan", "--request",
                              str(self.manifest(dict(self.request, observed_registry_generation=1))),
                              "--base", str(self.base)], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        self.assertEqual(json.loads(bad.stderr)["failed_predicate"], "REGISTRY_GENERATION_NOT_OBSERVED_TIP")


class Surface(unittest.TestCase):
    def test_contract_names_the_same_surfaces_as_the_code(self):
        contract = json.loads((ROOT / "contracts/canonical-task-registration-transition.v1.json").read_text())
        self.assertEqual(contract["transition"]["entrypoint"], crt.ENTRYPOINT)
        self.assertEqual(contract["transition"]["workflow"], crt.WORKFLOW)
        self.assertEqual(contract["manifest"]["schema"], crt.REQUEST_SCHEMA)
        self.assertEqual(contract["receipt"]["schema"], crt.RECEIPT_SCHEMA)
        self.assertEqual(contract["non_allow_fields"], list(SIX))
        # The parent-existence predicate (REGISTRATION_PARENT_*) is defined in its own module, which derive() calls.
        source = SCRIPT.read_text() + (ROOT / "scripts" / "registration_parent_existence.py").read_text()
        for predicate in contract["predicates"]:
            self.assertIn(f'"{predicate}"', source)

    def test_workflow_is_read_only_and_never_dispatches_or_appends(self):
        text = (ROOT / crt.WORKFLOW).read_text()
        self.assertIn("contents: read", text)
        for forbidden in ("contents: write", "workflow_dispatch", "git push", "schedule:", "emit.py append"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
