#!/usr/bin/env python3
import argparse,base64,hashlib,importlib.util,json,os,tempfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/".stegverse/transition-ledger/org-contract.json").read_text())
# The heartbeat is the ecosystem's time base and the kernel owns its derivation,
# loaded exactly as the repository ledger (.stegverse/transition-ledger/emit.py)
# loads it, so a repository receipt and the organization receipt consuming it
# cannot disagree about what an epoch is. `observed_at` stays as non-ordering
# provenance; ordering is the chain plus the heartbeat reference.
_kspec=importlib.util.spec_from_file_location("kernel",ROOT/"org-kernel/kernel.py")
kernel=importlib.util.module_from_spec(_kspec);_kspec.loader.exec_module(kernel)
# The ledger is addressed through the store seam, loaded exactly as the
# repository ledger (.stegverse/transition-ledger/emit.py) loads it.
_sspec=importlib.util.spec_from_file_location("ledger_store",ROOT/"resident-runtime/ledger_store.py")
ledger_store=importlib.util.module_from_spec(_sspec);_sspec.loader.exec_module(ledger_store)

def canon(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sha(v): return "sha256:"+hashlib.sha256(canon(v)).hexdigest()
class LedgerLocationRequired(ValueError):
    """No ledger root was supplied; nothing is appended and nothing is derived."""

    failed_predicate="LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER"

    def __init__(self, variable):
        super().__init__("ledger_location_required_from_materializer: "+variable)
        self.variable=variable

class LedgerStoreSelectionInvalid(LedgerLocationRequired):
    """The materializer named a ledger store this execution does not have."""

    failed_predicate="ORGANIZATION_LEDGER_STORE_SELECTION_INVALID"

def location_refusal(exc):
    """The append attempt's own disposition when no ledger root was supplied."""
    return {
        "schema":"stegverse.organization-ledger-append-refusal/v1",
        "organization":C["organization"],
        "disposition":"FAIL_CLOSED",
        "failed_predicate":exc.failed_predicate,
        "required_evidence_or_repair":"supply the organization ledger root as "+exc.variable,
        "retry_entrypoint":"resident-runtime/aggregate_repo_transition.py::aggregate_transition",
        "consequence_committed":False,
        "authority_effect":"NONE_REFUSAL_ONLY",
    }

def ledger_root():
    """The organization ledger root, as supplied to this execution.

    The ledger is the organization's runtime reality, so its location is
    supplied by whatever materialized this execution, exactly as the mesh is.
    It is never derived from the host: a home directory belongs to whichever
    machine happens to run this, and a chain written there is discarded with
    an ephemeral execution while appearing to have been appended.
    """
    o=os.getenv("STEGVERSE_ORG_LEDGER_ROOT")
    if o: return Path(o).expanduser().resolve()
    raise LedgerLocationRequired("STEGVERSE_ORG_LEDGER_ROOT")
def load(p): return json.loads(Path(p).read_text())

def _is_store(value): return value is not None and hasattr(value,"append_transaction")
def _is_posix(store): return getattr(store,"kind",None)=="POSIX_FILESYSTEM"

def organization_store(ledger=None):
    """The Organization ledger store, as supplied to this execution.

    A store or a root the caller holds is used as is. Otherwise the
    materializer selects the store: STEGVERSE_ORG_LEDGER_STORE=git with
    STEGVERSE_ORG_LEDGER_GIT_DIR, STEGVERSE_ORG_LEDGER_GIT_REF and optional
    STEGVERSE_ORG_LEDGER_GIT_REMOTE and STEGVERSE_ORG_LEDGER_GIT_CUSTODY names
    the durable Git ledger; absent, the POSIX root from ledger_root(), exactly
    as before. Nothing is derived from the host.
    """
    if _is_store(ledger): return ledger
    if ledger is not None: return ledger_store.PosixLedgerStore(Path(ledger).expanduser().resolve())
    selected=os.getenv("STEGVERSE_ORG_LEDGER_STORE") or "posix"
    if selected=="posix": return ledger_store.PosixLedgerStore(ledger_root())
    if selected!="git": raise LedgerStoreSelectionInvalid("STEGVERSE_ORG_LEDGER_STORE")
    for variable in ("STEGVERSE_ORG_LEDGER_GIT_DIR","STEGVERSE_ORG_LEDGER_GIT_REF"):
        if not os.getenv(variable): raise LedgerLocationRequired(variable)
    return ledger_store.GitLedgerStore(
        os.environ["STEGVERSE_ORG_LEDGER_GIT_DIR"],os.environ["STEGVERSE_ORG_LEDGER_GIT_REF"],
        remote=os.getenv("STEGVERSE_ORG_LEDGER_GIT_REMOTE") or None,
        custody=os.getenv("STEGVERSE_ORG_LEDGER_GIT_CUSTODY") or None,
    )

def store_refusal(exc):
    """The append attempt's own disposition when the store did not carry it."""
    return {**exc.refusal(),"organization":C["organization"]}

# Ledger custody transfer (F66-01). A root's custody passes to another
# materialization only by two Organization transitions on its own chain:
# RELEASED, appended at the predecessor, after which that root is read-only for
# writers, and ASSUMED, the first append permitted at the successor. Every
# receipt carries the custody_generation it was written in; a receipt without
# the field predates custody transfer and is generation 0, so existing chains
# verify unchanged and nothing is rewritten.
#
# The append lock serializes writers within one kernel only. A copy of the root
# taken before the release can still be written on another node, and source
# cannot prevent that without a shared serializer, which is not added. Such a
# copy is DETECTED wherever its receipts meet the release -- a superseded
# generation or a fork -- and refused FAIL_CLOSED; it is not prevented.
CUSTODY_RELEASED_CLASS="ORGANIZATION_LEDGER_CUSTODY_RELEASED"
CUSTODY_ASSUMED_CLASS="ORGANIZATION_LEDGER_CUSTODY_ASSUMED"
CUSTODY_CLASSES=(CUSTODY_RELEASED_CLASS,CUSTODY_ASSUMED_CLASS)
CUSTODY_KEY="organization_ledger_custody"
CUSTODY_TRANSFER_KEY="ledger_custody_transfer"
CUSTODY_EXCLUSIVITY="DETECTED_NOT_PREVENTED_ACROSS_KERNELS"
CUSTODY_RELEASE_RETRY="resident-runtime/aggregate_repo_transition.py::release_custody"
CUSTODY_ASSUME_RETRY="resident-runtime/aggregate_repo_transition.py::assume_custody"
CUSTODY_VERIFY_RETRY="resident-runtime/aggregate_repo_transition.py::verify_custody_lineage"
CUSTODY_APPEND_RETRY="resident-runtime/aggregate_repo_transition.py::aggregate_transition"
# A generation-0 receipt is written by a materialization nothing authenticates:
# it predates any custody transition, and the location check is only anomaly
# detection. Recorded on every generation-0 receipt so no reader takes a path
# match for custody authority.
CUSTODY_AUTHORITY_BASIS_GENERATION_0="PRE_EXISTING_MATERIALIZATION_UNAUTHENTICATED; LOCATION_CHECK_IS_ANOMALY_DETECTION_ONLY"

def custody_action_sha256(org_transition_class, subject):
    """The exact action a custody exclusivity attestation covers."""
    return sha({"org_transition_class":org_transition_class,"subject":subject})

class CustodyRefused(ValueError):
    """A custody predicate failed; nothing is appended. Always FAIL_CLOSED.

    The refusal is returned, not appended: a released root is read-only and a
    forked or superseded root is not one reality, so neither may take a receipt.
    """

    def __init__(self, failed_predicate, *, retry_entrypoint, detail="", repair=""):
        super().__init__(failed_predicate+(": "+detail if detail else ""))
        self.failed_predicate=failed_predicate
        self.retry_entrypoint=retry_entrypoint
        self.detail=detail
        self.repair=repair

    def refusal(self):
        return {
            "schema":"stegverse.organization-ledger-custody-refusal/v1",
            "organization":C["organization"],
            "disposition":"FAIL_CLOSED",
            "failed_predicate":self.failed_predicate,
            "detail":self.detail,
            "required_evidence_or_repair":self.repair,
            "retry_entrypoint":self.retry_entrypoint,
            "custody_exclusivity":CUSTODY_EXCLUSIVITY,
            "consequence_committed":False,
            "authority_effect":"NONE_REFUSAL_ONLY",
        }

def custody_generation(row):
    """The custody generation a receipt was written in; absent means 0."""
    value=row.get("custody_generation",0)
    if type(value) is not int or value<0:
        raise CustodyRefused("CUSTODY_GENERATION_INVALID",retry_entrypoint=CUSTODY_VERIFY_RETRY,
                             detail=str(row.get("receipt_sha256")))
    return value

def custody_record(row):
    """The custody evidence a RELEASED or ASSUMED receipt carries, else None."""
    if row.get("org_transition_class") not in CUSTODY_CLASSES: return None
    record=(row.get("boundary_evidence") or {}).get(CUSTODY_KEY)
    if not isinstance(record,dict):
        raise CustodyRefused("CUSTODY_GENERATION_CHAIN_INVALID",retry_entrypoint=CUSTODY_VERIFY_RETRY,
                             detail="custody evidence absent: "+str(row.get("receipt_sha256")))
    return record

def _custody_store(root):
    """The ledger store for a POSIX root or a store the caller holds."""
    return organization_store(root)

def _custody_rows(store):
    """Every self-verifying receipt in the store, by digest.

    A receipt that does not verify is left to the existing chain checks, which
    refuse it with their own reason.
    """
    rows={}
    prefix=ledger_store.RECEIPT_PREFIX
    for key in sorted(store.list_prefix(prefix)):
        try: row=store.get(key)
        except (OSError,ValueError): continue
        if not isinstance(row,dict): continue
        body=dict(row); claimed=body.pop("receipt_sha256",None)
        if not isinstance(claimed,str) or claimed!=sha(body) or key[len(prefix):-len(".json")]!=claimed[7:]: continue
        rows[claimed]=row
    return rows

def verify_custody_lineage(root, rows=None):
    """Refuse a root holding a superseded custody generation or a fork.

    Readback, the HEAD/chain walk, batch closure and every append run this. A
    RELEASED receipt closes its generation and an ASSUMED receipt closes every
    generation below its own; a receipt in a closed generation that is not an
    ancestor of the custody receipt that closed it was written by a superseded
    copy (CUSTODY_GENERATION_SUPERSEDED). Two receipts naming one predecessor
    are two writers of one root (ORGANIZATION_CUSTODY_FORK_DETECTED). Returns
    the rows scanned.
    """
    rows=_custody_rows(_custody_store(root)) if rows is None else rows
    repair=("a copy of this root was written after custody moved, or two copies were written; its receipts are "
            "not Organization reality. Restore the one authoritative materialization and retry.")
    closed=None
    for digest,row in rows.items():
        record=custody_record(row)
        if record is None: continue
        level=custody_generation(row) if row["org_transition_class"]==CUSTODY_RELEASED_CLASS else custody_generation(row)-1
        rank=1 if row["org_transition_class"]==CUSTODY_ASSUMED_CLASS else 0
        if closed is None or (level,rank)>closed[0]: closed=((level,rank),[digest])
        elif (level,rank)==closed[0]: closed[1].append(digest)
    if closed is not None:
        if len(closed[1])>1:
            raise CustodyRefused("ORGANIZATION_CUSTODY_FORK_DETECTED",retry_entrypoint=CUSTODY_VERIFY_RETRY,
                                 detail="custody transitions "+",".join(sorted(closed[1])),repair=repair)
        level=closed[0][0]; ancestors=set(); cursor=closed[1][0]
        while cursor in rows and cursor not in ancestors:
            ancestors.add(cursor); cursor=rows[cursor].get("previous_receipt_sha256")
        superseded=sorted(d for d,row in rows.items() if custody_generation(row)<=level and d not in ancestors)
        if superseded:
            raise CustodyRefused("CUSTODY_GENERATION_SUPERSEDED",retry_entrypoint=CUSTODY_VERIFY_RETRY,
                                 detail=",".join(superseded),repair=repair)
    children={}
    for digest,row in rows.items():
        parent=row.get("previous_receipt_sha256")
        if parent is not None: children.setdefault(parent,[]).append(digest)
    for parent,named in sorted(children.items()):
        if len(named)>1:
            raise CustodyRefused("ORGANIZATION_CUSTODY_FORK_DETECTED",retry_entrypoint=CUSTODY_VERIFY_RETRY,
                                 detail=parent+" <- "+",".join(sorted(named)),repair=repair)
    for digest,row in rows.items():
        parent=rows.get(row.get("previous_receipt_sha256"))
        generation=custody_generation(row)
        cls=row.get("org_transition_class")
        if parent is None:
            if row.get("previous_receipt_sha256") is None and generation!=0:
                raise CustodyRefused("CUSTODY_GENERATION_CHAIN_INVALID",retry_entrypoint=CUSTODY_VERIFY_RETRY,
                                     detail="genesis generation must be 0: "+digest)
            continue
        if parent.get("org_transition_class")==CUSTODY_RELEASED_CLASS:
            if cls!=CUSTODY_ASSUMED_CLASS:
                raise CustodyRefused("CUSTODY_RELEASED_ROOT_IS_READ_ONLY",retry_entrypoint=CUSTODY_VERIFY_RETRY,
                                     detail="receipt appended after release: "+digest,repair=repair)
            if generation!=custody_record(parent).get("next_custody_generation"):
                raise CustodyRefused("CUSTODY_GENERATION_CHAIN_INVALID",retry_entrypoint=CUSTODY_VERIFY_RETRY,detail=digest)
        elif cls==CUSTODY_ASSUMED_CLASS:
            raise CustodyRefused("CUSTODY_GENERATION_CHAIN_INVALID",retry_entrypoint=CUSTODY_VERIFY_RETRY,
                                 detail="assumption without release: "+digest)
        elif generation<custody_generation(parent):
            raise CustodyRefused("CUSTODY_GENERATION_SUPERSEDED",retry_entrypoint=CUSTODY_VERIFY_RETRY,detail=digest,repair=repair)
        elif generation!=custody_generation(parent):
            raise CustodyRefused("CUSTODY_GENERATION_CHAIN_INVALID",retry_entrypoint=CUSTODY_VERIFY_RETRY,detail=digest)
    return rows

def custody_transfer(parent_manifest):
    """The custody transfer the governing manifest declares."""
    transfer=parent_manifest.get(CUSTODY_TRANSFER_KEY) if isinstance(parent_manifest,dict) else None
    if not isinstance(transfer,dict):
        raise CustodyRefused("CUSTODY_TRANSFER_MANIFEST_DECLARATION_REQUIRED",retry_entrypoint=CUSTODY_RELEASE_RETRY,
                             repair="supply a governing manifest declaring "+CUSTODY_TRANSFER_KEY)
    successor=transfer.get("successor_materialization_id")
    head=transfer.get("predecessor_head_sha256")
    generation=transfer.get("next_custody_generation")
    if (not isinstance(successor,str) or not successor or not isinstance(head,str) or len(head)!=71
            or not head.startswith("sha256:") or type(generation) is not int or generation<1):
        raise CustodyRefused("CUSTODY_TRANSFER_MANIFEST_DECLARATION_INVALID",retry_entrypoint=CUSTODY_RELEASE_RETRY)
    return {"successor_materialization_id":successor,"predecessor_head_sha256":head,"next_custody_generation":generation}

def _custody_source(kind, record):
    """Deterministic source transition for a custody transition, so a retry is idempotent."""
    transition_id="ORG-LEDGER-CUSTODY-"+kind+":"+record["predecessor_head_sha256"]+":"+record["successor_materialization_id"]
    return {
        "schema":"stegverse.canonical-state-transition-receipt/v1",
        "transition_id":transition_id,
        "transition_sequence":1,
        "subject_or_correlation_id":record["successor_materialization_id"],
        "transition_outcome":"OBSERVED",
        "prior_state_ref_or_hash":record["predecessor_head_sha256"],
        "required_evidence_manifest":[{
            "evidence_id":"organization_ledger_custody",
            "evidence_type":"ORGANIZATION_LEDGER_CUSTODY_"+kind,
            "origin_transition_id":transition_id,
            "encoding":"canonical-json",
            "content":record,
            "sha256":hashlib.sha256(canon(record)).hexdigest(),
        }],
    }

def require_custody_exclusivity(rows, tip, org_transition_class, verifier, action_sha256):
    """Attestation of unique custody for a consequential write at a successor, else FAIL_CLOSED.

    Detection is not exclusivity. Once a root's custody has moved (its HEAD is
    in generation >= 1), any write other than the ASSUMED record itself needs
    an existing authority to attest that this successor materialization holds
    custody of this generation uniquely. That attestation is accepted only
    from the injected `verifier`; there is no default and no environment
    fallback, and this repository holds no such authority, so without one the
    successor makes no consequential write. A root never released
    (generation 0) is unaffected. custody_exclusivity records the limitation;
    it is never a passing predicate. `action_sha256` names the exact action
    (custody_action_sha256), or is a callable returning it, resolved only when
    an attestation is required.
    """
    if org_transition_class==CUSTODY_ASSUMED_CLASS or tip is None: return None
    tip_row=rows.get(tip)
    if tip_row is None or tip_row.get("org_transition_class")==CUSTODY_RELEASED_CLASS: return None
    generation=custody_generation(tip_row)
    if generation==0: return None
    assumed=[row for row in rows.values()
             if row.get("org_transition_class")==CUSTODY_ASSUMED_CLASS and custody_generation(row)==generation]
    if len(assumed)!=1:
        raise CustodyRefused("CUSTODY_GENERATION_CHAIN_INVALID",retry_entrypoint=CUSTODY_VERIFY_RETRY,
                             detail="generation "+str(generation)+" has no single assumption")
    successor=custody_record(assumed[0]).get("successor_materialization_id")
    repair=("inject custody_exclusivity_verifier from an existing authority that attests unique custody of "
            "this successor_materialization_id and custody_generation at this predecessor HEAD; none exists in this repository")
    detail=str(successor)+"@"+str(generation)+"@"+tip
    if verifier is None:
        raise CustodyRefused("CUSTODY_EXCLUSIVITY_UNAUTHENTICATED",retry_entrypoint=CUSTODY_APPEND_RETRY,
                             detail=detail,repair=repair)
    action=action_sha256() if callable(action_sha256) else action_sha256
    if action is None:
        raise CustodyRefused("CUSTODY_EXCLUSIVITY_UNAUTHENTICATED",retry_entrypoint=CUSTODY_APPEND_RETRY,
                             detail=detail,repair=repair)
    try: attestation=verifier(successor_materialization_id=successor,custody_generation=generation,
                              predecessor_head_sha256=tip,action_sha256=action)
    except Exception as exc:
        raise CustodyRefused("CUSTODY_EXCLUSIVITY_UNAUTHENTICATED",retry_entrypoint=CUSTODY_APPEND_RETRY,
                             detail=detail+": verifier unavailable: "+type(exc).__name__,repair=repair) from exc
    # The attestation binds this exact write: successor, generation, the HEAD
    # it extends and the action. One bound to another HEAD or action, or
    # already bound in a receipt, is a replay.
    if (not isinstance(attestation,dict) or attestation.get("unique_custody") is not True
            or attestation.get("successor_materialization_id")!=successor
            or attestation.get("custody_generation")!=generation
            or attestation.get("predecessor_head_sha256")!=tip
            or attestation.get("action_sha256")!=action):
        raise CustodyRefused("CUSTODY_EXCLUSIVITY_UNAUTHENTICATED",retry_entrypoint=CUSTODY_APPEND_RETRY,
                             detail=detail,repair=repair)
    if any(row.get("custody_exclusivity_attestation_sha256")==sha(attestation) for row in rows.values()):
        raise CustodyRefused("CUSTODY_EXCLUSIVITY_UNAUTHENTICATED",retry_entrypoint=CUSTODY_APPEND_RETRY,
                             detail=detail+": attestation replayed",repair=repair)
    return attestation

def require_no_relocation_anomaly(root, rows, tip, org_transition_class):
    """Refuse a consequential write where HEAD's recorded location is not the supplied one.

    Anomaly detection only, never custody authority: a matching location
    proves neither identity nor authority, and nothing here authenticates the
    materialization that writes (see CUSTODY_AUTHORITY_BASIS_GENERATION_0).
    HEAD.json records the locator of its tip. Reads and verification compare
    only the root-relative locator (#3057), so a root supplied elsewhere still
    reads back. A write where the recorded locator differs from the supplied
    one, with no RELEASED/ASSUMED handover having moved the root, is an
    ungoverned relocation or copy and is refused. The ASSUMED record is the
    one write a moved root may make, and it rewrites HEAD at its new location.
    On a POSIX root the locator is the absolute receipt path; on a Git ledger
    it is the ref locator. A byte copy at the identical location on another
    kernel passes this check; only fork detection
    (DETECTED_NOT_PREVENTED_ACROSS_KERNELS) covers it.
    """
    if org_transition_class==CUSTODY_ASSUMED_CLASS or tip is None: return
    tip_row=rows.get(tip)
    if tip_row is not None and tip_row.get("org_transition_class")==CUSTODY_RELEASED_CLASS: return
    store=_custody_store(root)
    recorded=(store.get(ledger_store.HEAD_KEY) or {}).get("receipt_path")
    here=store.locator(ledger_store.receipt_key(tip))
    if _is_posix(store):
        same=isinstance(recorded,str) and bool(recorded) and Path(recorded).resolve()==Path(here).resolve()
    else:
        same=recorded==here
    if not same:
        raise CustodyRefused("UNGOVERNED_RELOCATION_ANOMALY_DETECTED",retry_entrypoint=CUSTODY_RELEASE_RETRY,
                             detail="HEAD records "+str(recorded)+"; supplied ledger locates it at "+str(here),
                             repair="supply the root at the location its HEAD records, or move custody by release_custody "
                                    "there and assume_custody here")

def require_consequential_custody(root, rows, tip, org_transition_class, verifier, action_sha256):
    """Relocation anomaly check, then exclusivity: the attestation for a write, or FAIL_CLOSED."""
    require_no_relocation_anomaly(root,rows,tip,org_transition_class)
    return require_custody_exclusivity(rows,tip,org_transition_class,verifier,action_sha256)

def _read_tip(root):
    head=_custody_store(root).get(ledger_store.HEAD_KEY)
    return head.get("receipt_sha256") if head is not None else None

def _custody_gate(root, rows, tip, org_transition_class, boundary_evidence, verifier=None, action_sha256=None):
    """(custody generation of the next receipt, exclusivity attestation), or a FAIL_CLOSED refusal."""
    tip_row=rows.get(tip) if tip is not None else None
    if tip is not None and tip_row is None:
        raise CustodyRefused("ORGANIZATION_LEDGER_HEAD_UNVERIFIED",retry_entrypoint=CUSTODY_VERIFY_RETRY,detail=str(tip))
    record=(boundary_evidence or {}).get(CUSTODY_KEY)
    if org_transition_class==CUSTODY_ASSUMED_CLASS:
        if tip_row is None or tip_row.get("org_transition_class")!=CUSTODY_RELEASED_CLASS:
            pending=sorted(d for d,row in rows.items()
                           if row.get("org_transition_class")==CUSTODY_RELEASED_CLASS and row.get("previous_receipt_sha256")==tip)
            if pending:
                raise CustodyRefused("ORGANIZATION_LEDGER_CUSTODY_HANDOVER_INTERRUPTED",retry_entrypoint=CUSTODY_RELEASE_RETRY,
                                     detail="release "+pending[0]+" is not HEAD",
                                     repair="retry the release at the predecessor materialization to complete its HEAD, then supply that root here")
            raise CustodyRefused("ORGANIZATION_LEDGER_CUSTODY_RELEASE_MISSING",retry_entrypoint=CUSTODY_ASSUME_RETRY,
                                 detail="HEAD "+str(tip)+" is not a custody release",
                                 repair="supply the released predecessor root; assumption never starts a chain")
        release=custody_record(tip_row)
        if not isinstance(record,dict) or record.get("release_receipt_sha256")!=tip:
            raise CustodyRefused("ORGANIZATION_LEDGER_CUSTODY_RELEASE_MISSING",retry_entrypoint=CUSTODY_ASSUME_RETRY,detail=str(tip))
        if record.get("successor_materialization_id")!=release.get("successor_materialization_id"):
            raise CustodyRefused("CUSTODY_RELEASE_SUCCESSOR_MISMATCH",retry_entrypoint=CUSTODY_ASSUME_RETRY,
                                 detail=str(record.get("successor_materialization_id")))
        if not (record.get("predecessor_head_sha256")==release.get("predecessor_head_sha256")==tip_row.get("previous_receipt_sha256")):
            raise CustodyRefused("CUSTODY_RELEASE_PREDECESSOR_HEAD_MISMATCH",retry_entrypoint=CUSTODY_ASSUME_RETRY,
                                 detail=str(record.get("predecessor_head_sha256")))
        if not (record.get("custody_generation")==release.get("next_custody_generation")==custody_generation(tip_row)+1):
            raise CustodyRefused("CUSTODY_GENERATION_MISMATCH",retry_entrypoint=CUSTODY_ASSUME_RETRY,
                                 detail=str(record.get("custody_generation")))
        if record.get("governing_manifest_sha256")!=release.get("governing_manifest_sha256"):
            raise CustodyRefused("CUSTODY_TRANSFER_MANIFEST_MISMATCH",retry_entrypoint=CUSTODY_ASSUME_RETRY)
        return record["custody_generation"],None
    if tip_row is not None and tip_row.get("org_transition_class")==CUSTODY_RELEASED_CLASS:
        raise CustodyRefused("CUSTODY_RELEASED_ROOT_IS_READ_ONLY",retry_entrypoint=CUSTODY_ASSUME_RETRY,detail=tip,
                             repair="custody of this root was released; append at the successor after it assumes custody")
    pending=sorted(d for d,row in rows.items()
                   if row.get("org_transition_class")==CUSTODY_RELEASED_CLASS and row.get("previous_receipt_sha256")==tip)
    if pending:
        raise CustodyRefused("ORGANIZATION_LEDGER_CUSTODY_HANDOVER_INTERRUPTED",retry_entrypoint=CUSTODY_RELEASE_RETRY,
                             detail="release "+pending[0]+" is not HEAD",repair="retry the release to complete its HEAD")
    generation=custody_generation(tip_row) if tip_row is not None else 0
    if org_transition_class==CUSTODY_RELEASED_CLASS:
        if tip_row is None:
            raise CustodyRefused("CUSTODY_RELEASE_REQUIRES_EXISTING_HEAD",retry_entrypoint=CUSTODY_RELEASE_RETRY,
                                 repair="custody of an empty root cannot be released; a genesis is never fabricated")
        if not isinstance(record,dict) or record.get("predecessor_head_sha256")!=tip:
            raise CustodyRefused("CUSTODY_RELEASE_PREDECESSOR_HEAD_MISMATCH",retry_entrypoint=CUSTODY_RELEASE_RETRY,
                                 detail="HEAD is "+tip,repair="the manifest names a HEAD this root no longer holds")
        if record.get("custody_generation")!=generation or record.get("next_custody_generation")!=generation+1:
            raise CustodyRefused("CUSTODY_GENERATION_MISMATCH",retry_entrypoint=CUSTODY_RELEASE_RETRY,
                                 detail="current generation is "+str(generation))
    return generation,require_consequential_custody(root,rows,tip,org_transition_class,verifier,action_sha256)

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
            stream.write(json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
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

def _existing_exact_source(store, source, *, org_transition_class, predecessor_org_state_sha256, successor_org_state_sha256, boundary_evidence, authority_effect):
    """Reuse an immutable organization receipt for an exact already-recorded transition.

    The existing receipt directory is the only index; no new store or authority
    is introduced. A retry after an incomplete Master Records submission must
    not append a second organization transition for the same exact source.
    `hb_reference` and `observed_at` are deliberately not compared: a retry
    arrives at a later heartbeat, and that is not a different transition.
    """
    for key in sorted(store.list_prefix(ledger_store.RECEIPT_PREFIX)):
        row=store.get(key)
        if row.get("source_transition_sha256") != source["source_transition_sha256"]:
            continue
        if row.get("source_receipt_schema") != source["source_receipt_schema"]:
            raise ValueError("organization source digest/schema collision")
        body=dict(row)
        claimed=body.pop("receipt_sha256",None)
        if claimed != sha(body) or key[len(ledger_store.RECEIPT_PREFIX):-len(".json")] != claimed.split(":",1)[-1]:
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

def _packet_establishment_source(released_batch):
    """Deterministic source transition for a release-born packet establishment.

    The organization append owner performs this transition itself, so no
    external caller supplies its source receipt. It is derived from the exact
    released batch id, which makes an exact retry idempotent.
    """
    return {
        "schema": "stegverse.canonical-state-transition-receipt/v1",
        "transition_id": "ORG-RECEIPT-PACKET-ESTABLISHMENT:" + released_batch["batch_id"],
        "transition_sequence": 1,
        "subject_or_correlation_id": released_batch["batch_id"],
        "transition_outcome": "OBSERVED",
        "required_evidence_manifest": [
            {
                "evidence_id": "released_batch_commitment",
                "evidence_type": "ORGANIZATION_BATCH_COMMITMENT",
                "origin_transition_id": "ORG-RECEIPT-PACKET-ESTABLISHMENT:" + released_batch["batch_id"],
                "encoding": "canonical-json",
                "content": {
                    "batch_id": released_batch["batch_id"],
                    "last_org_receipt_sha256": released_batch["last_org_receipt_sha256"],
                    "closure_reason": released_batch["closure_reason"],
                },
                "sha256": hashlib.sha256(canon({
                    "batch_id": released_batch["batch_id"],
                    "last_org_receipt_sha256": released_batch["last_org_receipt_sha256"],
                    "closure_reason": released_batch["closure_reason"],
                })).hexdigest(),
            }
        ],
    }


def aggregate_transition(receipt, *, org_transition_class="ORGANIZATION_STATE_TRANSITION",
                         predecessor_org_state_sha256=None, successor_org_state_sha256=None,
                         boundary_evidence=None, authority_effect="NONE", parent_manifest=None,
                         establishes_packet=False, now_ns=None, ledger=None, hb_epoch=None,
                         custody_exclusivity_verifier=None):
    """Serialize appends; the governing parent manifest owns packet release.

    A manifested receipt packet's first receipt records its own establishment.
    `establishes_packet` marks the four-part WorkerCoordinator transition whose
    t(0) accounting opens the first packet; later packets are opened by the
    single transition that releases their predecessor.

    `ledger` is the organization ledger root when the caller holds it as
    supplied by its materializer (the kernel does), or a ledger store it
    holds; otherwise it is the store organization_store() selects for this
    execution. Either way it is supplied, never derived.

    `hb_epoch` is the carrier's heartbeat epoch. Supplied, every receipt this
    call writes carries that exact reference; absent, the reference is derived
    from the host clock and says so. An exact retry returns the original
    receipt whatever epoch it arrives at.

    `custody_exclusivity_verifier` is the only way an existing authority's
    attestation of unique custody reaches a successor's consequential append
    (require_custody_exclusivity); a root never released does not need it.
    """
    store = organization_store(ledger)
    if _is_posix(store):
        store.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        with store.exclusive():
            return _aggregate_transition_held(
                receipt, store, org_transition_class=org_transition_class,
                predecessor_org_state_sha256=predecessor_org_state_sha256,
                successor_org_state_sha256=successor_org_state_sha256,
                boundary_evidence=boundary_evidence, authority_effect=authority_effect,
                parent_manifest=parent_manifest, establishes_packet=establishes_packet,
                now_ns=now_ns, hb_epoch=hb_epoch, custody_exclusivity_verifier=custody_exclusivity_verifier)
    if parent_manifest is not None:
        # A manifested packet may carry a released batch to custody before its
        # receipt is published; refuse a surface that is not private custody
        # first, so nothing leaves before the refusal.
        store.require_private_custody()
    # A store without a local lock stages every write of this transition --
    # released batch, BATCH_HEAD, establishment receipt, work receipt, HEAD --
    # over one pinned snapshot and publishes them as one compare-and-swap
    # commit. A lost race or any refusal publishes none of them.
    with store.exclusive():
        staged = ledger_store.StagedLedgerTransaction(store)
        record = _aggregate_transition_held(
            receipt, staged, org_transition_class=org_transition_class,
            predecessor_org_state_sha256=predecessor_org_state_sha256,
            successor_org_state_sha256=successor_org_state_sha256,
            boundary_evidence=boundary_evidence, authority_effect=authority_effect,
            parent_manifest=parent_manifest, establishes_packet=establishes_packet,
            now_ns=now_ns, hb_epoch=hb_epoch, custody_exclusivity_verifier=custody_exclusivity_verifier)
        staged.commit()
        return record


def _aggregate_transition_held(receipt, store, *, org_transition_class, predecessor_org_state_sha256,
                               successor_org_state_sha256, boundary_evidence, authority_effect,
                               parent_manifest, establishes_packet, now_ns, hb_epoch,
                               custody_exclusivity_verifier):
    """aggregate_transition() for a caller holding `store` exclusively.

    `store` is the POSIX store under its append lock, or a staged transaction
    the caller publishes. Packet release and batch custody read and write
    through the same store as the receipts they batch.
    """
    # Before any packet release: at a successor without an attestation, or
    # at a root relocated without a handover, nothing is closed, submitted
    # or appended.
    require_consequential_custody(store, verify_custody_lineage(store), _read_tip(store),
                                  org_transition_class, custody_exclusivity_verifier,
                                  lambda: custody_action_sha256(org_transition_class,
                                                                verify_source(receipt)["source_transition_sha256"]))
    released = None
    effective_boundary_evidence = dict(boundary_evidence or {})
    if parent_manifest is not None:
        # The governing parent manifest owns packet release, authorized
        # once at establishment. A satisfied or expired prior packet is
        # released and carried through the existing canonical custody
        # client as a manifest-directed consequence. That custody result
        # is execution evidence only; it must never mint or replace the
        # parent manifest's governance disposition.
        import organization_batch_custody as batches
        # Establishment is declared by the manifest. A manifest without
        # one stays count-governed and unchanged, so manifests written
        # before packets had a t(0) remain valid.
        manifest_establishes = batches.manifest_declares_establishment(parent_manifest)
        if establishes_packet and not manifest_establishes:
            raise ValueError("t(0) establishment requires a manifest establishment declaration")
        if establishes_packet:
            effective_boundary_evidence[batches.ESTABLISHMENT_KEY] = batches.establishment_record(
                parent_manifest, kind="MANIFEST_ASSIGNMENT_T0"
            )
        released = batches.release_satisfied_packet_before_next_transition(
            parent_manifest, root=store, now_ns=now_ns,
            custody_exclusivity_verifier=custody_exclusivity_verifier,
        )
        if released is not None:
            if establishes_packet:
                raise ValueError("t(0) establishment cannot also release a prior packet")
            release_execution_result = batches.submit_released_batch(store, released["batch_id"])
            if release_execution_result.get("state") not in {"COMPLETED", "FAILED"}:
                raise ValueError("released organization batch execution result invalid")
            if release_execution_result.get("governance_disposition") is not None:
                raise ValueError("released organization batch attempted governance escalation")
            carried = {
                "batch_id": released["batch_id"],
                "execution_result": release_execution_result["state"],
                "reason": release_execution_result.get("reason"),
                "authority_effect": release_execution_result.get("authority_effect"),
            }
            if manifest_establishes:
                # Release and successor establishment are one transition
                # and one receipt. It is member #1 of the packet it
                # opens, so the release has its own identity rather than
                # riding as an attribute of an unrelated work transition.
                _aggregate_transition_locked(
                    _packet_establishment_source(released), store=store,
                    org_transition_class="ORGANIZATION_RECEIPT_PACKET_ESTABLISHMENT",
                    boundary_evidence={
                        batches.ESTABLISHMENT_KEY: batches.establishment_record(
                            parent_manifest, kind="PRIOR_PACKET_RELEASE", released_batch=carried
                        ),
                        "parent_manifest_released_batch": carried,
                    },
                    authority_effect="NONE",
                    hb_epoch=hb_epoch,
                    custody_exclusivity_verifier=custody_exclusivity_verifier,
                )
            else:
                effective_boundary_evidence["parent_manifest_released_batch"] = carried
    record = _aggregate_transition_locked(
        receipt, store=store, org_transition_class=org_transition_class,
        predecessor_org_state_sha256=predecessor_org_state_sha256,
        successor_org_state_sha256=successor_org_state_sha256,
        boundary_evidence=effective_boundary_evidence, authority_effect=authority_effect,
        hb_epoch=hb_epoch, custody_exclusivity_verifier=custody_exclusivity_verifier,
    )
    if released is not None:
        state = batches.open_packet_state(parent_manifest, root=store, now_ns=now_ns)
        if state["receipt_count"] != (2 if manifest_establishes else 1):
            raise ValueError("successor organization receipt packet did not initialize correctly")
    return record


def release_custody(parent_manifest, *, ledger=None, hb_epoch=None, custody_exclusivity_verifier=None):
    """Append ORGANIZATION_LEDGER_CUSTODY_RELEASED; this root is then read-only for writers.

    The governing manifest declares the successor materialization, the exact
    HEAD being released and the next custody generation. Appended under the
    existing lock by the existing emitter. Nothing here stops a copy of this
    root taken before the release from being written elsewhere: that copy is
    detected where its receipts meet this release, not prevented.
    """
    transfer = custody_transfer(parent_manifest)
    store = organization_store(ledger)
    record = {
        "custody_transition": "RELEASED",
        "successor_materialization_id": transfer["successor_materialization_id"],
        "predecessor_head_sha256": transfer["predecessor_head_sha256"],
        "custody_generation": transfer["next_custody_generation"] - 1,
        "next_custody_generation": transfer["next_custody_generation"],
        "governing_manifest_sha256": sha(parent_manifest),
        "custody_exclusivity": CUSTODY_EXCLUSIVITY,
        "disposition": "ALLOW",
    }
    with store.exclusive():
        return _aggregate_transition_locked(
            _custody_source("RELEASED", record), store=store, org_transition_class=CUSTODY_RELEASED_CLASS,
            predecessor_org_state_sha256=record["predecessor_head_sha256"],
            boundary_evidence={CUSTODY_KEY: record}, authority_effect="NONE", hb_epoch=hb_epoch,
            custody_exclusivity_verifier=custody_exclusivity_verifier,
        )


def assume_custody(parent_manifest, *, materialization_id, ledger=None, hb_epoch=None):
    """Append ORGANIZATION_LEDGER_CUSTODY_ASSUMED, the first append at the successor.

    `materialization_id` is this location's identity as its materializer
    supplies it. HEAD must be the release, read back through the existing HEAD
    and chain walk and verified_organization_receipt; the release must name this
    materialization, the manifest's HEAD and generation, and this manifest.
    """
    import organization_batch_custody as batches
    transfer = custody_transfer(parent_manifest)
    store = organization_store(ledger)
    root = store.root if _is_posix(store) else None
    with store.exclusive():
        store.initialize()
        tip = _read_tip(store)
        rows = verify_custody_lineage(store)
        release = None
        for row in rows.values():
            record = custody_record(row)
            if (record and record["custody_transition"] == "ASSUMED"
                    and record.get("successor_materialization_id") == materialization_id
                    and record.get("governing_manifest_sha256") == sha(parent_manifest)):
                return row  # The exact assumption retried is the receipt already recorded.
        if tip is None or (rows.get(tip) or {}).get("org_transition_class") != CUSTODY_RELEASED_CLASS:
            # No release at HEAD: the gate names whether it is missing or interrupted.
            _custody_gate(store, rows, tip, CUSTODY_ASSUMED_CLASS, None)
        else:
            try:
                if root is not None:
                    batches._verified_head(root)
                    batches._segment(root, tip, None)
                else:
                    cursor, seen = tip, set()
                    while cursor is not None:
                        if cursor in seen:
                            raise ValueError("organization ledger cycle")
                        seen.add(cursor)
                        cursor = batches._verified_receipt(store, cursor).get("previous_receipt_sha256")
                row = batches._verified_receipt(store, tip)
                row = batches.verified_organization_receipt(
                    store, tip, state_receipt_sha256=row.get("source_transition_sha256"))
            except batches.OrganizationReceiptRefused as exc:
                raise CustodyRefused(exc.failed_predicate, retry_entrypoint=CUSTODY_ASSUME_RETRY, detail=exc.detail) from exc
            except CustodyRefused:
                raise
            except ValueError as exc:
                raise CustodyRefused("ORGANIZATION_LEDGER_CHAIN_UNVERIFIED", retry_entrypoint=CUSTODY_ASSUME_RETRY,
                                     detail=str(exc)) from exc
            if row.get("org_transition_class") == CUSTODY_RELEASED_CLASS:
                release = custody_record(row)
        if release is not None and release.get("successor_materialization_id") != materialization_id:
            raise CustodyRefused("CUSTODY_RELEASE_SUCCESSOR_MISMATCH", retry_entrypoint=CUSTODY_ASSUME_RETRY,
                                 detail=str(materialization_id))
        record = {
            "custody_transition": "ASSUMED",
            "release_receipt_sha256": tip,
            "successor_materialization_id": materialization_id,
            "predecessor_head_sha256": transfer["predecessor_head_sha256"],
            "custody_generation": transfer["next_custody_generation"],
            "governing_manifest_sha256": sha(parent_manifest),
            "custody_exclusivity": CUSTODY_EXCLUSIVITY,
            "disposition": "ALLOW",
        }
        return _aggregate_transition_locked(
            _custody_source("ASSUMED", record), store=store, org_transition_class=CUSTODY_ASSUMED_CLASS,
            predecessor_org_state_sha256=tip, boundary_evidence={CUSTODY_KEY: record},
            authority_effect="NONE", hb_epoch=hb_epoch,
        )


def _aggregate_transition_locked(receipt, *, root=None, store=None, org_transition_class="ORGANIZATION_STATE_TRANSITION", predecessor_org_state_sha256=None, successor_org_state_sha256=None, boundary_evidence=None, authority_effect="NONE", hb_epoch=None, custody_exclusivity_verifier=None):
    """The append itself, for a caller already holding the organization append lock.

    The receipt and HEAD are published by the store's append_transaction on
    the HEAD read here. On POSIX that is the advisory lock the caller holds; on
    a networked store it is the store's own compare-and-swap, and a lost race
    is a typed FAIL_CLOSED with nothing published.
    """
    source=verify_source(receipt)
    if store is None:
        store=organization_store(root)
        held=store.assume_exclusive()
    else:
        held=store.exclusive()
    with held:
        return _append_locked(receipt,source,store,org_transition_class=org_transition_class,
            predecessor_org_state_sha256=predecessor_org_state_sha256,
            successor_org_state_sha256=successor_org_state_sha256,
            boundary_evidence=boundary_evidence,authority_effect=authority_effect,hb_epoch=hb_epoch,
            custody_exclusivity_verifier=custody_exclusivity_verifier)

def _retained_in_store(store, receipt, source):
    """The exact source receipt an earlier append committed beside its receipt."""
    stored=store.get(ledger_store.source_key(source["source_transition_sha256"]))
    if stored is None: raise ValueError("retained organization source receipt missing")
    if stored!=receipt or verify_source(stored)["source_transition_sha256"]!=source["source_transition_sha256"]:
        raise ValueError("retained organization source receipt conflict")

def _append_locked(receipt, source, store, *, org_transition_class, predecessor_org_state_sha256, successor_org_state_sha256, boundary_evidence, authority_effect, hb_epoch, custody_exclusivity_verifier=None):
    posix=_is_posix(store)
    store.initialize()
    rows=verify_custody_lineage(store)
    existing=_existing_exact_source(
        store,source,org_transition_class=org_transition_class,
        predecessor_org_state_sha256=predecessor_org_state_sha256,
        successor_org_state_sha256=successor_org_state_sha256,
        boundary_evidence=boundary_evidence,authority_effect=authority_effect,
    )
    if existing is not None:
        if posix: retain_source(store.root,receipt,source)
        else: _retained_in_store(store,receipt,source)
        head=store.get(ledger_store.HEAD_KEY)
        if org_transition_class in CUSTODY_CLASSES and (head or {}).get("receipt_sha256")==existing.get("previous_receipt_sha256"):
            # An interrupted custody append wrote its receipt but not HEAD; the
            # exact retry completes it rather than appending a second one.
            key=ledger_store.receipt_key(existing["receipt_sha256"])
            if not store.compare_and_swap(ledger_store.HEAD_KEY,head,{"organization":C["organization"],
                    "receipt_sha256":existing["receipt_sha256"],"receipt_path":store.locator(key)}):
                raise ledger_store.lost_race("HEAD no longer equals the expected head")
        return existing
    head=store.get(ledger_store.HEAD_KEY)
    generation,attestation=_custody_gate(store,rows,head.get("receipt_sha256") if head is not None else None,
                                         org_transition_class,boundary_evidence,custody_exclusivity_verifier,
                                         custody_action_sha256(org_transition_class,source["source_transition_sha256"]))
    # POSIX keeps the source receipt beside the ledger before the append, as
    # it always has; any other store commits it in the append's own boundary.
    immutable={}
    if posix: retain_source(store.root,receipt,source)
    else: immutable[ledger_store.source_key(source["source_transition_sha256"])]=receipt
    head=store.get(ledger_store.HEAD_KEY)
    prev=head.get("receipt_sha256") if head is not None else None
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
        "hb_reference":kernel.hb_reference(epoch=hb_epoch) if hb_epoch is not None else kernel.hb_reference(),
        "observed_at":datetime.now(timezone.utc).isoformat(),
        "previous_receipt_sha256":prev,
        "custody_generation":generation,
    }
    if attestation is not None: body["custody_exclusivity_attestation_sha256"]=sha(attestation)
    if generation==0: body["custody_authority_basis"]=CUSTODY_AUTHORITY_BASIS_GENERATION_0
    digest=sha(body); record={**body,"receipt_sha256":digest}; key=ledger_store.receipt_key(digest)
    stored=store.get(key)
    if stored is not None and stored!=record: raise ValueError("org receipt collision")
    new_head={"organization":C["organization"],"receipt_sha256":digest,"receipt_path":store.locator(key)}
    if not store.append_transaction(key,record,head,new_head,immutable=immutable):
        raise ledger_store.lost_race("HEAD no longer equals the expected head")
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
    p.add_argument("--parent-manifest")
    p.add_argument("--release-custody",action="store_true")
    p.add_argument("--assume-custody-as")
    a=p.parse_args()
    if a.release_custody or a.assume_custody_as:
        if not a.parent_manifest: raise SystemExit("governing parent manifest required")
        try:
            if a.release_custody: record=release_custody(load(a.parent_manifest))
            else: record=assume_custody(load(a.parent_manifest),materialization_id=a.assume_custody_as)
        except LedgerLocationRequired as exc:
            print(json.dumps(location_refusal(exc),sort_keys=True)); raise SystemExit(1)
        except ledger_store.LedgerStoreRefused as exc:
            print(json.dumps(store_refusal(exc),sort_keys=True)); raise SystemExit(1)
        except CustodyRefused as exc:
            print(json.dumps(exc.refusal(),sort_keys=True)); raise SystemExit(1)
        print(json.dumps(record,sort_keys=True)); return
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
            parent_manifest=load(a.parent_manifest) if a.parent_manifest else None,
        )
    except LedgerLocationRequired as exc:
        print(json.dumps(location_refusal(exc),sort_keys=True))
        raise SystemExit(1)
    except ledger_store.LedgerStoreRefused as exc:
        print(json.dumps(store_refusal(exc),sort_keys=True))
        raise SystemExit(1)
    except CustodyRefused as exc:
        print(json.dumps(exc.refusal(),sort_keys=True))
        raise SystemExit(1)
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(json.dumps(record,sort_keys=True))

if __name__=="__main__": main()
