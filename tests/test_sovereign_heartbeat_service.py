from __future__ import annotations
import importlib.util
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("install_sovereign_heartbeat_service",ROOT/"scripts"/"install_sovereign_heartbeat_service.py"); assert SPEC and SPEC.loader
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

def test_materialization_is_network_independent(tmp_path:Path):
    target=tmp_path/"heartbeat"; r=mod.materialize(ROOT,target)
    assert r["network_fetch_required"] is False and r["third_party_deployment_required"] is False and r["third_party_scheduler_required"] is False
    assert (target/"heartbeat_runtime"/"engine_v8.py").is_file() and (target/"control"/"worker-registry.json").is_file()

def test_linux_service_runs_continuous_runtime_directly(tmp_path:Path):
    root=tmp_path/"heartbeat"; mod.materialize(ROOT,root); r=mod.materialize_service(root,system="linux",env={"XDG_CONFIG_HOME":str(tmp_path/"config")}); text=Path(r["registration_path"]).read_text()
    assert r["registration_kind"]=="systemd-user" and "run_heartbeat_runtime.py" in text and "--continuous" in text and "Restart=always" in text
    assert "github" not in text.lower() and "render" not in text.lower()

def test_install_records_native_activation_without_granting_authority(tmp_path:Path):
    calls=[]
    def runner(command,**_kwargs): calls.append(command); return SimpleNamespace(returncode=0,stdout="",stderr="")
    target=tmp_path/"heartbeat"; r=mod.install(ROOT,target,runner=runner,system="linux",env={"XDG_CONFIG_HOME":str(tmp_path/"config")})
    assert r["active"] is True and r["execution_authority_effect"]=="NONE" and r["third_party_deployment_required"] is False and len(calls)==2
    assert (target/"receipts"/"sovereign-host"/"activation.latest.json").is_file()
