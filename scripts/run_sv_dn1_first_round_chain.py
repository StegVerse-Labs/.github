#!/usr/bin/env python3
"""Execute the canonical SV-DN-1 first-round task chain on one sovereign resident opportunity."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable, Mapping

from refresh_sovereign_worker_runtime_source import refresh

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_REL = Path("scripts/run_worker_runtime.py")
REGISTRY_REL = Path("control/worker-registry.json")
CARRIER_REL = Path("control/heartbeat-carrier-runtime-state.json")
CHAIN_RECEIPT_REL = Path("receipts/sovereign-host/sv-dn1-first-round-chain.latest.json")

TASKS = (
    "SV-DN1-SOURCE-MATERIALIZATION-001",
    "SV-DN1-RESIDENT-OBSERVER-001",
    "SV-DN1-INTR-RUNTIME-001",
    "SV-DN1-PRODUCTION-SOURCE-PREP-001",
    "SV-DN1-SDK-FIRST-ROUND-001",
    "SV-DN1-PUBLIC-PROMOTION-001",
)

HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS",
)
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "HF_TOKEN", "HUGGINGFACE_TOKEN", "HUGGING_FACE_HUB_TOKEN",
    "TVC_EPHEMERAL_GITHUB_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
    "AZURE_CLIENT_SECRET", "OAUTH_TOKEN",
)
NONSECRET_ENV = (
    "PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR",
    "XDG_STATE_HOME", "XDG_CONFIG_HOME", "STEGVERSE_HEARTBEAT_ROOT",
    "STEGVERSE_SV_DN1_SOURCE_ROOT", "STEGVERSE_SV_DN1_MATERIALIZED_SOURCE_ROOT",
    "STEGVERSE_SV_DN1_RESIDENT_STATE_ROOT", "STEGVERSE_SV_DN1_INTR_STATE_ROOT",
    "STEGVERSE_SV_DN1_SDK_FIRST_ROUND_STATE_ROOT",
    "STEGVERSE_SOURCE_MATERIALIZATION_ROOT", "STEGVERSE_SOURCE_PACKAGE_ROOT",
    "STEGVERSE_FORMALISM_TVC_SPOOL_ROOT", "STEGVERSE_SDK_SOURCE_ROOT",
    "STEGVERSE_STEGCORE_SOURCE_ROOT", "STEGVERSE_CORE_LITE_SOURCE_ROOT",
    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
)
Runner = Callable[..., subprocess.CompletedProcess[str]]

def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}

def hosted_environment(values: Mapping[str, str] | None = None) -> list[str]:
    env = os.environ if values is None else values
    return sorted(name for name in HOSTED_ENV if truthy(env.get(name)))

def clean_exec_env(values: Mapping[str, str] | None = None) -> dict[str, str]:
    source = dict(os.environ if values is None else values)
    env = {name: source[name] for name in NONSECRET_ENV if source.get(name)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env

def default_runtime_root(values: Mapping[str, str] | None = None) -> Path:
    env = os.environ if values is None else values
    override = str(env.get("STEGVERSE_HEARTBEAT_ROOT") or "").strip()
    if override:
        return Path(override).expanduser().resolve()
    base = Path(str(env.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state")))
    return (base / "stegverse" / "heartbeat-runtime").expanduser().resolve()

def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value

def _task(registry: Mapping[str, Any], task_id: str) -> dict[str, Any] | None:
    matches = [row for row in registry.get("tasks", []) if isinstance(row, dict) and row.get("task_id") == task_id]
    if len(matches) > 1:
        raise RuntimeError(f"duplicate task identity in runtime registry: {task_id}")
    return dict(matches[0]) if matches else None

def _bound_path(env_name: str, default: Path, values: Mapping[str, str]) -> Path:
    raw = str(values.get(env_name) or "").strip()
    return Path(raw).expanduser().resolve() if raw else default.expanduser().resolve()

def _receipt_specs(values: Mapping[str, str]) -> dict[str, tuple[Path, dict[str, Any]]]:
    source_root = Path.home() / ".stegverse" / "state" / "sv-dn1-source-materialization"
    resident_root = _bound_path("STEGVERSE_SV_DN1_RESIDENT_STATE_ROOT", Path.home()/".stegverse"/"state"/"sv-dn1-resident-observer", values)
    intr_root = _bound_path("STEGVERSE_SV_DN1_INTR_STATE_ROOT", Path.home()/".stegverse"/"state"/"sv-dn1-intr-runtime", values)
    source_prep_root = Path.home()/".stegverse"/"state"/"sv-dn1-production-source-prep"
    sdk_root = _bound_path("STEGVERSE_SV_DN1_SDK_FIRST_ROUND_STATE_ROOT", Path.home()/".stegverse"/"state"/"sv-dn1-sdk-first-round", values)
    promotion_root = Path.home()/".stegverse"/"state"/"sv-dn1-public-promotion"
    return {
        "SV-DN1-SOURCE-MATERIALIZATION-001": (source_root/"receipts"/"latest.json", {"state":"COMPLETE","transition_id":"SV_DN1_EXACT_SOURCE_MATERIALIZATION_COMPLETE","github_token_used":False,"repository_writeback_performed":False}),
        "SV-DN1-RESIDENT-OBSERVER-001": (resident_root/"receipts"/"latest.json", {"state":"COMPLETE","transition_id":"SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE","raw_response_sha256_present":True,"semantic_exchange_valid":True,"github_token_used":False,"repository_writeback_performed":False,"sdk_admitted":False}),
        "SV-DN1-INTR-RUNTIME-001": (intr_root/"receipts"/"latest.json", {"state":"COMPLETE","route_id":"SV-DN-1-HF-PUBLIC","destination_validation":"PASS","lineage_verified":True,"authority_effect":"NONE"}),
        "SV-DN1-PRODUCTION-SOURCE-PREP-001": (source_prep_root/"receipts"/"latest.json", {"schema":"stegverse.sv-dn1.production-source-prep-receipt/v2","state":"COMPLETE","transition_id":"SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE","source_identity_scheme":"sha256-content-manifest","migration_anchors_verified":True,"network_source_fetch_performed":False,"github_platform_required":False,"credential_used":False,"github_token_used":False,"repository_writeback_performed":False,"sdk_admitted":False}),
        "SV-DN1-SDK-FIRST-ROUND-001": (sdk_root/"receipts"/"latest.json", {"state":"COMPLETE","transition_id":"SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED","sdk_admission":"SDK_ADMITTED","master_records_custody_status":"RECORDED","replay_consequence_reexecuted":False,"reconstruction_consequence_reexecuted":False,"dashboard_generated":True,"dashboard_publicly_hosted":False,"github_token_used":False,"repository_writeback_performed":False}),
        "SV-DN1-PUBLIC-PROMOTION-001": (promotion_root/"receipts"/"latest.json", {"schema":"stegverse.sv-dn1.public-promotion-worker-receipt/v1","state":"COMPLETE","transition_id":"SV_DN1_PUBLIC_PROMOTION_READY","observation_class":"LIVE","exact_bytes_preserved":True,"semantic_rewrite_performed":False,"network_fetch_performed":False,"credential_used":False,"repository_writeback_performed":False,"deployment_performed":False,"release_performed":False,"certification_claimed":False,"authority_effect":"NONE_STATIC_PROJECTION_ONLY"}),
    }

def validate_durable_receipt(task_id: str, values: Mapping[str, str]) -> dict[str, Any]:
    path, expected = _receipt_specs(values)[task_id]
    if not path.is_file():
        raise RuntimeError(f"{task_id}: durable receipt missing: {path}")
    receipt = _load(path)
    failures = [f"{field}={receipt.get(field)!r}, expected {wanted!r}" for field,wanted in expected.items() if receipt.get(field)!=wanted]
    if task_id == "SV-DN1-PRODUCTION-SOURCE-PREP-001":
        components={"stegverse.sdk","stegverse.stegcore","stegverse.core-lite","stegverse.master-records"}
        identities=receipt.get("source_identities");roots=receipt.get("source_roots");env_map=receipt.get("source_root_env")
        required_env={"STEGVERSE_SDK_SOURCE_ROOT","STEGVERSE_STEGCORE_SOURCE_ROOT","STEGVERSE_CORE_LITE_SOURCE_ROOT","STEGVERSE_MASTER_RECORDS_SOURCE_ROOT"}
        if not isinstance(identities,dict) or set(identities)!=components: failures.append("source_identities must contain exactly four canonical components")
        elif not all(isinstance(v,str) and v.startswith("sha256:") and len(v)==71 and all(ch in "0123456789abcdef" for ch in v[7:]) for v in identities.values()): failures.append("source_identities must all be sha256:<64 lowercase hex>")
        if not isinstance(roots,dict) or set(roots)!=components or not all(isinstance(v,str) and v for v in roots.values()): failures.append("source_roots must contain exactly four non-empty canonical component roots")
        if not isinstance(env_map,dict) or set(env_map)!=required_env or not all(isinstance(v,str) and v for v in env_map.values()): failures.append("source_root_env must contain exactly four non-empty canonical locators")
        if isinstance(roots,dict) and isinstance(env_map,dict):
            pairs={"stegverse.sdk":"STEGVERSE_SDK_SOURCE_ROOT","stegverse.stegcore":"STEGVERSE_STEGCORE_SOURCE_ROOT","stegverse.core-lite":"STEGVERSE_CORE_LITE_SOURCE_ROOT","stegverse.master-records":"STEGVERSE_MASTER_RECORDS_SOURCE_ROOT"}
            for component,env_name in pairs.items():
                if roots.get(component)!=env_map.get(env_name): failures.append(f"{component} root disagrees with {env_name}")
    if task_id == "SV-DN1-PUBLIC-PROMOTION-001":
        if receipt.get("publication_state") not in {"PUBLIC_OBSERVED","PUBLIC_WITH_LIMITATIONS"}: failures.append("publication_state must be public-observable")
        src=receipt.get("source_artifact_sha256");dst=receipt.get("destination_artifact_sha256")
        if not isinstance(src,dict) or src!=dst or set(src)!={"first-round-analysis.json","production-pipeline-observation.json","result-receipt.json","report.md","index.html"}: failures.append("promotion artifact hash set mismatch")
    if failures:
        raise RuntimeError(f"{task_id}: durable receipt failed validation: "+"; ".join(failures))
    return {"task_id":task_id,"receipt_path":str(path)}

def _atomic_json(path:Path,value:Mapping[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_name("."+path.name+".tmp");temp.write_text(json.dumps(dict(value),indent=2,sort_keys=True)+"\n",encoding="utf-8");os.replace(temp,path)

def execute_chain(source_root:Path,runtime_root:Path,*,runner:Runner=subprocess.run,env:Mapping[str,str]|None=None)->dict[str,Any]:
    values=dict(os.environ if env is None else env)
    hosted=hosted_environment(values)
    if hosted: raise RuntimeError("hosted execution cannot produce sovereign SV-DN-1 evidence: "+",".join(hosted))
    source=source_root.expanduser().resolve();runtime=runtime_root.expanduser().resolve();refresh_receipt=refresh(source,runtime)
    carrier=runtime/CARRIER_REL
    if not carrier.is_file(): return {"schema":"stegverse.sv-dn1.sovereign-chain/v1","state":"HANDOFF_READY","transition_id":"SV_DN1_SOVEREIGN_CARRIER_REFERENCE_PENDING","completed_tasks":[],"next_task":TASKS[0],"runtime_root":str(runtime),"refresh_receipt":refresh_receipt,"authority_effect":"NONE"}
    runner_path=runtime/RUNNER_REL;registry_path=runtime/REGISTRY_REL
    if not runner_path.is_file() or not registry_path.is_file(): raise RuntimeError("targeted WorkerCoordinator runtime surfaces missing after refresh")
    child_env=clean_exec_env(values);completed_tasks=[];task_results=[]
    for task_id in TASKS:
        registry=_load(registry_path);row=_task(registry,task_id)
        if row is not None and row.get("state")=="COMPLETED":
            validated=validate_durable_receipt(task_id,values);completed_tasks.append(task_id);task_results.append({"task_id":task_id,"execution_attempted":False,"registry_state":"COMPLETED","durable_receipt":validated});continue
        if row is not None and row.get("state") in {"ACTIVE","BLOCKED"}:
            return {"schema":"stegverse.sv-dn1.sovereign-chain/v1","state":"HANDOFF_READY","transition_id":"SV_DN1_EXISTING_TASK_LIFECYCLE_MUST_RESOLVE","completed_tasks":completed_tasks,"next_task":task_id,"task_state":row.get("state"),"claim_id":row.get("claim_id"),"worker_id":row.get("worker_id"),"runtime_root":str(runtime),"refresh_receipt":refresh_receipt,"task_results":task_results,"authority_effect":"NONE"}
        command=[sys.executable,str(runner_path),"--root",str(runtime),"--task-id",task_id]
        completed=runner(command,cwd=runtime,capture_output=True,text=True,check=False,env=child_env,timeout=1200)
        registry=_load(registry_path);row=_task(registry,task_id);state=None if row is None else row.get("state")
        result={"task_id":task_id,"execution_attempted":True,"command":command,"returncode":completed.returncode,"registry_state":state,"stderr_tail":(completed.stderr or "")[-2000:]}
        if completed.returncode!=0 or state!="COMPLETED":
            task_results.append(result);return {"schema":"stegverse.sv-dn1.sovereign-chain/v1","state":"HANDOFF_READY","transition_id":"SV_DN1_CHAIN_STEP_NOT_TERMINAL","completed_tasks":completed_tasks,"next_task":task_id,"task_state":state,"runtime_root":str(runtime),"refresh_receipt":refresh_receipt,"task_results":task_results,"authority_effect":"NONE"}
        try: validated=validate_durable_receipt(task_id,values)
        except Exception as exc:
            result["durable_receipt_error"]=str(exc);task_results.append(result);return {"schema":"stegverse.sv-dn1.sovereign-chain/v1","state":"BLOCKED","transition_id":"SV_DN1_CHAIN_DURABLE_RECEIPT_MISMATCH","completed_tasks":completed_tasks,"next_task":task_id,"runtime_root":str(runtime),"refresh_receipt":refresh_receipt,"task_results":task_results,"authority_effect":"NONE"}
        result["durable_receipt"]=validated;task_results.append(result);completed_tasks.append(task_id)
        if task_id=="SV-DN1-SOURCE-MATERIALIZATION-001":
            receipt=_load(Path(validated["receipt_path"]));materialized=str(receipt.get("source_root") or "").strip()
            if materialized: child_env["STEGVERSE_SV_DN1_SOURCE_ROOT"]=materialized
        if task_id=="SV-DN1-PRODUCTION-SOURCE-PREP-001":
            receipt=_load(Path(validated["receipt_path"]));locators=receipt.get("source_root_env") or {}
            for name in ("STEGVERSE_SDK_SOURCE_ROOT","STEGVERSE_STEGCORE_SOURCE_ROOT","STEGVERSE_CORE_LITE_SOURCE_ROOT","STEGVERSE_MASTER_RECORDS_SOURCE_ROOT"):
                if locators.get(name): child_env[name]=str(locators[name])
    receipt={"schema":"stegverse.sv-dn1.sovereign-chain/v1","state":"COMPLETE","transition_id":"SV_DN1_SOVEREIGN_FIRST_ROUND_CHAIN_COMPLETE","completed_tasks":completed_tasks,"next_task":None,"runtime_root":str(runtime),"source_root":str(source),"refresh_receipt":refresh_receipt,"task_results":task_results,"credential_authority":"TV/TVC","github_token_required":False,"second_machine_required":False,"public_promotion_ready":True,"repository_writeback_performed":False,"deployment_performed":False,"authority_effect":"NONE"}
    _atomic_json(runtime/CHAIN_RECEIPT_REL,receipt);return receipt

def main()->int:
    parser=argparse.ArgumentParser(description="Execute the canonical SV-DN-1 sovereign first-round chain.");parser.add_argument("--source-root",type=Path,default=REPO_ROOT);parser.add_argument("--runtime-root",type=Path,default=default_runtime_root());args=parser.parse_args()
    try: result=execute_chain(args.source_root,args.runtime_root)
    except Exception as exc: result={"schema":"stegverse.sv-dn1.sovereign-chain/v1","state":"BLOCKED","transition_id":"SV_DN1_SOVEREIGN_CHAIN_BLOCKED","error":str(exc),"authority_effect":"NONE"}
    print(json.dumps(result,sort_keys=True));return 0 if result.get("state") in {"COMPLETE","HANDOFF_READY"} else 1
if __name__=="__main__":raise SystemExit(main())
