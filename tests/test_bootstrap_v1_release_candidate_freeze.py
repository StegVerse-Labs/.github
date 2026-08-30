from __future__ import annotations
import io,json,tempfile,unittest
from pathlib import Path
from unittest import mock
from workers import bootstrap_v1_release_candidate_freeze_worker as worker

def catalog():
    comps=[
      {"component_id":"stegverse.sdk","source_identity":"sha256:"+"1"*64},
      {"component_id":"stegverse.stegcore","source_identity":"sha256:"+"2"*64},
      {"component_id":"stegverse.core-lite","source_identity":"sha256:"+"3"*64},
      {"component_id":"stegverse.master-records","source_identity":"sha256:"+"4"*64},
    ]
    return {"schema":"stegverse.bootstrap.source-catalog/v1","catalog_version":"1.0.0","state":"FROZEN",
            "source_identity_scheme":"sha256-content-manifest","component_count":4,"components":comps,
            "source_identity_set_sha256":worker.digest(comps),"upstream_source_prep_receipt_sha256":"a"*64,
            "source_package_contract":{"schema":"stegverse.source-package/v1","version":"1.0.0"},
            "github_platform_required":False,"specific_external_platform_required":False,"network_locator_required":False,
            "package_integrity_confers_execution_authority":False,"execution_authority":"NONE","authority_effect":"NONE_IDENTITY_FREEZE_ONLY"}

def freeze_receipt(cat):
    return {"schema":"stegverse.bootstrap.source-identity-freeze-receipt/v1","state":"COMPLETE",
            "transition_id":"BOOTSTRAP_V1_SOURCE_IDENTITIES_FROZEN","catalog_sha256":worker.digest(cat),
            "source_identity_set_sha256":cat["source_identity_set_sha256"],"github_platform_required":False,
            "network_access_performed":False}

def invocation():
    return {"schema":"stegverse.worker-invocation/v0.1","task":{"task_id":worker.TASK_ID,"worker_id":worker.WORKER_ID,"claim_id":"claim-rc1","heartbeat_timing":{"fencing_token":23}}}

class BootstrapV1ReleaseCandidateFreezeTests(unittest.TestCase):
    def test_candidate_has_no_platform_or_execution_authority(self):
        cat=catalog(); fr=freeze_receipt(cat); worker.validate_upstream(cat,fr)
        c=worker.build_candidate(cat,fr)
        self.assertEqual(c["schema"],"stegverse.bootstrap.release-candidate/v1")
        self.assertEqual(c["candidate_version"],"1.0.0-rc.1")
        self.assertTrue(c["candidate_identity"].startswith("sha256:"))
        self.assertFalse(c["github_platform_required"])
        self.assertFalse(c["specific_external_platform_required"])
        self.assertFalse(c["network_locator_required"])
        self.assertFalse(c["transport_implementation_required"])
        self.assertFalse(c["credential_required"])
        self.assertFalse(c["package_integrity_confers_execution_authority"])
        self.assertFalse(c["release_activated"])
        self.assertEqual(c["execution_authority"],"NONE")

    def test_catalog_receipt_digest_mismatch_fails(self):
        cat=catalog(); fr=freeze_receipt(cat); fr["catalog_sha256"]="f"*64
        with self.assertRaisesRegex(RuntimeError,"catalog digest mismatch"):worker.validate_upstream(cat,fr)

    def test_execute_is_idempotent_and_conflict_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);up=root/"up";bound=root/"bound";(up/"catalog").mkdir(parents=True);(up/"receipts").mkdir()
            cat=catalog();fr=freeze_receipt(cat)
            (up/"catalog/bootstrap-v1-source-catalog.json").write_text(json.dumps(cat))
            (up/"receipts/latest.json").write_text(json.dumps(fr))
            env={worker.SOURCE_FREEZE_ENV:str(up),worker.BOUND_ENV:str(bound)}
            with mock.patch.dict("os.environ",env,clear=True):
                a=worker.execute(invocation());b=worker.execute(invocation())
                self.assertEqual(a["candidate_identity"],b["candidate_identity"])
                path=bound/"candidate/bootstrap-v1-1.0.0-rc.1.json";bad=json.loads(path.read_text());bad["release_activated"]=True;path.write_text(json.dumps(bad))
                with self.assertRaisesRegex(worker.FrozenCandidateConflict,"FROZEN_BOOTSTRAP_V1_RC1_CONFLICT"):worker.execute(invocation())

    def test_missing_upstream_returns_handoff_ready_without_platform(self):
        with tempfile.TemporaryDirectory() as td:
            with (mock.patch.dict("os.environ",{worker.SOURCE_FREEZE_ENV:td,worker.BOUND_ENV:td+"/out"},clear=True),
                  mock.patch("sys.stdin",io.StringIO(json.dumps(invocation())+"\n")),
                  mock.patch("sys.stdout",new_callable=io.StringIO) as stdout):
                self.assertEqual(worker.main(),0);result=json.loads(stdout.getvalue())
            self.assertEqual(result["state"],"HANDOFF_READY")
            self.assertFalse(result["blocker"]["github_platform_required"])
            self.assertFalse(result["blocker"]["third_party_runtime_required"])
            self.assertFalse(result["blocker"]["human_action_required"])

    def test_control_surfaces_preserve_zero_authority(self):
        root=Path(__file__).resolve().parents[1]
        h=json.loads((root/"handoffs/BOOTSTRAP-V1-RELEASE-CANDIDATE-FREEZE-001.json").read_text())
        a=json.loads((root/"control/process-worker-adapters.d/bootstrap-v1-release-candidate-freeze-001.json").read_text())
        self.assertFalse(h["authority"]["github_platform_required"])
        self.assertFalse(h["authority"]["network_access_authority"])
        self.assertFalse(h["authority"]["release_activation_authority"])
        self.assertFalse(h["authority"]["package_execution_authority"])
        self.assertNotIn("GITHUB_TOKEN",a["adapters"][0]["env_allowlist"])

if __name__=="__main__":unittest.main()
