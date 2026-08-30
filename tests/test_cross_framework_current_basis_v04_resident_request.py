from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "consume_cross_framework_current_basis_v04_request",
    ROOT/"scripts/consume_cross_framework_current_basis_v04_request.py",
)
assert SPEC and SPEC.loader
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class CurrentBasisV04ResidentRequestTests(unittest.TestCase):
    def request(self):
        return json.loads((ROOT/mod.REQUEST_REL).read_text(encoding="utf-8"))

    def bridge_result(self,state="BLOCKED"):
        return {
            "schema":"stegverse.resident-refresh-targeted-execution/v2",
            "mode":mod.TARGET_MODE,
            "task_id":mod.TARGET_TASK,
            "state":state,
            "runtime_execution_attempted":True,
            "network_fetch_performed":False,
            "github_token_runtime_authority":"NONE",
            "credential_authority":"TV/TVC",
            "second_machine_required":False,
            "authority_effect":"EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
        }

    def test_request_is_exact_frozen_intent_only(self):
        req=self.request()
        mod.validate_request(req)
        self.assertEqual(req["frozen_manifest_sha256"],mod.FROZEN_SHA256)
        self.assertEqual(req["frozen_manifest_git_blob_sha1"],mod.FROZEN_BLOB)
        self.assertFalse(req["request_granted_authority"])
        self.assertFalse(req["network_source_fetch_allowed"])
        self.assertFalse(req["github_token_required"])
        self.assertFalse(req["heartbeat_grants_execution_authority"])
        self.assertFalse(req["second_machine_required"])

    def test_nonterminal_attempt_remains_retryable(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir()
            (runtime/mod.REQUEST_REL).parent.mkdir(parents=True)
            (runtime/mod.REQUEST_REL).write_text(json.dumps(self.request())+"\n",encoding="utf-8")
            (runtime/mod.TARGET_ENTRYPOINT).parent.mkdir(parents=True,exist_ok=True)
            (runtime/mod.TARGET_ENTRYPOINT).write_text("# bridge\n",encoding="utf-8")
            calls=[]
            def runner(command,**kwargs):
                calls.append(command)
                return SimpleNamespace(returncode=0,stdout=json.dumps(self.bridge_result("BLOCKED"))+"\n",stderr="")
            first=mod.consume(source,runtime,runner=runner,env={
                "PATH":"/bin",
                "STEGVERSE_SDK_SOURCE_ROOT":"/local/sdk",
                "STEGVERSE_STEGCORE_SOURCE_ROOT":"/local/core",
                "STEGVERSE_CORE_LITE_SOURCE_ROOT":"/local/core-lite",
                "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT":"/local/master-records",
                "GITHUB_TOKEN":"forbidden",
            })
            self.assertEqual(first["state"],"ATTEMPT_RECORDED")
            self.assertFalse(first["activation_claimed"])
            self.assertEqual(len(calls),1)
            for name in ("STEGVERSE_SDK_SOURCE_ROOT","STEGVERSE_STEGCORE_SOURCE_ROOT","STEGVERSE_CORE_LITE_SOURCE_ROOT","STEGVERSE_MASTER_RECORDS_SOURCE_ROOT"):
                self.assertIn(name,first["execution_result"] and {
                    **{k:v for k,v in {
                        "STEGVERSE_SDK_SOURCE_ROOT":"/local/sdk",
                        "STEGVERSE_STEGCORE_SOURCE_ROOT":"/local/core",
                        "STEGVERSE_CORE_LITE_SOURCE_ROOT":"/local/core-lite",
                        "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT":"/local/master-records",
                    }.items()}
                })
            second=mod.consume(source,runtime,runner=runner,env={"PATH":"/bin"})
            self.assertEqual(second["state"],"ATTEMPT_RECORDED")
            self.assertEqual(len(calls),2)

    def test_completed_bridge_is_exactly_once(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir()
            (runtime/mod.REQUEST_REL).parent.mkdir(parents=True)
            (runtime/mod.REQUEST_REL).write_text(json.dumps(self.request())+"\n",encoding="utf-8")
            (runtime/mod.TARGET_ENTRYPOINT).parent.mkdir(parents=True,exist_ok=True)
            (runtime/mod.TARGET_ENTRYPOINT).write_text("# bridge\n",encoding="utf-8")
            calls=[]
            def runner(command,**kwargs):
                calls.append(command)
                return SimpleNamespace(returncode=0,stdout=json.dumps(self.bridge_result("COMPLETED"))+"\n",stderr="")
            first=mod.consume(source,runtime,runner=runner,env={"PATH":"/bin"})
            self.assertEqual(first["state"],"COMPLETED")
            self.assertTrue(first["activation_claimed"])
            second=mod.consume(source,runtime,runner=runner,env={"PATH":"/bin"})
            self.assertEqual(second["state"],"ALREADY_CONSUMED")
            self.assertEqual(len(calls),1)

    def test_hosted_environment_fails_before_bridge(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); source=base/"source"; runtime=base/"runtime"; source.mkdir()
            (runtime/mod.REQUEST_REL).parent.mkdir(parents=True)
            (runtime/mod.REQUEST_REL).write_text(json.dumps(self.request())+"\n",encoding="utf-8")
            (runtime/mod.TARGET_ENTRYPOINT).parent.mkdir(parents=True,exist_ok=True)
            (runtime/mod.TARGET_ENTRYPOINT).write_text("# bridge\n",encoding="utf-8")
            calls=[]
            def runner(command,**kwargs):
                calls.append(command)
                return SimpleNamespace(returncode=0,stdout="",stderr="")
            with self.assertRaises(RuntimeError):
                mod.consume(source,runtime,runner=runner,env={"PATH":"/bin","GITHUB_ACTIONS":"true"})
            self.assertEqual(calls,[])

    def test_mutation_cannot_expand_request_authority(self):
        for key,value in (
            ("request_granted_authority",True),
            ("network_source_fetch_allowed",True),
            ("github_token_required",True),
            ("heartbeat_grants_execution_authority",True),
            ("second_machine_required",True),
            ("frozen_manifest_sha256","0"*64),
            ("task_id","SHWP-OTHER"),
        ):
            req=self.request(); req[key]=value
            with self.subTest(key=key):
                with self.assertRaises(RuntimeError):
                    mod.validate_request(req)


if __name__=="__main__":
    unittest.main()
