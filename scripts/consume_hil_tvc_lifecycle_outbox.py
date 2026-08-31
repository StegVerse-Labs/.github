#!/usr/bin/env python3
"""Consume durable HIL custody→TVC lifecycle outbox events without gaining TVC authority."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Callable

TVC_SOURCE_FLOOR = "2787eece099604a4d2aad93c575167dc73e54037"
TVC_PROTECTED_PATHS = (
    "tools/hil_intr_lifecycle_intake.py",
    "tasks/hil_experiment_backend_adapter.py",
    "tasks/experiment_controlled_cycle.py",
    "config/experiment_backend.json",
    "config/package_registry.json",
)
WORKER_RECEIPT_REL = Path("receipts/hil-sovereign-receiver/SHWP-HIL-SOVEREIGN-RECEIVER-001.json")
CONSUMPTION_REL = Path("receipts/hil-sovereign-receiver/tvc-lifecycle-outbox-consumption.latest.json")
CREDENTIAL_AUTHORITY = "TV/TVC"

Runner = Callable[..., subprocess.CompletedProcess[str]]

class PredicatePending(RuntimeError):
    pass

def _load(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise RuntimeError(f"object_required:{path}")
    return value

def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False

def _clean_env(source: Mapping[str,str]|None=None)->dict[str,str]:
    values=dict(os.environ if source is None else source)
    hosted=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
    if any(str(values.get(k) or "").strip().lower() not in {"","0","false","no"} for k in hosted):
        raise RuntimeError("hosted_environment_not_admitted_for_hil_tvc_lifecycle")
    allowed=("PATH","HOME","LANG","LC_ALL","SSL_CERT_FILE","SSL_CERT_DIR","STEGVERSE_TVC_ROOT","STEGVERSE_RESIDENT_SOURCE_MANIFEST")
    env={k:values[k] for k in allowed if values.get(k)}
    env["PYTHONDONTWRITEBYTECODE"]="1"
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"
    return env

def _git(root:Path,args:list[str],*,runner:Runner,env:Mapping[str,str])->subprocess.CompletedProcess[str]:
    return runner(["git","-C",str(root),*args],capture_output=True,text=True,check=False,timeout=30,env=dict(env))

def validate_tvc_bundle_root(root: Path, manifest_path: Path) -> None:
    root = root.expanduser().resolve()
    manifest_path = manifest_path.expanduser().resolve()
    if not manifest_path.is_file():
        raise PredicatePending("TVC_PORTABLE_SOURCE_MANIFEST_NOT_AVAILABLE")
    manifest = _load(manifest_path)
    if manifest.get("schema") != "stegverse.sovereign-control-plane-bundle/v1":
        raise RuntimeError("tvc_portable_source_manifest_schema_invalid")
    if manifest.get("network_fetch_required") is not False:
        raise RuntimeError("tvc_portable_source_manifest_network_policy_invalid")
    if manifest.get("credential_authority") != "TV/TVC":
        raise RuntimeError("tvc_portable_source_manifest_credential_authority_invalid")
    if manifest.get("github_token_runtime_authority") != "NONE":
        raise RuntimeError("tvc_portable_source_manifest_github_authority_invalid")
    if manifest.get("bundle_grants_authority") is not False:
        raise RuntimeError("tvc_portable_source_manifest_authority_invalid")
    proofs = manifest.get("vendor_source_proofs") or {}
    proof = proofs.get("TVC") if isinstance(proofs, dict) else None
    if not isinstance(proof, dict) or proof.get("state") != "VERIFIED_LOCAL_GIT_SOURCE":
        raise PredicatePending("TVC_PORTABLE_SOURCE_PROOF_NOT_VERIFIED")
    if proof.get("repository") != "StegVerse-Labs/TVC":
        raise RuntimeError("tvc_portable_source_repository_identity_invalid")
    if proof.get("source_floor") != TVC_SOURCE_FLOOR or proof.get("source_floor_present") is not True:
        raise RuntimeError("tvc_portable_source_floor_invalid")
    if proof.get("protected_paths_unchanged_since_floor") is not True:
        raise RuntimeError("tvc_portable_source_protected_path_proof_invalid")
    if tuple(proof.get("protected_paths") or ()) != TVC_PROTECTED_PATHS:
        raise RuntimeError("tvc_portable_source_protected_path_set_invalid")
    subpath = str(proof.get("materialized_subpath") or "")
    if subpath != "vendor/TVC":
        raise RuntimeError("tvc_portable_source_subpath_invalid")
    expected_root = (manifest_path.parent / subpath).resolve()
    if root != expected_root:
        raise RuntimeError("tvc_portable_source_root_binding_invalid")
    declared = {
        str(entry.get("path")): entry
        for entry in manifest.get("files", [])
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    }
    for rel in TVC_PROTECTED_PATHS:
        path = root / rel
        if not path.is_file():
            raise RuntimeError(f"tvc_hil_lifecycle_source_missing:{rel}")
        entry = declared.get("vendor/TVC/" + rel)
        if not isinstance(entry, dict):
            raise RuntimeError(f"tvc_portable_source_manifest_entry_missing:{rel}")
        data = path.read_bytes()
        if len(data) != entry.get("size") or hashlib.sha256(data).hexdigest() != entry.get("sha256"):
            raise RuntimeError(f"tvc_portable_source_digest_mismatch:{rel}")


def validate_tvc_root(root:Path,*,runner:Runner=subprocess.run,env:Mapping[str,str]|None=None)->None:
    safe=_clean_env(env)
    root=root.expanduser().resolve()
    if not (root/"tools/hil_intr_lifecycle_intake.py").is_file():
        raise PredicatePending("TVC_HIL_LIFECYCLE_SOURCE_NOT_AVAILABLE")
    ancestor=_git(root,["merge-base","--is-ancestor",TVC_SOURCE_FLOOR,"HEAD"],runner=runner,env=safe)
    if ancestor.returncode!=0:
        raise PredicatePending("TVC_HIL_LIFECYCLE_SOURCE_FLOOR_NOT_PRESENT")
    changed=_git(root,["diff","--name-only",TVC_SOURCE_FLOOR,"HEAD","--",*TVC_PROTECTED_PATHS],runner=runner,env=safe)
    if changed.returncode!=0 or changed.stdout.strip():
        raise RuntimeError("tvc_hil_lifecycle_source_changed_since_validated_floor")
    working=_git(root,["diff","--name-only","--",*TVC_PROTECTED_PATHS],runner=runner,env=safe)
    staged=_git(root,["diff","--cached","--name-only","--",*TVC_PROTECTED_PATHS],runner=runner,env=safe)
    if working.returncode!=0 or staged.returncode!=0 or working.stdout.strip() or staged.stdout.strip():
        raise RuntimeError("tvc_hil_lifecycle_source_worktree_drift")
    for rel in TVC_PROTECTED_PATHS:
        if not (root/rel).is_file(): raise RuntimeError(f"tvc_hil_lifecycle_source_missing:{rel}")

def discover_tvc_root(values:Mapping[str,str],*,runner:Runner=subprocess.run)->tuple[Path,str]:
    candidates=[]
    if values.get("STEGVERSE_TVC_ROOT"): candidates.append(Path(values["STEGVERSE_TVC_ROOT"]))
    candidates += [
        Path.home()/".stegverse/repos/StegVerse-Labs/TVC",
        Path("/srv/stegverse/repos/StegVerse-Labs/TVC"),
        Path("/opt/stegverse/repos/StegVerse-Labs/TVC"),
        Path("/var/lib/stegverse/source/StegVerse-Labs/TVC"),
    ]
    manifest_raw=str(values.get("STEGVERSE_RESIDENT_SOURCE_MANIFEST") or "").strip()
    manifest_path=Path(manifest_raw) if manifest_raw else None
    errors=[]
    seen=set()
    for candidate in candidates:
        resolved=candidate.expanduser().resolve()
        if str(resolved) in seen:
            continue
        seen.add(str(resolved))
        try:
            validate_tvc_root(resolved,runner=runner,env=values)
            return resolved,"LOCAL_GIT_PROOF"
        except PredicatePending as exc:
            errors.append(str(exc))
            if manifest_path is not None:
                try:
                    validate_tvc_bundle_root(resolved,manifest_path)
                    return resolved,"VERIFIED_PORTABLE_BUNDLE_PROOF"
                except PredicatePending as bundle_exc:
                    errors.append(str(bundle_exc))
                    continue
            continue
    raise PredicatePending("TVC_HIL_LIFECYCLE_SOURCE_NOT_AVAILABLE:"+";".join(errors))

def _last_json(stdout:str)->dict[str,Any]|None:
    for line in reversed([v.strip() for v in stdout.splitlines() if v.strip()]):
        try: value=json.loads(line)
        except Exception: continue
        if isinstance(value,dict): return value
    return None

def consume(runtime_root:Path,*,runner:Runner=subprocess.run,env:Mapping[str,str]|None=None)->dict[str,Any]:
    runtime=runtime_root.expanduser().resolve()
    worker_path=runtime/WORKER_RECEIPT_REL
    if not worker_path.is_file():
        return {"schema":"stegverse.hil.tvc-lifecycle-outbox-consumption/v1","state":"NO_EVENT","authority_effect":"NONE"}
    worker=_load(worker_path)
    if worker.get("receiver_ready") is not True: raise PredicatePending("HIL_RECEIVER_NOT_READY")
    durable_raw=worker.get("durable_state_root")
    if not isinstance(durable_raw,str) or not durable_raw: raise RuntimeError("hil_durable_state_root_missing")
    durable=Path(durable_raw).expanduser().resolve()
    outbox=durable/"intr-outbox/tvc-hil-lifecycle"
    if not outbox.is_dir():
        return {"schema":"stegverse.hil.tvc-lifecycle-outbox-consumption/v1","state":"NO_EVENT","authority_effect":"NONE"}
    queues=sorted(outbox.glob("*.json"))
    if not queues:
        return {"schema":"stegverse.hil.tvc-lifecycle-outbox-consumption/v1","state":"NO_EVENT","authority_effect":"NONE"}

    values=dict(os.environ if env is None else env)
    tvc_root,tvc_source_validation_mode=discover_tvc_root(values,runner=runner)
    safe=_clean_env(values)
    output_root=durable/"tvc-lifecycle-admission"
    results=[]
    failures=[]
    for queue_path in queues:
        queue=_load(queue_path)
        if queue.get("schema")!="stegverse.hil.tvc_interlock_queue/v1" or queue.get("state")!="READY_FOR_INTERLOCK_ADMISSION":
            failures.append({"queue":str(queue_path),"reason":"queue_contract_invalid"}); continue
        receipt_ref=queue.get("receiver_receipt_ref")
        if not isinstance(receipt_ref,str) or not receipt_ref:
            failures.append({"queue":str(queue_path),"reason":"receiver_receipt_ref_missing"}); continue
        receipt_path=Path(receipt_ref).expanduser().resolve()
        if not _inside(receipt_path,durable/"receiver-receipts") or not receipt_path.is_file():
            failures.append({"queue":str(queue_path),"reason":"receiver_receipt_ref_invalid"}); continue
        command=[
            sys.executable,str(tvc_root/"tools/hil_intr_lifecycle_intake.py"),
            "--queue",str(queue_path),
            "--receiver-receipt",str(receipt_path),
            "--output-root",str(output_root),
        ]
        completed=runner(command,cwd=tvc_root,capture_output=True,text=True,check=False,timeout=900,env=safe)
        result=_last_json(completed.stdout)
        admitted=bool(
            completed.returncode==0 and isinstance(result,dict)
            and result.get("state")=="ADMITTED_TO_TVC_HIL_LIFECYCLE"
            and result.get("credential_authority")=="TV/TVC"
            and result.get("authority_transfer") is False
            and result.get("private_review_completed") is False
            and result.get("publication_authorized") is False
        )
        row={
            "submission_id":queue.get("submission_id"),
            "queue_hash":queue.get("queue_hash"),
            "returncode":completed.returncode,
            "admitted":admitted,
            "tvc_admission_hash":result.get("admission_hash") if isinstance(result,dict) else None,
            "tvc_interlock_receipt_hash":((result.get("tvc_interlock_receipt") or {}).get("receipt_hash") if isinstance(result,dict) else None),
            "next_required_transition":result.get("next_required_transition") if isinstance(result,dict) else None,
        }
        results.append(row)
        if not admitted: failures.append({"queue":str(queue_path),"reason":"tvc_admission_not_observed","returncode":completed.returncode})

    state="ADMITTED_TO_TVC_HIL_LIFECYCLE" if results and not failures and all(r["admitted"] for r in results) else "FAIL_CLOSED"
    receipt={
        "schema":"stegverse.hil.tvc-lifecycle-outbox-consumption/v1",
        "state":state,
        "runtime_root":str(runtime),
        "durable_state_root":str(durable),
        "tvc_source_floor":TVC_SOURCE_FLOOR,
        "tvc_source_validation_mode":tvc_source_validation_mode,
        "queue_count":len(queues),
        "results":results,
        "failures":failures,
        "credential_authority":CREDENTIAL_AUTHORITY,
        "credential_value_exposed":False,
        "github_token_runtime_authority":"NONE",
        "tvc_private_review_authority_owner":"StegVerse-Labs/TVC#8",
        "private_review_completed":False,
        "publication_authorized":False,
        "master_record_authorized":False,
        "second_user_device_required":False,
        "g18_completion_required":False,
        "authority_effect":"NONE_TRANSPORT_TRIGGER_ONLY",
    }
    path=runtime/CONSUMPTION_REL
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return receipt

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",type=Path)
    p.add_argument("--runtime-root",type=Path,required=True)
    args=p.parse_args()
    try: result=consume(args.runtime_root)
    except PredicatePending as exc:
        result={"schema":"stegverse.hil.tvc-lifecycle-outbox-consumption/v1","state":"PREDICATE_PENDING","reason":str(exc),"credential_authority":"TV/TVC","authority_effect":"NONE"}
        print(json.dumps(result,sort_keys=True)); return 0
    except Exception as exc:
        result={"schema":"stegverse.hil.tvc-lifecycle-outbox-consumption/v1","state":"FAIL_CLOSED","reason":f"{type(exc).__name__}:{exc}","credential_authority":"TV/TVC","authority_effect":"NONE"}
        print(json.dumps(result,sort_keys=True)); return 1
    print(json.dumps(result,sort_keys=True))
    return 0 if result["state"] in {"NO_EVENT","ADMITTED_TO_TVC_HIL_LIFECYCLE"} else 1

if __name__=="__main__": raise SystemExit(main())
