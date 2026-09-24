from __future__ import annotations
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
WORKER=ROOT/"workers"/"erl_household_economic_conditions_worker.py"
TASK="ERL-HOUSEHOLD-ECONOMIC-CONDITIONS-SITE-001"


def load_worker():
    spec=importlib.util.spec_from_file_location("erl_household_worker_failure_test",WORKER)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ErlHouseholdWorkerEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.erl=self.root/"Executive_Rhetoric_Ledger"
        script=self.erl/"scripts"/"acquire_census_b25140.py"
        script.parent.mkdir(parents=True)
        script.write_text("# source test placeholder\n",encoding="utf-8")
        self.worker=load_worker()
        self.worker.ROOT=self.root
        self.worker.RECEIPT=self.root/"receipts"/"erl-household-economic-conditions"/"latest.json"
        self.sg=self.root/"stegfin-governance"
        self.tvc=self.root/"TVC"
        self.roots={"StegVerse-Labs/Executive_Rhetoric_Ledger":self.erl}
        self.worker.roots=lambda:self.roots
        self.invocation=json.dumps({"schema":"stegverse.worker-invocation/v0.1",
                         "heartbeat_epoch":1,"task":{"task_id":TASK,"claim_id":"fixture-claim",
                         "heartbeat_timing":{"fencing_token":11}}})
    def candidate(self,out):
        out.mkdir(parents=True,exist_ok=True)
        raw=b"fixture ACS table-based source bytes"
        (out/"census_acs_housing_cost_burden.raw").write_bytes(raw)
        body={"schema":"stegverse.erl.household-economic-source-candidate/v1",
              "goal_task_id":TASK,"inventory_series_id":"CENSUS_ACS_HOUSING_COST_BURDEN",
              "required_cost_scope":"HOUSING_COST_BURDEN_ONLY",
              "status":"NORMALIZED_SOURCE_OBSERVATIONS","source_vintage":"2024 ACS 1-year",
              "acquired_at":"2026-09-24T00:00:00Z","raw_sha256":hashlib.sha256(raw).hexdigest(),
              "observations":[{"evidence_class":"DIRECT_OBSERVATION"} for _ in range(10)]+
                             [{"evidence_class":"DERIVED_FROM_DIRECT_OBSERVATIONS"} for _ in range(6)],
              "finding_authority":False,"public_activation_authorized":False}
        (out/"census_acs_housing_cost_burden.candidate.json").write_text(json.dumps(body),encoding="utf-8")
    def execute(self,runner):
        stdout=io.StringIO()
        with patch.object(sys,"stdin",io.StringIO(self.invocation)),patch.object(sys,"stdout",stdout),patch.object(self.worker.subprocess,"run",side_effect=runner):
            result=self.worker.main()
        receipt=json.loads((self.root/"receipts"/"erl-household-economic-conditions"/"latest.json").read_text())
        return result,receipt,json.loads(stdout.getvalue())
    def test_valid_census_finishes_without_bea_provider_roots(self):
        def runner(argv,**kwargs):
            self.candidate(Path(argv[argv.index("--output-dir")+1]))
            return subprocess.CompletedProcess(argv,0,"","")
        rc,receipt,summary=self.execute(runner)
        self.assertEqual(rc,0)
        self.assertEqual(summary["state"],"COMPLETED")
        self.assertEqual(receipt["census_credential_free"]["direct_count"],10)
        self.assertEqual(receipt["census_credential_free"]["derived_count"],6)
        self.assertEqual(receipt["bea_readiness_state"],"UNKNOWN_NOT_OBSERVED")
        self.assertIsNone(receipt["bea_execution"])
        self.assertIs(receipt["public_activation_authorized"],False)
    def test_census_failure_retains_blocking_receipt_instead_of_false_completion(self):
        def runner(argv,**kwargs):
            return subprocess.CompletedProcess(argv,1,"","source failure")
        rc,receipt,summary=self.execute(runner)
        self.assertEqual(rc,0)
        self.assertEqual(summary["state"],"BLOCKED")
        self.assertEqual(receipt["transition_id"],"CENSUS_EVIDENCE_CAPTURE_FAILED")
        self.assertIs(receipt["public_activation_authorized"],False)
    def test_old_ready_file_cannot_trigger_bea_operation(self):
        readiness_script=self.sg/"scripts"/"check_tvc_bea_credential_readiness.py"
        readiness_script.parent.mkdir(parents=True)
        readiness_script.write_text("# source test placeholder\n",encoding="utf-8")
        self.roots["StegVerse-Labs/stegfin-governance"]=self.sg
        path=self.root/"receipts"/"erl-household-economic-conditions"/"bea-readiness.json"
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({"decision":"READY"}),encoding="utf-8")
        def runner(argv,**kwargs):
            if "acquire_census_b25140.py" in " ".join(argv):
                self.candidate(Path(argv[argv.index("--output-dir")+1]))
                return subprocess.CompletedProcess(argv,0,"","")
            return subprocess.CompletedProcess(argv,2,"","no secret")
        with patch.object(self.worker,"run_json",side_effect=AssertionError("stale BEA READY must never be consumed")):
            _,receipt,_=self.execute(runner)
        self.assertEqual(receipt["bea_readiness_state"],"UNKNOWN_NOT_OBSERVED")
        self.assertIsNone(receipt["bea_execution"])
        self.assertFalse(path.exists())
    def test_fresh_metadata_ready_invokes_existing_bea_once(self):
        readiness_script=self.sg/"scripts"/"check_tvc_bea_credential_readiness.py"
        readiness_script.parent.mkdir(parents=True)
        readiness_script.write_text("# source test placeholder\n",encoding="utf-8")
        tvc_script=self.tvc/"scripts"/"tvc_execute_bea_readonly.py"
        tvc_script.parent.mkdir(parents=True)
        tvc_script.write_text("# source test placeholder\n",encoding="utf-8")
        self.roots.update({"StegVerse-Labs/stegfin-governance":self.sg,"StegVerse-Labs/TVC":self.tvc})
        readiness={"schema":"stegverse.tvc.bea-credential-readiness/v1","provider":"bea",
                   "credential_authority":"TV/TVC","secret_ref":"vault://tvc/providers/bea/api-key",
                   "decision":"READY","secret_material_read":False,"secret_material_returned":False,
                   "secret_material_logged":False,"secret_material_hashed":False,"provider_contacted":False}
        calls=[]
        def runner(argv,**kwargs):
            if "acquire_census_b25140.py" in " ".join(argv):
                self.candidate(Path(argv[argv.index("--output-dir")+1]))
            else:
                Path(argv[argv.index("--out")+1]).write_text(json.dumps(readiness),encoding="utf-8")
            return subprocess.CompletedProcess(argv,0,"","")
        def bea(argv,cwd,timeout):
            calls.append(list(argv))
            Path(argv[argv.index("--out")+1]).write_text(json.dumps({
                "schema":"stegverse.tvc.bea-readonly-execution/v1",
                "public_activation_authorized":False,"credential_material_returned":False,
                "provider_result":{"raw_sha256":"sha256:fixture","source_vintage":"fixture"}}),encoding="utf-8")
            return 0,{}
        with patch.object(self.worker,"run_json",side_effect=bea):
            _,receipt,_=self.execute(runner)
        self.assertEqual(len(calls),1)
        self.assertEqual(receipt["bea_readiness_state"],"READY")
        self.assertEqual(receipt["bea_execution"]["state"],"NON_AUTHORIZING_RESULT_RETAINED")
        self.assertIs(receipt["public_activation_authorized"],False)


if __name__=="__main__":
    unittest.main()
