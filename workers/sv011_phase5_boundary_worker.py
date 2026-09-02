#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, os, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
TASK_ID = "SHWP-SV011-PHASE5-BOUNDARY-001"
CAPABILITY = "sv011_phase5_boundary_probe"
REQUIRED_ANCESTOR = "cf2777d9d21a97289f4ec7b0d9b0b21597047666"
RECEIPT_PATH = ROOT / "receipts/sv011-phase5-boundary/SHWP-SV011-PHASE5-BOUNDARY-001.json"
EVIDENCE_DIR = ROOT / "receipts/sv011-phase5-boundary/evidence"
EXPECTED_BLOBS = {
    "resident-runtime/run_phase5_probe.py": "bb66bb78e458bae91c71eaabc8d15724c8bf8cba",
    "resident-runtime/requests/phase5-allow.json": "b17f563acc051d45ca988b139ccc3d9321123251",
    "resident-runtime/requests/phase5-deny.json": "185f174d01a52e6db72dab60072ba429386311bb",
    "org-boundary/runtime/intr_transport.py": "c52bde0587f3203a7d77789d8735007a25bb6267",
    "org-boundary/runtime/process_boundary.py": "4a167a3af36f894e45362ee67f0a9050dca287fb",
    "org-boundary/runtime/denial_adapter.py": "207e9e9fab484ed3c3a2bdf622ba1580e354c6b8",
    "org-boundary/registry/services.json": "08bd4ba431a071a17abba76ac45536f92ebb7f6e",
}
IDENTITY_FILE = ".stegverse-source-identity.json"
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

def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\\0".encode() + raw).hexdigest()

def exact_blob_status(root: Path) -> tuple[bool, dict[str, str]]:
    observed: dict[str, str] = {}
    for rel, expected in EXPECTED_BLOBS.items():
        p = root / rel
        actual = git_blob_sha1(p.read_bytes()) if p.is_file() else "MISSING"
        observed[rel] = actual
        if actual != expected:
            return False, observed
    return True, observed

def materialized_identity_ok(root: Path) -> bool:
    path = root / IDENTITY_FILE
    if not path.is_file():
        return False
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return bool(
        isinstance(value, dict)
        and value.get("schema") == "stegverse.sv011-materialized-source-identity/v0.1"
        and value.get("repository") == "SV-011/.github"
        and value.get("source_basis_commit") == REQUIRED_ANCESTOR
        and value.get("verified_git_blob_count") == 7
        and value.get("authority_effect") == "NONE_SOURCE_MATERIALIZATION_ONLY"
    )

def source_ok(root: Path) -> dict[str, Any]:
    root = root.expanduser().resolve()
    blobs_ok, observed_blobs = exact_blob_status(root) if root.is_dir() else (False, {})
    git_present = (root / ".git").is_dir()
    head = git(root, "rev-parse", "HEAD") if git_present else None
    clean = git(root, "status", "--porcelain") if git_present else None
    ancestor = git(root, "merge-base", "--is-ancestor", REQUIRED_ANCESTOR, "HEAD") if git_present else None
    git_ok = bool(
        git_present and head and head.returncode == 0
        and clean and clean.returncode == 0 and clean.stdout.strip() == ""
        and ancestor and ancestor.returncode == 0
        and blobs_ok
    )
    materialized_ok = bool((not git_present) and blobs_ok and materialized_identity_ok(root))
    return {
      "path": str(root),
      "head": head.stdout.strip() if head and head.returncode == 0 else "",
      "clean_worktree": clean.returncode == 0 and clean.stdout.strip() == "" if clean else None,
      "required_ancestor_present": ancestor.returncode == 0 if ancestor else None,
      "required_files_present": all((root / p).is_file() for p in REQUIRED_FILES),
      "exact_git_blobs_verified": blobs_ok,
      "observed_git_blobs": observed_blobs,
      "materialized_identity_verified": materialized_identity_ok(root) if root.is_dir() else False,
      "source_mode": "CLEAN_GIT_CHECKOUT" if git_ok else ("VERIFIED_MATERIALIZED_TREE" if materialized_ok else "UNVERIFIED"),
      "verified": git_ok or materialized_ok,
    }

def locate_source():
    candidates=[]
    for env_name in ("STEGVERSE_SV011_ORG_ROOT", "STEGVERSE_SV011_MATERIALIZED_ROOT"):
        raw=os.environ.get(env_name)
        if raw: candidates.append(Path(raw).expanduser())
    candidates += [
      Path.home()/".stegverse/repos/SV-011/.github",
      Path.home()/".stegverse/source/SV-011/.github",
      Path("/var/lib/stegverse/source/SV-011/.github"),
      Path("/srv/stegverse/repos/SV-011/.github"),
      Path("/opt/stegverse/repos/SV-011/.github"),
    ]
    observed=[]
    seen=set()
    for p in candidates:
        resolved=p.expanduser().resolve()
        if str(resolved) in seen or not resolved.is_dir(): continue
        seen.add(str(resolved))
        row=source_ok(resolved); observed.append(row)
        if row["verified"]:
            row["selected"]=True; return resolved,observed
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
              "sv011_source_mode":source_ok(source)["source_mode"],"sv011_exact_git_blobs_verified":source_ok(source)["exact_git_blobs_verified"],
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
