#!/usr/bin/env python3
"""The REAL-GOVERNANCE-ASSESSMENT-SAMPLE-001 request spec is wired, non-authorizing, and moves no state.

PROPOSED -> INGRESS_ADMITTED needs authentic Interlock/InTr ingress and consumption
receipts produced by the resident dispatcher cycle actually running. No synthetic or
test receipt may count toward that transition.
"""
import hashlib
import importlib.util
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "REAL-GOVERNANCE-ASSESSMENT-SAMPLE-001"
CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"
REQUEST = ROOT / "control" / "resident-execution-request.d" / "canonical-work-real-governance-assessment-sample-001.json"
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
CONSUMPTION_REL = "receipts/sovereign-host/canonical-work-real-governance-assessment-sample-request-consumption.latest.json"


def load_consumer():
    spec = importlib.util.spec_from_file_location("canonical_work_real_governance_consumer_test", CONSUMER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def registry_task():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows = [row for row in registry["tasks"] if row["task_id"] == TASK_ID]
    if rows:
        return rows[0]
    return json.loads((ROOT / "data" / "canonical-task-records" / f"{TASK_ID}.json").read_text(encoding="utf-8"))


class RealGovernanceAssessmentSampleRequestWiringTests(unittest.TestCase):
    def test_consumer_registers_exact_spec_once(self):
        consumer = load_consumer()
        matches = [row for row in consumer.mod.REQUEST_SPECS if row.get("task_id") == TASK_ID]
        self.assertEqual(len(matches), 1)
        row = matches[0]
        self.assertEqual(row["request_rel"].as_posix(), "control/resident-execution-request.d/canonical-work-real-governance-assessment-sample-001.json")
        self.assertEqual(row["consumption_rel"].as_posix(), CONSUMPTION_REL)
        self.assertEqual(row["bootstrap_runtime_rel"].as_posix(), "runtime/canonical-work-real-governance-assessment-sample")
        self.assertTrue((ROOT / row["request_rel"]).is_file())
        consumer.mod.validate_spec(row)

    def test_request_is_non_authorizing_and_valid_for_the_consumer(self):
        consumer = load_consumer()
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        consumer.mod.validate_request(request, consumer.REAL_GOVERNANCE_ASSESSMENT_SAMPLE_SPEC)
        self.assertEqual(request["task_id"], TASK_ID)
        self.assertEqual(request["authority_effect"], "NONE_REQUEST_ONLY")
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["advances_state"])
        self.assertTrue(request["stages_request_only"])
        self.assertEqual(request["coordination_state_effect"], "NONE_PROPOSED_UNCHANGED")
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertEqual(request["github_token_runtime_authority"], "NONE")
        self.assertFalse(request["second_machine_required"])
        self.assertFalse(request["network_source_fetch_allowed"])

    def test_wiring_adds_no_parallel_plane_dispatch_or_schedule(self):
        source = CONSUMER.read_text(encoding="utf-8")
        self.assertIn("REAL_GOVERNANCE_ASSESSMENT_SAMPLE_SPEC", source)
        self.assertIn("mod.REQUEST_SPECS", source)
        self.assertNotIn("REAL_GOVERNANCE_ASSESSMENT_SAMPLE_DISPATCHER", source)
        self.assertNotIn("REAL_GOVERNANCE_ASSESSMENT_SAMPLE_SCHEDULER", source)
        for workflow in (ROOT / ".github" / "workflows").glob("*.y*ml"):
            text = workflow.read_text(encoding="utf-8")
            self.assertFalse(
                TASK_ID in text or "real-governance-assessment-sample" in text,
                f"workflow {workflow.name} must not carry or trigger the assessment sample request",
            )

    def test_source_holds_no_ingress_or_consumption_receipt_so_state_stays_proposed(self):
        task = registry_task()
        self.assertEqual(task["coordination_state"], "PROPOSED")
        self.assertIsNone(task["worker_claim"]["claim_ref"])
        self.assertIsNone(task["worker_claim"]["fence_ref"])
        self.assertFalse(task.get("runtime_refs"))
        self.assertFalse((ROOT / CONSUMPTION_REL).exists(), "a committed consumption receipt would be a non-authentic receipt")
        self.assertFalse((ROOT / "runtime" / "canonical-work-real-governance-assessment-sample").exists())
        # No committed ingress or consumption receipt may name this task.
        offenders = []
        for base in (ROOT / "receipts", ROOT / "runtime"):
            if not base.is_dir():
                continue
            for path in base.rglob("*.json"):
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                if TASK_ID in text and re.search(r"canonical-work-intr-materialization-(ingress|consumption)/v1", text):
                    offenders.append(path.as_posix())
        self.assertEqual(offenders, [])

    def test_synthetic_runner_result_without_authentic_ingress_moves_no_state(self):
        consumer = load_consumer()
        before = hashlib.sha256(REGISTRY.read_bytes()).hexdigest()

        def synthetic_runner(command, **kwargs):
            # A stand-in for the bootstrap: it produces no authentic ingress receipt.
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="FAIL_CLOSED: synthetic_test_runner_no_authentic_interlock_intr_ingress")

        with tempfile.TemporaryDirectory() as tmp:
            receipt = consumer.mod.consume_for_spec(
                ROOT, Path(tmp), consumer.REAL_GOVERNANCE_ASSESSMENT_SAMPLE_SPEC, runner=synthetic_runner, env={}
            )
            self.assertEqual(receipt["state"], "ATTEMPT_RECORDED")
            self.assertEqual(receipt["disposition"], "FAIL_CLOSED")
            self.assertFalse(receipt["claim_or_fence_minted"])
            self.assertEqual(receipt["authority_effect"], "NONE_CONSUMPTION_EVIDENCE_ONLY")
            self.assertFalse(receipt["request_grants_execution_authority"])
            runtime_task = json.loads((Path(tmp) / "data" / "canonical-task-registry.json").read_text(encoding="utf-8"))
            rows = [row for row in runtime_task["tasks"] if row["task_id"] == TASK_ID]
            if rows:
                self.assertEqual(rows[0]["coordination_state"], "PROPOSED")
                self.assertFalse(rows[0].get("runtime_refs"))
        self.assertEqual(hashlib.sha256(REGISTRY.read_bytes()).hexdigest(), before)
        self.assertFalse((ROOT / CONSUMPTION_REL).exists())


if __name__ == "__main__":
    unittest.main()
