from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from heartbeat_runtime.independent_oscillator import PROTOCOL_ANCHOR_UNIX_NS
from heartbeat_runtime.intr_derived_carrier import derive_intr_carrier_signal
from heartbeat_runtime.intr_subsignal_runtime import persist_local_intr_subsignal

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("chain", ROOT / "scripts/consume_stegos_kv_intr_chain_request.py")
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

class StegOSKvIntrChainResidentRequestTests(unittest.TestCase):
    def shared_signal(self, root: Path, packet_id: str, receipt_hex: str):
        signal = derive_intr_carrier_signal(
            packet_id=packet_id,
            payload_hash="sha256:" + "6" * 64,
            sampled_unix_ms=PROTOCOL_ANCHOR_UNIX_NS // 1_000_000 + 777,
            packet_bytes=("{\"packet\":\"" + packet_id + "\"}").encode(),
            intr_transport_profile="stegverse.universal-intr.adjacent-hop/v1",
            boundary_from="DEVICE_SYSTEM",
            boundary_to="KV",
            packet_receipt_hash=receipt_hex,
        )
        persisted = persist_local_intr_subsignal(root=root, signal=signal)
        return signal, persisted

    def request(self):
        return {
            "schema":"stegverse.resident-execution-request/v1",
            "request_id":"RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-003",
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
                    hb_root = root / "heartbeat"
                    request_signal, request_shared = self.shared_signal(hb_root, "DEVICE-KV-REQ", "a" * 64)
                    response_signal, response_shared = self.shared_signal(hb_root, "DEVICE-KV-RESP", "b" * 64)
                    receipt.update({
                        "hb_derived_carrier_transport_observed":True,
                        "request_transported_on_hb_derived_carrier":True,
                        "response_transported_on_hb_derived_carrier":True,
                        "request_carrier_packet_recovery_verified":True,
                        "response_carrier_packet_recovery_verified":True,
                        "request_carrier_signal_id":request_signal["signal_id"],
                        "request_receipt_hash":"sha256:" + "a" * 64,
                        "request_shared_hb_signal_ref":request_shared["signal_ref"],
                        "request_shared_hb_signal_sha256":request_shared["signal_sha256"],
                        "response_carrier_signal_id":response_signal["signal_id"],
                        "response_receipt_hash":"sha256:" + "b" * 64,
                        "response_shared_hb_signal_ref":response_shared["signal_ref"],
                        "response_shared_hb_signal_sha256":response_shared["signal_sha256"],
                    })
                path.write_text(json.dumps(receipt)+"\n",encoding="utf-8")
                return SimpleNamespace(returncode=0,stdout=json.dumps({"task_id":task})+"\n",stderr="")
            result=mod.consume(root/"source",runtime,runner=runner,env={"PATH":"/bin","HOME":str(root),"STEGVERSE_HEARTBEAT_ROOT":str(root/"heartbeat")})
            self.assertEqual(result["state"],"COMPLETED")
            self.assertEqual(calls,[row[0] for row in mod.STEPS])

    def test_legacy_device_kv_terminal_without_hb_carrier_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); runtime=self._runtime(root)
            step=next(row for row in mod.STEPS if row[0]==mod.DEVICE_KV_TASK_ID)
            path=runtime/step[1]; path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps({"state":step[2],"transition_id":step[3]})+"\n",encoding="utf-8")
            hb_env={"STEGVERSE_HEARTBEAT_ROOT":str(root/"heartbeat")}
            self.assertFalse(mod.terminal(runtime,step,hb_env))
            value={
                "state":step[2],"transition_id":step[3],
                "hb_derived_carrier_transport_observed":True,
                "request_transported_on_hb_derived_carrier":True,
                "response_transported_on_hb_derived_carrier":True,
                "request_carrier_packet_recovery_verified":True,
                "response_carrier_packet_recovery_verified":True,
            }
            path.write_text(json.dumps(value)+"\n",encoding="utf-8")
            self.assertFalse(mod.terminal(runtime,step,hb_env))
            request_signal, request_shared = self.shared_signal(root/"heartbeat","LEGACY-REQ","c"*64)
            response_signal, response_shared = self.shared_signal(root/"heartbeat","LEGACY-RESP","d"*64)
            value.update({
                "request_carrier_signal_id":request_signal["signal_id"],
                "request_receipt_hash":"sha256:"+"c"*64,
                "request_shared_hb_signal_ref":request_shared["signal_ref"],
                "request_shared_hb_signal_sha256":request_shared["signal_sha256"],
                "response_carrier_signal_id":response_signal["signal_id"],
                "response_receipt_hash":"sha256:"+"d"*64,
                "response_shared_hb_signal_ref":response_shared["signal_ref"],
                "response_shared_hb_signal_sha256":response_shared["signal_sha256"],
            })
            path.write_text(json.dumps(value)+"\n",encoding="utf-8")
            self.assertTrue(mod.terminal(runtime,step,hb_env))
            value["request_shared_hb_signal_sha256"]="0"*64
            path.write_text(json.dumps(value)+"\n",encoding="utf-8")
            self.assertFalse(mod.terminal(runtime,step,hb_env))

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
