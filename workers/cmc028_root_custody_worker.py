#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
TASK_ID = "SHWP-CMC028-ROOT-CUSTODY-EVIDENCE-001"
CAPABILITY = "tvc_cmc028_root_custody_evidence"
REQUIRED_TVC_ANCESTOR = "dd3734084eba4887c0c08e2e47eab3a20565c820"
RECEIPT_PATH = ROOT / "receipts" / "cmc028-root-custody" / f"{TASK_ID}.json"

REQUIRED_TVC_FILES = (
    "tools/task_dispatcher.py",
    "scripts/validate_certificate_root_key_custody_028.py",
    "tvc_certificate_root_key_custody_runtime_tasks.py",
    "config/task_catalog.d/certificate-root-key-custody-028.json",
    "tasks/TVC-CERTIFICATE-ROOT-KEY-CUSTODY-028.json",
    "docs/CERTIFICATE_ROOT_KEY_CUSTODY_028_MIRROR_HANDOFF.md",
)

HOSTED_ENV = (
    "GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","VERCEL_ENV",
    "CF_PAGES","CLOUDFLARE_WORKERS",
)
FORBIDDEN_ENV = (
    "GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "PRIVATE_KEY","WALLET_PRIVATE_KEY","SEED","MNEMONIC",
    "STEGVERSE_MAIL_CLIENT_SECRET","STEGVERSE_MAIL_ACCESS_TOKEN",
    "STEGVERSE_MAIL_REFRESH_TOKEN","AZURE_CLIENT_SECRET",
)


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"","0","false","no"}


def _hosted_runtime_active() -> list[str]:
    return [name for name in HOSTED_ENV if _truthy(os.environ.get(name))]


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git","-C",str(root),*args],
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )


def _git_head(root: Path) -> str:
    p=_git(root,"rev-parse","HEAD")
    return p.stdout.strip() if p.returncode==0 else ""


def _clean(root: Path) -> bool:
    p=_git(root,"status","--porcelain")
    return p.returncode==0 and p.stdout.strip()==""


def _contains_required_ancestor(root: Path) -> bool:
    return _git(root,"merge-base","--is-ancestor",REQUIRED_TVC_ANCESTOR,"HEAD").returncode==0


def locate_tvc() -> tuple[Path | None,list[dict[str,Any]]]:
    candidates=[]
    raw=os.environ.get("STEGVERSE_TVC_ROOT","").strip()
    if raw:
        candidates.append(Path(raw).expanduser())
    candidates.extend([
        Path.home()/".stegverse"/"repos"/"StegVerse-Labs"/"TVC",
        Path("/var/lib/stegverse/source/StegVerse-Labs/TVC"),
        Path("/srv/stegverse/repos/StegVerse-Labs/TVC"),
        Path("/opt/stegverse/repos/StegVerse-Labs/TVC"),
    ])
    observed=[]
    for candidate in candidates:
        if not (candidate/".git").is_dir():
            continue
        row={
            "path":str(candidate),
            "head":_git_head(candidate),
            "clean_worktree":_clean(candidate),
            "required_ancestor_present":_contains_required_ancestor(candidate),
            "required_source_present":all((candidate/p).is_file() for p in REQUIRED_TVC_FILES),
        }
        observed.append(row)
        if row["head"] and row["clean_worktree"] and row["required_ancestor_present"] and row["required_source_present"]:
            row["selected"]=True
            return candidate.resolve(),observed
    return None,observed


def child_env() -> dict[str,str]:
    allow={
        "HOME","USER","LOGNAME","SHELL","PATH","PYTHONPATH","LANG","LC_ALL",
        "TMPDIR","XDG_CONFIG_HOME","XDG_STATE_HOME","STEGVERSE_TVC_ROOT"
    }
    env={k:os.environ[k] for k in allow if os.environ.get(k)}
    for k in FORBIDDEN_ENV:
        env.pop(k,None)
    return env


def atomic_write(path: Path,value: dict[str,Any]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,delete=False) as h:
        json.dump(value,h,indent=2,sort_keys=True)
        h.write("\n")
        tmp=h.name
    os.replace(tmp,path)


def parse_dispatcher(proc: subprocess.CompletedProcess[str]) -> dict[str,Any] | None:
    try:
        value=json.loads(proc.stdout)
    except Exception:
        return None
    return value if isinstance(value,dict) else None


def task_control_identity(invocation: dict[str,Any],task: dict[str,Any]) -> dict[str,Any]:
    lease=task.get("lease") if isinstance(task.get("lease"),dict) else {}
    timing=task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"),dict) else {}
    fence=lease.get("fencing_token",timing.get("fencing_token"))
    epoch=invocation.get("heartbeat_epoch")
    return {
        "claim_id":task.get("claim_id") if isinstance(task.get("claim_id"),str) else None,
        "fencing_token":fence if isinstance(fence,int) else None,
        "observed_heartbeat_epoch":epoch if isinstance(epoch,int) else None,
        "heartbeat_reference_only":True,
        "heartbeat_grants_execution_authority":False,
    }


