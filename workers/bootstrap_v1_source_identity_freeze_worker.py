#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Mapping

TASK_ID="BOOTSTRAP-V1-SOURCE-IDENTITY-FREEZE-001"
WORKER_ID="bootstrap-v1-source-identity-freeze-worker"
SOURCE_PREP_ENV="STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT"
BOUND_ENV="STEGVERSE_BOUND_STATE_ROOT"
DEFAULT_SOURCE_PREP=Path.home()/".stegverse"/"state"/"sv-dn1-production-source-prep"
DEFAULT_BOUND=Path.home()/".stegverse"/"state"/"bootstrap-v1-source-identity-freeze"
COMPONENTS=("stegverse.sdk","stegverse.stegcore","stegverse.core-lite","stegverse.master-records")
HOSTED=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN=("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN","HF_TOKEN","HUGGINGFACE_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","OAUTH_TOKEN")

class UpstreamPending(RuntimeError): pass
class FrozenIdentityConflict(RuntimeError): pass

def truthy(v:str|None)->bool:
    return str(v or "").strip().lower() not in {"","0","false","no"}

def canonical_bytes(v:Any)->bytes:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")

def sha256(v:Any)->str:
    return hashlib.sha256(canonical_bytes(v)).hexdigest()

def load(path:Path, pending:bool=False)->dict[str,Any]:
    if not path.is_file():
        if pending: raise UpstreamPending(f"required upstream receipt not present: {path}")
        raise RuntimeError(f"required JSON not present: {path}")
    v=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise RuntimeError(f"expected JSON object: {path}")
    return v

