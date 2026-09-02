from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sv002_consumer",ROOT/"scripts/consume_sv002_org_runtime_activation_request.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

def test_sv002_consumer_uses_existing_hb_worker_substrate_not_second_executor(monkeypatch):
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
        (principal/"tools").mkdir(parents=True); (principal/"experiments/self-characterization-001").mkdir(parents=True)
        (principal/"tools/run_self_characterization_principal.py").write_text("# principal\n")
        (principal/"experiments/self-characterization-001/EXPERIMENT_CONTRACT.v0.3.json").write_text("{}")

        monkeypatch.setenv("STEGVERSE_ORG_CONTROL_ROOT",str(source_org))
        monkeypatch.setenv("STEGVERSE_SV002_ORG_ROOT",str(target))
        monkeypatch.setenv("STEGVERSE_SDK_SOURCE_ROOT",str(sdk))
        monkeypatch.setenv("STEGVERSE_MICRO_NODE_RUNTIME_ROOT",str(principal))

        seen=[]
        def runner(cmd,**kwargs):
            seen.append(cmd)
            assert cmd[1].endswith("run_sv002_self_characterization_roundtrip.py")
            assert "resident_executor.py" not in " ".join(cmd)
            result={
                "experiment_id":"STEGVERSE-002-SELF-CHARACTERIZATION-001",
                "principal_execution_owner":"StegVerse-002/.github",
                "cross_organization_principal_execution":False
            }
            return subprocess.CompletedProcess(cmd,0,stdout=json.dumps(result)+"\n",stderr="")

        receipt=MOD.consume(ROOT,runtime,runner=runner)
        assert receipt["state"]=="COMPLETED"
        assert receipt["terminal_round_trip_observed"] is True
        assert receipt["runtime_substrate"]=="HEARTBEAT_SEPARATED_NATIVE_WORKER_COORDINATOR"
        assert receipt["second_resident_executor_required"] is False
        assert len(seen)==1
