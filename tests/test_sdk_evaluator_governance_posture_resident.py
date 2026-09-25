import importlib.util, json, tempfile, unittest, types, sys
from unittest.mock import patch
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sdk_eval_consumer", ROOT/"scripts/consume_sdk_evaluator_governance_posture_request.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

class SDKEvaluatorGovernancePostureResidentTests(unittest.TestCase):
    def test_missing_manifest_waits_without_claim(self):
        with tempfile.TemporaryDirectory() as td:
            runtime=Path(td)
            p=runtime/MOD.REQUEST_REL; p.parent.mkdir(parents=True)
            p.write_text((ROOT/MOD.REQUEST_REL).read_text())
            result=MOD.consume(ROOT,runtime,env={})
            self.assertEqual(result["state"],"INPUT_NOT_MATERIALIZED")
            self.assertFalse(result["runtime_execution_attempted"])

    def test_exact_source_staging_readback_precedes_existing_sdk_execution(self):
        with tempfile.TemporaryDirectory() as td:
            runtime=Path(td)/"runtime"; runtime.mkdir()
            sdk=Path(td)/"sdk"; sdk.mkdir()
            rp=runtime/MOD.REQUEST_REL; rp.parent.mkdir(parents=True)
            request=json.loads((ROOT/MOD.REQUEST_REL).read_text())
            rp.write_text(json.dumps(request))
            archive=types.ModuleType("stegverse.evaluator_historical_source_recovery")
            manifest={"schema":"synthetic-only","extensions":{}}
            stage={
                "state":"HISTORICAL_SOURCE_STAGED_NOT_RUNTIME_PROVEN",
                "artifact_id":request["historical_source_artifact_id"],
                "manifest_sha256":request["historical_manifest_sha256"],
                "manifest_ref":request["manifest_ref"],
                "authority_effect":"NONE_SOURCE_STAGING_ONLY",
            }
            def stage_source(*,runtime_root,request):
                mp=runtime_root/Path(request["manifest_ref"]);mp.parent.mkdir(parents=True,exist_ok=True)
                mp.write_text(json.dumps(manifest))
                sp=runtime_root/"runtime-state/sdk-evaluator-governance-posture/source-evidence-reconstruction.json"
                sp.write_text(json.dumps(stage))
                return stage
            archive.materialize_historical_source=stage_source
            runner=types.ModuleType("stegverse.evaluator_governance_runtime")
            runner.run_evaluator_governance_manifest=lambda *a,**k:{
                "posture_bound_execution":False,"sdk_resolved_posture":False}
            real_hash=MOD.file_sha256
            def synthetic_hash(p):
                if Path(p).name=="manifest.json":
                    return request["historical_manifest_sha256"]
                return real_hash(p)
            with patch.dict(sys.modules,{
                "stegverse.evaluator_historical_source_recovery":archive,
                "stegverse.evaluator_governance_runtime":runner,
            }),patch.object(MOD,"file_sha256",side_effect=synthetic_hash):
                out=MOD.consume(ROOT,runtime,env={"STEGVERSE_SDK_SOURCE_ROOT":str(sdk)})
            self.assertEqual(out["source_staging_state"],"HISTORICAL_SOURCE_STAGED_NOT_RUNTIME_PROVEN")
            self.assertEqual(out["historical_source_artifact_id"],10176800336)
            self.assertEqual(out["state"],"MASTER_RECORDS_VALIDATION_PENDING_OR_FAILED")
            self.assertFalse(out["posture_bound_execution"])

    def test_forged_staging_receipt_fails_before_execution(self):
        with tempfile.TemporaryDirectory() as td:
            runtime=Path(td)/"runtime";runtime.mkdir()
            sdk=Path(td)/"sdk";sdk.mkdir()
            rp=runtime/MOD.REQUEST_REL;rp.parent.mkdir(parents=True)
            request=json.loads((ROOT/MOD.REQUEST_REL).read_text());rp.write_text(json.dumps(request))
            archive=types.ModuleType("stegverse.evaluator_historical_source_recovery")
            def forged(*,runtime_root,request):
                mp=runtime_root/Path(request["manifest_ref"]);mp.parent.mkdir(parents=True)
                mp.write_text("{}")
                sp=runtime_root/"runtime-state/sdk-evaluator-governance-posture/source-evidence-reconstruction.json"
                sp.write_text(json.dumps({"artifact_id":0,"state":"FAKE"}))
                return {"artifact_id":request["historical_source_artifact_id"],
                        "state":"HISTORICAL_SOURCE_STAGED_NOT_RUNTIME_PROVEN"}
            archive.materialize_historical_source=forged
            with patch.dict(sys.modules,{"stegverse.evaluator_historical_source_recovery":archive}),patch.object(MOD,"file_sha256",return_value=request["historical_manifest_sha256"]):
                out=MOD.consume(ROOT,runtime,env={"STEGVERSE_SDK_SOURCE_ROOT":str(sdk)})
            self.assertEqual(out["state"],"SOURCE_MATERIALIZATION_REJECTED")
            self.assertEqual(out["failure_class"],"EXACT_SOURCE_STAGING_RECEIPT_READBACK_MISMATCH")
            self.assertFalse(out["runtime_execution_attempted"])

    def test_exact_manifest_calls_sdk_entrypoint_and_retains_binding(self):
        with tempfile.TemporaryDirectory() as td:
            runtime=Path(td)/"runtime"; sdk=Path(td)/"sdk"
            runtime.mkdir(); (sdk/"stegverse").mkdir(parents=True)
            (sdk/"stegverse/__init__.py").write_text("")
            (sdk/"stegverse/evaluator_governance_runtime.py").write_text(
                "def run_evaluator_governance_manifest(manifest, *, custody_db, host_identity='x'):\n"
                "    return {'posture_bound_execution':True,'sdk_resolved_posture':False,"
                "'intr_security_posture_binding':{'resolution_authority':'INTERLOCK_INTR',"
                "'transition_request_sha256':'sha256:t','payload_sha256':'sha256:p',"
                "'projection':{'posture_instance':{'instance_id':'pi-1','instance_sha256':'sha256:i'}}}}\n"
            )
            rp=runtime/MOD.REQUEST_REL; rp.parent.mkdir(parents=True)
            rp.write_text((ROOT/MOD.REQUEST_REL).read_text())
            mp=runtime/"runtime-state/sdk-evaluator-governance-posture/manifest.json"; mp.parent.mkdir(parents=True)
            manifest={"schema":"x","manifest_sha256":"sha256:m","extensions":{"governance_reference_graph":{"graph_sha256":"sha256:g"}}}
            mp.write_text(json.dumps(manifest,sort_keys=True))
            result=MOD.consume(ROOT,runtime,env={"STEGVERSE_SDK_SOURCE_ROOT":str(sdk)})
            self.assertEqual(result["state"],"MASTER_RECORDS_VALIDATION_PENDING_OR_FAILED")
            self.assertEqual(result["master_records_reason"],"CANONICAL_MASTER_RECORDS_CUSTODY_SURFACE_UNAVAILABLE")
            self.assertTrue(result["posture_bound_execution"])
            self.assertFalse(result["sdk_resolved_posture"])
            self.assertEqual(result["resolution_authority"],"INTERLOCK_INTR")
            self.assertEqual(result["graph_sha256"],"sha256:g")
            self.assertEqual(result["transition_request_sha256"],"sha256:t")
            self.assertTrue((runtime/MOD.RECEIPT_REL).is_file())

if __name__=="__main__":
    unittest.main()
