#!/usr/bin/env python3
"""Materialize and activate the canonical heartbeat on a StegVerse-owned node."""
from __future__ import annotations
import argparse, json, os, platform, plistlib, shutil, subprocess, sys
from pathlib import Path
from typing import Any, Callable
Runner = Callable[..., subprocess.CompletedProcess[Any]]
COPY_DIRS=("heartbeat_runtime","control","handoffs","authorizations","workers","schemas","checkpoints","events","receipts","heartbeats","cost-basis")
COPY_FILES=("scripts/run_heartbeat_runtime.py","scripts/verify_sovereign_runtime_activation.py")
CANONICAL_RUNTIME="scripts.run_heartbeat_runtime.select_runtime(HB29=>engine_v12;compat=>engine_v11)"
DEFAULT_INTERVAL_MS=10.0

def default_runtime_root(env=None):
    values=dict(os.environ if env is None else env); override=values.get("STEGVERSE_HEARTBEAT_ROOT")
    if override: return Path(override).expanduser().resolve()
    name=platform.system().lower()
    if name=="windows": base=Path(values.get("LOCALAPPDATA",Path.home()/"AppData"/"Local"))
    elif name=="darwin": base=Path.home()/"Library"/"Application Support"
    else: base=Path(values.get("XDG_STATE_HOME",Path.home()/".local"/"state"))
    return (base/"stegverse"/"heartbeat-runtime").resolve()

def _nominal_cycles_per_second(interval_ms: float) -> float | None:
    if interval_ms <= 0:
        return None
    return 1000.0 / interval_ms

def materialize(source_root:Path,target_root:Path,*,interval_ms:float=DEFAULT_INTERVAL_MS):
    source_root=source_root.resolve(); target_root=target_root.resolve(); target_root.mkdir(parents=True,exist_ok=True)
    for rel in COPY_DIRS:
        src=source_root/rel
        if src.exists(): shutil.copytree(src,target_root/rel,dirs_exist_ok=True)
    for rel in COPY_FILES:
        src=source_root/rel
        if not src.is_file(): raise RuntimeError(f"missing canonical runtime file: {rel}")
        dst=target_root/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
    required=(
        target_root/"heartbeat_runtime"/"__init__.py",
        target_root/"heartbeat_runtime"/"engine_v11.py",
        target_root/"heartbeat_runtime"/"engine_v12.py",
        target_root/"control"/"heartbeat-state.json",
        target_root/"control"/"heartbeat-subsignals.json",
        target_root/"control"/"worker-registry.json",
        target_root/"schemas"/"heartbeat-carrier-runtime-state.schema.json",
        target_root/"schemas"/"heartbeat-carrier-observation.schema.json",
        target_root/"schemas"/"worker-control-plane-coordination.schema.json",
        target_root/"scripts"/"run_heartbeat_runtime.py",
        target_root/"scripts"/"verify_sovereign_runtime_activation.py",
    )
    if not all(p.is_file() for p in required): raise RuntimeError("materialized runtime is incomplete")
    init_text=(target_root/"heartbeat_runtime"/"__init__.py").read_text(encoding="utf-8")
    runner_text=(target_root/"scripts"/"run_heartbeat_runtime.py").read_text(encoding="utf-8")
    if "from .engine_v11 import HeartbeatRuntime" not in init_text:
        raise RuntimeError("materialized library compatibility does not bind engine_v11")
    if "HeartbeatRuntimeV12" not in runner_text or "select_runtime" not in runner_text or "CUTOVER_EPOCH = 29" not in runner_text:
        raise RuntimeError("materialized production runner does not bind HB29-aware engine_v12 selector")
    receipt={
        "schema":"stegverse.sovereign-heartbeat-materialization/v3",
        "source_root":str(source_root),
        "runtime_root":str(target_root),
        "canonical_runtime":CANONICAL_RUNTIME,
        "library_compatibility_runtime":"heartbeat_runtime.engine_v11.HeartbeatRuntime",
        "hb29_cutover_runtime":"heartbeat_runtime.engine_v12.HeartbeatRuntime",
        "hb29_cutover_epoch":29,
        "hb29_legacy_state_immutable":True,
        "heartbeat_default_interval_ms":float(interval_ms),
        "nominal_cycles_per_second":_nominal_cycles_per_second(float(interval_ms)),
        "worker_coordination_surface":"control/worker-control-plane-coordination.json after HB29 cutover",
        "legacy_worker_coordination_source":"control/heartbeat-subsignals.json#worker_coordination",
        "worker_lease_clock":"canonical_heartbeat_reference",
        "wall_clock_worker_expiry_authority":False,
        "network_fetch_required":False,
        "third_party_process_host_required":False,
        "third_party_scheduler_required":False,
        "third_party_deployment_required":False,
        "github_runtime_dependency":False,
        "render_runtime_dependency":False,
        "cloudflare_runtime_dependency":False,
        "heartbeat_timing_authority":"NONE_CARRIER_IS_REFERENCE_ONLY",
        "credential_authority":"TV/TVC",
        "non_tv_tvc_secret_or_token_required":False,
        "execution_authority_effect":"NONE",
        "manual_action_required":False,
    }
    path=target_root/"receipts"/"sovereign-host"/"materialization.latest.json"; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    return receipt

