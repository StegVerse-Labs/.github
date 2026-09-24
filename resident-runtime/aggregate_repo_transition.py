#!/usr/bin/env python3
import argparse,hashlib,json,os,fcntl,tempfile
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


def _atomic_json(path, value):
    """Write once by content address, or atomically advance existing HEAD."""
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(value,indent=2,sort_keys=True)+"\n"
    if path.exists() and path.name!="HEAD.json":
        if load(path)!=value: raise ValueError("organization_write_once_collision")
        return
    with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",dir=path.parent,
                                     prefix=".org-ledger-",delete=False) as handle:
        temp=Path(handle.name)
        try:
            handle.write(raw);handle.flush();os.fsync(handle.fileno())
        except Exception:
            temp.unlink(missing_ok=True)
            raise
    try:
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)

def _audit_chain_unlocked(root=None):
    """Read-only, whole-chain org receipt audit. No transition or repair inferred."""
    root=Path(root) if root is not None else ledger_root()
    d=root/"receipts"; h=root/"HEAD.json"
    paths=list(d.glob("*.json")) if d.exists() else []
    result={"schema":"stegverse.organization-transition-ledger-audit/v1",
            "organization":C["organization"],"state":"EMPTY_NOT_OBSERVED",
            "head_receipt_sha256":None,"reconstructed_receipt_count":0,
            "failure_transitions":[],"partial_transitions":[],"unknown_source_receipts":[],
            "orphan_receipts":[],"orphan_source_receipts":[],"recovered_legacy_source_receipts":[],"integrity_errors":[],"authority_effect":"NONE_READ_ONLY"}
    if not h.is_file():
        if paths:
            result["state"]="INTEGRITY_FAILURE"
            result["integrity_errors"].append("HEAD_MISSING_WITH_RETAINED_RECEIPTS")
        sources=root/"sources"
        if sources.exists():
            result["orphan_source_receipts"]=sorted(p.name for p in sources.glob("*.json"))
            if result["orphan_source_receipts"]:
                result["state"]="INTEGRITY_FAILURE"
                result["integrity_errors"].append("ORPHAN_SOURCE_RECEIPTS_PENDING_RECONCILIATION")
        return result
    referenced_sources=set()
    try:
        head=load(h); current=head.get("receipt_sha256")
        result["head_receipt_sha256"]=current
        if head.get("organization")!=C["organization"]:
            result["integrity_errors"].append("HEAD_ORGANIZATION_MISMATCH")
        seen=set()
        while current is not None:
            if not isinstance(current,str) or not current.startswith("sha256:") or len(current)!=71:
                result["integrity_errors"].append("INVALID_PREDECESSOR_REFERENCE");break
            if current in seen:
                result["integrity_errors"].append("CYCLE_IN_PREDECESSOR_CHAIN");break
            seen.add(current)
            path=d/(current.split(":",1)[1]+".json")
            if not path.is_file():
                result["integrity_errors"].append("MISSING_ORGANIZATION_RECEIPT:"+current);break
            row=load(path); body=dict(row); claimed=body.pop("receipt_sha256",None)
            if claimed!=current or sha(body)!=current:
                result["integrity_errors"].append("RECEIPT_HASH_MISMATCH:"+current);break
            if row.get("organization")!=C["organization"]:
                result["integrity_errors"].append("RECEIPT_ORGANIZATION_MISMATCH:"+current);break
            retained=row.get("source_receipt_ref")
            if retained is None:
                legacy=Path("sources")/(row["source_transition_sha256"].split(":",1)[1]+".json")
                if (root/legacy).is_file():
                    retained=legacy.as_posix()
                    result["recovered_legacy_source_receipts"].append(current)
            if retained:
                referenced_sources.add(Path(retained).name)
                source_file=root/retained
                if not source_file.is_file():
                    result["integrity_errors"].append("SOURCE_RECEIPT_MISSING:"+current)
                else:
                    source=load(source_file)
                    try:
                        observed_source=verify_source(source)
                    except (ValueError,KeyError,TypeError):
                        observed_source={}
                    if observed_source.get("source_transition_sha256")!=row.get("source_transition_sha256"):
                        result["integrity_errors"].append("SOURCE_RECEIPT_DIGEST_MISMATCH:"+current)
                    elif source.get("schema")!=row.get("source_receipt_schema"):
                        result["integrity_errors"].append("SOURCE_RECEIPT_SCHEMA_MISMATCH:"+current)
                    elif source.get("transition_id")!=row.get("source_transition_id"):
                        result["integrity_errors"].append("SOURCE_RECEIPT_TRANSITION_MISMATCH:"+current)
                    elif source.get("transition_outcome") in ("FAILED","FAIL_CLOSED","DENY"):
                        result["failure_transitions"].append({"org_receipt_sha256":current,
                            "source_transition_id":source.get("transition_id"),
                            "outcome":source["transition_outcome"],
                            "reason":(source.get("transition_evidence") or {}).get("reason")})
                    elif source.get("transition_outcome")=="PARTIAL":
                        result["partial_transitions"].append({"org_receipt_sha256":current,
                            "source_transition_id":source.get("transition_id")})
            else:
                result["unknown_source_receipts"].append(current)
            result["reconstructed_receipt_count"]+=1
            current=row.get("previous_receipt_sha256")
        result["orphan_receipts"]=sorted(p.stem for p in paths if "sha256:"+p.stem not in seen)
        sources=root/"sources"
        result["orphan_source_receipts"]=sorted(p.name for p in sources.glob("*.json") if p.name not in referenced_sources) if sources.exists() else []
        if result["orphan_source_receipts"]:
            result["integrity_errors"].append("ORPHAN_SOURCE_RECEIPTS_PENDING_RECONCILIATION")
        if result["orphan_receipts"]:
            result["integrity_errors"].append("ORPHAN_ORGANIZATION_RECEIPTS")
        result["state"]="INTEGRITY_FAILURE" if result["integrity_errors"] else (
            "RECONSTRUCTED_WITH_FAILURE_TRANSITIONS" if result["failure_transitions"] else
            "RECONSTRUCTED_WITH_LEGACY_SOURCE_GAPS" if result["unknown_source_receipts"] else
            "RECONSTRUCTED_WITH_PARTIAL_TRANSITIONS" if result["partial_transitions"] else
            "RECONSTRUCTED_PASS")
    except (ValueError,KeyError,OSError,TypeError) as exc:
        result["state"]="INTEGRITY_FAILURE"
        result["integrity_errors"].append("AUDIT_READ_ERROR:"+type(exc).__name__)
    return result

