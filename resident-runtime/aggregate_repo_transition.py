#!/usr/bin/env python3
import argparse,base64,contextlib,contextvars,hashlib,importlib.util,json,os,tempfile
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

def canon(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
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

class LedgerLocusNotDeclared(LedgerLocationRequired):
    """The Organization manifest declares no ledger locus (OL-1b).

    The destination of every Organization append is the manifest's to choose,
    so there is no environment-only fallback: nothing is appended.
    """

    failed_predicate="ORGANIZATION_LEDGER_LOCUS_NOT_DECLARED"
    repair="declare organization_ledger in .stegverse/transition-ledger/org-contract.json"

    def __init__(self, field):
        ValueError.__init__(self,"organization_ledger_locus_not_declared: "+field)
        self.variable=field

class LedgerLocusMismatch(LedgerLocationRequired):
    """A materializer value, or a caller-held store, disagrees with the manifest-declared locus (OL-1b)."""

    failed_predicate="ORGANIZATION_LEDGER_LOCUS_MISMATCH"

    def __init__(self, variable, declared, *, repair=None):
        ValueError.__init__(self,"organization_ledger_locus_mismatch: "+variable)
        self.variable=variable
        self.declared=declared
        self.repair=repair or "unset "+variable+" or make it equal the declared organization_ledger value "+json.dumps(declared)

STORE_LOCUS_REPAIR=("supply the store organization_store() selects for the declared organization_ledger locus; "
                    "a caller-held store of another kind or ref is a second chain beside the declared one")

def require_declared_store(store):
    """A caller-held store is admitted only as the declared locus (OL-1b), else FAIL_CLOSED.

    Any object with append_transaction used to be taken as is, so a store on
    a foreign ref, or of another kind than the manifest declares, could take
    an append unchecked. A staged transaction is checked by the store it
    stages over. A Git store must carry the declared ref; a POSIX store is
    admitted only under a declared {store: posix} (its root is the
    materializer's, as OL-3 admits an explicit root there).
    """
    inner=store.store if isinstance(store,ledger_store.StagedLedgerTransaction) else store
    locus=declared_ledger_locus()
    kind=getattr(inner,"kind",None)
    if locus["store"]=="git":
        if kind!="GIT_REF":
            raise LedgerLocusMismatch("ledger:"+str(kind),locus,repair=STORE_LOCUS_REPAIR)
        if getattr(inner,"ref",None)!=locus["ref"]:
            raise LedgerLocusMismatch("ledger:"+str(kind)+":"+str(getattr(inner,"ref",None)),locus,repair=STORE_LOCUS_REPAIR)
    elif kind!="POSIX_FILESYSTEM":
        raise LedgerLocusMismatch("ledger:"+str(kind),locus,repair=STORE_LOCUS_REPAIR)
    return store

class LedgerStoreKindMismatch(LedgerLocationRequired):
    """A raw POSIX ledger read was asked for while the manifest declares another store (OL-2).

    The read path and the append path are always the one declared store, so a
    POSIX root is never read silently while appends go to the Git ref.
    """

    failed_predicate="ORGANIZATION_LEDGER_STORE_KIND_MISMATCH"

    def __init__(self, declared, repair=None):
        ValueError.__init__(self,"organization_ledger_store_kind_mismatch: declared "+str(declared))
        self.variable=LEDGER_LOCUS_KEY+".store"
        self.declared=declared
        self.repair=repair or "read the Organization ledger through organization_store() and the store read API"

EXPLICIT_ROOT_REPAIR=("omit the explicit POSIX Organization ledger root; the declared store is "
                      "organization_store(), selected by the Organization manifest")

def refuse_explicit_posix_root():
    """An explicitly supplied POSIX root is admitted only under a declared {store: posix} (OL-3).

    Under any other declaration it would append to or read a second chain
    beside the declared store, so it is FAIL_CLOSED
    ORGANIZATION_LEDGER_STORE_KIND_MISMATCH before anything is read or
    appended. Without a declaration the explicit root behaves as before.
    """
    locus=C.get(LEDGER_LOCUS_KEY)
    store=locus.get("store") if isinstance(locus,dict) else None
    if store is not None and store!="posix": raise LedgerStoreKindMismatch(store,EXPLICIT_ROOT_REPAIR)

def location_refusal(exc):
    """The append attempt's own disposition when no ledger root was supplied."""
    return {
        "schema":"stegverse.organization-ledger-append-refusal/v1",
        "organization":C["organization"],
        "disposition":"FAIL_CLOSED",
        "failed_predicate":exc.failed_predicate,
        "required_evidence_or_repair":getattr(exc,"repair",None) or "supply the organization ledger root as "+exc.variable,
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

    The root exists only for a declared {store: posix} locus (OL-2). Under any
    other declaration it is FAIL_CLOSED ORGANIZATION_LEDGER_STORE_KIND_MISMATCH:
    readers use organization_store() and the store's own read API instead.
    """
    store=declared_ledger_locus()["store"]
    if store!="posix": raise LedgerStoreKindMismatch(store)
    o=os.getenv("STEGVERSE_ORG_LEDGER_ROOT")
    if o: return Path(o).expanduser().resolve()
    raise LedgerLocationRequired("STEGVERSE_ORG_LEDGER_ROOT")
def load(p): return json.loads(Path(p).read_text())

def _is_store(value): return value is not None and hasattr(value,"append_transaction")
def _is_posix(store): return getattr(store,"kind",None)=="POSIX_FILESYSTEM"

LEDGER_LOCUS_KEY="organization_ledger"
LEDGER_STORES=("git","posix")

def declared_ledger_locus():
    """The Organization ledger locus the manifest declares (OL-1b).

    Absent or malformed, nothing is selected: FAIL_CLOSED
    ORGANIZATION_LEDGER_LOCUS_NOT_DECLARED, never an environment fallback.
    """
    locus=C.get(LEDGER_LOCUS_KEY)
    if not isinstance(locus,dict) or not locus.get("store"): raise LedgerLocusNotDeclared(LEDGER_LOCUS_KEY)
    if locus["store"] not in LEDGER_STORES: raise LedgerStoreSelectionInvalid(LEDGER_LOCUS_KEY+".store")
    if locus["store"]=="git" and not locus.get("ref"): raise LedgerLocusNotDeclared(LEDGER_LOCUS_KEY+".ref")
    return locus

def propagation_remote(locus):
    """The declared propagate_target remote, only when it is declared PRIVATE.

    A null or non-private target yields no remote, so propagate returns its
    existing typed non-gating refusal; no transition waits on it.
    """
    target=locus.get("propagate_target")
    if not isinstance(target,dict) or target.get("custody")!=ledger_store.PRIVATE_CUSTODY: return None
    return target.get("remote") or None

def _require_equal(variable, declared):
    """A materializer value is non-authoritative: present, it must equal the declaration."""
    supplied=os.getenv(variable)
    if supplied and supplied!=declared: raise LedgerLocusMismatch(variable,declared)

def organization_store(ledger=None):
    """The Organization ledger store, as the Organization manifest declares it.

    A store the caller holds is used only if it is the declared locus
    (require_declared_store: the declared kind, and for git the declared
    ref), else FAIL_CLOSED ORGANIZATION_LEDGER_LOCUS_MISMATCH; a root only
    under a declared {store: posix} (OL-3, refuse_explicit_posix_root). Otherwise the locus is
    org-contract.json's organization_ledger (OL-1b): store "git" with its ref,
    custody and propagate_target, or store "posix" at the materialized
    ledger_root(). STEGVERSE_ORG_LEDGER_STORE / _GIT_REF / _GIT_REMOTE /
    _GIT_CUSTODY are non-authoritative: each one present must equal the
    declared value, else FAIL_CLOSED ORGANIZATION_LEDGER_LOCUS_MISMATCH. A
    missing declaration is FAIL_CLOSED ORGANIZATION_LEDGER_LOCUS_NOT_DECLARED.
    Only STEGVERSE_ORG_LEDGER_GIT_DIR (and the POSIX root) stays host
    supplied: it is the local materialization path, not the destination.
    The ledger is the local git dir; the remote is only the target of the
    store's explicit materialize/propagate steps and is never awaited by a
    transition (F75-01).
    """
    if _is_store(ledger): return require_declared_store(ledger)
    if ledger is not None:
        refuse_explicit_posix_root()
        return ledger_store.PosixLedgerStore(Path(ledger).expanduser().resolve())
    locus=declared_ledger_locus()
    _require_equal("STEGVERSE_ORG_LEDGER_STORE",locus["store"])
    git=locus["store"]=="git"
    remote=propagation_remote(locus) if git else None
    _require_equal("STEGVERSE_ORG_LEDGER_GIT_REF",locus.get("ref") if git else None)
    _require_equal("STEGVERSE_ORG_LEDGER_GIT_REMOTE",remote)
    _require_equal("STEGVERSE_ORG_LEDGER_GIT_CUSTODY",locus.get("custody") if git else None)
    if not git: return ledger_store.PosixLedgerStore(ledger_root())
    if not os.getenv("STEGVERSE_ORG_LEDGER_GIT_DIR"): raise LedgerLocationRequired("STEGVERSE_ORG_LEDGER_GIT_DIR")
    return ledger_store.GitLedgerStore(
        os.environ["STEGVERSE_ORG_LEDGER_GIT_DIR"],locus["ref"],remote=remote,custody=locus.get("custody"),
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
            stream.write(json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n")
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

RETAINED_SUBMISSION_KEY="parent_manifest_released_batch_submission"

def _caller_context(boundary_evidence):
    """Boundary evidence as the caller supplied it, without what the ledger itself derived.

    The retained post-commit submission outcome (#3012) is read from the store
    at append time, so a retry arriving after the outcome was recorded derives
    a value the original append could not; it is ledger state, not a different
    transition context, and is not compared.
    """
    evidence=dict(boundary_evidence or {})
    evidence.pop(RETAINED_SUBMISSION_KEY,None)
    # Which batch this append released is ledger state too: an exact retry after
    # the release committed derives no release of its own (B-P36q).
    evidence.pop("parent_manifest_released_batch",None)
    return evidence

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
            or _caller_context(row.get("boundary_evidence")) != _caller_context(boundary_evidence)
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
                         custody_exclusivity_verifier=None, repository_ledger=None):
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
    call writes carries that exact reference; an absent or invalid one raises
    OrgLedgerEpochRefused (six-field FAIL_CLOSED; HB_EPOCH_NOT_SUPPLIED when
    absent) before the store is resolved or created, and no clock is read to
    stand in for it. An exact retry returns the original receipt whatever
    epoch it arrives at.

    `custody_exclusivity_verifier` is the only way an existing authority's
    attestation of unique custody reaches a successor's consequential append
    (require_custody_exclusivity); a root never released does not need it.

    A repository source receipt must be its designated repository ledger's own,
    reachable from its HEAD, and that ledger must pair with this organization
    store (source_ledger_refusal). The designated ledger is the materializer's
    STEGVERSE_REPO_LEDGER_ROOT, or the kernel custody's materializer-supplied
    store, bound by `with _materialized_repository_ledger(store):` -- a private
    channel, never a keyword, an environment variable or a request field. A
    public `repository_ledger` is accepted only when it is that same ledger.
    """
    _refuse_invalid_epoch(hb_epoch)
    _refuse_clock_source(receipt)
    _refuse_unbound_request(receipt, boundary_evidence)
    store = organization_store(ledger)
    # Resolved, not opened or written: the source's repository ledger must pair with it.
    _refuse_source_not_on_ledger(receipt, repository_ledger, organization=store,
                                 materialized=_MATERIALIZED.get())
    checked = _SOURCE_CHECKED.set(True)
    try:
        return _aggregate_transition_checked(receipt, store, org_transition_class=org_transition_class,
            predecessor_org_state_sha256=predecessor_org_state_sha256,
            successor_org_state_sha256=successor_org_state_sha256,
            boundary_evidence=boundary_evidence, authority_effect=authority_effect,
            parent_manifest=parent_manifest, establishes_packet=establishes_packet,
            now_ns=now_ns, hb_epoch=hb_epoch, custody_exclusivity_verifier=custody_exclusivity_verifier)
    finally:
        _SOURCE_CHECKED.reset(checked)


def _aggregate_transition_checked(receipt, store, *, org_transition_class, predecessor_org_state_sha256,
                                  successor_org_state_sha256, boundary_evidence, authority_effect,
                                  parent_manifest, establishes_packet, now_ns, hb_epoch,
                                  custody_exclusivity_verifier):
    """aggregate_transition() after its source was checked: the lock, the packet release and the append."""
    if _is_posix(store):
        store.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        with store.exclusive():
            record = _aggregate_transition_held(
                receipt, store, org_transition_class=org_transition_class,
                predecessor_org_state_sha256=predecessor_org_state_sha256,
                successor_org_state_sha256=successor_org_state_sha256,
                boundary_evidence=boundary_evidence, authority_effect=authority_effect,
                parent_manifest=parent_manifest, establishes_packet=establishes_packet,
                now_ns=now_ns, hb_epoch=hb_epoch, custody_exclusivity_verifier=custody_exclusivity_verifier)
        # The append lock is released; the committed transition is authoritative.
        _carry_released_batch_after_commit(store, parent_manifest, hb_epoch)
        return record
    if parent_manifest is not None:
        # A manifested packet may carry a released batch to custody after its
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
    # The compare-and-swap transaction is published and its snapshot unpinned.
    _carry_released_batch_after_commit(store, parent_manifest, hb_epoch)
    return record


def _carry_released_batch_after_commit(store, parent_manifest, hb_epoch):
    """Master Records carriage of a released batch, after the sovereign commit (#3012).

    The same shape as the Git ledger's `propagate` step (F75-01): invoked only
    once the local append is committed and its lock or transaction released,
    never inside it, so no transition waits on another machine. Master
    Records is non-gating by design -- its outcome is recorded as an immutable
    submission receipt beside the receipts (organization_batch_custody
    .submit_pending_released_batch) and retained on the next manifest-directed
    append; it is never a predicate of the committed transition and nothing
    here raises into it.
    """
    if parent_manifest is None:
        return None
    import organization_batch_custody as batches
    return batches.submit_pending_released_batch(store, hb_epoch=hb_epoch)


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
        # An exact retry is recognised before anything is released: under an
        # establishment-bound manifest the release's establishment receipt
        # and this one already fill the successor packet, so releasing first
        # would close it again (W4). The recorded receipt is returned.
        if _existing_exact_source(
            store, verify_source(receipt), org_transition_class=org_transition_class,
            predecessor_org_state_sha256=predecessor_org_state_sha256,
            successor_org_state_sha256=successor_org_state_sha256,
            boundary_evidence=effective_boundary_evidence, authority_effect=authority_effect,
        ) is not None:
            return _aggregate_transition_locked(
                receipt, store=store, org_transition_class=org_transition_class,
                predecessor_org_state_sha256=predecessor_org_state_sha256,
                successor_org_state_sha256=successor_org_state_sha256,
                boundary_evidence=effective_boundary_evidence, authority_effect=authority_effect,
                hb_epoch=hb_epoch, custody_exclusivity_verifier=custody_exclusivity_verifier,
            )
        # The last released batch's post-commit submission outcome, read from
        # this store before any release moves BATCH_HEAD, is retained on this
        # receipt once (#3012). Read-only and derived from the ledger, so an
        # exact retry derives the same value and it is not caller context.
        # An unindexed batch a faulted release wrote is indexed first (B-P36q).
        batches.adopt_unindexed_batch(store)
        retained = batches.retained_submission_evidence(store)
        if retained is not None:
            effective_boundary_evidence[batches.RELEASED_BATCH_SUBMISSION_KEY] = retained
        # A release a faulted attempt committed is resumed, not repeated: a
        # released batch whose carrying receipt never landed is carried by
        # this one (B-P36q).
        released = batches.pending_manifest_release(store)
        if released is None:
            # Expiry and release read the supplied epoch when one is in hand, never a clock.
            released = batches.release_satisfied_packet_before_next_transition(
                parent_manifest, root=store, now_ns=now_ns,
                custody_exclusivity_verifier=custody_exclusivity_verifier,
                epoch=int(str(hb_epoch)) if hb_epoch is not None else None,
            )
        if released is not None:
            if establishes_packet:
                raise ValueError("t(0) establishment cannot also release a prior packet")
            # No transport here: the sovereign receipt names the batch and the
            # key of its post-commit submission receipt, nothing that depended
            # on Master Records. Carriage runs after the commit (#3012).
            carried = batches.released_batch_carriage(released)
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
        state = batches.open_packet_state(parent_manifest, root=store, now_ns=now_ns,
                                          epoch=int(str(hb_epoch)) if hb_epoch is not None else None)
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
    _refuse_invalid_epoch(hb_epoch)
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
    _refuse_invalid_epoch(hb_epoch)
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


def _aggregate_transition_locked(receipt, *, root=None, store=None, org_transition_class="ORGANIZATION_STATE_TRANSITION", predecessor_org_state_sha256=None, successor_org_state_sha256=None, boundary_evidence=None, authority_effect="NONE", hb_epoch=None, custody_exclusivity_verifier=None, repository_ledger=None):
    """The append itself, for a caller already holding the organization append lock.

    The receipt and HEAD are published by the store's append_transaction on
    the HEAD read here. On POSIX that is the advisory lock the caller holds; on
    a networked store it is the store's own compare-and-swap, and a lost race
    is a typed FAIL_CLOSED with nothing published.
    """
    _refuse_invalid_epoch(hb_epoch)
    _refuse_clock_source(receipt)
    _refuse_unbound_request(receipt, boundary_evidence)
    source=verify_source(receipt)
    if store is None:
        store=organization_store(root)
        held=store.assume_exclusive()
    else:
        held=store.exclusive()
    if not _SOURCE_CHECKED.get():
        _refuse_source_not_on_ledger(receipt, repository_ledger, organization=store,
                                     materialized=_MATERIALIZED.get())
    with held:
        return _append_locked(receipt,source,store,org_transition_class=org_transition_class,
            predecessor_org_state_sha256=predecessor_org_state_sha256,
            successor_org_state_sha256=successor_org_state_sha256,
            boundary_evidence=boundary_evidence,authority_effect=authority_effect,hb_epoch=hb_epoch,
            custody_exclusivity_verifier=custody_exclusivity_verifier)

#: An append's epoch is supplied by its caller and checked by the kernel's
#: shared rule (SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH); an absent or invalid
#: one is refused six-field FAIL_CLOSED before anything is written, as
#: StegVerse-org/.github#189 does for the organization ledger there.
EPOCH_RETRY_ENTRYPOINT="resident-runtime/aggregate_repo_transition.py::aggregate_transition (hb_epoch=, or --hb-epoch)"
OrgLedgerEpochRefused=kernel.SuppliedEpochRefused

def epoch_refusal(hb_epoch):
    """The six-field FAIL_CLOSED refusal of an append's epoch, or None."""
    return kernel.writer_epoch_refusal(hb_epoch,retry_entrypoint=EPOCH_RETRY_ENTRYPOINT)

def require_supplied_epoch(hb_epoch):
    """The heartbeat reference of the supplied epoch, or OrgLedgerEpochRefused."""
    return kernel.supplied_hb_reference(hb_epoch,retry_entrypoint=EPOCH_RETRY_ENTRYPOINT)

def _retained_in_store(store, receipt, source):
    """The exact source receipt an earlier append committed beside its receipt."""
    stored=store.get(ledger_store.source_key(source["source_transition_sha256"]))
    if stored is None: raise ValueError("retained organization source receipt missing")
    if stored!=receipt or verify_source(stored)["source_transition_sha256"]!=source["source_transition_sha256"]:
        raise ValueError("retained organization source receipt conflict")

def _refuse_invalid_epoch(hb_epoch):
    """OrgLedgerEpochRefused for an absent or invalid epoch, before any store opens. No clock is read."""
    require_supplied_epoch(hb_epoch)

#: O-1: a repository source receipt is consumed only when its own heartbeat
#: reference is SUPPLIED (or CARRIED), never CLOCK or unmarked. Checked by the
#: kernel's shared rule on the receipt's reference, before any store opens.
SOURCE_CLOCK_PROVENANCE="SOURCE_RECEIPT_IS_CLOCK_PROVENANCE"
SOURCE_PROVENANCE_RETRY_ENTRYPOINT=(".stegverse/transition-ledger/emit.py::append (hb_epoch=, or --hb-epoch), "
                                    "then resident-runtime/aggregate_repo_transition.py::aggregate_transition")

def source_provenance_refusal(receipt):
    """The six-field FAIL_CLOSED of a repository source receipt stamped from a clock, or None.

    Only a repo-transition receipt carries an hb_reference. A CLOCK reference
    (derived_from_clock not False, or a sampled_unix_ns) and an unmarked one
    are refused; nothing is written and no clock is read. A legacy CLOCK
    receipt is never mutated: its transition is re-emitted under a supplied epoch.
    """
    if not isinstance(receipt,dict) or receipt.get("schema")!="stegverse.repo-transition-receipt/v1":
        return None
    reference=receipt.get("hb_reference")
    epoch=reference.get("epoch") if isinstance(reference,dict) else None
    failure=kernel.supplied_epoch_failure(epoch,reference if reference is not None else {})
    if failure is None and isinstance(reference,dict) and ("source" in reference or "head_receipt_sha" in reference):
        # The shared rule passes a CARRIED reference; this destination does not
        # accept CARRIED crossings at its writers either (B-P36m option 1, row 7),
        # so a source receipt claiming one is refused before anything is written.
        return {"disposition":"FAIL_CLOSED","failure_code":kernel.CARRIED_NOT_ACCEPTED_BY_DESTINATION,
                "failed_predicate":"DESTINATION_ACCEPTS_CARRIED_CROSSINGS",
                "detail":"source receipt "+str(receipt.get("receipt_sha256"))+" claims CARRIED provenance",
                "required_evidence_or_repair":"re-send with the SUPPLIED epoch",
                "retry_entrypoint":SOURCE_PROVENANCE_RETRY_ENTRYPOINT,
                "owning_existing_goal":kernel.HB_EPOCH_OWNING_EXISTING_GOAL,
                "next_attempt":"append again consuming a receipt minted with a SUPPLIED epoch; nothing was written",
                "derived_from_clock":False,"consequence_committed":False}
    if failure is None:
        return None
    code,detail=failure
    return {"disposition":"FAIL_CLOSED","failure_code":SOURCE_CLOCK_PROVENANCE,
            "failed_predicate":kernel.HB_EPOCH_PREDICATE,
            "detail":"source receipt "+str(receipt.get("receipt_sha256"))+": "+code+": "+detail,
            "required_evidence_or_repair":("the repository receipt this append consumes carries a SUPPLIED "
                                           "hb_reference (digits >= "+str(kernel.HB_ANCHOR_EPOCH)+", "
                                           "derived_from_clock false); a CLOCK or unmarked one is re-emitted "
                                           "under a supplied epoch, never mutated"),
            "retry_entrypoint":SOURCE_PROVENANCE_RETRY_ENTRYPOINT,
            "owning_existing_goal":kernel.HB_EPOCH_OWNING_EXISTING_GOAL,
            "next_attempt":"append again consuming a receipt minted with the supplied epoch; nothing was written",
            "derived_from_clock":False,"consequence_committed":False}

def _refuse_clock_source(receipt):
    """OrgLedgerEpochRefused (SOURCE_RECEIPT_IS_CLOCK_PROVENANCE) before any store opens."""
    refusal=source_provenance_refusal(receipt)
    if refusal is not None:
        raise OrgLedgerEpochRefused(refusal)

#: A repository source receipt is consumed only as the repository ledger's own:
#: byte-for-byte the receipt its digest addresses there, reachable from that
#: ledger's HEAD (VALIDATOR row 8). A self-consistent receipt minted anywhere
#: else, or no repository ledger supplied at all, is refused before any write.
SOURCE_NOT_ON_LEDGER="SOURCE_RECEIPT_NOT_ON_LEDGER"
SOURCE_ON_LEDGER_PREDICATE="SOURCE_RECEIPT_IS_THE_REPOSITORY_LEDGERS_OWN"

def _repository_ledger():
    """The repository ledger's own emitter module (its store and verified chain walk)."""
    spec=importlib.util.spec_from_file_location("aggregate_source_repository_ledger",
                                                ROOT/".stegverse/transition-ledger/emit.py")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

#: Lead ruling 2026-10-24T21:00Z, option (b): the source ledger is only this
#: repository's designated ledger. A caller-held store is accepted only when it
#: is that same ledger (by realpath, and for a git store the same ref and
#: namespace); a receipt of another repository is not admissible here until a
#: route verifies it on that repository's own designated ledger.
CALLER_CHOSEN_LEDGER="CALLER_CHOSEN_SOURCE_LEDGER_REJECTED"
ROOT_NOT_DESIGNATED="LEDGER_ROOT_NOT_CONTRACT_DESIGNATED"
CROSS_REPO_UNVERIFIED="SPPA_CROSS_REPO_OBSERVATION_UNVERIFIED"

def _ledger_identity(store):
    """What a ledger store is, by location: ('git', git dir realpath, ref, namespace) or ('posix', root realpath)."""
    if hasattr(store,"store") and hasattr(store,"kind"):
        store=store.store  # a StagedLedgerTransaction over the store it publishes to
    if hasattr(store,"git_dir") and hasattr(store,"ref"):
        return ("git",os.path.realpath(store.git_dir),store.ref,getattr(store,"namespace",None))
    if hasattr(store,"root"):
        return ("posix",os.path.realpath(store.root))
    return ("unknown",repr(store))

def _tracked_files_under(root):
    """True when `root` lies inside this checkout and holds files git tracks: a committed tree, never a ledger."""
    resolved=os.path.realpath(root)
    if not Path(resolved).is_relative_to(os.path.realpath(ROOT)):
        return False
    import subprocess
    listed=subprocess.run(["git","-C",str(ROOT),"ls-files","--",resolved],capture_output=True,text=True)
    return listed.returncode==0 and bool(listed.stdout.strip())

def source_ledger_refusal(receipt, repository_ledger=None, *, organization=None, materialized=None):
    """The six-field FAIL_CLOSED of a repository source receipt not on this repository's designated ledger, or None.

    The receipt must be this repository's (another repository's receipt is
    SPPA_CROSS_REPO_OBSERVATION_UNVERIFIED). The ledger is the one the
    materializer supplied (STEGVERSE_REPO_LEDGER_ROOT, read by
    emit.repository_store()): a git locator must name contract.json's ref and
    namespace, and a plain directory holding git-tracked files is
    LEDGER_ROOT_NOT_CONTRACT_DESIGNATED.

    Lead ruling 21:13Z (paired override): the designated ledger is the one the
    materializer supplied -- STEGVERSE_REPO_LEDGER_ROOT, or `materialized`, the
    kernel custody's repo_ledger_root passed through aggregate's internal
    channel (harness/CI and materializer redirection are its only intended
    users). Either way it must PAIR with `organization`, the organization store
    being appended: a git repository ledger is the same git repository (by
    realpath) and the same ref as the git organization ledger, at contract.json's
    namespace; a POSIX one pairs only with a POSIX organization ledger, neither
    root holding git-tracked files (a mixed pair is MIXED_LEDGER_KIND_PAIR,
    lead ruling 21:42Z). An unpaired ledger, or a public
    `repository_ledger` that is not the designated one, is
    CALLER_CHOSEN_SOURCE_LEDGER_REJECTED. None supplied is the location
    refusal, never a pass. The walk is emit.chain, which proves every node is
    the receipt its address names.
    """
    if not isinstance(receipt,dict) or receipt.get("schema")!="stegverse.repo-transition-receipt/v1":
        return None
    digest=receipt.get("receipt_sha256")
    def refused(detail,terminal=True,code=SOURCE_NOT_ON_LEDGER,repair=None):
        return {"disposition":"FAIL_CLOSED","failure_code":code,"terminal":terminal,
                "failed_predicate":SOURCE_ON_LEDGER_PREDICATE,"detail":"source receipt "+str(digest)+": "+detail,
                "required_evidence_or_repair":repair or ("consume the receipt this repository's designated ledger holds, "
                                               "byte-for-byte, reachable from its HEAD, with that ledger supplied "
                                               "(STEGVERSE_REPO_LEDGER_ROOT)"),
                "retry_entrypoint":SOURCE_PROVENANCE_RETRY_ENTRYPOINT,
                "owning_existing_goal":kernel.HB_EPOCH_OWNING_EXISTING_GOAL,
                "next_attempt":("retry once the repository ledger is readable; nothing was written" if not terminal
                                else "append again consuming the repository ledger's own receipt; nothing was written"),
                "derived_from_clock":False,"consequence_committed":False}
    repository=_repository_ledger()
    if receipt.get("repository")!=repository.C["repository"]:
        return refused("the receipt is "+repr(receipt.get("repository"))+"'s, not "+repository.C["repository"]+"'s",
                       code=CROSS_REPO_UNVERIFIED,
                       repair=("verify the receipt on its own repository's contract-designated ledger (that repository's "
                               "contract.json ref and namespace, fetched fresh) before it is consumed here"))
    if materialized is None and not os.getenv("STEGVERSE_REPO_LEDGER_ROOT"):
        # Nothing designated to check against is a refusal, never a pass: the same
        # location refusal every writer gives when its materializer supplied no ledger.
        raise LedgerLocationRequired("STEGVERSE_REPO_LEDGER_ROOT")
    try:
        designated=materialized if materialized is not None else repository.repository_store()
        identity=_ledger_identity(designated)
        paired=_ledger_identity(organization) if organization is not None else None
        # Lead ruling 21:42Z: both halves of a pair are the same kind. A git
        # repository ledger is the subtree of the organization ledger ref it pairs
        # with; a POSIX one pairs only with a POSIX organization ledger, and
        # neither root holds git-tracked files.
        if paired is not None and identity[0]!=paired[0]:
            return refused("MIXED_LEDGER_KIND_PAIR: a "+identity[0]+" repository ledger "+repr(identity)
                           +" with a "+paired[0]+" organization ledger "+repr(paired),code=CALLER_CHOSEN_LEDGER)
        if identity[0]=="git" and (paired is None or identity[1:3]!=paired[1:3]):
            return refused("the repository ledger "+repr(identity)+" does not pair with the organization ledger "
                           +repr(paired)+" being appended",code=CALLER_CHOSEN_LEDGER)
        if paired is not None and paired[0]=="posix" and _tracked_files_under(paired[1]):
            return refused("the organization ledger root "+paired[1]+" holds git-tracked files",code=ROOT_NOT_DESIGNATED)
        location=repository.C.get("repository_ledger_location") or {}
        if identity[0]=="git" and (identity[2],identity[3])!=(location.get("ref"),location.get("namespace")):
            return refused("the supplied git ledger "+repr(identity[2:])+" is not contract.json's "
                           +repr((location.get("ref"),location.get("namespace"))),code=ROOT_NOT_DESIGNATED)
        if identity[0]=="posix" and _tracked_files_under(identity[1]):
            return refused("the supplied ledger root "+identity[1]+" holds git-tracked files",code=ROOT_NOT_DESIGNATED)
        if repository_ledger is not None and _ledger_identity(repository_ledger)!=identity:
            return refused("the caller's ledger "+repr(_ledger_identity(repository_ledger))
                           +" is not this repository's designated ledger "+repr(identity),code=CALLER_CHOSEN_LEDGER)
        store=designated
        head=store.get(ledger_store.HEAD_KEY)
        # The whole chain is walked and verified even after a match, as emit.recorded
        # does, so the answer is never read off a chain that is broken further back.
        held=None
        for row in repository.chain(store,head):
            if held is None and row.get("receipt_sha256")==digest: held=row
    except (ValueError,RecursionError,MemoryError) as exc:
        # A chain that does not verify, or a corrupt stored receipt: terminal, nothing is believed.
        return refused(type(exc).__name__+": "+str(exc))
    except OSError as exc:
        # The ledger could not be read this time (row 9): non-terminal, the same append may be retried.
        return refused(type(exc).__name__+": "+str(exc),terminal=False)
    if held is None:
        return refused("not reachable from the repository ledger's HEAD")
    if held!=receipt:
        return refused("differs from the receipt the repository ledger holds at that address")
    return None

#: An organization receipt carried off this organization (Master Records
#: submission) is first proven to be this ledger's own (VALIDATOR row 4).
ORG_RECEIPT_NOT_ON_LEDGER="ORGANIZATION_RECEIPT_NOT_ON_LEDGER"
ORG_RECEIPT_ON_LEDGER_PREDICATE="ORGANIZATION_RECEIPT_IS_THE_ORGANIZATION_LEDGERS_OWN"

def organization_receipt_ledger_refusal(receipt, store=None, *, retry_entrypoint):
    """The six-field FAIL_CLOSED of an organization receipt that is not this ledger's own, or None.

    Its receipt_sha256 must be the hash of its body, and it must be, byte-for-byte,
    the receipt this organization ledger holds at that address, reachable from
    HEAD along previous_receipt_sha256 with every node self-verifying. `store` is
    the store the caller holds, else organization_store() (the declared locus).
    No ledger, an unreadable one or a broken chain is a refusal, never a pass.
    """
    digest=receipt.get("receipt_sha256") if isinstance(receipt,dict) else None
    def refused(code,detail,repair,terminal=True):
        return {"disposition":"FAIL_CLOSED","failure_code":code,"failed_predicate":ORG_RECEIPT_ON_LEDGER_PREDICATE,
                "terminal":terminal,
                "detail":"organization receipt "+str(digest)+": "+detail,"required_evidence_or_repair":repair,
                "retry_entrypoint":retry_entrypoint,"owning_existing_goal":kernel.HB_EPOCH_OWNING_EXISTING_GOAL,
                "next_attempt":"submit the organization ledger's own receipt; nothing was published",
                "derived_from_clock":False,"consequence_committed":False,"authority_effect":"NONE_REFUSAL_ONLY"}
    repair=("submit the receipt this organization ledger holds, byte-for-byte, reachable from its HEAD, "
            "with that ledger supplied by the materializer")
    if not isinstance(receipt,dict) or not isinstance(digest,str):
        return refused("CARRIED_REFERENCE_SELF_HASH_MISMATCH","no receipt_sha256",repair)
    if digest!=sha({k:v for k,v in receipt.items() if k!="receipt_sha256"}):
        return refused("CARRIED_REFERENCE_SELF_HASH_MISMATCH","receipt_sha256 is not the hash of its body "
                       "(edited after it was minted)",repair)
    try:
        store=store if store is not None else organization_store()
        rows=_custody_rows(store)
        cursor=_read_tip(store); seen=set(); held=None
        while cursor is not None:
            if cursor in seen or cursor not in rows:
                return refused(ORG_RECEIPT_NOT_ON_LEDGER,"the chain from HEAD breaks at "+str(cursor),repair)
            seen.add(cursor)
            if cursor==digest: held=rows[cursor]
            cursor=rows[cursor].get("previous_receipt_sha256")
    except OSError as exc:
        return refused(ORG_RECEIPT_NOT_ON_LEDGER,type(exc).__name__+": "+str(exc),repair,terminal=False)
    except (ValueError,RecursionError,MemoryError) as exc:
        return refused(ORG_RECEIPT_NOT_ON_LEDGER,type(exc).__name__+": "+str(exc),repair)
    if held is None:
        return refused(ORG_RECEIPT_NOT_ON_LEDGER,"not reachable from the organization ledger's HEAD",repair)
    if held!=receipt:
        return refused(ORG_RECEIPT_NOT_ON_LEDGER,"differs from the receipt the ledger holds at that address",repair)
    return None

#: The kernel custody's materializer-supplied repository ledger, bound only by
#: `with _materialized_repository_ledger(store):` (lead rulings 21:13Z, 21:23Z):
#: never a keyword, an environment variable or a request field. Its in-tree
#: users are the kernel's crossing custody, the claim consumer and SPPA.
_MATERIALIZED=contextvars.ContextVar("aggregate_materialized_repository_ledger",default=None)
#: Set by aggregate_transition() while it appends a receipt it already checked,
#: so its own nested _aggregate_transition_locked calls do not check again.
_SOURCE_CHECKED=contextvars.ContextVar("aggregate_source_ledger_checked",default=False)

@contextlib.contextmanager
def _materialized_repository_ledger(store):
    """Bind the materializer-supplied repository ledger for the appends inside this block (still paired and checked)."""
    token=_MATERIALIZED.set(store)
    try:
        yield store
    finally:
        _MATERIALIZED.reset(token)

def _refuse_unbound_request(receipt, boundary_evidence):
    """CommittedRequestRefused before any store opens (rows 5 and 7).

    A caller's boundary evidence never carries committed_request. A source
    receipt that carries one was written in a request run, so it must name the
    committed request this run was started from, verified against its file.
    """
    kernel.refuse_caller_committed_request(boundary_evidence,"boundary_evidence")
    if not isinstance(receipt,dict) or kernel.COMMITTED_REQUEST_KEY not in receipt:
        return
    bound=kernel.committed_request()
    if bound is None or receipt[kernel.COMMITTED_REQUEST_KEY]!=bound:
        raise kernel.CommittedRequestRefused("COMMITTED_REQUEST_DIGEST_UNVERIFIED",
            "the source receipt's committed_request "+json.dumps(receipt[kernel.COMMITTED_REQUEST_KEY],sort_keys=True)
            +" is not this run's "+json.dumps(bound,sort_keys=True),
            repair="consume the source receipt in the request run it was written in, from that committed request")

def _refuse_source_not_on_ledger(receipt, repository_ledger=None, *, organization=None, materialized=None):
    """OrgLedgerEpochRefused (source_ledger_refusal) before anything is written to the organization store."""
    refusal=source_ledger_refusal(receipt,repository_ledger,organization=organization,materialized=materialized)
    if refusal is not None:
        raise OrgLedgerEpochRefused(refusal)

def _append_reference(hb_epoch):
    return require_supplied_epoch(hb_epoch)

def _append_locked(receipt, source, store, *, org_transition_class, predecessor_org_state_sha256, successor_org_state_sha256, boundary_evidence, authority_effect, hb_epoch, custody_exclusivity_verifier=None):
    reference=_append_reference(hb_epoch)
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
        "hb_reference":reference,
        # The supplied heartbeat, not a host clock reading.
        "observed_at":reference["heartbeat_id"],
        "previous_receipt_sha256":prev,
        "custody_generation":generation,
    }
    # In a request run the organization receipt binds the verified committed request too (row 1),
    # written at the request's own epoch.
    bound=kernel.committed_request(reference["epoch"])
    if bound is not None: body[kernel.COMMITTED_REQUEST_KEY]=bound
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
    p.add_argument("--hb-epoch",type=str,default=None,
                   help="carrier-supplied heartbeat epoch, ASCII digits >= 32; required, never coerced")
    a=p.parse_args()
    # The epoch is checked as typed, before any receipt is read or store opened.
    refused=epoch_refusal(a.hb_epoch)
    if refused is not None:
        print(json.dumps(refused,sort_keys=True)); raise SystemExit(1)
    hb_epoch=int(a.hb_epoch)
    # Inputs are read with #3290's kernel.cli_input_json / cli_json_text before
    # any writer is called; an unreadable one is CLI_INPUT_INVALID (F-INPUT-TRACE),
    # reported by kernel.run_writer_cli in __main__.
    entry="resident-runtime/aggregate_repo_transition.py"
    boundary_evidence=kernel.cli_json_text(a.boundary_evidence_json,"--boundary-evidence-json",retry_entrypoint=entry)
    parent_manifest=kernel.cli_input_json(a.parent_manifest,"--parent-manifest",retry_entrypoint=entry) if a.parent_manifest else None
    if a.release_custody or a.assume_custody_as:
        if not a.parent_manifest: raise SystemExit("governing parent manifest required")
        try:
            if a.release_custody: record=release_custody(parent_manifest,hb_epoch=hb_epoch)
            else: record=assume_custody(parent_manifest,materialization_id=a.assume_custody_as,hb_epoch=hb_epoch)
        except LedgerLocationRequired as exc:
            print(json.dumps(location_refusal(exc),sort_keys=True)); raise SystemExit(1)
        except ledger_store.LedgerStoreRefused as exc:
            print(json.dumps(store_refusal(exc),sort_keys=True)); raise SystemExit(1)
        except CustodyRefused as exc:
            print(json.dumps(exc.refusal(),sort_keys=True)); raise SystemExit(1)
        except OrgLedgerEpochRefused as exc:
            print(json.dumps(exc.refusal,sort_keys=True)); raise SystemExit(1)
        print(json.dumps(record,sort_keys=True)); return
    source_path=a.transition_receipt or a.repo_receipt
    if not source_path: raise SystemExit("transition receipt required")
    receipt=kernel.cli_input_json(source_path,"--transition-receipt/--repo-receipt",retry_entrypoint=entry)
    default_class="REPO_STATE_PROPAGATION" if receipt.get("schema")=="stegverse.repo-transition-receipt/v1" else "ORGANIZATION_STATE_TRANSITION"
    try:
        record=aggregate_transition(
            receipt,
            org_transition_class=a.org_transition_class or default_class,
            predecessor_org_state_sha256=a.predecessor_org_state_sha256,
            successor_org_state_sha256=a.successor_org_state_sha256,
            boundary_evidence=boundary_evidence,
            authority_effect=a.authority_effect,
            parent_manifest=parent_manifest,
            hb_epoch=hb_epoch,
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
    except OrgLedgerEpochRefused as exc:
        # The six fields of a refused epoch or a CLOCK source (O-1); nothing was written.
        print(json.dumps(exc.refusal,sort_keys=True))
        raise SystemExit(1)
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(json.dumps(record,sort_keys=True))

if __name__=="__main__": raise SystemExit(kernel.run_writer_cli(lambda: main() or 0, retry_entrypoint="resident-runtime/aggregate_repo_transition.py"))
