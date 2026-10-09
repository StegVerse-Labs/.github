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
                         establishes_packet=False, now_ns=None, ledger=None, hb_epoch=None):
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
    """
    store = organization_store(ledger)
    root = store.root if _is_posix(store) else None
    if root is not None:
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
    elif parent_manifest is not None:
        # Packet release and batch custody still read and write a POSIX root.
        # Until they are carried by the store seam, a manifested packet on any
        # other store is refused rather than half-committed.
        raise ledger_store.LedgerStoreRefused(
            "ORGANIZATION_BATCH_CUSTODY_NOT_CARRIED_BY_LEDGER_STORE",
            "route organization_batch_custody packet release through the ledger store seam, "
            "or supply a POSIX Organization ledger root for a manifested packet",
            detail=getattr(store, "kind", ""),
        )
    with store.exclusive():
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
                        _packet_establishment_source(released), root=root, store=store,
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
            receipt, root=root, store=store, org_transition_class=org_transition_class,
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


def _aggregate_transition_locked(receipt, *, root=None, store=None, org_transition_class="ORGANIZATION_STATE_TRANSITION", predecessor_org_state_sha256=None, successor_org_state_sha256=None, boundary_evidence=None, authority_effect="NONE", hb_epoch=None):
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
            boundary_evidence=boundary_evidence,authority_effect=authority_effect,hb_epoch=hb_epoch)

def _retained_in_store(store, receipt, source):
    """The exact source receipt an earlier append committed beside its receipt."""
    stored=store.get(ledger_store.source_key(source["source_transition_sha256"]))
    if stored is None: raise ValueError("retained organization source receipt missing")
    if stored!=receipt or verify_source(stored)["source_transition_sha256"]!=source["source_transition_sha256"]:
        raise ValueError("retained organization source receipt conflict")

def _append_locked(receipt, source, store, *, org_transition_class, predecessor_org_state_sha256, successor_org_state_sha256, boundary_evidence, authority_effect, hb_epoch):
    posix=_is_posix(store)
    store.initialize()
    existing=_existing_exact_source(
        store,source,org_transition_class=org_transition_class,
        predecessor_org_state_sha256=predecessor_org_state_sha256,
        successor_org_state_sha256=successor_org_state_sha256,
        boundary_evidence=boundary_evidence,authority_effect=authority_effect,
    )
    if existing is not None:
        if posix: retain_source(store.root,receipt,source)
        else: _retained_in_store(store,receipt,source)
        return existing
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
    }
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
            parent_manifest=load(a.parent_manifest) if a.parent_manifest else None,
        )
    except LedgerLocationRequired as exc:
        print(json.dumps(location_refusal(exc),sort_keys=True))
        raise SystemExit(1)
    except ledger_store.LedgerStoreRefused as exc:
        print(json.dumps(store_refusal(exc),sort_keys=True))
        raise SystemExit(1)
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(json.dumps(record,sort_keys=True))

if __name__=="__main__": main()
