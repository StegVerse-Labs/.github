from __future__ import annotations
import importlib.util, json, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("shwp_bootstrap",ROOT/"workers/shwp_manifest_intr_event_bootstrap.py")
assert SPEC and SPEC.loader
mod=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(mod)

class FakeServer:
    def __init__(self,address,runtime,max_requests):
        self.server_address=("127.0.0.1",43123);self.closed=False;self.handled=False
    def handle_request(self): self.handled=True
    def server_close(self): self.closed=True

class Tests(unittest.TestCase):
    def test_missing_existing_tvc_authorization_is_precise_nonallow_without_listener(self):
        with tempfile.TemporaryDirectory() as td:
            result=mod.run_cycle(ROOT,Path(td),env={"PATH":"/usr/bin","HOME":td})
        self.assertEqual(result["disposition"],"FAIL_CLOSED")
        self.assertEqual(result["failed_predicate"],"TV_TVC_RELAY_AUTHORIZATION_REQUIRED")
        self.assertFalse(result["shared_listener_started"])
        self.assertFalse(result["device_inventory_queried"])
        self.assertFalse(result["second_machine_required"])

    def test_existing_authorization_materializes_one_shared_loopback_listener(self):
        calls=[]
        with tempfile.TemporaryDirectory() as td:
            def runner(command,**kwargs):
                calls.append((command,kwargs))
                payload={"schema":"stegverse.shwp-manifest-invocation/v1","state":"FAIL_CLOSED","disposition":"FAIL_CLOSED","evaluation_boundary":"SDK_MANIFEST_TRANSPORT_ATTACHMENT","failed_predicate":"TEST_BOUNDARY","runtime_execution_attempted":False}
                return SimpleNamespace(returncode=1,stdout=json.dumps(payload)+"\n",stderr="")
            result=mod.run_cycle(ROOT,Path(td),runner=runner,env={"PATH":"/usr/bin","HOME":td,"STEGVERSE_TVC_RELAY_AUTHORIZATION_ID":"AUTH-EXISTING"},server_factory=FakeServer)
        self.assertTrue(result["shared_listener_started"])
        self.assertEqual(result["listener_max_requests"],1)
        self.assertFalse(result["second_listener_implementation_created"])
        self.assertEqual(result["failed_predicate"],"TEST_BOUNDARY")
        child_env=calls[0][1]["env"]
        self.assertEqual(child_env["STEGVERSE_UNIVERSAL_INTR_INGRESS_URL"],"http://127.0.0.1:43123/intr/materialization")
        self.assertEqual(child_env["STEGVERSE_TVC_RELAY_AUTHORIZATION_ID"],"AUTH-EXISTING")
        self.assertNotIn("GITHUB_TOKEN",child_env)

if __name__=="__main__":
    unittest.main()