def main() -> int:
    try:
        invocation=json.load(sys.stdin)
    except Exception:
        return 2
    if invocation.get("schema")!="stegverse.worker-invocation/v0.1":
        return 3
    task=invocation.get("task") or {}
    handoff=invocation.get("handoff") or {}
    if task.get("task_id")!=TASK_ID:
        return 4
    execution=handoff.get("execution") or {}
    if CAPABILITY not in set(execution.get("required_capabilities") or []):
        return 5
    if "receipts/cmc028-root-custody/**" not in set(execution.get("allowed_paths") or []):
        return 6

    control=task_control_identity(invocation,task)
    now=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    hosted=_hosted_runtime_active()

    if hosted:
        state="BLOCKED"
        result={
            "reason":"HOSTED_RUNTIME_PROHIBITED",
            "hosted_markers":hosted,
            "credential_authority":"TV/TVC",
            "protected_material_read":False,
            "protected_material_hashed":False,
            "protected_material_exported":False,
            "source_mutation_performed":False,
            "network_source_fetch_performed":False,
        }
    else:
        tvc,observed=locate_tvc()
        if tvc is None:
            state="BLOCKED"
            result={
                "reason":"CURRENT_LOCAL_TVC_SOURCE_NOT_MATERIALIZED",
                "required_ancestor":REQUIRED_TVC_ANCESTOR,
                "observed_candidates":observed,
                "credential_authority":"TV/TVC",
                "protected_material_read":False,
                "protected_material_hashed":False,
                "protected_material_exported":False,
                "source_mutation_performed":False,
                "network_source_fetch_performed":False,
            }
        else:
            proc=subprocess.run(
                ["python","tools/task_dispatcher.py","tvc.certificate_root_custody.observe"],
                cwd=tvc,
                env=child_env(),
                text=True,
                capture_output=True,
                timeout=240,
                check=False,
            )
            report=parse_dispatcher(proc)
            task_result=report.get("result") if isinstance(report,dict) else None
            success=(
                proc.returncode==0
                and isinstance(report,dict)
                and report.get("status")=="ok"
                and isinstance(task_result,dict)
                and task_result.get("state")=="CUSTODY_RECOVERY_EVIDENCE_VERIFIED"
                and task_result.get("credential_authority")=="TV/TVC"
                and task_result.get("protected_material_exported") is False
                and task_result.get("protected_material_read") is False
                and task_result.get("protected_material_hashed") is False
                and task_result.get("certificate_issuance_authority") is False
                and task_result.get("signing_authority_granted") is False
                and task_result.get("runtime_activation_claimed") is False
            )
            state="COMPLETED" if success else "BLOCKED"
            result={
                "reason":"CMC028_CUSTODY_RECOVERY_EVIDENCE_RECORDED" if success else "CMC028_RESIDENT_EVIDENCE_BLOCKED",
                "tvc_source_root":str(tvc),
                "tvc_source_head":_git_head(tvc),
                "required_ancestor":REQUIRED_TVC_ANCESTOR,
                "dispatcher_exit_code":proc.returncode,
                "dispatcher_report":report,
                "dispatcher_stderr_tail":(proc.stderr or "")[-4000:],
                "receipt_path":task_result.get("receipt_path") if isinstance(task_result,dict) else None,
                "key_id":task_result.get("key_id") if isinstance(task_result,dict) else None,
                "runtime_id":task_result.get("runtime_id") if isinstance(task_result,dict) else None,
                "public_fingerprint":task_result.get("public_fingerprint") if isinstance(task_result,dict) else None,
                "credential_authority":"TV/TVC",
                "protected_material_read":False,
                "protected_material_hashed":False,
                "protected_material_exported":False,
                "certificate_issuance_authority":False,
                "signing_authority_granted":False,
                "source_mutation_performed":False,
                "network_source_fetch_performed":False,
            }

    receipt={
        "schema":"stegverse.cmc028-root-custody-worker-receipt/v0.1",
        "task_id":TASK_ID,
        "task_control":control,
        "generated_at":now,
        "state":state,
        "result":result,
        "credential_authority":"TV/TVC",
        "heartbeat_grants_execution_authority":False,
        "github_token_runtime_authority":"NONE",
        "authority_effect":"TVC_CMC028_EVIDENCE_EXECUTION_ONLY",
    }
    atomic_write(RECEIPT_PATH,receipt)

    blocker=None
    if state!="COMPLETED":
        blocker={
            "dependency_class":"INTERNAL_CAPABILITY",
            "problem_statement":result["reason"],
            "solution_required":True,
            "may_remain_blocked":True,
            "next_solution_action":"RECHECK_ELIGIBLE_TVC_RESIDENT_AND_CMC028_EVIDENCE_INPUTS",
            "machine_observable_release_condition":"A sovereign worker cycle records CUSTODY_RECOVERY_EVIDENCE_VERIFIED without protected-material read/hash/export",
        }
    response={
        "schema":"stegverse.worker-response/v0.1",
        "state":state,
        "transition_id":f"CMC028_ROOT_CUSTODY_{state}",
        "transition_sequence":1,
        "expected_next_transition":None if state=="COMPLETED" else "CMC028_ROOT_CUSTODY_RECHECK",
        "expected_next_earliest_epoch":None,
        "expected_next_latest_epoch":None,
        "recheck_policy":None if state=="COMPLETED" else "SEPARATE_TASK_CONTROL_EVALUATION",
        "checkpoint_ref":"receipts/cmc028-root-custody/SHWP-CMC028-ROOT-CUSTODY-EVIDENCE-001.json",
        "evidence_refs":[
            "handoffs/SHWP-CMC028-ROOT-CUSTODY-EVIDENCE-001.json",
            "receipts/cmc028-root-custody/SHWP-CMC028-ROOT-CUSTODY-EVIDENCE-001.json",
            "StegVerse-Labs/TVC/tasks/TVC-CERTIFICATE-ROOT-KEY-CUSTODY-028.json",
        ],
        "blocker":blocker,
        "cost_observation":{
            "task_control_evaluations":1,
            "observed_heartbeat_reference_count":1 if control["observed_heartbeat_epoch"] is not None else 0,
            "compute_units":1,
            "external_cost_usd":0,
            "task_class":"tvc_cmc028_root_custody_evidence",
        },
    }
    json.dump(response,sys.stdout,sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