def _command(root,interval_ms): return [sys.executable,str(root/"scripts"/"run_heartbeat_runtime.py"),"--root",str(root),"--continuous","--interval-ms",str(interval_ms)]

def materialize_service(root:Path,*,interval_ms=DEFAULT_INTERVAL_MS,system=None,env=None):
    name=(system or platform.system()).lower(); values=dict(os.environ if env is None else env); command=_command(root,interval_ms)
    if name=="linux":
        path=Path(values.get("XDG_CONFIG_HOME",Path.home()/".config"))/"systemd"/"user"/"stegverse-heartbeat.service"
        content="\n".join(["[Unit]","Description=StegVerse Single Heartbeat Runtime","After=local-fs.target","","[Service]","Type=simple","ExecStart="+" ".join(f'\"{p}\"' for p in command),"Restart=always","RestartSec=2",f'Environment=STEGVERSE_HEARTBEAT_ROOT={root}',"","[Install]","WantedBy=default.target",""])
        activate=[["systemctl","--user","daemon-reload"],["systemctl","--user","enable","--now",path.name]]; kind="systemd-user"
    elif name=="darwin":
        path=Path.home()/"Library"/"LaunchAgents"/"org.stegverse.heartbeat.plist"; uid=getattr(os,"getuid",lambda:int(values.get("UID","0")))(); domain=f"gui/{uid}"
        content=plistlib.dumps({"Label":"org.stegverse.heartbeat","ProgramArguments":command,"RunAtLoad":True,"KeepAlive":True,"EnvironmentVariables":{"STEGVERSE_HEARTBEAT_ROOT":str(root)},"StandardOutPath":str(root/"receipts"/"sovereign-host"/"stdout.log"),"StandardErrorPath":str(root/"receipts"/"sovereign-host"/"stderr.log")}).decode()
        activate=[["launchctl","bootout",domain,str(path)],["launchctl","bootstrap",domain,str(path)]]; kind="launch-agent"
    elif name=="windows":
        path=Path(values.get("APPDATA",Path.home()/"AppData"/"Roaming"))/"StegVerse"/"heartbeat-start.cmd"; content="@echo off\r\n"+subprocess.list2cmdline(command)+"\r\n"; activate=[["schtasks","/Create","/F","/SC","ONLOGON","/TN","StegVerse Heartbeat","/TR",str(path)]]; kind="scheduled-task"
    else: raise RuntimeError(f"unsupported sovereign host platform: {name}")
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(content)
    return {
        "schema":"stegverse.sovereign-heartbeat-service/v3",
        "platform":name,
        "registration_kind":kind,
        "registration_path":str(path),
        "activation_commands":activate,
        "runtime_root":str(root),
        "canonical_runtime":CANONICAL_RUNTIME,
        "heartbeat_interval_ms":float(interval_ms),
        "nominal_cycles_per_second":_nominal_cycles_per_second(float(interval_ms)),
        "native_process_supervision_only":True,
        "third_party_process_host_required":False,
        "third_party_deployment_required":False,
        "third_party_scheduler_required":False,
        "manual_action_required":False,
    }

def install(source_root,target_root,runner=subprocess.run,*,interval_ms=DEFAULT_INTERVAL_MS,system=None,env=None):
    materialization=materialize(source_root,target_root,interval_ms=interval_ms); service=materialize_service(target_root,interval_ms=interval_ms,system=system,env=env); results=[]
    for command in service["activation_commands"]:
        completed=runner(command,check=False,capture_output=True,text=True); results.append({"command":command,"returncode":completed.returncode})
    receipt={**materialization,**service,"activation_results":results,"active":bool(results) and results[-1]["returncode"]==0}; path=target_root/"receipts"/"sovereign-host"/"activation.latest.json"; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n"); return receipt

def main():
    p=argparse.ArgumentParser(); p.add_argument("--source-root",type=Path,default=Path(__file__).resolve().parents[1]); p.add_argument("--runtime-root",type=Path); p.add_argument("--interval-ms",type=float,default=DEFAULT_INTERVAL_MS); p.add_argument("--materialize-only",action="store_true"); a=p.parse_args(); root=(a.runtime_root or default_runtime_root()).resolve()
    if a.interval_ms < 0: raise SystemExit("interval-ms must be >= 0")
    if a.materialize_only:
        result=materialize(a.source_root,root,interval_ms=a.interval_ms); result["service"]=materialize_service(root,interval_ms=a.interval_ms)
    else: result=install(a.source_root,root,interval_ms=a.interval_ms)
    print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result.get("active",True) else 1
if __name__=="__main__": raise SystemExit(main())
