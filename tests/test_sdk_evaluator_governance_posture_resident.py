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
            self.assertEqual(result["missing"],"sdk_source_root_for_manifest_materialization")
            self.assertFalse(result["runtime_execution_attempted"])


    def test_missing_manifest_is_materialized_from_existing_sdk_builder_inputs(self):
        with tempfile.TemporaryDirectory() as td:
            runtime=Path(td)/"runtime"; sdk=Path(td)/"sdk"
            runtime.mkdir(); (sdk/"stegverse").mkdir(parents=True)
            (sdk/"stegverse/__init__.py").write_text("")
            (sdk/"stegverse/security_posture_request.py").write_text(
                "def build_security_posture_request(**kwargs):\n"
                "    return {'schema':'stegverse.sdk.security-posture-request.v1','task_id':kwargs['task_id'],"
                "'selected_tier':kwargs.get('selected_tier'),'selection_present':kwargs.get('selection_present',False),"
                "'organization_minimum_tier':kwargs.get('organization_minimum_tier','SECURE'),"
                "'data_class':kwargs.get('data_class'),'channel':kwargs.get('channel'),"
                "'authority_effect':'NONE_REQUEST_INPUT_ONLY'}\n"
            )
            (sdk/"stegverse/evaluator_manifest_builder.py").write_text(
                "def build_evaluator_governance_manifest(**kwargs):\n"
                "    return {'manifest_profile':'stegverse.ingress-manifest.v1',"
                "'source_framework':kwargs['source_framework'],'source_output_id':kwargs['source_output_id'],"
                "'payload':kwargs['data'],'extensions':{'stegverse_governance_request':kwargs['governance_request'],"
                "'evaluation_declaration':kwargs['evaluation_declaration'],"
                "'security_posture_request':kwargs['security_posture_request']}}\n"
            )
            (sdk/"stegverse/evaluator_governance_runtime.py").write_text(
                "def run_evaluator_governance_manifest(manifest, *, custody_db, host_identity='x'):\n"
                "    return {'posture_bound_execution':True,'sdk_resolved_posture':False,"
                "'intr_security_posture_binding':{'resolution_authority':'INTERLOCK_INTR',"
                "'transition_request_sha256':'sha256:t','payload_sha256':'sha256:p',"
                "'projection':{'posture_instance':{'instance_id':'pi-1','instance_sha256':'sha256:i'}}}}\n"
            )
            inputs={
                "inspection/examples/elan-relational-state-test1.json":{"event":"materialize"},
                "inspection/examples/elan-governance-request.example.json":{"candidate":{},"judgment":{},"signal":{},"execution":{},"capability":{},"continuity":{},"approval":{},"permission_present":True},
                "inspection/examples/elan-evaluation-declaration-test1.json":{"what":"test","how":"existing builder","why":"runtime proof","expected_observation":None},
            }
            for rel,value in inputs.items():
                p=sdk/rel; p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text(json.dumps(value,sort_keys=True))
            rp=runtime/MOD.REQUEST_REL; rp.parent.mkdir(parents=True)
            rp.write_text((ROOT/MOD.REQUEST_REL).read_text())
            result=MOD.consume(ROOT,runtime,env={"STEGVERSE_SDK_SOURCE_ROOT":str(sdk)})
            mp=runtime/"runtime-state/sdk-evaluator-governance-posture/manifest.json"
            self.assertTrue(mp.is_file())
            materialized=json.loads(mp.read_text())
            self.assertEqual(
                materialized["extensions"]["security_posture_request"]["task_id"],
                MOD.TARGET_TASK,
            )
            self.assertEqual(result["state"],"MASTER_RECORDS_VALIDATION_PENDING_OR_FAILED")
            self.assertEqual(result["master_records_reason"],"CANONICAL_MASTER_RECORDS_CUSTODY_SURFACE_UNAVAILABLE")
            self.assertEqual(result["manifest_materialization"]["state"],"MATERIALIZED")
            self.assertEqual(result["manifest_materialization"]["authority_effect"],"NONE_INPUT_MATERIALIZATION_ONLY")
            self.assertTrue(result["runtime_execution_attempted"])
            self.assertEqual(result["resolution_authority"],"INTERLOCK_INTR")

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