def audit_chain(root=None, *, _caller_holds_lock=False):
    """Read-only snapshot; share the existing writer lock when called externally."""
    root=Path(root) if root is not None else ledger_root()
    if _caller_holds_lock:
        return _audit_chain_unlocked(root)
    lock_path=root/".ledger.lock"
    if not lock_path.is_file():
        return _audit_chain_unlocked(root)
    with lock_path.open("r") as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_SH)
        return _audit_chain_unlocked(root)


def _recover_interrupted_append(root, receipt, source, prev, integrity, *,
                                org_transition_class, predecessor_org_state_sha256,
                                successor_org_state_sha256, boundary_evidence,
                                authority_effect, expected_previous_receipt_sha256,
                                enforce_expected_previous):
    """Recover only an exactly reconstructed interrupted write under ledger lock.

    A source-only orphan is preappend evidence, not a state transition. A fully
    retained exact successor may advance HEAD only after all bindings and its
    existing predecessor independently reconstruct. No new receipt is minted
    for an interrupted append.
    """
    digest=source["source_transition_sha256"]
    source_name=digest.split(":",1)[1]+".json"
    source_file=root/"sources"/source_name
    orphan_sources=integrity.get("orphan_source_receipts") or []
    errors=set(integrity.get("integrity_errors") or [])
    if source_file.is_file() and load(source_file)!=receipt:
        raise ValueError("organization_interrupted_source_mismatch")
    if enforce_expected_previous and prev!=expected_previous_receipt_sha256:
        raise ValueError("organization_expected_immediate_predecessor_mismatch")
    if (errors=={"ORPHAN_SOURCE_RECEIPTS_PENDING_RECONCILIATION"}
        and orphan_sources==[source_name] and source_file.is_file()
        and not integrity.get("orphan_receipts")):
        return "EXACT_SOURCE_ONLY"
    # An interrupted HEAD update may strand one already-written organization
    # receipt. Recover precisely that receipt; never make a new successor.
    d=root/"receipts"
    candidates=list(d.glob("*.json")) if d.is_dir() else []
    if integrity.get("head_receipt_sha256") is None and len(candidates)!=1:
        return None
    if integrity.get("head_receipt_sha256") is not None:
        candidates=[d/(stem+".json") for stem in integrity.get("orphan_receipts",[])]
    if len(candidates)!=1 or not candidates[0].is_file():
        return None
    candidate=load(candidates[0])
    body=dict(candidate); claimed=body.pop("receipt_sha256",None)
    if claimed!=sha(body) or candidates[0].stem!=claimed.split(":",1)[-1]:
        return None
    expected_predecessor=predecessor_org_state_sha256 or prev
    expected_successor=successor_org_state_sha256 or digest
    if (candidate.get("schema")!="stegverse.organization-transition-receipt/v1"
        or candidate.get("organization")!=C["organization"]
        or candidate.get("previous_receipt_sha256")!=prev
        or candidate.get("source_transition_sha256")!=digest
        or candidate.get("source_transition_id")!=source["source_transition_id"]
        or candidate.get("source_receipt_schema")!=source["source_receipt_schema"]
        or candidate.get("source_receipt_ref")!=("sources/"+source_name)
        or candidate.get("predecessor_org_state_sha256")!=expected_predecessor
        or candidate.get("successor_org_state_sha256")!=expected_successor
        or candidate.get("org_transition_class")!=org_transition_class
        or candidate.get("boundary_evidence")!=dict(boundary_evidence or {})
        or candidate.get("authority_effect")!=authority_effect):
        return None
    allowed={"ORPHAN_ORGANIZATION_RECEIPTS","ORPHAN_SOURCE_RECEIPTS_PENDING_RECONCILIATION",
             "HEAD_MISSING_WITH_RETAINED_RECEIPTS"}
    if not errors.issubset(allowed) or "ORPHAN_ORGANIZATION_RECEIPTS" not in errors and prev is not None:
        return None
    if orphan_sources and orphan_sources!=[source_name]:
        return None
    if not source_file.is_file():
        # The exact caller-carried source still has to match the org receipt
        # digest. Retain it before recovering the already-written org receipt.
        if verify_source(receipt)["source_transition_sha256"]!=digest:
            return None
        _atomic_json(source_file,receipt)
    _atomic_json(root/"HEAD.json",{"organization":C["organization"],
                                   "receipt_sha256":claimed,
                                   "receipt_path":str(candidates[0])})
    return candidate


