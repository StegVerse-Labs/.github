#!/usr/bin/env python3
import argparse,base64,fcntl,hashlib,importlib.util,json,os,tempfile
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

def canon(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sha(v): return "sha256:"+hashlib.sha256(canon(v)).hexdigest()
class LedgerLocationRequired(ValueError):
    """No ledger root was supplied; nothing is appended and nothing is derived."""

    failed_predicate="LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER"

    def __init__(self, variable):
        super().__init__("ledger_location_required_from_materializer: "+variable)
        self.variable=variable

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

def _custody_rows(root):
    """Every self-verifying receipt under root/receipts, by digest.

    A file that does not verify is left to the existing chain checks, which
    refuse it with their own reason.
    """
    rows={}
    for path in sorted((Path(root)/"receipts").glob("*.json")):
        try: row=load(path)
        except (OSError,ValueError): continue
        if not isinstance(row,dict): continue
        body=dict(row); claimed=body.pop("receipt_sha256",None)
        if not isinstance(claimed,str) or claimed!=sha(body) or path.stem!=claimed[7:]: continue
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
    rows=_custody_rows(root) if rows is None else rows
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

def _read_tip(root):
    h=Path(root)/"HEAD.json"
    return load(h).get("receipt_sha256") if h.exists() else None

def _custody_gate(root, rows, tip, org_transition_class, boundary_evidence):
    """The custody generation of the next receipt, or a FAIL_CLOSED refusal."""
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
        return record["custody_generation"]
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
    return generation

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

def _existing_exact_source(d, source, *, org_transition_class, predecessor_org_state_sha256, successor_org_state_sha256, boundary_evidence, authority_effect):
    """Reuse an immutable organization receipt for an exact already-recorded transition.

    The existing receipt directory is the only index; no new store or authority
    is introduced. A retry after an incomplete Master Records submission must
    not append a second organization transition for the same exact source.
    `hb_reference` and `observed_at` are deliberately not compared: a retry
    arrives at a later heartbeat, and that is not a different transition.
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

def _atomic_json(path, value):
    """Durably replace a JSON record while holding the organization append lock."""
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix=".append-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


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
                         establishes_packet=False, now_ns=None, ledger=None, hb_epoch=None):
    """Serialize appends; the governing parent manifest owns packet release.

    A manifested receipt packet's first receipt records its own establishment.
    `establishes_packet` marks the four-part WorkerCoordinator transition whose
    t(0) accounting opens the first packet; later packets are opened by the
    single transition that releases their predecessor.

    `ledger` is the organization ledger root when the caller holds it as
    supplied by its materializer (the kernel does); otherwise it is the one
    supplied to this execution. Either way it is supplied, never derived.

    `hb_epoch` is the carrier's heartbeat epoch. Supplied, every receipt this
    call writes carries that exact reference; absent, the reference is derived
    from the host clock and says so. An exact retry returns the original
    receipt whatever epoch it arrives at.
    """
    root = Path(ledger).expanduser().resolve() if ledger is not None else ledger_root()
    with _ledger_lock(root):
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
                    parent_manifest, root=root, now_ns=now_ns
                )
                if released is not None:
                    if establishes_packet:
                        raise ValueError("t(0) establishment cannot also release a prior packet")
                    release_execution_result = batches.submit_released_batch(root, released["batch_id"])
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
                            _packet_establishment_source(released), root=root,
                            org_transition_class="ORGANIZATION_RECEIPT_PACKET_ESTABLISHMENT",
                            boundary_evidence={
                                batches.ESTABLISHMENT_KEY: batches.establishment_record(
                                    parent_manifest, kind="PRIOR_PACKET_RELEASE", released_batch=carried
                                ),
                                "parent_manifest_released_batch": carried,
                            },
                            authority_effect="NONE",
                            hb_epoch=hb_epoch,
                        )
                    else:
                        effective_boundary_evidence["parent_manifest_released_batch"] = carried
            record = _aggregate_transition_locked(
                receipt, root=root, org_transition_class=org_transition_class,
                predecessor_org_state_sha256=predecessor_org_state_sha256,
                successor_org_state_sha256=successor_org_state_sha256,
                boundary_evidence=effective_boundary_evidence, authority_effect=authority_effect,
                hb_epoch=hb_epoch,
            )
            if released is not None:
                state = batches.open_packet_state(parent_manifest, root=root, now_ns=now_ns)
                if state["receipt_count"] != (2 if manifest_establishes else 1):
                    raise ValueError("successor organization receipt packet did not initialize correctly")
            return record


class _ledger_lock:
    """ORGANIZATION_LEDGER_LOCK: the fcntl lock on <root>/.append.lock (one kernel only)."""

    def __init__(self, root):
        self.root = Path(root)

    def __enter__(self):
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.lock = (self.root / ".append.lock").open("a+b")
        fcntl.flock(self.lock.fileno(), fcntl.LOCK_EX)
        return self.root

    def __exit__(self, *exc):
        try:
            fcntl.flock(self.lock.fileno(), fcntl.LOCK_UN)
        finally:
            self.lock.close()
        return False


def release_custody(parent_manifest, *, ledger=None, hb_epoch=None):
    """Append ORGANIZATION_LEDGER_CUSTODY_RELEASED; this root is then read-only for writers.

    The governing manifest declares the successor materialization, the exact
    HEAD being released and the next custody generation. Appended under the
    existing lock by the existing emitter. Nothing here stops a copy of this
    root taken before the release from being written elsewhere: that copy is
    detected where its receipts meet this release, not prevented.
    """
    transfer = custody_transfer(parent_manifest)
    root = Path(ledger).expanduser().resolve() if ledger is not None else ledger_root()
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
    with _ledger_lock(root):
        return _aggregate_transition_locked(
            _custody_source("RELEASED", record), root=root, org_transition_class=CUSTODY_RELEASED_CLASS,
            predecessor_org_state_sha256=record["predecessor_head_sha256"],
            boundary_evidence={CUSTODY_KEY: record}, authority_effect="NONE", hb_epoch=hb_epoch,
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
    root = Path(ledger).expanduser().resolve() if ledger is not None else ledger_root()
    with _ledger_lock(root):
        tip = _read_tip(root)
        rows = verify_custody_lineage(root)
        release = None
        for row in rows.values():
            record = custody_record(row)
            if (record and record["custody_transition"] == "ASSUMED"
                    and record.get("successor_materialization_id") == materialization_id
                    and record.get("governing_manifest_sha256") == sha(parent_manifest)):
                return row  # The exact assumption retried is the receipt already recorded.
        if tip is None or (rows.get(tip) or {}).get("org_transition_class") != CUSTODY_RELEASED_CLASS:
            # No release at HEAD: the gate names whether it is missing or interrupted.
            _custody_gate(root, rows, tip, CUSTODY_ASSUMED_CLASS, None)
        else:
            try:
                batches._verified_head(root)
                batches._segment(root, tip, None)
                row = batches._verified_receipt(root, tip)
                row = batches.verified_organization_receipt(
                    root, tip, state_receipt_sha256=row.get("source_transition_sha256"))
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
            _custody_source("ASSUMED", record), root=root, org_transition_class=CUSTODY_ASSUMED_CLASS,
            predecessor_org_state_sha256=tip, boundary_evidence={CUSTODY_KEY: record},
            authority_effect="NONE", hb_epoch=hb_epoch,
        )


def _aggregate_transition_locked(receipt, *, root=None, org_transition_class="ORGANIZATION_STATE_TRANSITION", predecessor_org_state_sha256=None, successor_org_state_sha256=None, boundary_evidence=None, authority_effect="NONE", hb_epoch=None):
    source=verify_source(receipt)
    root=root if root is not None else ledger_root(); d=root/"receipts"; d.mkdir(parents=True,exist_ok=True); h=root/"HEAD.json"
    rows=verify_custody_lineage(root)
    existing=_existing_exact_source(
        d,source,org_transition_class=org_transition_class,
        predecessor_org_state_sha256=predecessor_org_state_sha256,
        successor_org_state_sha256=successor_org_state_sha256,
        boundary_evidence=boundary_evidence,authority_effect=authority_effect,
    )
    if existing is not None:
        retain_source(root,receipt,source)
        if org_transition_class in CUSTODY_CLASSES and _read_tip(root)==existing.get("previous_receipt_sha256"):
            # An interrupted custody append wrote its receipt but not HEAD; the
            # exact retry completes it rather than appending a second one.
            _atomic_json(h,{"organization":C["organization"],"receipt_sha256":existing["receipt_sha256"],
                            "receipt_path":str(d/(existing["receipt_sha256"][7:]+".json"))})
        return existing
    prev=_read_tip(root)
    generation=_custody_gate(root,rows,prev,org_transition_class,boundary_evidence)
    retain_source(root,receipt,source)
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
    digest=sha(body); record={**body,"receipt_sha256":digest}; fp=d/(digest.split(":",1)[1]+".json")
    if fp.exists() and load(fp)!=record: raise ValueError("org receipt collision")
    if not fp.exists(): _atomic_json(fp,record)
    _atomic_json(h,{"organization":C["organization"],"receipt_sha256":digest,"receipt_path":str(fp)})
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
    except CustodyRefused as exc:
        print(json.dumps(exc.refusal(),sort_keys=True))
        raise SystemExit(1)
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(json.dumps(record,sort_keys=True))

if __name__=="__main__": main()
