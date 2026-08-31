from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("chain", ROOT / "scripts/consume_stegos_kv_intr_chain_request.py")
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

class StegOSKvIntrChainResidentRequestTests(unittest.TestCase):
    def request(self):
        return {
            "schema":"stegverse.resident-execution-request/v1",
            "request_id":"RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-002",
            "state":"REQUESTED","task_id":mod.CHAIN_TASK_ID,"mode":mod.MODE,
            "entrypoint":str(mod.ENTRYPOINT),"steps":[row[0] for row in mod.STEPS],
            "credential_authority":"TV/TVC","github_token_required":False,
            "github_token_runtime_authority":"NONE","heartbeat_grants_execution_authority":False,
            "request_granted_authority":False,"network_source_fetch_allowed":False,
            "second_machine_required":False,"authority_effect":"NONE_REQUEST_ONLY",
        }

    def _runtime(self, root):
        runtime = root / "runtime"
        (runtime / mod.REQUEST_REL).parent.mkdir(parents=True)
        (runtime / mod.REQUEST_REL).write_text(json.dumps(self.request())+"\n", encoding="utf-8")
        (runtime / mod.ENTRYPOINT).parent.mkdir(parents=True)
        (runtime / mod.ENTRYPOINT).write_text("# target\n", encoding="utf-8")
        return runtime

    def test_chain_advances_only_after_terminal_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); runtime=self._runtime(root); calls=[]
            def runner(command, **kwargs):
                task=command[command.index("--task-id")+1]; calls.append(task)
                step=next(row for row in mod.STEPS if row[0]==task)
                path=runtime/step[1]; path.parent.mkdir(parents=True,exist_ok=True)
                receipt={"state":step[2],"transition_id":step[3]}
                if task == mod.DEVICE_KV_TASK_ID:
                    receipt.update({
                        "hb_derived_carrier_transport_observed":True,
                        "request_transported_on_hb_derived_carrier":True,
                        "response_transported_on_hb_derived_carrier":True,
                        "request_carrier_packet_recovery_verified":True,
                        "response_carrier_packet_recovery_verified":True,
                    })
                path.write_text(json.dumps(receipt)+"\n",encoding="utf-8")
                return SimpleNamespace(returncode=0,stdout=json.dumps({"task_id":task})+"\n",stderr="")
            result=mod.consume(root/"source",runtime,runner=runner,env={"PATH":"/bin","HOME":str(root)})
            self.assertEqual(result["state"],"COMPLETED")
            self.assertEqual(calls,[row[0] for row in mod.STEPS])

    def test_legacy_device_kv_terminal_without_hb_carrier_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); runtime=self._runtime(root)
            step=next(row for row in mod.STEPS if row[0]==mod.DEVICE_KV_TASK_ID)
            path=runtime/step[1]; path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps({"state":step[2],"transition_id":step[3]})+"\n",encoding="utf-8")
            self.assertFalse(mod.terminal(runtime,step))
            value={
                "state":step[2],"transition_id":step[3],
                "hb_derived_carrier_transport_observed":True,
                "request_transported_on_hb_derived_carrier":True,
                "response_transported_on_hb_derived_carrier":True,
                "request_carrier_packet_recovery_verified":True,
                "response_carrier_packet_recovery_verified":True,
            }
            path.write_text(json.dumps(value)+"\n",encoding="utf-8")
            self.assertTrue(mod.terminal(runtime,step))

    def test_chain_stops_at_first_nonterminal_step(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); runtime=self._runtime(root); calls=[]
            def runner(command, **kwargs):
                task=command[command.index("--task-id")+1]; calls.append(task)
                return SimpleNamespace(returncode=0,stdout=json.dumps({"task_id":task,"state":"BLOCKED"})+"\n",stderr="")
            result=mod.consume(root/"source",runtime,runner=runner,env={"PATH":"/bin","HOME":str(root)})
            self.assertEqual(result["state"],"ATTEMPT_RECORDED")
            self.assertEqual(result["blocked_step"],mod.STEPS[0][0])
            self.assertEqual(calls,[mod.STEPS[0][0]])

    def test_request_and_dispatch_are_fail_closed_and_wired(self):
        bad=self.request(); bad["github_token_required"]=True
        with self.assertRaises(RuntimeError): mod.validate_request(bad)
        bad=self.request(); bad["steps"]=list(reversed(bad["steps"]))
        with self.assertRaises(RuntimeError): mod.validate_request(bad)
        refresh_execute=(ROOT/"scripts/refresh_and_execute_resident_task.py").read_text()
        refresh_dispatch=(ROOT/"scripts/refresh_and_dispatch_resident_requests.py").read_text()
        dispatcher=(ROOT/"scripts/dispatch_resident_execution_requests.py").read_text()
        self.assertIn('"STEGVERSE_KV_SOURCE_ROOT"',refresh_execute)
        self.assertIn('"STEGVERSE_KV_SOURCE_ROOT"',refresh_dispatch)
        self.assertIn('"STEGVERSE_KV_SOURCE_ROOT"',dispatcher)
        self.assertIn('"STEGVERSE_KV_ROOT"',refresh_execute)
        self.assertIn('"STEGVERSE_KV_ROOT"',refresh_dispatch)
        self.assertIn('"STEGVERSE_KV_ROOT"',dispatcher)
        self.assertIn('"stegos_kv_intr_chain"',refresh_dispatch)
        self.assertIn('("stegos_kv_intr_chain", "scripts/consume_stegos_kv_intr_chain_request.py")',dispatcher)

if __name__ == "__main__":
    unittest.main()
