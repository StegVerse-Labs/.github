#!/usr/bin/env python3
from __future__ import annotations

import json, os, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
TASK_ID = "SHWP-SV011-PHASE5-BOUNDARY-001"
CAPABILITY = "sv011_phase5_boundary_probe"
REQUIRED_ANCESTOR = "cf2777d9d21a97289f4ec7b0d9b0b21597047666"
RECEIPT_PATH = ROOT / "receipts/sv011-phase5-boundary/SHWP-SV011-PHASE5-BOUNDARY-001.json"
EVIDENCE_DIR = ROOT / "receipts/sv011-phase5-boundary/evidence"
REQUIRED_FILES = (
    "resident-runtime/run_phase5_probe.py",
    "resident-runtime/requests/phase5-allow.json",
    "resident-runtime/requests/phase5-deny.json",
    "org-boundary/runtime/intr_transport.py",
    "org-boundary/runtime/process_boundary.py",
    "org-boundary/runtime/denial_adapter.py",
    "org-boundary/registry/services.json",
)
HOSTED_ENV = ("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","VERCEL_ENV","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN_ENV = ("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","ACTIONS_RUNTIME_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","WALLET_PRIVATE_KEY","PRIVATE_KEY","SEED","MNEMONIC")

def truthy(v): return str(v or "").strip().lower() not in {"","0","false","no"}

def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as h:
        json.dump(value,h,indent=2,sort_keys=True); h.write("\n"); tmp=h.name
    os.replace(tmp,path)

def git(root: Path,*args):
    return subprocess.run(["git","-C",str(root),*args],capture_output=True,text=True,check=False,timeout=20)

def source_ok(root: Path) -> dict[str, Any]:
    head=git(root,"rev-parse","HEAD")
    clean=git(root,"status","--porcelain")
    ancestor=git(root,"merge-base","--is-ancestor",REQUIRED_ANCESTOR,"HEAD")
    return {
      "path":str(root),
      "head":head.stdout.strip() if head.returncode==0 else "",
      "clean_worktree":clean.returncode==0 and clean.stdout.strip()=="",
      "required_ancestor_present":ancestor.returncode==0,
      "required_files_present":all((root/p).is_file() for p in REQUIRED_FILES),
    }

def locate_source():
    candidates=[]
    if os.environ.get("STEGVERSE_SV011_ORG_ROOT"): candidates.append(Path(os.environ["STEGVERSE_SV011_ORG_ROOT"]).expanduser())
    candidates += [
      Path.home()/".stegverse/repos/SV-011/.github",
      Path("/var/lib/stegverse/source/SV-011/.github"),
      Path("/srv/stegverse/repos/SV-011/.github"),
      Path("/opt/stegverse/repos/SV-011/.github"),
    ]
    observed=[]
    for p in candidates:
        if not (p/".git").is_dir(): continue
        row=source_ok(p); observed.append(row)
        if row["head"] and row["clean_worktree"] and row["required_ancestor_present"] and row["required_files_present"]:
            row["selected"]=True; return p.resolve(),observed
    return None,observed

def child_env():
    allow={"HOME","USER","LOGNAME","SHELL","PATH","PYTHONPATH","LANG","LC_ALL","TMPDIR","XDG_CONFIG_HOME","XDG_STATE_HOME"}
    env={k:os.environ[k] for k in allow if os.environ.get(k)}
    for k in FORBIDDEN_ENV: env.pop(k,None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"
    return env

def run_probe(source: Path, request_name: str, observer: str):
    req=source/"resident-runtime/requests"/request_name
    proc=subprocess.run(
      [sys.executable,str(source/"resident-runtime/run_phase5_probe.py"),"--request",str(req),"--evidence-dir",str(EVIDENCE_DIR),"--runtime-observer",observer],
      cwd=source,env=child_env(),capture_output=True,text=True,check=False,timeout=120
    )
    request=json.loads(req.read_text(encoding="utf-8"))
    evidence_path=EVIDENCE_DIR/(request["request_id"]+".json")
    evidence=json.loads(evidence_path.read_text(encoding="utf-8")) if evidence_path.is_file() else None
    return proc,evidence,str(evidence_path)

def main():
    try: invocation=json.load(sys.stdin)
    except Exception: return 2
    if invocation.get("schema")!="stegverse.worker-invocation/v0.1": return 3
    task=invocation.get("task") or {}; handoff=invocation.get("handoff") or {}
    if task.get("task_id")!=TASK_ID: return 4
    execution=handoff.get("execution") or {}
    if CAPABILITY not in set(execution.get("required_capabilities") or []): return 5
    if "receipts/sv011-phase5-boundary/**" not in set(execution.get("allowed_paths") or []): return 6

    hosted=[k for k in HOSTED_ENV if truthy(os.environ.get(k))]
    now=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    observer=str(invocation.get("worker_instance_id") or invocation.get("worker_id") or "sv011-phase5-boundary-worker")
    source=None; observed=[]
    if hosted:
        state="BLOCKED"; result={"reason":"HOSTED_RUNTIME_PROHIBITED","hosted_markers":hosted}
    else:
        source,observed=locate_source()
        if source is None:
            state="BLOCKED"; result={"reason":"CURRENT_LOCAL_SV011_ORG_SOURCE_NOT_MATERIALIZED","required_ancestor":REQUIRED_ANCESTOR,"observed_candidates":observed}
        else:
            allow_proc,allow_ev,allow_path=run_probe(source,"phase5-allow.json",observer)
            deny_proc,deny_ev,deny_path=run_probe(source,"phase5-deny.json",observer)
            allow_result=(allow_ev or {}).get("result") or {}
            deny_result=(deny_ev or {}).get("result") or {}
            allow_exec=allow_result.get("execution") or {}
            deny_receipt=deny_result.get("denial_receipt") or {}
            success=(
              allow_proc.returncode==0 and deny_proc.returncode==0
              and allow_result.get("decision")=="ALLOW"
              and len(allow_exec.get("receipts") or [])==5
              and deny_result.get("decision")=="DENY"
              and deny_receipt.get("consumed") is False
              and deny_receipt.get("consequence_reachable") is False
            )
            state="COMPLETED" if success else "BLOCKED"
            result={
              "reason":"SV011_PHASE5_ALLOW_DENY_OBSERVED" if success else "SV011_PHASE5_PROBE_BLOCKED",
              "sv011_source_root":str(source),"sv011_source_head":source_ok(source)["head"],
              "allow_returncode":allow_proc.returncode,"deny_returncode":deny_proc.returncode,
              "allow_evidence_ref":allow_path,"deny_evidence_ref":deny_path,
              "allow_decision":allow_result.get("decision"),"allow_receipt_count":len(allow_exec.get("receipts") or []),
              "deny_decision":deny_result.get("decision"),"deny_consumed":deny_receipt.get("consumed"),
              "deny_consequence_reachable":deny_receipt.get("consequence_reachable"),
            }
    result.update({
      "network_source_fetch_performed":False,"source_mutation_performed":False,
      "credential_authority":"TV/TVC","credential_material_exported":False,
      "github_token_runtime_authority":"NONE","heartbeat_grants_execution_authority":False,
      "execution_authorized_by_request":False,"publication_authorized":False,"proofs_accepted":False,
    })
    receipt={"schema":"stegverse.sv011-phase5-boundary-worker-receipt/v0.1","task_id":TASK_ID,"generated_at":now,"state":state,"result":result,"authority_effect":"EXISTING_ADMITTED_TASK_AUTHORITY_ONLY"}
    atomic_write(RECEIPT_PATH,receipt)
    blocker=None if state=="COMPLETED" else {
      "dependency_class":"INTERNAL_CAPABILITY","problem_statement":result["reason"],"solution_required":True,"may_remain_blocked":True,
      "next_solution_action":"RECHECK_ALREADY_LOCAL_SV011_SOURCE_AND_PHASE5_PROBES",
      "machine_observable_release_condition":"one resident WorkerCoordinator execution records both SV-011 Phase-5 ALLOW and DENY observations"
    }
    response={
      "schema":"stegverse.worker-response/v0.1","state":state,"transition_id":f"SV011_PHASE5_BOUNDARY_{state}","transition_sequence":1,
      "expected_next_transition":None if state=="COMPLETED" else "SV011_PHASE5_BOUNDARY_RECHECK",
      "expected_next_earliest_epoch":None,"expected_next_latest_epoch":None,
      "recheck_policy":None if state=="COMPLETED" else "SEPARATE_TASK_CONTROL_EVALUATION",
      "checkpoint_ref":"receipts/sv011-phase5-boundary/SHWP-SV011-PHASE5-BOUNDARY-001.json",
      "evidence_refs":["handoffs/SHWP-SV011-PHASE5-BOUNDARY-001.json","receipts/sv011-phase5-boundary/SHWP-SV011-PHASE5-BOUNDARY-001.json"],
      "blocker":blocker,
      "cost_observation":{"task_control_evaluations":1,"compute_units":2,"external_cost_usd":0,"task_class":"sv011_phase5_boundary_probe"}
    }
    json.dump(response,sys.stdout,sort_keys=True); sys.stdout.write("\n"); return 0

if __name__=="__main__": raise SystemExit(main())