def aggregate_transition(receipt, *, org_transition_class="ORGANIZATION_STATE_TRANSITION", predecessor_org_state_sha256=None, successor_org_state_sha256=None, boundary_evidence=None, authority_effect="NONE", expected_previous_receipt_sha256=None, enforce_expected_previous=False):
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
        integrity=audit_chain(root,_caller_holds_lock=True)
        if integrity["state"]=="INTEGRITY_FAILURE":
            recovered=_recover_interrupted_append(
                root,receipt,source,prev,integrity,
                org_transition_class=org_transition_class,
                predecessor_org_state_sha256=predecessor_org_state_sha256,
                successor_org_state_sha256=successor_org_state_sha256,
                boundary_evidence=boundary_evidence,authority_effect=authority_effect,
                expected_previous_receipt_sha256=expected_previous_receipt_sha256,
                enforce_expected_previous=enforce_expected_previous)
            if isinstance(recovered,dict):
                return recovered
            if recovered!="EXACT_SOURCE_ONLY":
                raise ValueError("organization_existing_chain_integrity_failure:"+
                                 ",".join(integrity["integrity_errors"]))
        # Source receipt and hash-linked org receipt stay in the SAME existing
        # organization ledger; no secondary ledger or synthesized transition.
        retained_ref=Path("sources")/(source["source_transition_sha256"].split(":",1)[1]+".json")
        retained=root/retained_ref
        if retained.exists() and load(retained)!=receipt:
            raise ValueError("organization_source_receipt_collision")
        # An identical source transition may be retried after Master Records
        # custody failed. Preserve its original org receipt and predecessor.
        for prior_path in d.glob("*.json"):
            prior_row=load(prior_path)
            if prior_row.get("source_transition_sha256")!=source["source_transition_sha256"]:
                continue
            if (prior_row.get("source_receipt_schema")!=source["source_receipt_schema"]
                or prior_row.get("source_transition_id")!=source["source_transition_id"]
                or (predecessor_org_state_sha256 is not None and prior_row.get("predecessor_org_state_sha256")!=predecessor_org_state_sha256)
                or (successor_org_state_sha256 is not None and prior_row.get("successor_org_state_sha256")!=successor_org_state_sha256)
                or prior_row.get("org_transition_class")!=org_transition_class
                or prior_row.get("boundary_evidence")!=dict(boundary_evidence or {})
                or prior_row.get("authority_effect")!=authority_effect):
                raise ValueError("organization_duplicate_source_binding_mismatch")
            prior_body=dict(prior_row)
            prior_claim=prior_body.pop("receipt_sha256",None)
            if prior_claim!=sha(prior_body):
                raise ValueError("organization_duplicate_receipt_reconstruction_failed")
            if enforce_expected_previous and prior_row.get("previous_receipt_sha256")!=expected_previous_receipt_sha256:
                raise ValueError("organization_duplicate_predecessor_mismatch")
            if retained.exists() and load(retained)!=receipt:
                raise ValueError("organization_source_receipt_collision")
            _atomic_json(retained,receipt)
            return prior_row
        if enforce_expected_previous and prev!=expected_previous_receipt_sha256:
            raise ValueError("organization_expected_immediate_predecessor_mismatch")
        predecessor=predecessor_org_state_sha256 or prev
        successor=successor_org_state_sha256 or source["source_transition_sha256"]
        body={
            "schema":"stegverse.organization-transition-receipt/v1",
            "source_receipt_ref":retained_ref.as_posix(),
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
        _atomic_json(retained,receipt)
        _atomic_json(fp,record)
        _atomic_json(h,{"organization":C["organization"],"receipt_sha256":digest,"receipt_path":str(fp)})
        return record

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--audit",action="store_true")
    p.add_argument("--repo-receipt")
    p.add_argument("--transition-receipt")
    p.add_argument("--org-transition-class",default=None)
    p.add_argument("--predecessor-org-state-sha256")
    p.add_argument("--successor-org-state-sha256")
    p.add_argument("--boundary-evidence-json",default="{}")
    p.add_argument("--authority-effect",default="NONE")
    a=p.parse_args()
    if a.audit:
        report=audit_chain()
        print(json.dumps(report,sort_keys=True))
        if report["state"]=="INTEGRITY_FAILURE": raise SystemExit(2)
        return
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
