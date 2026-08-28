from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workers" / "g18_resident_request_consumption_resolution_worker.py"
SPEC = importlib.util.spec_from_file_location("g18_resolution", SCRIPT)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


class G18ResidentRequestResolutionTests(unittest.TestCase):
    def test_hosted_surface_fails_closed_and_requires_escalation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            result=mod.run_resolution(root,root/"runtime",env={"GITHUB_ACTIONS":"true"})
        self.assertEqual(result["state"],"BLOCKED")
        self.assertEqual(result["transition_id"],"HOSTED_SURFACE_REJECTED")
        self.assertFalse(result["blocker"]["may_remain_blocked"])
        self.assertFalse(result["second_machine_required"])
        self.assertFalse(result["new_g18_claim_allowed"])

    def test_missing_resident_registry_attempts_canonical_v13_bootstrap_first(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            source=base/"source"; runtime=base/"runtime"
            (source/"scripts").mkdir(parents=True)
            (source/"scripts"/"bootstrap_sovereign_runtime.py").write_text("# bootstrap\n",encoding="utf-8")
            (source/"scripts"/"refresh_sovereign_worker_runtime_source.py").write_text("# refresh\n",encoding="utf-8")
            calls=[]
            def runner(command,**kwargs):
                calls.append(list(command))
                if "bootstrap_sovereign_runtime.py" in str(command[1]):
                    (runtime/"control").mkdir(parents=True,exist_ok=True)
                    (runtime/"control"/"worker-registry.json").write_text(json.dumps({
                        "tasks":[{
                            "task_id":mod.TARGET_TASK,
                            "state":"BLOCKED",
                            "claim_id":mod.EXPECTED_CLAIM,
                            "worker_id":"sovereign-runtime-activation-worker",
                            "worker_instance_id":"g18-instance",
                            "heartbeat_timing":{"fencing_token":mod.EXPECTED_FENCE}
                        }]
                    })+"\n",encoding="utf-8")
                    receipt=runtime/mod.BOOTSTRAP_RECEIPT_REL
                    receipt.parent.mkdir(parents=True,exist_ok=True)
                    receipt.write_text(json.dumps({"state":"COMPLETE","reason":"SOVEREIGN_RUNTIME_SELF_BOOTSTRAP_VERIFIED"})+"\n",encoding="utf-8")
                    return subprocess.CompletedProcess(command,0,stdout="",stderr="")
                if "refresh_sovereign_worker_runtime_source.py" in str(command[1]):
                    (runtime/"scripts").mkdir(parents=True,exist_ok=True)
                    (runtime/"scripts"/"consume_g18_resident_execution_request.py").write_text("# consumer\n",encoding="utf-8")
                    return subprocess.CompletedProcess(command,0,stdout="",stderr="")
                receipt=runtime/mod.CONSUMPTION_REL
                receipt.parent.mkdir(parents=True,exist_ok=True)
                receipt.write_text(json.dumps({
                    "state":"ATTEMPT_RECORDED",
                    "request_id":"RESIDENT-EXEC-G18-RESUME-FENCE18-001",
                    "request_sha256":"abc",
                    "runtime_execution_attempted":True,
                    "exact_existing_claim_observed":True,
                    "bridge_mode_valid":True
                })+"\n",encoding="utf-8")
                return subprocess.CompletedProcess(command,0,stdout="",stderr="")
            result=mod.run_resolution(source,runtime,runner=runner,env={})
        self.assertEqual(result["state"],"COMPLETED")
        self.assertEqual(result["transition_id"],"G18_RESIDENT_REQUEST_CONSUMPTION_VERIFIED")
        self.assertTrue(result["bootstrap_attempted"])
        self.assertEqual(result["bootstrap_returncode"],0)
        self.assertEqual(result["bootstrap_state"],"COMPLETE")
        self.assertEqual(len(calls),3)
        self.assertIn("--skip-post-bootstrap-stegfin",calls[0])
        self.assertIn("bootstrap_sovereign_runtime.py",calls[0][1])

    def test_failed_bootstrap_remains_active_fail_closed_resolution(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            source=base/"source"; runtime=base/"runtime"
            (source/"scripts").mkdir(parents=True)
            (source/"scripts"/"bootstrap_sovereign_runtime.py").write_text("# bootstrap\n",encoding="utf-8")
            def runner(command,**kwargs):
                receipt=runtime/mod.BOOTSTRAP_RECEIPT_REL
                receipt.parent.mkdir(parents=True,exist_ok=True)
                receipt.write_text(json.dumps({"state":"REVIEW_REQUIRED","reason":"SOVEREIGN_ACTIVATION_PROOF_INCOMPLETE"})+"\n",encoding="utf-8")
                return subprocess.CompletedProcess(command,1,stdout="",stderr="")
            result=mod.run_resolution(source,runtime,runner=runner,env={})
        self.assertEqual(result["state"],"BLOCKED")
        self.assertEqual(result["transition_id"],"SOVEREIGN_RESIDENT_BOOTSTRAP_REPAIR_REQUIRED")
        self.assertTrue(result["bootstrap_attempted"])
        self.assertEqual(result["blocker"]["dependency_class"],"INTERNAL_CAPABILITY")
        self.assertFalse(result["blocker"]["may_remain_blocked"])

    def test_exact_existing_g18_claim_is_required(self):
        with tempfile.TemporaryDirectory() as td:
            runtime=Path(td)
            (runtime/"control").mkdir()
            (runtime/"control"/"worker-registry.json").write_text(json.dumps({
                "tasks":[{
                    "task_id":mod.TARGET_TASK,
                    "state":"BLOCKED",
                    "claim_id":"wrong",
                    "heartbeat_timing":{"fencing_token":18}
                }]
            })+"\n",encoding="utf-8")
            self.assertIsNone(mod.exact_g18_claim(runtime))

    def test_success_refreshes_local_source_then_consumes_exact_request(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            source=base/"source"; runtime=base/"runtime"
            (source/"scripts").mkdir(parents=True)
            refresh_script=source/"scripts"/"refresh_sovereign_worker_runtime_source.py"
            refresh_script.write_text("# refresh\n",encoding="utf-8")
            (runtime/"control").mkdir(parents=True)
            (runtime/"control"/"worker-registry.json").write_text(json.dumps({
                "tasks":[{
                    "task_id":mod.TARGET_TASK,
                    "state":"BLOCKED",
                    "claim_id":mod.EXPECTED_CLAIM,
                    "worker_id":"sovereign-runtime-activation-worker",
                    "worker_instance_id":"g18-instance",
                    "heartbeat_timing":{"fencing_token":mod.EXPECTED_FENCE}
                }]
            })+"\n",encoding="utf-8")
            calls=[]
            def runner(command,**kwargs):
                calls.append(list(command))
                if "refresh_sovereign_worker_runtime_source.py" in str(command[1]):
                    (runtime/"scripts").mkdir(parents=True,exist_ok=True)
                    (runtime/"scripts"/"consume_g18_resident_execution_request.py").write_text("# consumer\n",encoding="utf-8")
                    return subprocess.CompletedProcess(command,0,stdout="",stderr="")
                receipt=runtime/mod.CONSUMPTION_REL
                receipt.parent.mkdir(parents=True,exist_ok=True)
                receipt.write_text(json.dumps({
                    "state":"ATTEMPT_RECORDED",
                    "request_id":"RESIDENT-EXEC-G18-RESUME-FENCE18-001",
                    "request_sha256":"abc",
                    "runtime_execution_attempted":True,
                    "exact_existing_claim_observed":True,
                    "bridge_mode_valid":True
                })+"\n",encoding="utf-8")
                return subprocess.CompletedProcess(command,0,stdout="",stderr="")
            result=mod.run_resolution(source,runtime,runner=runner,env={})
        self.assertEqual(result["state"],"COMPLETED")
        self.assertEqual(result["transition_id"],"G18_RESIDENT_REQUEST_CONSUMPTION_VERIFIED")
        self.assertTrue(result["runtime_execution_attempted"])
        self.assertEqual(len(calls),2)
        self.assertIn("refresh_sovereign_worker_runtime_source.py",calls[0][1])
        self.assertIn("consume_g18_resident_execution_request.py",calls[1][1])

    def test_registry_and_adapter_use_unique_resolution_capability(self):
        fragment=json.loads((ROOT/"control/worker-registry.d/g18-resident-request-consumption-resolution-001.json").read_text())
        adapter=json.loads((ROOT/"control/process-worker-adapters.d/g18-resident-request-consumption-resolution-001.json").read_text())
        caps={"runtime_observation","bounded_process_execution","durable_state_reconstruction","g18_resident_request_consumption_resolution","sovereign_runtime_self_bootstrap"}
        self.assertEqual(set(fragment["workers"][0]["capabilities"]),caps)
        self.assertEqual(set(adapter["adapters"][0]["capabilities"]),caps)
        self.assertEqual(fragment["tasks"][0]["state"],"HANDOFF_READY")
        self.assertGreater(fragment["tasks"][0]["admission"]["minimum_fencing_token_exclusive"],22-1)
        profiles=json.loads((ROOT/"control/worker-capability-profiles.json").read_text())
        profile=next(x for x in profiles["profiles"] if x["profile_id"]=="sovereign-runtime-worker-v1")
        self.assertIn("g18_resident_request_consumption_resolution",profile["allowed_capabilities"])
        self.assertIn("sovereign_runtime_self_bootstrap",profile["allowed_capabilities"])


if __name__ == "__main__":
    unittest.main()
