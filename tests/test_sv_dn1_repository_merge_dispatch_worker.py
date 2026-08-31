from __future__ import annotations
import base64, hashlib, json, tempfile
from pathlib import Path
import unittest
from unittest import mock
from workers import sv_dn1_repository_merge_dispatch_worker as worker

def package_fixture():
    rows=[]
    for name in worker.FILES:
        raw=("authentic-"+name+"\n").encode()
        rows.append({"path":f"{worker.TARGET_ROOT}/{name}","sha256":hashlib.sha256(raw).hexdigest(),"size":len(raw),"content_base64":base64.b64encode(raw).decode()})
    body={"schema":"stegverse.sv-dn1.repository-persistence-package/v1","state":"READY_FOR_ADMITTED_REPOSITORY_MUTATION","target_repository":worker.TARGET_REPO,"target_ref":"main","target_root":worker.TARGET_ROOT,"files":rows}
    value=dict(body);value["package_sha256"]=worker.sha_bytes(worker.stable_package_bytes(body));return value

def persistence_receipt(pkg):
    return {"schema":"stegverse.sv-dn1.repository-persistence-dispatch-receipt/v1","state":"COMPLETE","transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_PR_CREATED","package_sha256":pkg["package_sha256"],"base_sha":"1"*40,"branch":"sv-dn1/publication-"+pkg["package_sha256"][:12],"head_sha":"2"*40,"pull_request_number":77,"credential_used":False,"consumer_credential_present":False,"repository_mutation_performed_by_worker":False,"merge_performed":False,"deployment_performed":False,"authority_effect":"NONE_REQUEST_STAGING_ONLY"}

class MergeDispatchTests(unittest.TestCase):
    def test_request_binds_exact_upstream_identity_and_no_authority(self):
        pkg=package_fixture();p=persistence_receipt(pkg)
        base,head,branch,pr=worker.validate_persistence_receipt(p,pkg["package_sha256"])
        req=worker.merge_request(pkg["package_sha256"],base,head,branch,pr)
        self.assertEqual(req["repository"],worker.TARGET_REPO)
        self.assertEqual(req["pull_request_number"],77)
        self.assertEqual(req["expected_base_sha"],"1"*40)
        self.assertEqual(req["expected_head_sha"],"2"*40)
        self.assertFalse(req["consumer_credential_present"])
        self.assertFalse(req["secret_values_present"])
        self.assertFalse(req["merge_request_grants_authority"])
        self.assertNotIn("token",json.dumps(req).lower())

    def test_merge_receipt_requires_exact_request_and_terminal_merge(self):
        pkg=package_fixture();p=persistence_receipt(pkg)
        base,head,branch,pr=worker.validate_persistence_receipt(p,pkg["package_sha256"])
        req=worker.merge_request(pkg["package_sha256"],base,head,branch,pr)
        rec={"schema":worker.MERGE_RECEIPT_SCHEMA,"state":"COMPLETE","transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_PR_MERGED","request_id":req["request_id"],"request_sha256":worker.canonical_hash(req),"repository":worker.TARGET_REPO,"base_ref":"main","pull_request_number":77,"base_sha":base,"head_ref":branch,"head_sha":head,"merge_commit_sha":"3"*40,"package_sha256":pkg["package_sha256"],"file_count":5,"exact_bytes_verified":True,"credential_authority":"TV/TVC","credential_value_exposed":False,"non_tv_tvc_secret_or_token_used":False,"scope_expanded":False,"deployment_performed":False,"publication_observed":False,"authority_effect":"BOUNDED_SV_DN1_REPOSITORY_MERGE_ONLY"}
        self.assertEqual(worker.validate_merge_receipt(req,rec),"3"*40)
        rec["exact_bytes_verified"]=False
        with self.assertRaisesRegex(worker.Pending,"exact_bytes_verified"): worker.validate_merge_receipt(req,rec)

    def test_execute_stages_merge_request_without_credential(self):
        pkg=package_fixture();p=persistence_receipt(pkg)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);pkgroot=root/"pkg";persist=root/"persist";bound=root/"bound"
            (pkgroot/"packages").mkdir(parents=True);(persist/"receipts").mkdir(parents=True)
            (pkgroot/"packages/latest.json").write_text(json.dumps(pkg));(persist/"receipts/latest.json").write_text(json.dumps(p))
            inv={"schema":"stegverse.worker-invocation/v0.1","task":{"task_id":worker.TASK_ID,"worker_id":worker.WORKER_ID,"claim_id":"claim-1","heartbeat_timing":{"fencing_token":31}}}
            with mock.patch.dict("os.environ",{worker.PACKAGE_ENV:str(pkgroot),worker.PERSIST_DISPATCH_ENV:str(persist),worker.BOUND_ENV:str(bound),"PATH":"/usr/bin"},clear=True):
                with self.assertRaisesRegex(worker.Pending,"merge receipt"): worker.execute(inv)
            staged=json.loads((bound/"staged/merge-request.json").read_text())
            self.assertTrue((bound/f"outbox/{staged['request_id']}.json").is_file())
            self.assertFalse(staged["merge_request_grants_authority"])

    def test_hosted_or_credential_environment_fails_closed(self):
        with mock.patch.dict("os.environ",{"GITHUB_ACTIONS":"true"},clear=True):
            with self.assertRaisesRegex(RuntimeError,"hosted environment"): worker.execute({})
        with mock.patch.dict("os.environ",{"TVC_EPHEMERAL_GITHUB_TOKEN":"secret"},clear=True):
            with self.assertRaisesRegex(RuntimeError,"credential-bearing environment"): worker.execute({})

if __name__=="__main__": unittest.main()
