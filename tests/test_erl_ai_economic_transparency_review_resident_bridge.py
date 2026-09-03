from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "erl_review_consumer",
    ROOT/"scripts/consume_erl_ai_economic_transparency_review_request.py",
)
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class ERLAIEconomicTransparencyResidentBridgeTests(unittest.TestCase):
    def request(self):
        return json.loads(
            (ROOT/"control/resident-execution-request.d/erl-ai-economic-transparency-review-001.json").read_text()
        )

    def bridge(self):
        return {
            "schema":"stegverse.resident-refresh-targeted-execution/v2",
            "mode":mod.TARGET_MODE,
            "task_id":mod.TARGET_TASK,
            "runtime_execution_attempted":True,
            "network_fetch_performed":False,
            "github_token_runtime_authority":"NONE",
            "credential_authority":"TV/TVC",
            "authority_effect":"EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
            "execution_result":{"state":"COMPLETED"},
        }

    def test_request_is_intent_only(self):
        r=self.request()
        mod.validate_request(r)
        self.assertFalse(r["request_granted_authority"])
        self.assertFalse(r["heartbeat_grants_execution_authority"])
        self.assertFalse(r["github_token_required"])
        self.assertFalse(r["network_source_fetch_allowed"])
        self.assertFalse(r["provider_credential_material_allowed"])

    def test_consumer_is_exactly_once_and_strips_secrets(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            source=base/"source"
            runtime=base/"runtime"
            source.mkdir()
            (runtime/mod.REQUEST_REL).parent.mkdir(parents=True)
            (runtime/mod.REQUEST_REL).write_text(json.dumps(self.request())+"\n")
            (runtime/mod.TARGET_ENTRYPOINT).parent.mkdir(parents=True,exist_ok=True)
            (runtime/mod.TARGET_ENTRYPOINT).write_text("# bridge\n")
            calls=[]
            def runner(command,**kwargs):
                calls.append((command,kwargs))
                return SimpleNamespace(returncode=0,stdout=json.dumps(self.bridge())+"\n",stderr="")
            env={
                "PATH":"/bin",
                "HOME":"/home/sv",
                "STEGVERSE_HEARTBEAT_ROOT":"/srv/runtime",
                "GITHUB_TOKEN":"forbidden",
                "OPENAI_API_KEY":"forbidden",
                "ANTHROPIC_API_KEY":"forbidden",
                "PRIVATE_KEY":"forbidden",
            }
            first=mod.consume(source,runtime,runner=runner,env=env)
            self.assertEqual(first["state"],"ATTEMPT_RECORDED")
            self.assertEqual(len(calls),1)
            forwarded=calls[0][1]["env"]
            self.assertEqual(forwarded["STEGVERSE_HEARTBEAT_ROOT"],"/srv/runtime")
            self.assertNotIn("GITHUB_TOKEN",forwarded)
            self.assertNotIn("OPENAI_API_KEY",forwarded)
            self.assertNotIn("ANTHROPIC_API_KEY",forwarded)
            self.assertNotIn("PRIVATE_KEY",forwarded)
            second=mod.consume(source,runtime,runner=runner,env=env)
            self.assertEqual(second["state"],"ALREADY_CONSUMED")
            self.assertEqual(len(calls),1)

    def test_hosted_environment_fails_before_execution(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            source=base/"source"
            runtime=base/"runtime"
            source.mkdir()
            (runtime/mod.REQUEST_REL).parent.mkdir(parents=True)
            (runtime/mod.REQUEST_REL).write_text(json.dumps(self.request())+"\n")
            (runtime/mod.TARGET_ENTRYPOINT).parent.mkdir(parents=True,exist_ok=True)
            (runtime/mod.TARGET_ENTRYPOINT).write_text("# bridge\n")
            calls=[]
            def runner(*args,**kwargs):
                calls.append(args)
                return SimpleNamespace(returncode=0,stdout="",stderr="")
            with self.assertRaises(RuntimeError):
                mod.consume(source,runtime,runner=runner,env={"PATH":"/bin","GITHUB_ACTIONS":"true"})
            self.assertEqual(calls,[])

    def test_wiring_is_materialized(self):
        dispatcher=(ROOT/"scripts/dispatch_resident_execution_requests.py").read_text()
        refresh=(ROOT/"scripts/refresh_sovereign_worker_runtime_source.py").read_text()
        refresh_base=(ROOT/"scripts/refresh_sovereign_worker_runtime_source_base.py").read_text()
        install=(ROOT/"scripts/install_sovereign_worker_source_refresh_service.py").read_text()
        self.assertIn('("erl_ai_economic_transparency_review", "scripts/consume_erl_ai_economic_transparency_review_request.py")',dispatcher)
        self.assertIn('Path("scripts/consume_erl_ai_economic_transparency_review_request.py")',refresh)
        self.assertIn('Path("scripts/consume_erl_ai_economic_transparency_review_request.py")',refresh_base)
        self.assertIn('Path("review-packages")',refresh)
        self.assertIn('Path("review-packages")',refresh_base)
        self.assertIn('source / "review-packages"',install)
        self.assertTrue((ROOT/"review-packages/erl-ai-economic-transparency-001/manifest.json").is_file())
        self.assertTrue((ROOT/"workers/erl_ai_economic_transparency_review_worker.py").is_file())

if __name__=="__main__":
    unittest.main()
