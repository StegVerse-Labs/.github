from __future__ import annotations
import importlib.util, json, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sv011_consumer",ROOT/"scripts/consume_sv011_phase5_resident_execution_request.py")
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class Tests(unittest.TestCase):
    def request(self):
        return json.loads((ROOT/"control/resident-execution-request.d/sv011-phase5-boundary-001.json").read_text())
    def bridge(self):
        return {"schema":"stegverse.resident-refresh-targeted-execution/v2","mode":mod.TARGET_MODE,"task_id":mod.TARGET_TASK,"runtime_execution_attempted":True,"network_fetch_performed":False,"github_token_runtime_authority":"NONE","credential_authority":"TV/TVC","authority_effect":"EXISTING_ADMITTED_TASK_AUTHORITY_ONLY","execution_result":{"state":"BLOCKED"}}
    def test_request_intent_only(self):
        r=self.request(); mod.validate_request(r)
        self.assertFalse(r["request_granted_authority"]); self.assertFalse(r["heartbeat_grants_execution_authority"]); self.assertFalse(r["github_token_required"]); self.assertFalse(r["network_source_fetch_allowed"])
    def test_consumer_exactly_once_and_nonsecret_locator(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir()
            (runtime/mod.REQUEST_REL).parent.mkdir(parents=True); (runtime/mod.REQUEST_REL).write_text(json.dumps(self.request())+"\n")
            (runtime/mod.TARGET_ENTRYPOINT).parent.mkdir(parents=True,exist_ok=True); (runtime/mod.TARGET_ENTRYPOINT).write_text("# bridge\n")
            calls=[]
            def runner(command,**kwargs):
                calls.append((command,kwargs)); return SimpleNamespace(returncode=0,stdout=json.dumps(self.bridge())+"\n",stderr="")
            env={"PATH":"/bin","HOME":"/home/sv","STEGVERSE_SV011_ORG_ROOT":"/srv/SV-011/.github","GITHUB_TOKEN":"forbidden","PRIVATE_KEY":"forbidden"}
            first=mod.consume(source,runtime,runner=runner,env=env)
            self.assertEqual(first["state"],"ATTEMPT_RECORDED"); self.assertEqual(len(calls),1)
            self.assertEqual(calls[0][1]["env"]["STEGVERSE_SV011_ORG_ROOT"],"/srv/SV-011/.github")
            self.assertNotIn("GITHUB_TOKEN",calls[0][1]["env"]); self.assertNotIn("PRIVATE_KEY",calls[0][1]["env"])
            second=mod.consume(source,runtime,runner=runner,env=env)
            self.assertEqual(second["state"],"ALREADY_CONSUMED"); self.assertEqual(len(calls),1)
    def test_hosted_fails_before_execution(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir()
            (runtime/mod.REQUEST_REL).parent.mkdir(parents=True); (runtime/mod.REQUEST_REL).write_text(json.dumps(self.request())+"\n")
            (runtime/mod.TARGET_ENTRYPOINT).parent.mkdir(parents=True,exist_ok=True); (runtime/mod.TARGET_ENTRYPOINT).write_text("# bridge\n")
            calls=[]
            def runner(*a,**k): calls.append(a); return SimpleNamespace(returncode=0,stdout="",stderr="")
            with self.assertRaises(RuntimeError): mod.consume(source,runtime,runner=runner,env={"PATH":"/bin","GITHUB_ACTIONS":"true"})
            self.assertEqual(calls,[])
    def test_wiring_is_materialized(self):
        dispatcher=(ROOT/"scripts/dispatch_resident_execution_requests.py").read_text()
        refresh=(ROOT/"scripts/refresh_sovereign_worker_runtime_source.py").read_text()
        bridge=(ROOT/"scripts/refresh_and_execute_resident_task.py").read_text()
        self.assertIn('("sv011_phase5", "scripts/consume_sv011_phase5_resident_execution_request.py")',dispatcher)
        self.assertIn('Path("scripts/consume_sv011_phase5_resident_execution_request.py")',refresh)
        self.assertIn('"STEGVERSE_SV011_ORG_ROOT"',dispatcher)
        self.assertIn('"STEGVERSE_SV011_ORG_ROOT"',bridge)
if __name__=="__main__": unittest.main()
