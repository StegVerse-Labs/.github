from __future__ import annotations
import base64, json
from pathlib import Path
import tempfile, unittest
from unittest import mock
from workers import sv_dn1_repository_persistence_package_worker as worker

def write_json(path:Path,value:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value)+"\n",encoding="utf-8")

class PersistencePackageTests(unittest.TestCase):
    def invocation(self):
        return {"schema":"stegverse.worker-invocation/v0.1","task":{"task_id":worker.TASK_ID,"worker_id":worker.WORKER_ID,"claim_id":"claim-persist","heartbeat_timing":{"fencing_token":41}}}

    def setup_fixture(self,base:Path):
        promotion=base/"promotion"; demo=base/"demo"; bound=base/"bound"; public=demo/"public/sv-dn1"; public.mkdir(parents=True)
        hashes={}
        for name in worker.FILES:
            data=("authentic-"+name+"\n").encode()
            (public/name).write_bytes(data); hashes[name]=worker.sha_bytes(data)
        write_json(promotion/"receipts/latest.json",{
            "schema":"stegverse.sv-dn1.public-promotion-worker-receipt/v1","state":"COMPLETE",
            "transition_id":"SV_DN1_PUBLIC_PROMOTION_READY","exchange_id":"ex-1","manifest_receipt_id":"mr-1",
            "publication_state":"PUBLIC_OBSERVED","observation_class":"LIVE","destination_artifact_sha256":hashes,
            "exact_bytes_preserved":True,"semantic_rewrite_performed":False,"network_fetch_performed":False,
            "credential_used":False,"repository_writeback_performed":False,"deployment_performed":False,
            "release_performed":False,"certification_claimed":False,"authority_effect":"NONE_STATIC_PROJECTION_ONLY"})
        return promotion,demo,bound,hashes

    def test_packages_exact_five_bytes_and_target(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); promotion,demo,bound,hashes=self.setup_fixture(base)
            with mock.patch.dict("os.environ",{worker.PROMOTION_ENV:str(promotion),worker.DEMO_ENV:str(demo),worker.BOUND_ENV:str(bound),"PATH":"/usr/bin"},clear=True):
                receipt=worker.execute(self.invocation())
            self.assertEqual(receipt["transition_id"],"SV_DN1_REPOSITORY_PERSISTENCE_PACKAGE_READY")
            package=json.loads((bound/"packages/latest.json").read_text())
            self.assertEqual(package["target_repository"],"StegVerse-org/stegverse-demo-suite")
            self.assertEqual(package["target_ref"],"main")
            self.assertEqual(len(package["files"]),5)
            for row in package["files"]:
                name=Path(row["path"]).name
                self.assertEqual(row["sha256"],hashes[name])
                self.assertEqual(worker.sha_bytes(base64.b64decode(row["content_base64"])),hashes[name])
            body=dict(package); body.pop("package_sha256")
            self.assertEqual(package["package_sha256"],worker.sha_bytes(worker.stable_bytes(body)))
            self.assertFalse(receipt["repository_writeback_performed"])

    def test_tampered_promoted_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); promotion,demo,bound,_=self.setup_fixture(base)
            (demo/"public/sv-dn1/index.html").write_text("tampered")
            with mock.patch.dict("os.environ",{worker.PROMOTION_ENV:str(promotion),worker.DEMO_ENV:str(demo),worker.BOUND_ENV:str(bound)},clear=True):
                with self.assertRaisesRegex(RuntimeError,"hash mismatch"):
                    worker.execute(self.invocation())

    def test_hosted_or_credential_environment_rejected(self):
        with mock.patch.dict("os.environ",{"GITHUB_ACTIONS":"true"},clear=True):
            with self.assertRaisesRegex(RuntimeError,"hosted environment"): worker.execute(self.invocation())
        with mock.patch.dict("os.environ",{"GITHUB_TOKEN":"secret"},clear=True):
            with self.assertRaisesRegex(RuntimeError,"credential-bearing"): worker.execute(self.invocation())

if __name__=="__main__": unittest.main()
