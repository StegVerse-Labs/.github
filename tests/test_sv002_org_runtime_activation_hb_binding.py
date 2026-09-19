from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sv002_consumer",ROOT/"scripts/consume_sv002_org_runtime_activation_request.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

DISPATCH_SPEC=importlib.util.spec_from_file_location("resident_dispatch",ROOT/"scripts/dispatch_resident_execution_requests.py")
DISPATCH=importlib.util.module_from_spec(DISPATCH_SPEC); DISPATCH_SPEC.loader.exec_module(DISPATCH)


class SV002HBResidentBindingTests(unittest.TestCase):
    def _request(self):
        return {
            "schema":"stegverse.resident-execution-request/v1",
            "request_id":"RESIDENT-EXEC-SV002-ORG-RUNTIME-ACTIVATION-001",
            "state":"REQUESTED",
            "task_id":"SHWP-SV002-ORG-RUNTIME-ACTIVATION-001",
            "goal_task_id":"STEGVERSE-002-EXPERIMENT-RERUN-001",
            "cosv_task_vector":"50000000107000",
            "mode":"TARGETED_INDEPENDENT_TASK_CONTROL",
            "entrypoint":"scripts/consume_sv002_org_runtime_activation_request.py",
            "operation":"REQUEST_SELF_CHARACTERIZATION",
            "deterministic_packet_id":"SV002-RERUN-C796D0BFD181CEC5D99E4C23",
            "current_callable_ref":"StegVerse-002/.github:resident-runtime/invoke_sv002_experiment_rerun.py",
            "request_bound_master_records_required":True,
            "request_bound_required_evidence_exact_bytes":True,
            "credential_authority":"TV/TVC",
            "github_token_required":False,
            "github_token_runtime_authority":"NONE",
            "heartbeat_grants_execution_authority":False,
            "second_machine_required":False,
            "network_source_fetch_allowed":False,
            "request_granted_authority":False,
            "authority_effect":"NONE_REQUEST_ONLY",
        }

    def test_uses_existing_hb_worker_substrate_and_current_rerun_callable(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            runtime=base/"runtime"; runtime.mkdir()
            req=runtime/"control/resident-execution-request.d/sv002-org-runtime-activation-001.json"
            req.parent.mkdir(parents=True)
            req.write_text(json.dumps(self._request()))

            source=base/"StegVerse-Labs/.github"
            (source/"workers").mkdir(parents=True)
            (source/"workers/canonical_state_transition_custody.py").write_text("# canonical custody client\n")

            target=base/"StegVerse-002/.github"
            (target/"resident-runtime").mkdir(parents=True)
            (target/"resident-runtime/invoke_sv002_experiment_rerun.py").write_text("# current rerun callable\n")
            (target/"resident-runtime/activation-manifest.json").write_text("{}")

            env={
                "STEGVERSE_SV002_ORG_ROOT":str(target),
                "STEGVERSE_MASTER_RECORDS_ENDPOINT":"https://master-records.example.test",
                "STEGVERSE_MASTER_RECORDS_TOKEN":"custody-token",
                "STEGVERSE_ORG_FEDERATION_GATEWAY_URL":"https://federation.example.test",
                "GITHUB_TOKEN":"forbidden",
            }
            seen=[]
            def runner(cmd,**kwargs):
                seen.append((cmd,kwargs))
                self.assertTrue(cmd[1].endswith("resident-runtime/invoke_sv002_experiment_rerun.py"))
                self.assertNotIn("run_sv002_self_characterization_roundtrip.py"," ".join(cmd))
                self.assertNotIn("resident_executor.py"," ".join(cmd))
                child_env=kwargs["env"]
                self.assertNotIn("GITHUB_TOKEN",child_env)
                roots=json.loads(child_env["STEGVERSE_REPO_ROOTS_JSON"])
                self.assertEqual(roots["StegVerse-Labs/.github"],str(source.resolve()))
                self.assertEqual(roots["StegVerse-002/.github"],str(target.resolve()))
                self.assertEqual(child_env["STEGVERSE_MASTER_RECORDS_ENDPOINT"],env["STEGVERSE_MASTER_RECORDS_ENDPOINT"])
                self.assertEqual(child_env["STEGVERSE_MASTER_RECORDS_TOKEN"],env["STEGVERSE_MASTER_RECORDS_TOKEN"])
                self.assertEqual(child_env["STEGVERSE_ORG_FEDERATION_GATEWAY_URL"],env["STEGVERSE_ORG_FEDERATION_GATEWAY_URL"])
                result={
                    "state":"BLOCKED",
                    "goal_task_id":"STEGVERSE-002-EXPERIMENT-RERUN-001",
                    "cosv_id":"50000000107000",
                    "experiment_id":"STEGVERSE-002-SELF-CHARACTERIZATION-001",
                    "operation":"REQUEST_SELF_CHARACTERIZATION",
                    "invocation_count":1,
                    "packet_id":"SV002-RERUN-C796D0BFD181CEC5D99E4C23",
                    "packet_sha256":"sha256:"+"a"*64,
                    "request_sha256":"sha256:"+"b"*64,
                    "manifest_sha256":"29222a589eb4c2958d2787743e266f067ee07e1373c51f60b553f1f359789828",
                    "frame_sha256":"sha256:"+"c"*64,
                    "request_bound_claimed":True,
                    "request_bound_master_records_state":"RECORDED",
                    "request_bound_master_records_reconstruction_status":"PASS",
                    "request_bound_master_records_required_evidence_validation_status":"PASS",
                    "request_bound_master_records_required_evidence_count":1,
                    "request_bound_master_records_receipt_sha256":"d"*64,
                    "request_bound_master_records_reconstructed_receipt_sha256":"d"*64,
                    "request_bound_master_record_ref":"master-record:state-transition:sha256:"+"d"*64,
                }
                return subprocess.CompletedProcess(cmd,2,stdout=json.dumps(result)+"\n",stderr="")

            with mock.patch.dict(os.environ,env,clear=False):
                receipt=MOD.consume(source,runtime,runner=runner)

            self.assertEqual(receipt["state"],"ATTEMPT_RECORDED")
            self.assertTrue(receipt["request_bound_custodied"])
            self.assertFalse(receipt["terminal_round_trip_observed"])
            self.assertFalse(receipt["second_resident_executor_required"])
            self.assertFalse(receipt["second_request_required"])
            self.assertEqual(receipt["request_bound_master_records_receipt_sha256"],"d"*64)
            self.assertEqual(len(seen),1)

    def test_dispatch_preserves_existing_custody_and_federation_bindings(self):
        values={
            "PATH":"/usr/bin",
            "HOME":"/tmp/home",
            "STEGVERSE_MASTER_RECORDS_ENDPOINT":"https://master-records.example.test",
            "STEGVERSE_MASTER_RECORDS_TOKEN":"custody-token",
            "STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS":"11",
            "STEGVERSE_ORG_FEDERATION_GATEWAY_URL":"https://federation.example.test",
            "STEGVERSE_ORG_FEDERATION_ROOT":"/var/lib/stegverse/federation",
            "GITHUB_TOKEN":"forbidden",
        }
        clean=DISPATCH.clean_exec_env(values)
        self.assertEqual(clean["STEGVERSE_MASTER_RECORDS_ENDPOINT"],values["STEGVERSE_MASTER_RECORDS_ENDPOINT"])
        self.assertEqual(clean["STEGVERSE_MASTER_RECORDS_TOKEN"],values["STEGVERSE_MASTER_RECORDS_TOKEN"])
        self.assertEqual(clean["STEGVERSE_ORG_FEDERATION_GATEWAY_URL"],values["STEGVERSE_ORG_FEDERATION_GATEWAY_URL"])
        self.assertEqual(clean["STEGVERSE_ORG_FEDERATION_ROOT"],values["STEGVERSE_ORG_FEDERATION_ROOT"])
        self.assertNotIn("GITHUB_TOKEN",clean)
        self.assertEqual(clean["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"],"TV/TVC")
        self.assertEqual(clean["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"],"NONE")


if __name__=="__main__":
    unittest.main()
