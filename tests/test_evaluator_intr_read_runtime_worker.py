from __future__ import annotations
import importlib.util, json, os, tempfile
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("evaluator_intr_read_runtime_worker",ROOT/"workers/evaluator_intr_read_runtime_worker.py")
assert SPEC and SPEC.loader
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class EvaluatorInTrReadRuntimeWorkerTests(unittest.TestCase):
    def invocation(self):
        return {
            "schema":"stegverse.worker-invocation/v0.1",
            "task":{"task_id":mod.TASK_ID,"worker_id":mod.WORKER_ID,"claim_id":"c1","heartbeat_timing":{"fencing_token":44}},
            "handoff":{"authority":{"credential_authority":"TV/TVC","github_token_required":False,"non_tv_tvc_secret_or_token_allowed":False,"heartbeat_grants_execution_authority":False}}
        }
    def test_valid_invocation_requires_fence_and_preserves_authority(self):
        task=mod.validate_invocation(self.invocation())
        self.assertEqual(task["claim_id"],"c1")
    def test_missing_route_config_is_machine_retryable(self):
        with tempfile.TemporaryDirectory() as td:
            prior=os.environ.get(mod.CONFIG_ENV)
            os.environ[mod.CONFIG_ENV]=str(Path(td)/"missing.json")
            try:
                with self.assertRaises(mod.RoutePending):
                    mod.load_config()
            finally:
                if prior is None: os.environ.pop(mod.CONFIG_ENV,None)
                else: os.environ[mod.CONFIG_ENV]=prior
    def test_public_route_requires_tls_material(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            for name in ("Site","StegOS","runtime"): (base/name).mkdir()
            cfg=base/"route.json"
            cfg.write_text(json.dumps({
                "site_root":str(base/"Site"),"stegos_root":str(base/"StegOS"),"runtime_root":str(base/"runtime"),
                "host":"0.0.0.0","port":8765,"allowed_origin":"https://stegverse.org","boundary_identity_ref":"node:1",
                "credential_authority":"TV/TVC","github_token_runtime_authority":"NONE"
            }))
            prior=os.environ.get(mod.CONFIG_ENV); os.environ[mod.CONFIG_ENV]=str(cfg)
            try:
                with self.assertRaises(mod.RoutePending):
                    mod.load_config()
            finally:
                if prior is None: os.environ.pop(mod.CONFIG_ENV,None)
                else: os.environ[mod.CONFIG_ENV]=prior
    def test_hosted_execution_fails_closed(self):
        inv=self.invocation()
        prior=os.environ.get("GITHUB_ACTIONS"); os.environ["GITHUB_ACTIONS"]="true"
        try:
            with self.assertRaises(RuntimeError):
                mod.execute(inv)
        finally:
            if prior is None: os.environ.pop("GITHUB_ACTIONS",None)
            else: os.environ["GITHUB_ACTIONS"]=prior

if __name__=="__main__": unittest.main()
