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

class SV002HBResidentBindingTests(unittest.TestCase):
    def test_uses_existing_hb_worker_substrate_not_second_executor(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            runtime=base/"runtime"; runtime.mkdir()
            req=runtime/"control/resident-execution-request.d/sv002-org-runtime-activation-001.json"
            req.parent.mkdir(parents=True)
            req.write_text(json.dumps({
                "schema":"stegverse.resident-execution-request/v1",
                "state":"REQUESTED",
                "task_id":"SHWP-SV002-ORG-RUNTIME-ACTIVATION-001",
                "credential_authority":"TV/TVC",
                "github_token_required":False,
                "github_token_runtime_authority":"NONE",
                "heartbeat_grants_execution_authority":False,
                "request_granted_authority":False,
                "network_source_fetch_allowed":False,
                "authority_effect":"NONE_REQUEST_ONLY",
            }))

            source_org=base/"StegVerse-org/.github"; (source_org/"resident-runtime").mkdir(parents=True)
            (source_org/"resident-runtime/run_sv002_self_characterization_roundtrip.py").write_text("# roundtrip\n")
            target=base/"StegVerse-002/.github"; (target/"resident-runtime").mkdir(parents=True)
            (target/"resident-runtime/self_characterization_surface.py").write_text("# target\n")
            sdk=base/"StegVerse-org/StegVerse-SDK"; (sdk/"stegverse").mkdir(parents=True)
            (sdk/"stegverse/external_interlock_bootstrap.py").write_text("# sdk\n")
            principal=base/"StegVerse-002/micro-node-runtime"
            (principal/"tools").mkdir(parents=True)
            (principal/"experiments/self-characterization-001").mkdir(parents=True)
            (principal/"tools/run_self_characterization_principal.py").write_text("# principal\n")
            (principal/"experiments/self-characterization-001/EXPERIMENT_CONTRACT.v0.3.json").write_text("{}")

            env={
                "STEGVERSE_ORG_CONTROL_ROOT":str(source_org),
                "STEGVERSE_SV002_ORG_ROOT":str(target),
                "STEGVERSE_SDK_SOURCE_ROOT":str(sdk),
                "STEGVERSE_MICRO_NODE_RUNTIME_ROOT":str(principal),
            }
            seen=[]
            def runner(cmd,**kwargs):
                seen.append(cmd)
                self.assertTrue(cmd[1].endswith("run_sv002_self_characterization_roundtrip.py"))
                self.assertNotIn("resident_executor.py"," ".join(cmd))
                result={
                    "experiment_id":"STEGVERSE-002-SELF-CHARACTERIZATION-001",
                    "principal_execution_owner":"StegVerse-002/.github",
                    "cross_organization_principal_execution":False
                }
                return subprocess.CompletedProcess(cmd,0,stdout=json.dumps(result)+"\n",stderr="")

            with mock.patch.dict(os.environ,env,clear=False):
                receipt=MOD.consume(ROOT,runtime,runner=runner)

            self.assertEqual(receipt["state"],"COMPLETED")
            self.assertTrue(receipt["terminal_round_trip_observed"])
            self.assertEqual(receipt["runtime_substrate"],"HEARTBEAT_SEPARATED_NATIVE_WORKER_COORDINATOR")
            self.assertFalse(receipt["second_resident_executor_required"])
            self.assertEqual(len(seen),1)

if __name__=="__main__":
    unittest.main()
