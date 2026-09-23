#!/usr/bin/env python3
import argparse,hashlib,json,os,fcntl
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/".stegverse/transition-ledger/org-contract.json").read_text())

def canon(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sha(v): return "sha256:"+hashlib.sha256(canon(v)).hexdigest()
def ledger_root():
    o=os.getenv("STEGVERSE_ORG_LEDGER_ROOT")
    if o: return Path(o).expanduser().resolve()
    return (Path(os.getenv("XDG_STATE_HOME",str(Path.home()/".local/state")))/"stegverse/org-ledgers"/C["organization"]).resolve()
def load(p): return json.loads(Path(p).read_text())

def verify_source(receipt):
    schema=receipt.get("schema")
    allowed=C.get("consumes")
    if isinstance(allowed,str): allowed=[allowed]
    if schema not in (allowed or []): raise ValueError("organization source receipt schema mismatch")
    if schema=="stegverse.repo-transition-receipt/v1":
        repository=str(receipt.get("repository",""))
        if not repository.startswith(C["organization"]+"/"): raise ValueError("repo outside organization")
        claimed=receipt.get("receipt_sha256"); body=dict(receipt); body.pop("receipt_sha256",None)
        if claimed!=sha(body): raise ValueError("repo receipt hash mismatch")
        return {
            "source_receipt_schema":schema,
            "source_transition_sha256":claimed,
            "source_transition_id":receipt["transition_id"],
            "source_repository":repository,
            "repo_receipt_sha256":claimed,
            "repo_transition_id":receipt["transition_id"],
            "canonical_state_transition_receipt_sha256":None,
            "subject_or_correlation_id":None,
        }
    digest=sha(receipt)
    return {
        "source_receipt_schema":schema,
        "source_transition_sha256":digest,
        "source_transition_id":receipt["transition_id"],
        "source_repository":None,
        "repo_receipt_sha256":None,
        "repo_transition_id":None,
        "canonical_state_transition_receipt_sha256":digest,
        "subject_or_correlation_id":receipt.get("subject_or_correlation_id"),
    }

def aggregate_transition(receipt, *, org_transition_class="ORGANIZATION_STATE_TRANSITION", predecessor_org_state_sha256=None, successor_org_state_sha256=None, boundary_evidence=None, authority_effect="NONE"):
    source=verify_source(receipt)
    root=ledger_root(); root.mkdir(parents=True,exist_ok=True)
    # Existing organization ledger is single-writer while HEAD is verified and advanced.
    with (root/".ledger.lock").open("a+") as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
        root=ledger_root(); d=root/"receipts"; d.mkdir(parents=True,exist_ok=True); h=root/"HEAD.json"
        prev=load(h).get("receipt_sha256") if h.exists() else None
        if prev is not None:
            if not isinstance(prev,str) or not prev.startswith("sha256:"):
                raise ValueError("organization_head_sha_invalid")
            predecessor_file=d/(prev.split(":",1)[1]+".json")
            if not predecessor_file.is_file(): raise ValueError("organization_immediate_predecessor_unavailable")
            predecessor_record=load(predecessor_file)
            predecessor_body=dict(predecessor_record); predecessor_claim=predecessor_body.pop("receipt_sha256",None)
            if predecessor_claim!=prev or sha(predecessor_body)!=prev:
                raise ValueError("organization_immediate_predecessor_reconstruction_failed")
        elif any(d.glob("*.json")):
            raise ValueError("organization_genesis_conflicts_existing_receipts")
        predecessor=predecessor_org_state_sha256 or prev
        successor=successor_org_state_sha256 or source["source_transition_sha256"]
        body={
            "schema":"stegverse.organization-transition-receipt/v1",
            "organization":C["organization"],
            **source,
            "org_transition_class":org_transition_class,
            "predecessor_org_state_sha256":predecessor,
            "successor_org_state_sha256":successor,
            "boundary_evidence":dict(boundary_evidence or {}),
            "authority_effect":authority_effect,
            "observed_at":datetime.now(timezone.utc).isoformat(),
            "previous_receipt_sha256":prev,
        }
        digest=sha(body); record={**body,"receipt_sha256":digest}; fp=d/(digest.split(":",1)[1]+".json")
        if fp.exists() and load(fp)!=record: raise ValueError("org receipt collision")
        if not fp.exists(): fp.write_text(json.dumps(record,indent=2,sort_keys=True)+"\n")
        h.write_text(json.dumps({"organization":C["organization"],"receipt_sha256":digest,"receipt_path":str(fp)},indent=2,sort_keys=True)+"\n")
        return record

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo-receipt")
    p.add_argument("--transition-receipt")
    p.add_argument("--org-transition-class",default=None)
    p.add_argument("--predecessor-org-state-sha256")
    p.add_argument("--successor-org-state-sha256")
    p.add_argument("--boundary-evidence-json",default="{}")
    p.add_argument("--authority-effect",default="NONE")
    a=p.parse_args()
    source_path=a.transition_receipt or a.repo_receipt
    if not source_path: raise SystemExit("transition receipt required")
    receipt=load(source_path)
    default_class="REPO_STATE_PROPAGATION" if receipt.get("schema")=="stegverse.repo-transition-receipt/v1" else "ORGANIZATION_STATE_TRANSITION"
    try:
        record=aggregate_transition(
            receipt,
            org_transition_class=a.org_transition_class or default_class,
            predecessor_org_state_sha256=a.predecessor_org_state_sha256,
            successor_org_state_sha256=a.successor_org_state_sha256,
            boundary_evidence=json.loads(a.boundary_evidence_json),
            authority_effect=a.authority_effect,
        )
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(json.dumps(record,sort_keys=True))

if __name__=="__main__": main()
