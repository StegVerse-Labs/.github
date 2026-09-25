#!/usr/bin/env python3
import argparse,base64,hashlib,json,os,tempfile
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

def verify_required_evidence(receipt):
    """Require exact inline canonical evidence bytes for organization-local replay."""
    manifest=receipt.get("required_evidence_manifest")
    if not isinstance(manifest,list): raise ValueError("canonical required evidence manifest missing")
    seen=set()
    for item in manifest:
        if not isinstance(item,dict): raise ValueError("canonical evidence entry invalid")
        for key in ("evidence_id","evidence_type","origin_transition_id","encoding","sha256","content"):
            if key not in item: raise ValueError("canonical evidence field missing: "+key)
        identity=item["evidence_id"]
        if not isinstance(identity,str) or not identity or identity in seen:
            raise ValueError("canonical evidence identity invalid")
        seen.add(identity)
        if not isinstance(item["evidence_type"],str) or not item["evidence_type"] or item["origin_transition_id"]!=receipt.get("transition_id"):
            raise ValueError("canonical evidence transition binding invalid")
        encoding=item["encoding"]
        content=item["content"]
        if encoding=="canonical-json": raw=canon(content)
        elif encoding=="utf-8" and isinstance(content,str): raw=content.encode("utf-8")
        elif encoding=="base64" and isinstance(content,str):
            try: raw=base64.b64decode(content.encode("ascii"),validate=True)
            except (ValueError,UnicodeError) as exc: raise ValueError("canonical evidence base64 invalid") from exc
        else: raise ValueError("canonical evidence encoding invalid")
        digest=item["sha256"]
        if not isinstance(digest,str) or len(digest)!=64 or hashlib.sha256(raw).hexdigest()!=digest:
            raise ValueError("canonical required evidence digest mismatch")


def retain_source(root, receipt, verified):
    """Keep immutable exact source bytes under the existing private org ledger root."""
    digest=verified["source_transition_sha256"]
    if not isinstance(digest,str) or len(digest)!=71 or not digest.startswith("sha256:"):
        raise ValueError("organization source hash invalid")
    directory=root/"source-receipts"
    directory.mkdir(mode=0o700,parents=True,exist_ok=True)
    path=directory/(digest[7:]+".json")
    if path.exists():
        stored=load(path)
        if stored!=receipt or verify_source(stored)["source_transition_sha256"]!=digest:
            raise ValueError("retained organization source receipt conflict")
        return path
    fd,name=tempfile.mkstemp(prefix=".source-",dir=str(directory))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as stream:
            stream.write(json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+"\\n")
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            stored=load(path)
            if stored!=receipt: raise ValueError("retained organization source receipt conflict")
        else: os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)
    return path


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
    verify_required_evidence(receipt)
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

def _existing_exact_source(d, source, *, org_transition_class, predecessor_org_state_sha256, successor_org_state_sha256, boundary_evidence, authority_effect):
    """Reuse an immutable organization receipt for an exact already-recorded transition.

    The existing receipt directory is the only index; no new store or authority
    is introduced. A retry after an incomplete Master Records submission must
    not append a second organization transition for the same exact source.
    """
    for path in sorted(d.glob("*.json")):
        row=load(path)
        if row.get("source_transition_sha256") != source["source_transition_sha256"]:
            continue
        if row.get("source_receipt_schema") != source["source_receipt_schema"]:
            raise ValueError("organization source digest/schema collision")
        body=dict(row)
        claimed=body.pop("receipt_sha256",None)
        if claimed != sha(body) or path.stem != claimed.split(":",1)[-1]:
            raise ValueError("existing organization receipt integrity invalid")
        if (
            row.get("source_transition_id") != source["source_transition_id"]
            or row.get("org_transition_class") != org_transition_class
            or row.get("authority_effect") != authority_effect
            or row.get("boundary_evidence") != dict(boundary_evidence or {})
            or (predecessor_org_state_sha256 is not None and row.get("predecessor_org_state_sha256") != predecessor_org_state_sha256)
            or (successor_org_state_sha256 is not None and row.get("successor_org_state_sha256") != successor_org_state_sha256)
        ):
            raise ValueError("existing organization source transition context conflict")
        return row
    return None

def aggregate_transition(receipt, *, org_transition_class="ORGANIZATION_STATE_TRANSITION", predecessor_org_state_sha256=None, successor_org_state_sha256=None, boundary_evidence=None, authority_effect="NONE"):
    source=verify_source(receipt)
    root=ledger_root(); d=root/"receipts"; d.mkdir(parents=True,exist_ok=True); h=root/"HEAD.json"
    existing=_existing_exact_source(
        d,source,org_transition_class=org_transition_class,
        predecessor_org_state_sha256=predecessor_org_state_sha256,
        successor_org_state_sha256=successor_org_state_sha256,
        boundary_evidence=boundary_evidence,authority_effect=authority_effect,
    )
    if existing is not None:
        retain_source(root,receipt,source)
        return existing
    retain_source(root,receipt,source)
    prev=load(h).get("receipt_sha256") if h.exists() else None
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
