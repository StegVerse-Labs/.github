import importlib, importlib.util, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sdk_eval_consumer", ROOT/"scripts/consume_sdk_evaluator_governance_posture_request.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)


FAKE_ENTRYPOINT=(
    "def run_evaluator_governance_manifest(manifest, *, custody_db, host_identity='x'):\n"
    "    return {'posture_bound_execution':True,'sdk_resolved_posture':False,"
    "'intr_security_posture_binding':{'resolution_authority':'INTERLOCK_INTR',"
    "'transition_request_sha256':'sha256:t','payload_sha256':'sha256:p',"
    "'projection':{'posture_instance':{'instance_id':'pi-1','instance_sha256':'sha256:i'}}}}\n"
)
# A different `stegverse` package another test, an installed SDK or a second
# checkout may already have imported into this process.
DECOY_ENTRYPOINT=(
    "def run_evaluator_governance_manifest(manifest, *, custody_db, host_identity='x'):\n"
    "    raise ValueError('decoy stegverse package answered instead of STEGVERSE_SDK_SOURCE_ROOT')\n"
)


def write_fake_sdk(root, entrypoint=FAKE_ENTRYPOINT):
    (root/"stegverse").mkdir(parents=True)
    (root/"stegverse/__init__.py").write_text("")
    (root/"stegverse/evaluator_governance_runtime.py").write_text(entrypoint)


def stegverse_modules():
    return {name: module for name, module in sys.modules.items() if name=="stegverse" or name.startswith("stegverse.")}


class SDKEvaluatorGovernancePostureResidentTests(unittest.TestCase):
    def test_missing_manifest_waits_without_claim(self):
        with tempfile.TemporaryDirectory() as td:
            runtime=Path(td)
            p=runtime/MOD.REQUEST_REL; p.parent.mkdir(parents=True)
            p.write_text((ROOT/MOD.REQUEST_REL).read_text())
            result=MOD.consume(ROOT,runtime,env={})
            self.assertEqual(result["state"],"INPUT_NOT_MATERIALIZED")
            self.assertFalse(result["runtime_execution_attempted"])

    def test_exact_manifest_calls_sdk_entrypoint_and_retains_binding(self):
        with tempfile.TemporaryDirectory() as td:
            runtime=Path(td)/"runtime"; sdk=Path(td)/"sdk"
            runtime.mkdir()
            write_fake_sdk(sdk)
            rp=runtime/MOD.REQUEST_REL; rp.parent.mkdir(parents=True)
            rp.write_text((ROOT/MOD.REQUEST_REL).read_text())
            mp=runtime/"runtime-state/sdk-evaluator-governance-posture/manifest.json"; mp.parent.mkdir(parents=True)
            manifest={"schema":"x","manifest_sha256":"sha256:m","extensions":{"governance_reference_graph":{"graph_sha256":"sha256:g"}}}
            mp.write_text(json.dumps(manifest,sort_keys=True))
            org_root=Path(td)/"org-ledger"
            with patch.dict("os.environ",{"STEGVERSE_ORG_LEDGER_ROOT":str(org_root)}):
                result=MOD.consume(ROOT,runtime,env={"STEGVERSE_SDK_SOURCE_ROOT":str(sdk)})
            head=json.loads((org_root/"HEAD.json").read_text())
            org_receipt=json.loads((org_root/"receipts"/(head["receipt_sha256"][7:]+".json")).read_text())
            source=json.loads((org_root/"source-receipts"/(org_receipt["source_transition_sha256"][7:]+".json")).read_text())
            assert source["required_evidence_manifest"][0]["encoding"]=="canonical-json"
            assert source["required_evidence_manifest"][0]["content"]["task_id"]==MOD.TARGET_TASK
            assert org_receipt["source_transition_sha256"]==org_receipt["canonical_state_transition_receipt_sha256"]
            self.assertEqual(result["state"],"COMPLETED")
            self.assertEqual(result["organization_recording_state"],"RECORDED")
            self.assertFalse(result["master_records_submission_performed"])
            self.assertEqual(result["master_records_role"],"ORGANIZATION_RECORDS_AND_RECONSTRUCTION_ONLY")
            self.assertTrue(result["posture_bound_execution"])
            self.assertFalse(result["sdk_resolved_posture"])
            self.assertEqual(result["resolution_authority"],"INTERLOCK_INTR")
            self.assertEqual(result["graph_sha256"],"sha256:g")
            self.assertEqual(result["transition_request_sha256"],"sha256:t")
            self.assertTrue((runtime/MOD.RECEIPT_REL).is_file())

    def test_declared_sdk_root_wins_over_an_already_imported_stegverse_package(self):
        """Regression: the suite-order failure seen when an earlier test imported a real SDK."""
        with tempfile.TemporaryDirectory() as td:
            runtime=Path(td)/"runtime"; sdk=Path(td)/"sdk"; decoy=Path(td)/"decoy"
            runtime.mkdir()
            write_fake_sdk(sdk); write_fake_sdk(decoy, DECOY_ENTRYPOINT)
            saved_modules=stegverse_modules(); saved_path=list(sys.path)
            try:
                for name in saved_modules:
                    del sys.modules[name]
                sys.path.insert(0,str(decoy))
                importlib.import_module("stegverse.evaluator_governance_runtime")
                before_modules=stegverse_modules(); before_path=list(sys.path)
                rp=runtime/MOD.REQUEST_REL; rp.parent.mkdir(parents=True)
                rp.write_text((ROOT/MOD.REQUEST_REL).read_text())
                mp=runtime/"runtime-state/sdk-evaluator-governance-posture/manifest.json"; mp.parent.mkdir(parents=True)
                mp.write_text(json.dumps({"schema":"x","manifest_sha256":"sha256:m","extensions":{"governance_reference_graph":{"graph_sha256":"sha256:g"}}},sort_keys=True))
                with patch.dict("os.environ",{"STEGVERSE_ORG_LEDGER_ROOT":str(Path(td)/"org-ledger")}):
                    result=MOD.consume(ROOT,runtime,env={"STEGVERSE_SDK_SOURCE_ROOT":str(sdk)})
                self.assertEqual(result["state"],"COMPLETED")
                self.assertEqual(result["transition_request_sha256"],"sha256:t")
                # The caller's stegverse modules are restored exactly, and the
                # declared SDK root is not left on sys.path. (consume also adds
                # this repository's workers/ directory, as before.)
                self.assertEqual(stegverse_modules(),before_modules)
                workers=str((ROOT/"workers").resolve())
                self.assertEqual([p for p in sys.path if p!=workers],[p for p in before_path if p!=workers])
                self.assertNotIn(str(sdk.resolve()),sys.path)
            finally:
                for name in list(stegverse_modules()):
                    del sys.modules[name]
                sys.modules.update(saved_modules)
                sys.path[:]=saved_path

    def test_entrypoint_outside_the_declared_root_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            sdk=Path(td)/"sdk"; sdk.mkdir()
            with MOD._declared_sdk_import_scope([sdk.resolve()]):
                pass
            self.assertFalse(MOD._module_is_under(str(Path(td)/"elsewhere/x.py"),sdk))
            self.assertTrue(MOD._module_is_under(str(sdk/"stegverse/x.py"),sdk))

if __name__=="__main__":
    unittest.main()
