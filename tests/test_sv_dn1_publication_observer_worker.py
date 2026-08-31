from __future__ import annotations
import io, json, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from workers import sv_dn1_publication_observer_worker as worker

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value)+"\n")

class Tests(unittest.TestCase):
    def invocation(self):
        return {"schema":"stegverse.worker-invocation/v0.1","task":{"task_id":worker.TASK_ID,"worker_id":worker.WORKER_ID,"claim_id":"claim-observe","heartbeat_timing":{"fencing_token":51}}}

    def test_hosted_and_credential_env_fail_closed(self):
        with mock.patch.dict("os.environ",{"GITHUB_ACTIONS":"true"},clear=True):
            with self.assertRaisesRegex(RuntimeError,"hosted environment"): worker.execute(self.invocation())
        with mock.patch.dict("os.environ",{"GITHUB_TOKEN":"secret"},clear=True):
            with self.assertRaisesRegex(RuntimeError,"credential-bearing"): worker.execute(self.invocation())

    def test_stale_public_bytes_are_retryable(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); persist=base/"persist"; demo=base/"demo"; bound=base/"bound"
            write_json(persist/"packages/latest.json",{"schema":"stegverse.sv-dn1.repository-persistence-package/v1","state":"READY_FOR_ADMITTED_REPOSITORY_MUTATION"})
            (demo/"scripts").mkdir(parents=True); (demo/"scripts/verify_sv_dn1_public_publication.py").write_text("# observer\n")
            fake=SimpleNamespace(returncode=1,stdout="",stderr="public artifact bytes do not match governed package")
            with mock.patch.dict("os.environ",{worker.PERSIST_ENV:str(persist),worker.DEMO_ENV:str(demo),worker.BOUND_ENV:str(bound),"PATH":"/usr/bin"},clear=True), mock.patch.object(worker.subprocess,"run",return_value=fake):
                with self.assertRaises(worker.Pending): worker.execute(self.invocation())

    def test_success_freezes_worker_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); persist=base/"persist"; demo=base/"demo"; bound=base/"bound"
            write_json(persist/"packages/latest.json",{"schema":"stegverse.sv-dn1.repository-persistence-package/v1","state":"READY_FOR_ADMITTED_REPOSITORY_MUTATION"})
            (demo/"scripts").mkdir(parents=True); (demo/"scripts/verify_sv_dn1_public_publication.py").write_text("# observer\n")
            observed={"schema":"stegverse.sv-dn1.publication-observation/v1","state":"COMPLETE","transition_id":"SV_DN1_AUTHENTIC_PUBLICATION_OBSERVED","exchange_id":"ex","manifest_receipt_id":"mr","publication_state":"PUBLIC_OBSERVED","public_base_url":"https://stegverse-org.github.io/stegverse-demo-suite/sv-dn1/","artifacts":{"index.html":{"sha256":"a"*64}},"all_public_artifacts_observed":True,"exact_bytes_preserved":True,"credential_used":False,"authorization_header_sent":False,"repository_writeback_performed":False,"deployment_performed":False,"governance_executed":False,"sdk_execution_performed":False,"authority_effect":"NONE_PUBLICATION_OBSERVATION_ONLY"}
            def run(*args,**kwargs):
                write_json(bound/"product-observation/latest.json",observed)
                return SimpleNamespace(returncode=0,stdout="{}",stderr="")
            with mock.patch.dict("os.environ",{worker.PERSIST_ENV:str(persist),worker.DEMO_ENV:str(demo),worker.BOUND_ENV:str(bound),"PATH":"/usr/bin"},clear=True), mock.patch.object(worker.subprocess,"run",side_effect=run):
                receipt=worker.execute(self.invocation())
            self.assertEqual(receipt["transition_id"],"SV_DN1_AUTHENTIC_PUBLICATION_OBSERVED")
            self.assertFalse(receipt["credential_used"])
            self.assertTrue((bound/"receipts/latest.json").is_file())

    def test_main_maps_pending_to_handoff_ready(self):
        with mock.patch.object(worker,"execute",side_effect=worker.Pending("not yet deployed")), mock.patch("sys.stdin",io.StringIO(json.dumps({"schema":"x"})+"\n")), mock.patch("sys.stdout",new_callable=io.StringIO) as out:
            self.assertEqual(worker.main(),0)
            result=json.loads(out.getvalue())
        self.assertEqual(result["state"],"HANDOFF_READY")
        self.assertEqual(result["transition_id"],"SV_DN1_PUBLICATION_NOT_YET_OBSERVED")

if __name__=="__main__": unittest.main()
