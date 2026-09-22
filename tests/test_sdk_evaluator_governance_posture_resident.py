import importlib.util, json, tempfile, unittest
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