def atomic_json(path:Path,v:Mapping[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix="."+path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as h:
            json.dump(dict(v),h,indent=2,sort_keys=True); h.write("\n")
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def source_prep_root()->Path:
    return Path(os.environ.get(SOURCE_PREP_ENV,str(DEFAULT_SOURCE_PREP))).expanduser().resolve()

def bound_root()->Path:
    return Path(os.environ.get(BOUND_ENV,str(DEFAULT_BOUND))).expanduser().resolve()

def validate_upstream(receipt:Mapping[str,Any])->dict[str,str]:
    if receipt.get("schema")!="stegverse.sv-dn1.production-source-prep-receipt/v2":
        raise UpstreamPending("source-prep v2 receipt is required")
    if receipt.get("state")!="COMPLETE" or receipt.get("transition_id")!="SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE":
        raise UpstreamPending("source-prep has not completed")
    if receipt.get("source_identity_scheme")!="sha256-content-manifest":
        raise RuntimeError("source identity scheme drift")
    if receipt.get("network_source_fetch_performed") is not False or receipt.get("github_platform_required") is not False:
        raise RuntimeError("source-prep receipt retains platform/network dependency")
    if receipt.get("credential_used") is not False or receipt.get("github_token_used") is not False or receipt.get("repository_writeback_performed") is not False:
        raise RuntimeError("source-prep authority/credential invariant violated")
    ids=receipt.get("source_identities")
    roots=receipt.get("source_roots")
    if not isinstance(ids,dict) or set(ids)!=set(COMPONENTS):
        raise RuntimeError("source identity component set mismatch")
    if not isinstance(roots,dict) or set(roots)!=set(COMPONENTS):
        raise RuntimeError("source root component set mismatch")
    out={}
    for c in COMPONENTS:
        ident=ids[c]
        if not isinstance(ident,str) or len(ident)!=71 or not ident.startswith("sha256:"):
            raise RuntimeError(f"invalid source identity: {c}")
        try: int(ident[7:],16)
        except ValueError as exc: raise RuntimeError(f"invalid source identity hex: {c}") from exc
        if not isinstance(roots[c],str) or not roots[c]:
            raise RuntimeError(f"missing local source root: {c}")
        out[c]=ident
    return out

def build_catalog(receipt:Mapping[str,Any],ids:Mapping[str,str])->dict[str,Any]:
    upstream_digest=sha256(receipt)
    entries=[{"component_id":c,"source_identity":ids[c]} for c in COMPONENTS]
    identity_digest=sha256(entries)
    return {
        "schema":"stegverse.bootstrap.source-catalog/v1",
        "catalog_version":"1.0.0",
        "state":"FROZEN",
        "source_identity_scheme":"sha256-content-manifest",
        "component_count":len(entries),
        "components":entries,
        "source_identity_set_sha256":identity_digest,
        "upstream_source_prep_receipt_sha256":upstream_digest,
        "source_package_contract":{"schema":"stegverse.source-package/v1","version":"1.0.0"},
        "github_platform_required":False,
        "specific_external_platform_required":False,
        "network_locator_required":False,
        "package_integrity_confers_execution_authority":False,
        "execution_authority":"NONE",
        "authority_effect":"NONE_IDENTITY_FREEZE_ONLY",
    }

def execute(invocation:Mapping[str,Any])->dict[str,Any]:
    if any(truthy(os.getenv(x)) for x in HOSTED):
        raise RuntimeError("hosted environment cannot freeze sovereign Bootstrap v1 source identities")
    present=[x for x in FORBIDDEN if truthy(os.getenv(x))]
    if present: raise RuntimeError("credential-bearing environment forbidden: "+",".join(sorted(present)))
    if invocation.get("schema")!="stegverse.worker-invocation/v0.1": raise RuntimeError("worker invocation schema mismatch")
    task=invocation.get("task") or {}
    if task.get("task_id")!=TASK_ID or task.get("worker_id")!=WORKER_ID: raise RuntimeError("task/worker identity mismatch")
    if not task.get("claim_id"): raise RuntimeError("canonical task claim required")
    upstream=load(source_prep_root()/"receipts"/"latest.json",pending=True)
    ids=validate_upstream(upstream)
    catalog=build_catalog(upstream,ids)
    bound=bound_root()
    catalog_path=bound/"catalog"/"bootstrap-v1-source-catalog.json"
    if catalog_path.is_file():
        existing=load(catalog_path)
        if existing!=catalog: raise FrozenIdentityConflict("FROZEN_SOURCE_IDENTITY_CONFLICT")
    else:
        atomic_json(catalog_path,catalog)
    receipt={
        "schema":"stegverse.bootstrap.source-identity-freeze-receipt/v1",
        "task_id":TASK_ID,"worker_id":WORKER_ID,"state":"COMPLETE",
        "transition_id":"BOOTSTRAP_V1_SOURCE_IDENTITIES_FROZEN",
        "claim_id":task.get("claim_id"),
        "fencing_token":(task.get("heartbeat_timing") or {}).get("fencing_token"),
        "catalog_path":str(catalog_path),
        "catalog_sha256":sha256(catalog),
        "source_identity_set_sha256":catalog["source_identity_set_sha256"],
        "upstream_source_prep_receipt_sha256":catalog["upstream_source_prep_receipt_sha256"],
        "component_count":4,
        "source_identity_scheme":"sha256-content-manifest",
        "github_platform_required":False,
        "network_access_performed":False,
        "credential_used":False,
        "github_token_used":False,
        "repository_writeback_performed":False,
        "execution_authority":"NONE",
        "authority_effect":"NONE_IDENTITY_FREEZE_ONLY",
    }
    atomic_json(bound/"receipts"/"latest.json",receipt)
    return receipt

def response(receipt:Mapping[str,Any])->dict[str,Any]:
    return {"schema":"stegverse.worker-response/v0.1","state":"COMPLETED",
            "transition_id":"BOOTSTRAP_V1_SOURCE_IDENTITIES_FROZEN","transition_sequence":1,
            "expected_next_transition":"BOOTSTRAP_V1_RELEASE_CANDIDATE_FROZEN",
            "checkpoint_ref":"receipts/latest.json",
            "evidence_refs":["catalog/bootstrap-v1-source-catalog.json","receipts/latest.json"],
            "catalog_sha256":receipt["catalog_sha256"],"github_platform_required":False,
            "authority_effect":"NONE_IDENTITY_FREEZE_ONLY"}

def main()->int:
    try:
        raw=sys.stdin.readline(); invocation=json.loads(raw)
        receipt=execute(invocation); print(json.dumps(response(receipt),sort_keys=True)); return 0
    except UpstreamPending as exc:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"HANDOFF_READY",
                          "transition_id":"BOOTSTRAP_V1_SOURCE_PREP_RECEIPT_PENDING",
                          "transition_sequence":1,"expected_next_transition":"BOOTSTRAP_V1_SOURCE_IDENTITIES_FROZEN",
                          "error":str(exc),"github_platform_required":False,
                          "blocker":{"dependency_class":"SOURCE_PREP_RECEIPT","problem_statement":str(exc),
                                     "solution_required":True,"may_remain_blocked":False,
                                     "next_solution_action":"Wait for the machine-owned platform-independent source-prep v2 receipt; do not obtain source from a platform-specific fallback.",
                                     "machine_observable_release_condition":"completed source-prep v2 receipt contains exactly four sha256-content-manifest source identities",
                                     "physical_additional_machine_required":False,"third_party_runtime_required":False,
                                     "github_platform_required":False,"human_action_required":False}},sort_keys=True)); return 0
    except FrozenIdentityConflict as exc:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED",
                          "transition_id":"BOOTSTRAP_V1_FROZEN_SOURCE_IDENTITY_CONFLICT",
                          "transition_sequence":1,"error":str(exc),"github_platform_required":False,
                          "authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED",
                          "transition_id":"BOOTSTRAP_V1_SOURCE_IDENTITY_FREEZE_BLOCKED",
                          "transition_sequence":1,"error":str(exc),"github_platform_required":False,
                          "authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
