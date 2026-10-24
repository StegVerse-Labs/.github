#!/usr/bin/env python3
"""Universal StegVerse organization resident kernel.

Organization-neutral runtime behavior extracted from StegVerse-Labs/.github.
No GitHub, hosted scheduler, provider, or carrier grants authority.
"""
from __future__ import annotations
import base64, hashlib, importlib.util, json, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# StegOS node state is addressed by key, not located by path. The seam lives
# beside this module so the kernel loads it without depending on a package
# layout a node may not have.
_store_spec=importlib.util.spec_from_file_location(
    "stegos_node_store", Path(__file__).resolve().parent/"node_store.py")
node_store_module=importlib.util.module_from_spec(_store_spec)
_store_spec.loader.exec_module(node_store_module)
PosixStateStore=node_store_module.PosixStateStore

HB_ANCHOR_EPOCH=32
HB_ANCHOR_UNIX_NS=1_787_511_600_000_000_000
HB_PERIOD_NS=10_000_000
HB_HZ=100
CHANNEL_COUNT=16
SCHEMA="stegverse.org-resident-kernel/v1"
CARRIER_SCHEMA="stegverse.org-resident-kernel.carrier/v1"
PACKET_SCHEMA="stegverse.intr.org-boundary.v1"

def canon(v:Any)->bytes:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()

def sha(v:Any)->str:
    raw=v if isinstance(v,(bytes,bytearray)) else canon(v)
    return "sha256:"+hashlib.sha256(bytes(raw)).hexdigest()

def validate_hb_reference(ref:dict[str,Any])->dict[str,Any]:
    """A carrier frame's heartbeat reference is part of what the frame asserts.

    recover_packet verified the frame and packet digests but never the
    reference, so an incoherent or fabricated epoch rode through a validly
    hashed frame unchallenged.
    """
    if not isinstance(ref,dict): raise ValueError("heartbeat_reference_invalid")
    given=epoch=ref.get("epoch")
    # The shared rule's digits: "4096" is 4096; "+4096", " 4096" and 4096.0 are not.
    if isinstance(epoch,str) and supplied_epoch_failure(epoch) is None: epoch=int(epoch)
    if not isinstance(epoch,int) or isinstance(epoch,bool) or epoch<HB_ANCHOR_EPOCH:
        raise ValueError("heartbeat_epoch_invalid")
    if ref.get("generation") not in (epoch,given) or isinstance(ref.get("generation"),bool):
        raise ValueError("heartbeat_generation_mismatch")
    if ref.get("heartbeat_id")!=f"HB:{epoch}": raise ValueError("heartbeat_id_mismatch")
    if ref.get("frequency_hz")!=HB_HZ: raise ValueError("heartbeat_frequency_mismatch")
    if ref.get("progression_dependency")!="OSCILLATOR_ONLY":
        raise ValueError("heartbeat_progression_not_oscillator")
    return ref

def hb_reference(now_ns:int|None=None, *, epoch:int|None=None, source:str|None=None,
                 head_receipt_sha:str|None=None)->dict[str,Any]:
    """Build the heartbeat reference for a crossing.

    Progression is OSCILLATOR_ONLY: the epoch is a count of heartbeat periods,
    not a reading of a wall clock. Supply `epoch` from the carrier wherever the
    tick is available; the reference is then reproducible, so the same packet
    at the same epoch yields the same frame digest.

    Deriving the epoch from a host clock instead makes the reference depend on
    that host's clock discipline, so a derived reference says so and carries
    the sample it was derived from.

    `source` and `head_receipt_sha` are optional and go together: with a
    supplied epoch they mark the reference CARRIED (e.g. source
    ORGANIZATION_LEDGER_HEAD and that head's receipt sha). Without them the
    reference is SUPPLIED or CLOCK, unchanged.
    """
    if (source is None)!=(head_receipt_sha is None):
        raise ValueError("carried_provenance_needs_source_and_head_receipt_sha")
    if source is not None:
        if epoch is None: raise ValueError("carried_provenance_needs_a_supplied_epoch")
        if not isinstance(source,str) or not source or not isinstance(head_receipt_sha,str) or not head_receipt_sha:
            raise ValueError("carried_provenance_invalid")
    if epoch is not None:
        if now_ns is not None: raise ValueError("supply_epoch_or_sample_not_both")
        if not isinstance(epoch,int) or isinstance(epoch,bool) or epoch<HB_ANCHOR_EPOCH:
            raise ValueError("epoch_precedes_hb32_anchor")
        ref={"epoch":epoch,"generation":epoch,"heartbeat_id":f"HB:{epoch}",
             "phase_offset_ns":0,"frequency_hz":HB_HZ,"progression_dependency":"OSCILLATOR_ONLY",
             "derived_from_clock":False,"authority_effect":"NONE"}
        if source is not None:
            ref["source"]=source; ref["head_receipt_sha"]=head_receipt_sha
        return validate_hb_reference(ref)
    if now_ns is None:
        now_ns=int(datetime.now(timezone.utc).timestamp()*1_000_000_000)
    if now_ns<HB_ANCHOR_UNIX_NS:
        raise ValueError("sample_precedes_hb32_anchor")
    q,phase=divmod(now_ns-HB_ANCHOR_UNIX_NS,HB_PERIOD_NS)
    epoch=HB_ANCHOR_EPOCH+q
    return validate_hb_reference({"epoch":epoch,"generation":epoch,"heartbeat_id":f"HB:{epoch}",
            "sampled_unix_ns":now_ns,"phase_offset_ns":phase,"frequency_hz":HB_HZ,
            "progression_dependency":"OSCILLATOR_ONLY","derived_from_clock":True,
            "authority_effect":"NONE"})

def derive_channel(payload_hash:str)->dict[str,Any]:
    if not isinstance(payload_hash,str) or not payload_hash.startswith("sha256:") or len(payload_hash)!=71:
        raise ValueError("payload_hash_invalid")
    slot=int(payload_hash[7:23],16)%CHANNEL_COUNT
    return {"channel_id":f"HB:H1:P{slot}","phase_slot":slot,"phase_slot_count":CHANNEL_COUNT,
            "derivation":"PAYLOAD_SHA256_FIRST64_MOD_16","authority_effect":"NONE_CARRIER_ONLY"}

def carrier_frame(packet:dict[str,Any], *, now_ns:int|None=None, epoch:int|None=None)->dict[str,Any]:
    raw=canon(packet); payload_hash=sha(packet.get("payload",{})); ref=hb_reference(now_ns,epoch=epoch); channel=derive_channel(payload_hash)
    body={"schema":CARRIER_SCHEMA,"packet_id":packet["packet_id"],"packet_sha256":sha(raw),
          "packet_base64":base64.b64encode(raw).decode("ascii"),"heartbeat_reference":ref,
          "channel":channel,"origin_org":packet["origin"]["org"],"destination_org":packet["destination"]["org"],
          "intr_profile":packet["intr_profile"],"authority_effect":"NONE_CARRIER_ONLY"}
    return {**body,"frame_sha256":sha(body)}

def recover_packet(frame:dict[str,Any])->dict[str,Any]:
    body=dict(frame); claimed=body.pop("frame_sha256",None)
    if claimed!=sha(body): raise ValueError("carrier_frame_hash_mismatch")
    raw=base64.b64decode(frame["packet_base64"].encode("ascii"),validate=True)
    if sha(raw)!=frame["packet_sha256"]: raise ValueError("packet_hash_mismatch")
    validate_hb_reference(frame.get("heartbeat_reference"))
    packet=json.loads(raw)
    if packet["packet_id"]!=frame["packet_id"]: raise ValueError("packet_id_mismatch")
    if packet["destination"]["org"]!=frame["destination_org"]: raise ValueError("destination_org_mismatch")
    return packet

def receipt(kind:str, packet_id:str, subject:str, previous:str|None, detail:dict[str,Any])->dict[str,Any]:
    body={"kind":kind,"packet_id":packet_id,"subject":subject,"previous_receipt_id":previous,"detail":detail}
    rid=kind.lower()+"-"+hashlib.sha256(canon(body)).hexdigest()[:24]
    return {**body,"receipt_id":rid,"evidence_hash":sha(body)}

def load_registry(root:Path)->dict[str,Any]:
    return json.loads((root/"org-boundary/registry/services.json").read_text())

def node_standing(root:Path):
    """Load the organization's node-standing module from its boundary runtime.

    Standing is a precondition of ingress, not a capability, so it resolves here
    rather than being something a crossing can be addressed to. Resolved from the
    dispatch root because this kernel is organization-neutral, and a root without
    it fails closed: a boundary that cannot validate the predecessor it is
    required to carry must not admit a crossing claiming one.
    """
    path=root/"org-boundary/runtime/node_standing.py"
    if not path.is_file(): raise ValueError("org_boundary_node_standing_missing")
    spec=importlib.util.spec_from_file_location("node_standing",path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def manifest_selection(root:Path):
    """Load the organization's manifest-selection module from its boundary runtime.

    Processing is selected by the admitted manifest, not by the addressed row.
    Resolved from the dispatch root for the same reason as `node_standing`, and
    a root with no selection module fails closed: dispatching into a boundary
    that cannot say how processing was selected must not happen silently.
    """
    path=root/"org-boundary/runtime/manifest_selection.py"
    if not path.is_file(): raise ValueError("org_boundary_manifest_selection_missing")
    spec=importlib.util.spec_from_file_location("manifest_selection",path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

#: The boundary role whose dispatch resolves a bound capability's address.
#:
#: The role vocabulary is this kernel's, as `BOUNDARY_LOCAL_DIAGNOSTIC` and
#: `BOUNDARY_LOCAL_CONTROL` already are. `capability_ingress.ROLE` is that
#: module's assertion of which role it serves. A resolver serving a role the
#: kernel never dispatches would be unreachable.
CAPABILITY_INGRESS_ROLE="BOUNDARY_LOCAL_CAPABILITY_INGRESS"

def capability_ingress(root:Path):
    """Load the organization's capability-ingress module from its boundary runtime.

    A registered capability is bound to a receiving operation in the
    organization's own overlay. This resolves the address to that operation,
    from the dispatch root for the same reason as `manifest_selection`. A root
    without it fails closed when a capability address is dispatched: an address
    that cannot resolve which capability it serves must not run anything.
    """
    path=root/"org-boundary/runtime/capability_ingress.py"
    if not path.is_file(): raise ValueError("org_boundary_capability_ingress_missing")
    spec=importlib.util.spec_from_file_location("capability_ingress",path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def carried_standing(request_packet:dict[str,Any])->dict[str,Any]:
    """Carry a request's standing onto its response, unchanged and marked as carried.

    A response is not a new crossing and has no standing of its own to establish,
    so the only truthful options are to carry the request's standing forward or
    to refuse.
    """
    declared=request_packet.get("standing")
    if not isinstance(declared,dict): raise ValueError("response_requires_request_standing")
    return {**declared,"standing_carried_forward_from_request":True}

def resolve_endpoint_adapter(root:Path, service:dict[str,Any])->Path:
    """Resolve only an adapter the capability map explicitly admits.

    An INTERNAL_ENDPOINT is consumed here, inside this organization, when its
    row declares an adapter and admits it. Filesystem presence is not
    admissibility: the registry's disposition is the policy, and the path is
    only where the admitted adapter is materialized.
    """
    if service.get("endpoint_adapter_disposition")!="ALLOW_DECLARED_ADAPTER":
        raise ValueError(str(service.get("endpoint_adapter_disposition") or "FAIL_CLOSED_ENDPOINT_ADAPTER_UNDECLARED"))
    candidate=Path(str(service["endpoint_adapter"]))
    candidate=(candidate if candidate.is_absolute() else root/candidate).resolve()
    if not candidate.is_file(): raise ValueError("FAIL_CLOSED_ENDPOINT_ADAPTER_NOT_MATERIALIZED")
    return candidate

#: The effect an endpoint adapter declares in `endpoint_adapter_effect`. A pure
#: adapter writes nothing but its result; a node-state adapter writes only
#: through the write-once store at the node-state root it is handed.
NODE_STATE_WRITE_ONCE="NODE_STATE_WRITE_ONCE"

#: An endpoint adapter whose row declares `endpoint_adapter_hb_epoch` as
#: CARRIER_SUPPLIED is handed the heartbeat epoch of the carrier frame that
#: delivered the packet (`--hb-epoch`), so its receipts reference the crossing's
#: own tick rather than one the adapter derives from the host clock. The shared
#: epoch rule is the one TVC's broker applies (StegVerse-Labs/TVC#517, P1): the
#: carrier supplies the epoch, it is ASCII digits with value >= 32 (the HB32
#: anchor), and nothing on this path reads a clock. A reference the sender
#: derived from its clock is not a supplied epoch. INDEX H34b.
ENDPOINT_ADAPTER_HB_EPOCH_CARRIER_SUPPLIED="CARRIER_SUPPLIED"
HB_EPOCH_NOT_SUPPLIED="HB_EPOCH_NOT_SUPPLIED"
HB_EPOCH_INVALID="HB_EPOCH_INVALID"
#: The marker vocabulary of a heartbeat reference. SUPPLIED: derived_from_clock
#: explicitly false, with no sampled_unix_ns. CARRIED: false, plus `source` (e.g.
#: ORGANIZATION_LEDGER_HEAD) and `head_receipt_sha`; the shared rule treats it as
#: SUPPLIED and only the writer verifies the sha is the current verified head
#: (CARRIED_PROVENANCE_UNVERIFIED otherwise). CLOCK: derived_from_clock true, or a
#: bare sampled_unix_ns (legacy CLOCK, never SUPPLIED). supplied_epoch_failure
#: checks a reference in this order, with no source/sha exemption:
#: (1) derived_from_clock present and not exactly False -> HB_EPOCH_INVALID;
#: (2) sampled_unix_ns present -> HB_EPOCH_INVALID;
#: (3) derived_from_clock absent -> HB_EPOCH_PROVENANCE_UNMARKED (an unmarked
#: clock value is laundering, and a carrier cannot self-assert CARRIED).
HB_EPOCH_PROVENANCE_UNMARKED="HB_EPOCH_PROVENANCE_UNMARKED"
HB_EPOCH_PREDICATE="SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH"
HB_EPOCH_OWNING_EXISTING_GOAL="INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001"
HB_EPOCH_RETRY_ENTRYPOINT=("org-kernel/kernel.py::consume_and_respond: the sender re-publishes the packet in a "
                           "carrier frame stamped with a supplied epoch (publish_packet(..., epoch=<digits >= 32>))")
SIX_FIELDS=("failure_code","failed_predicate","required_evidence_or_repair",
            "retry_entrypoint","owning_existing_goal","next_attempt")

class CarrierEpochRefusal(ValueError):
    """FAIL_CLOSED refusal of a missing or invalid carrier epoch, carrying the six fields."""
    def __init__(self, failure_code:str, *, required_evidence_or_repair:str, next_attempt:str)->None:
        super().__init__(failure_code)
        self.record={"disposition":"FAIL_CLOSED","failure_code":failure_code,
                     "failed_predicate":HB_EPOCH_PREDICATE,
                     "required_evidence_or_repair":required_evidence_or_repair,
                     "retry_entrypoint":HB_EPOCH_RETRY_ENTRYPOINT,
                     "owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
                     "next_attempt":next_attempt,"derived_from_clock":False,
                     "consequence_committed":False}

def adapter_takes_carrier_epoch(service:dict[str,Any]|None)->bool:
    return (service or {}).get("endpoint_adapter_hb_epoch")==ENDPOINT_ADAPTER_HB_EPOCH_CARRIER_SUPPLIED

def supplied_epoch_failure(hb_epoch: Any, reference: Any = None) -> tuple[str, str] | None:
    """The shared supplied-epoch rule (SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH).

    Byte-identical in StegVerse-org/.github#185 and StegVerse-Labs/.github#3212
    and #3213. `hb_epoch` absent (None) is HB_EPOCH_NOT_SUPPLIED. Otherwise it
    must be ASCII [0-9]+ only -- an int is read as its decimal text; a bool, a
    float or anything coerced ('+33', ' 33', '3_3', '33.0') is refused -- with
    integer value >= 32 (the HB32 anchor). `reference`, the carrier frame's
    heartbeat reference when there is one, must be an object, and a
    `derived_from_clock` it carries must be exactly false. Any failure is
    HB_EPOCH_INVALID. Returns (failure_code, detail), or None when the epoch is
    supplied. No clock is read.
    """
    if reference is not None and not isinstance(reference, dict):
        return "HB_EPOCH_INVALID", "the carrier's heartbeat reference is not an object"
    if hb_epoch is None:
        return "HB_EPOCH_NOT_SUPPLIED", "no hb_epoch was supplied and no clock is read"
    if isinstance(hb_epoch, bool):
        text = None
    elif isinstance(hb_epoch, int):
        text = str(hb_epoch)
    elif isinstance(hb_epoch, str):
        text = hb_epoch
    else:
        text = None
    if text is None or not text.isascii() or not text.isdigit():
        return "HB_EPOCH_INVALID", "hb_epoch " + repr(hb_epoch) + " is not ASCII [0-9]+"
    if int(text) < 32:
        return "HB_EPOCH_INVALID", "hb_epoch " + text + " is below the HB32 anchor (32)"
    if reference is not None and "derived_from_clock" in reference \
            and reference["derived_from_clock"] is not False:
        return "HB_EPOCH_INVALID", ("the carrier's derived_from_clock is not exactly false; "
                                    "a clock-derived epoch is not a supplied one")
    if reference is not None and "sampled_unix_ns" in reference: return "HB_EPOCH_INVALID", "the carrier's heartbeat reference carries sampled_unix_ns; a sampled clock value is CLOCK, never a supplied epoch"
    if reference is not None and "derived_from_clock" not in reference: return "HB_EPOCH_PROVENANCE_UNMARKED", "the carrier's heartbeat reference carries no derived_from_clock; an unmarked clock value is laundering, and a carrier cannot self-assert CARRIED provenance"
    return None

class SuppliedEpochRefused(ValueError):
    """A receipt writer's refusal of an absent or invalid supplied epoch.

    `refusal` is the six-field FAIL_CLOSED from `writer_epoch_refusal`. Raised
    before anything is written; no clock is read to stand in for the epoch.
    """
    def __init__(self, refusal:dict[str,Any])->None:
        super().__init__(refusal["failure_code"]+": "+refusal["detail"])
        self.disposition=refusal["disposition"]
        self.failed_predicate=refusal["failed_predicate"]
        self.refusal=dict(refusal)

def writer_epoch_refusal(hb_epoch:Any, *, retry_entrypoint:str, reference:Any=None)->dict[str,Any]|None:
    """The six-field FAIL_CLOSED of a receipt writer's epoch, or None when it is supplied.

    The shape StegVerse-org/.github#189 gave the organization ledger
    (`epoch_refusal`): a receipt references the heartbeat epoch its caller
    supplies, checked by `supplied_epoch_failure`; an absent one is
    HB_EPOCH_NOT_SUPPLIED and is never derived from a clock.
    """
    failure=supplied_epoch_failure(hb_epoch,reference)
    if failure is None:
        return None
    code,detail=failure
    return {"disposition":"FAIL_CLOSED","failure_code":code,"failed_predicate":HB_EPOCH_PREDICATE,
            "detail":detail,
            "required_evidence_or_repair":("the caller supplies hb_epoch= (or --hb-epoch): ASCII digits with "
                                           "value >= "+str(HB_ANCHOR_EPOCH)+"; it is never derived from a clock"),
            "retry_entrypoint":retry_entrypoint,
            "owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
            "next_attempt":"call again with the supplied epoch; nothing was written",
            "derived_from_clock":False,"consequence_committed":False}

def supplied_hb_reference(hb_epoch:Any, *, retry_entrypoint:str, source:str|None=None,
                          head_receipt_sha:str|None=None)->dict[str,Any]:
    """The heartbeat reference of a supplied epoch, or SuppliedEpochRefused. No clock is read.

    With `source` and `head_receipt_sha` the reference is CARRIED; the caller
    has verified that sha is the current verified head.
    """
    refusal=writer_epoch_refusal(hb_epoch,retry_entrypoint=retry_entrypoint)
    if refusal is not None:
        raise SuppliedEpochRefused(refusal)
    return hb_reference(epoch=int(str(hb_epoch)),source=source,head_receipt_sha=head_receipt_sha)

#: A production caller with no supplied epoch in scope does not write and does
#: not read a clock to make one up: it refuses six-field FAIL_CLOSED under this
#: code (WU-B13 slice g). The shape is writer_epoch_refusal's.
NO_EPOCH_CALLER_FAILS_CLOSED="NO_EPOCH_CALLER_FAILS_CLOSED"

def no_epoch_caller_refusal(caller:str, *, retry_entrypoint:str)->dict[str,Any]:
    """The six-field FAIL_CLOSED of a production caller that has no supplied epoch in scope."""
    return {"disposition":"FAIL_CLOSED","failure_code":NO_EPOCH_CALLER_FAILS_CLOSED,
            "failed_predicate":HB_EPOCH_PREDICATE,
            "detail":caller+" has no supplied hb_epoch in scope; no clock is read and nothing is written",
            "required_evidence_or_repair":("thread the carrier-supplied hb_epoch (ASCII digits with value >= "
                                           +str(HB_ANCHOR_EPOCH)+") to "+caller+"; it is never derived from a clock"),
            "retry_entrypoint":retry_entrypoint,
            "owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
            "next_attempt":"call again once the caller carries the supplied epoch; nothing was written",
            "derived_from_clock":False,"consequence_committed":False}

class CliInputRefused(ValueError):
    """A writer CLI's input file could not be read as declared: the caller's fault, terminal."""
    def __init__(self, record:dict[str,Any])->None:
        super().__init__(record["failure_code"]+": "+record["detail"])
        self.record=dict(record)

def cli_input_json(path:Any, argument:str, *, retry_entrypoint:str, expect:type|tuple[type,...]=dict)->Any:
    """Read one CLI input file as JSON, before and outside the own-state fault handling.

    A missing, unreadable, non-UTF-8, non-JSON or wrongly typed file is the
    terminal six-field CLI_INPUT_INVALID (F-INPUT-TRACE); nothing is written.
    """
    try:
        text=Path(path).read_text(encoding="utf-8")
    except (OSError,ValueError) as exc:
        raise _cli_input_refused(exc,argument,retry_entrypoint) from None
    return cli_json_text(text,argument,retry_entrypoint=retry_entrypoint,expect=expect)

def cli_json_text(text:str, argument:str, *, retry_entrypoint:str, expect:type|tuple[type,...]=dict)->Any:
    """Parse one CLI argument's JSON text, as cli_input_json does a file's."""
    try:
        value=json.loads(text)
        if expect is not None and not isinstance(value,expect):
            raise ValueError("top-level value is "+type(value).__name__)
    except ValueError as exc:
        raise _cli_input_refused(exc,argument,retry_entrypoint) from None
    return value

def _cli_input_refused(exc:Exception, argument:str, retry_entrypoint:str)->CliInputRefused:
    return CliInputRefused({
        "disposition":"FAIL_CLOSED","failure_code":"CLI_INPUT_INVALID","terminal":True,
        "failed_predicate":"CLI_INPUT_IS_READABLE_JSON_OF_THE_DECLARED_TYPE:"+argument,
        "detail":type(exc).__name__+": "+str(exc),
        "required_evidence_or_repair":"pass "+argument+" as a readable UTF-8 JSON file of the declared type",
        "retry_entrypoint":retry_entrypoint,"owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
        "next_attempt":"run again with a valid "+argument+"; nothing was written",
        "consequence_committed":False})

def writer_fault_record(exc:BaseException, retry_entrypoint:str)->dict[str,Any]:
    """A fault in a writer's own state, as a non-terminal six-field record (F-WRITER-TRACE)."""
    committed="HEAD committed" in str(exc)
    return {"disposition":"FAIL_CLOSED",
            "failure_code":"WRITER_IO_FAILED" if isinstance(exc,OSError) else "WRITER_FAILED","terminal":False,
            "failed_predicate":"WRITER_COMPLETES_ITS_OWN_WRITES:"+type(exc).__name__,
            "detail":str(exc) or type(exc).__name__,
            "required_evidence_or_repair":"this writer's own state or ledger write completes",
            "retry_entrypoint":retry_entrypoint,"owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
            "next_attempt":("retry: HEAD is committed and the retry returns the recorded receipt" if committed else
                            "retry: an append whose HEAD did not advance left nothing behind"),
            "consequence_committed":committed}

def run_writer_cli(main:Any, *, retry_entrypoint:str)->int:
    """Run a writer CLI so that every failure is six fields on stdout, never a traceback."""
    try:
        return main()
    except (SystemExit,KeyboardInterrupt):
        raise
    except Exception as exc:  # noqa: BLE001 -- a writer CLI reports, it does not trace back
        # Matched by name: a CLI may load more than one copy of this kernel.
        name=type(exc).__name__
        if name=="CliInputRefused":
            print(json.dumps(exc.record,sort_keys=True)); return 2
        if name in ("SuppliedEpochRefused","RepoLedgerEpochRefused","OrgLedgerEpochRefused"):
            print(json.dumps(exc.refusal,sort_keys=True)); return 1
        if name=="CarrierEpochRefusal":
            print(json.dumps(exc.record,sort_keys=True)); return 1
        print(json.dumps(writer_fault_record(exc,retry_entrypoint),sort_keys=True)); return 1

def carrier_epoch(heartbeat_reference:Any)->int:
    """Return the epoch the carrier supplied, or refuse FAIL_CLOSED. No clock is read."""
    epoch=heartbeat_reference.get("epoch") if isinstance(heartbeat_reference,dict) else None
    failure=supplied_epoch_failure(epoch,heartbeat_reference)
    if failure is not None:
        code,detail=failure
        raise CarrierEpochRefusal(code,
            required_evidence_or_repair=(detail+"; the carrier frame supplies heartbeat_reference.epoch as "
                                         "ASCII digits with value >= 32 (the HB32 anchor), with any "
                                         "derived_from_clock exactly false; no clock is read"),
            next_attempt="re-publish the packet in a frame stamped with a supplied epoch >= 32")
    refuse_reference(heartbeat_reference)
    return int(str(epoch))

def refuse_reference(heartbeat_reference:Any)->None:
    """Refuse, six-field, a reference that claims CARRIED or is incoherent with its epoch.

    CARRIED: this kernel's writers cannot record source/head_receipt_sha, so the
    destination does not accept a CARRIED crossing (B-P36m option 1) on any
    route. Incoherent: a generation or heartbeat_id that does not follow from
    the epoch (HB_REFERENCE_INVALID, B-P36o). No clock is read.
    """
    if not isinstance(heartbeat_reference,dict):
        return
    if "source" in heartbeat_reference or "head_receipt_sha" in heartbeat_reference:
        refusal=CarrierEpochRefusal(CARRIED_NOT_ACCEPTED_BY_DESTINATION,
            required_evidence_or_repair="re-send with the SUPPLIED epoch",
            next_attempt="the sender re-publishes the packet in a SUPPLIED frame; nothing was written")
        refusal.record["failed_predicate"]="DESTINATION_ACCEPTS_CARRIED_CROSSINGS"
        raise refusal
    try:
        validate_hb_reference(heartbeat_reference)
    except ValueError as exc:
        reason=str(exc)
        if reason in ("heartbeat_generation_mismatch","heartbeat_id_mismatch"):
            raise CarrierEpochRefusal(HB_REFERENCE_INVALID,
                required_evidence_or_repair=(reason+"; generation and heartbeat_id follow from the epoch"),
                next_attempt="re-publish the packet in a coherent carrier frame") from None

ADAPTER_WRITE_FAULT_EXIT=75
ADAPTER_INPUT_FAULT_EXIT=65

class EndpointWriteFault(RuntimeError):
    """The adapter's own write faulted (exit 75): non-terminal, the frame stays pending."""

class EndpointInputFault(ValueError):
    """The adapter refused or failed on this frame (exit 65, 1, other, crash): terminal."""

def run_endpoint_adapter(root:Path, adapter:Path, packet:dict[str,Any], *,
                         service:dict[str,Any]|None=None, node_state:Any|None=None,
                         heartbeat_reference:dict[str,Any]|None=None)->dict[str,Any]:
    """Run an admitted adapter on the packet that crossed, and return its result.

    The adapter runs under this interpreter, so what it can import is what this
    boundary was materialized with rather than whatever a bare `python3` on the
    host path resolves to. Only an adapter declared NODE_STATE_WRITE_ONCE is
    handed this node's supplied state location, never the checkout; a pure
    adapter is given nothing it could write to. An adapter declared to take the
    carrier epoch is handed the epoch of `heartbeat_reference`, the carrier
    frame's; without a supplied one it does not run (FAIL_CLOSED, six fields).
    """
    hb_epoch=carrier_epoch(heartbeat_reference) if adapter_takes_carrier_epoch(service) else None
    with tempfile.TemporaryDirectory() as td:
        envelope=Path(td)/"packet.json"; out=Path(td)/"endpoint-response.json"
        envelope.write_text(json.dumps(packet,indent=2,sort_keys=True)+"\n")
        command=[sys.executable,str(adapter),"--packet",str(envelope),"--out",str(out)]
        if (service or {}).get("endpoint_adapter_effect")==NODE_STATE_WRITE_ONCE and node_state is not None:
            command+=["--node-state-root",str(node_state.root)]
        if hb_epoch is not None:
            command+=["--hb-epoch",str(hb_epoch)]
        completed=subprocess.run(command,cwd=root,capture_output=True,text=True,check=False)
        if completed.returncode!=0 or not out.is_file():
            detail=(completed.stderr or completed.stdout or "").strip().splitlines()
            reason=("endpoint_adapter_execution_failed"+(":"+detail[-1] if detail else "")
                    +" (exit "+str(completed.returncode)+")")
            # DC#10's split: 75 is the adapter's own write fault, non-terminal;
            # 65, 1, any other exit and a crash are terminal for this frame.
            if completed.returncode==ADAPTER_WRITE_FAULT_EXIT:
                raise EndpointWriteFault(reason)
            raise EndpointInputFault(reason)
        result=json.loads(out.read_text())
    if not isinstance(result,dict): raise ValueError("endpoint_adapter_result_invalid")
    return result

def dispatch(root:Path, packet:dict[str,Any], *, mesh_root:Path|None=None, node_state:Any|None=None,
             heartbeat_reference:dict[str,Any]|None=None)->dict[str,Any]:
    """Dispatch a recovered packet. `node_state` is this node's supplied state store.

    `heartbeat_reference` is the reference of the carrier frame that delivered
    the packet; an endpoint adapter and a capability-ingress operation requiring
    the carrier epoch are handed its supplied epoch and refused without one.

    `root` is the organization's materialized source: it is read, never written.
    Anything the crossing records (work intake) goes to `node_state`.
    """
    # Every route: a CARRIED or incoherent reference is refused before anything
    # is loaded or written (rows 7 and 12).
    refuse_reference(heartbeat_reference)
    registry=load_registry(root)
    if packet["destination"]["org"]!=registry["organization"]: raise ValueError("wrong_destination_org")
    service=next((s for s in registry["services"] if s["service_id"]==packet["destination"]["service"]),None)
    if service is None: raise ValueError("unknown_service")
    # Resolved before any receipt is minted, and before the role branch, because
    # the contract covers every ingress class rather than every boundary role.
    # Refused as the contract's own disposition rather than a bare error, so a
    # caller is never left guessing which of ALLOW/DENY/FAIL_CLOSED it earned.
    standing_module=node_standing(root)
    try:
        standing=standing_module.require(standing_module.load_contract(root),packet)
    except SystemExit as refused:
        raise ValueError("node_standing_refused:"+str(refused)) from None
    role=service.get("boundary_role")
    endpoint=role=="INTERNAL_ENDPOINT" and bool(service.get("endpoint_adapter"))
    if not endpoint and role not in {"BOUNDARY_LOCAL_DIAGNOSTIC","BOUNDARY_LOCAL_CONTROL",CAPABILITY_INGRESS_ROLE}:
        raise ValueError("endpoint_adapter_not_installed")
    # Resolved before any receipt is minted: a dispatch that cannot state how
    # processing was selected must not leave a chain implying it was consumed.
    # An internal endpoint whose packet declares no admitted capability and
    # route is refused here rather than processed by whichever adapter the
    # addressed row names.
    try:
        selected=manifest_selection(root).select_processing(service,packet["payload"])
    except SystemExit as refused:
        raise ValueError(str(refused)) from None
    # Resolved before any receipt is minted: an adapter the registry does not
    # admit must not leave a chain implying the crossing was consumed.
    adapter=resolve_endpoint_adapter(root,service) if endpoint else None
    # Also before any receipt: an adapter that takes the carrier epoch is not
    # run, and no chain implies it was, without one the carrier supplied.
    if endpoint and adapter_takes_carrier_epoch(service): carrier_epoch(heartbeat_reference)
    # Also before any receipt: a capability address hands the submission to an
    # operation that appends at both ledger levels. Without the carrier's epoch
    # that append fell back to the host clock, so it is refused here instead,
    # before the operation is loaded and before any store is opened.
    capability_epoch=carrier_epoch(heartbeat_reference) if role==CAPABILITY_INGRESS_ROLE else None
    # Also before any receipt: a work request is recorded in node state, so a
    # node materialized without one cannot consume it.
    if (role=="BOUNDARY_LOCAL_CONTROL" and node_state is None
            and (packet.get("payload") or {}).get("message_class")=="ecosystem.work.request"):
        raise ValueError("node_state_location_required_from_materializer")
    prev=None; receipts=[]
    for kind in ("INGRESS_ACCEPTED","DISPATCHED","CONSUMED","RESULT_BOUND","EGRESS_EMITTED"):
        r=receipt(kind,packet["packet_id"],service["service_id"],prev,{"payload_hash":sha(packet["payload"])})
        receipts.append(r); prev=r["receipt_id"]
    if endpoint:
        application_result=run_endpoint_adapter(root,adapter,packet,service=service,node_state=node_state,
                                                heartbeat_reference=heartbeat_reference)
    elif role=="BOUNDARY_LOCAL_CONTROL":
        application_result=handle_control_message(
            root,packet,registry,node_state=node_state,
            epoch=_frame_epoch({"heartbeat_reference":heartbeat_reference}))
    elif role==CAPABILITY_INGRESS_ROLE:
        # The address resolves to the receiving operation the overlay binds,
        # which records its own dispositions at both ledger levels. Its refusal
        # is surfaced as this boundary's refusal rather than becoming a consumed
        # crossing with a refusal buried in its application result. Loaded only
        # for this role: a root that never serves a capability address is not
        # defective for having no capability resolver.
        try:
            application_result=capability_ingress(root).receive(root,service,packet,registry=registry,
                                                                mesh_root=mesh_root,hb_epoch=capability_epoch)
        except SystemExit as refused:
            raise ValueError("capability_ingress_refused:"+str(refused)) from None
    else:
        application_result={"echo":packet["payload"]}
    return {"schema_version":SCHEMA,"organization":registry["organization"],"packet_id":packet["packet_id"],
            "service_id":service["service_id"],"consumed":True,"application_result":application_result,
            **selected,**standing,
            "authority_effect":packet["transition"]["authority_effect"],"receipts":receipts,
            "reconstruction":{"same_execution_required":True,"status":"RECONSTRUCTED","terminal_receipt_id":prev}}

def persist_outbox(root:Path, frame:dict[str,Any], *, store:Any|None=None)->Path:
    """Record a published frame in this node's outbox, atomically and write-once by key."""
    target=store or node_state_store(root)
    key=node_store_module.outbox_key(frame["packet_id"])
    try:
        target.put_once(key,frame)
    except node_store_module.WriteOnceCollision:
        raise ValueError("write_once_collision")
    return Path(target.locator(key))

def ingest_frame(root:Path, frame:dict[str,Any], *, mesh_root:Path|None=None, node_state:Any|None=None,
                 crossing_reference:dict[str,Any]|None=None)->dict[str,Any]:
    # The shared epoch rule first: an absent or invalid carrier epoch is the
    # six-field CarrierEpochRefusal, not a bare heartbeat_* error from recovery.
    failure=_frame_epoch_failure(frame)
    if failure is not None:
        code,detail=failure
        raise CarrierEpochRefusal(code,
            required_evidence_or_repair=(detail+"; the carrier frame supplies heartbeat_reference.epoch as "
                                         "ASCII digits with value >= 32 (the HB32 anchor); no clock is read"),
            next_attempt="re-publish the packet in a frame stamped with a supplied epoch >= 32")
    try:
        packet=recover_packet(frame)
    except ValueError as exc:
        # A reference inconsistent with its epoch is six-field, as in consume.
        reason=str(exc)
        if not reason.startswith("heartbeat_"):
            raise
        raise CarrierEpochRefusal(HB_EPOCH_INVALID if reason=="heartbeat_epoch_invalid" else HB_REFERENCE_INVALID,
            required_evidence_or_repair=(reason+"; the carrier frame's heartbeat_reference carries generation "
                                         "and heartbeat_id consistent with its epoch"),
            next_attempt="re-publish the packet in a coherent carrier frame") from None
    # A CARRIED claim is never consumed here: this destination does not accept
    # CARRIED crossings (B-P36m option 1), and the claim is never stripped and
    # accepted as SUPPLIED (B-P36k).
    if _claims_carried(frame):
        raise CarrierEpochRefusal(CARRIED_PROVENANCE_UNVERIFIED,
            required_evidence_or_repair=("the frame's heartbeat_reference asserts source/head_receipt_sha; "
                                         "it is admitted only when head_receipt_sha is this organization's "
                                         "current verified ledger head, recorded derived_from_clock false"),
            next_attempt="re-publish with a SUPPLIED reference, or a CARRIED one naming the verified head")
    registry=load_registry(root)
    if frame["destination_org"]!=registry["organization"]:
        return {"status":"IGNORED_NOT_ADDRESSED","packet_id":frame["packet_id"]}
    # A cycle at a supplied epoch hands the crossing that epoch's reference; the
    # frame's own reference is then provenance only.
    result=dispatch(root,packet,mesh_root=mesh_root,node_state=node_state,
                    heartbeat_reference=crossing_reference or frame.get("heartbeat_reference"))
    return {"status":"CONSUMED","packet":packet,"execution_result":result}

__all__=["hb_reference","validate_hb_reference","derive_channel","carrier_frame","recover_packet","dispatch",
         "persist_outbox","ingest_frame","mesh_store","node_state_store","node_state_provenance",
         "resolve_federation_root","resolve_node_state_root","addressed_node_state_store",
         "record_federation_cycle","federation_cycles","manifest_selection","capability_ingress",
         "CAPABILITY_INGRESS_ROLE","crossing_custody",
         "record_crossing","record_refusal","ingest_recorded","CROSSING_CONSUMED_CLASS","CROSSING_REFUSED_CLASS",
         "carrier_epoch","CarrierEpochRefusal","HB_EPOCH_NOT_SUPPLIED","HB_EPOCH_INVALID","HB_EPOCH_PROVENANCE_UNMARKED",
         "SuppliedEpochRefused","writer_epoch_refusal","supplied_hb_reference",
         "NO_EPOCH_CALLER_FAILS_CLOSED","no_epoch_caller_refusal"]


# --- Federation mesh v1.1 additions ---
def federation_root(root:Path|str|None)->Path:
    return resolve_federation_root(root)[0]

def resolve_federation_root(root:Path|str|None)->tuple[Path,str]:
    """Return the mesh location supplied by the node materializer.

    The mesh is never derived from an environment variable, a home directory,
    a checkout or any other host property: a mesh under one host's home belongs
    to that host and is lost with an ephemeral one. A materializer either
    supplies the mesh location or the node fails closed.
    """
    if root is None:
        raise ValueError("mesh_location_required_from_materializer")
    return Path(root).expanduser().resolve(), node_store_module.SUPPLIED

def mesh_store(root:Path|str|None=None, env:dict[str,str]|None=None)->Any:
    """The shared frame medium between nodes, explicitly supplied."""
    if env is not None:
        raise ValueError("host_environment_mesh_binding_forbidden")
    resolved,provenance=resolve_federation_root(root)
    return PosixStateStore(resolved, provenance=provenance)

def node_state_store(root:Path)->Any:
    """One node's own markers, outbox and work intake, under the root it was handed."""
    return PosixStateStore(Path(root)/"resident-runtime",
                           provenance=node_store_module.SUPPLIED)

def node_state_provenance(root:Path|str|None=None, env:dict[str,str]|None=None)->dict[str,Any]:
    """What this node's supplied mesh state depends on."""
    store=mesh_store(root,env)
    return {"schema_version":"stegverse.stegos-node-state-provenance/v1",
            "mesh_locator":str(store.root),"mesh_provenance":store.provenance,
            "mesh_portable":store.portable,"store_kind":store.kind,
            "authority_effect":"NONE_REPORT_ONLY"}

def publish_frame(frame:dict[str,Any], *, root:Path|None=None, store:Any|None=None)->Path:
    """Publish a frame to the mesh, addressed by what it carries.

    The key is `frames.d/<sha256(packet_id|frame_sha256)>.json`, the layout the
    mesh already had, so existing meshes and peers read it unchanged.
    """
    target=store or mesh_store(root)
    key=node_store_module.frame_key(frame)
    try:
        target.put_once(key,frame)
    except node_store_module.WriteOnceCollision:
        raise ValueError("federation_frame_write_once_collision")
    return Path(target.locator(key))

#: Reference cap on one frames.d file; a larger one is never parsed (B-P36p).
FRAME_SIZE_CAP_BYTES=1024*1024

def _read_frame(target:Any, key:str)->Any:
    path=Path(target.locator(key))
    if path.exists() and not path.is_file():
        raise OSError("frame_unreadable: "+path.name+" is not a regular file")
    if path.is_file() and path.stat().st_size>FRAME_SIZE_CAP_BYTES:
        raise ValueError("frame_oversized: more than "+str(FRAME_SIZE_CAP_BYTES)+" bytes")
    frame=target.get(key)
    if frame is not None and not isinstance(frame,dict):
        raise ValueError("frame_not_an_object: "+type(frame).__name__)
    return frame

def scan_addressed_frames(organization:str, *, root:Path|None=None, store:Any|None=None,
                          seen:set[str]|None=None, include_unreadable:bool=False)->list[dict[str,Any]]:
    """Frames in the mesh addressed to `organization` and not already consumed.

    Each file is read on its own guard: an unreadable, non-UTF-8, non-JSON,
    non-object or oversized file never stops the scan. It is skipped, or, with
    `include_unreadable`, returned with `scan_failure` so the consumer can
    quarantine it by name.
    """
    target=store or mesh_store(root)
    consumed=seen or set()
    out=[]
    for key in target.list_prefix(node_store_module.MESH_FRAME_PREFIX):
        if node_store_module.frame_name(key) in consumed:
            continue
        try:
            frame=_read_frame(target,key)
        except Exception as exc:  # noqa: BLE001 -- one bad file never stops the scan
            if include_unreadable:
                out.append({"key":key,"name":node_store_module.frame_name(key),"path":target.locator(key),
                            "frame":None,"scan_failure":exc})
            continue
        if frame is not None and frame.get("destination_org")==organization:
            out.append({"key":key,"name":node_store_module.frame_name(key),
                        "path":target.locator(key),"frame":frame})
    return out

def build_packet(*, origin_org:str, origin_service:str, destination_org:str, destination_service:str,
                 payload:dict[str,Any], standing:dict[str,Any], transition_reference:str="federation.v1",
                 authority_effect:str="NONE", packet_id:str|None=None)->dict[str,Any]:
    """Build an ingress packet. `standing` is required and has no default.

    Every ingress class the contract covers requires canonical node standing, so
    a standing-less packet is not a packet this boundary can construct. A default
    here would be a caller-editable claim, and the contract holds that a
    caller-editable classification does not establish identity.
    """
    pid=packet_id or "pkt-"+hashlib.sha256(canon({
        "origin_org":origin_org,"origin_service":origin_service,"destination_org":destination_org,
        "destination_service":destination_service,"payload":payload,"transition_reference":transition_reference
    })).hexdigest()[:24]
    return {
      "schema_version":PACKET_SCHEMA,
      "packet_id":pid,
      "direction":"INGRESS",
      "origin":{"org":origin_org,"service":origin_service},
      "destination":{"org":destination_org,"service":destination_service},
      "carrier":{"kind":"HB_DERIVED","reference":"org-federation"},
      "intr_profile":"stegverse.intr.org-boundary.v1",
      "transition":{"reference":transition_reference,"authority_effect":authority_effect,"conditions":[]},
      "payload":payload,
      "standing":standing,
      "evidence":{"ingress_receipt":None,"dispatch_receipt":None,"consumption_receipt":None,"egress_receipt":None,"reconstruction_reference":None}
    }

def publish_packet(packet:dict[str,Any], *, root:Path|None=None, now_ns:int|None=None,
                   epoch:int|None=None)->dict[str,Any]:
    frame=carrier_frame(packet,now_ns=now_ns,epoch=epoch)
    path=publish_frame(frame,root=root)
    return {"packet":packet,"frame":frame,"path":str(path)}

def consume_addressed_frames(repo_root:Path, *, mesh_root:Path|None=None, seen:set[str]|None=None,
                             node_state_root:Path|None=None, repo_ledger_root:Path|None=None,
                             org_ledger_root:Path|None=None, hb_epoch:Any=None)->list[dict[str,Any]]:
    # The same custody as consume_and_respond: a crossing consumed here is a
    # transition within the organization and is recorded before it is returned.
    # `hb_epoch` is the pass's own supplied epoch, as in consume_and_respond; a
    # frame that lends none is recorded under it, and with neither nothing is
    # recorded (ingest_recorded refuses NO_EPOCH_CALLER_FAILS_CLOSED).
    cycle_epoch=(None if hb_epoch is None else
                 int(supplied_hb_reference(hb_epoch,retry_entrypoint=CYCLE_EPOCH_RETRY_ENTRYPOINT)["epoch"]))
    custody=crossing_custody(repo_root,repo_ledger_root=repo_ledger_root,org_ledger_root=org_ledger_root)
    node_state=addressed_node_state_store(node_state_root) if node_state_root is not None else None
    registry=load_registry(repo_root)
    organization=registry["organization"]
    results=[]
    for item in scan_addressed_frames(organization,root=mesh_root,seen=seen):
        epoch=cycle_epoch if cycle_epoch is not None else _frame_epoch(item["frame"])
        result,recorded=ingest_recorded(repo_root,item,custody,registry,mesh_root=mesh_root,
                                        node_state=node_state,epoch=epoch)
        results.append({"path":item["path"],"result":result,"organization_record":recorded})
    return results


# --- Ecosystem-wide communication v1.2 additions ---
def organization_slug(organization:str)->str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in organization).strip("-")

def build_ecosystem_packets(*, origin_org:str, origin_service:str, organizations:list[str], standing:dict[str,Any],
                            message_class:str, subject:str, body:dict[str,Any],
                            requested_action:str|None=None, transition_reference:str="ecosystem.communication.v1",
                            authority_effect:str="NONE", communication_id:str|None=None)->dict[str,Any]:
    ordered=sorted(dict.fromkeys(organizations))
    if not ordered:
        raise ValueError("organizations_required")
    comm_id=communication_id or "ecosystem-"+hashlib.sha256(canon({
        "origin_org":origin_org,"origin_service":origin_service,"organizations":ordered,
        "message_class":message_class,"subject":subject,"body":body,
        "requested_action":requested_action,"transition_reference":transition_reference
    })).hexdigest()[:24]
    packets=[]
    for org in ordered:
        service=organization_slug(org)+".org-control"
        payload={
          "communication_id":comm_id,
          "message_class":message_class,
          "subject":subject,
          "body":body,
          "requested_action":requested_action,
          "audience":"ECOSYSTEM",
          "target_organization":org,
          "target_count":len(ordered)
        }
        packet=build_packet(
          origin_org=origin_org,
          origin_service=origin_service,
          destination_org=org,
          destination_service=service,
          payload=payload,
          standing=standing,
          transition_reference=transition_reference,
          authority_effect=authority_effect,
          packet_id=comm_id+":"+organization_slug(org)
        )
        packets.append(packet)
    return {"communication_id":comm_id,"organization_count":len(ordered),"packets":packets}

def publish_ecosystem_message(*, origin_org:str, origin_service:str, organizations:list[str],
                              standing:dict[str,Any], message_class:str, subject:str, body:dict[str,Any],
                              requested_action:str|None=None, transition_reference:str="ecosystem.communication.v1",
                              authority_effect:str="NONE", communication_id:str|None=None,
                              root:Path|None=None, now_ns:int|None=None)->dict[str,Any]:
    built=build_ecosystem_packets(
      origin_org=origin_org,origin_service=origin_service,organizations=organizations,standing=standing,
      message_class=message_class,subject=subject,body=body,requested_action=requested_action,
      transition_reference=transition_reference,authority_effect=authority_effect,
      communication_id=communication_id
    )
    publications=[publish_packet(packet,root=root,now_ns=now_ns) for packet in built["packets"]]
    return {"communication_id":built["communication_id"],"organization_count":built["organization_count"],
            "published_count":len(publications),"publications":publications}

def aggregate_ecosystem_results(communication_id:str, results_by_org:dict[str,list[dict[str,Any]]])->dict[str,Any]:
    rows=[]
    for org,items in sorted(results_by_org.items()):
        matched=[]
        for item in items:
            result=item.get("result") or {}
            packet=result.get("packet") or {}
            payload=packet.get("payload") or {}
            if payload.get("communication_id")==communication_id:
                matched.append(item)
        status="CONSUMED" if any((x.get("result") or {}).get("status")=="CONSUMED" for x in matched) else "NOT_OBSERVED"
        terminal=None
        for x in matched:
            er=(x.get("result") or {}).get("execution_result") or {}
            terminal=(er.get("reconstruction") or {}).get("terminal_receipt_id") or terminal
        rows.append({"organization":org,"status":status,"terminal_receipt_id":terminal})
    consumed=sum(1 for row in rows if row["status"]=="CONSUMED")
    return {"communication_id":communication_id,"organization_count":len(rows),
            "consumed_count":consumed,"pending_count":len(rows)-consumed,
            "complete":consumed==len(rows) and len(rows)>0,"organizations":rows}


# --- Ecosystem control/response v1.3 additions ---
def load_federation_directory(root:Path)->dict[str,Any]:
    path=root/"org-boundary/registry/federation.json"
    value=json.loads(path.read_text())
    if value.get("denominator")!=len(value.get("organizations") or []):
        raise ValueError("federation_directory_denominator_mismatch")
    return value

def resident_status(root:Path, registry:dict[str,Any]|None=None, *, epoch:int|None=None)->dict[str,Any]:
    reg=registry or load_registry(root)
    activation_path=root/"resident-runtime/activation-manifest.json"
    activation=json.loads(activation_path.read_text()) if activation_path.exists() else {}
    kernel=(activation.get("kernel") or {})
    return {
      "organization":reg["organization"],
      "kernel_version":kernel.get("version"),
      "activation_state":activation.get("state"),
      "registered_service_count":len(reg.get("services") or []),
      "registered_services":[s.get("service_id") for s in reg.get("services") or []],
      "org_control_service":organization_slug(reg["organization"])+".org-control",
      "heartbeat_reference":hb_reference(epoch=epoch) if epoch is not None else hb_reference(),
      "runtime_observation_claimed":False
    }

def persist_work_request(root:Path, packet:dict[str,Any], *, store:Any|None=None)->dict[str,Any]:
    payload=packet.get("payload") or {}
    communication_id=payload.get("communication_id")
    record={
      "schema_version":"stegverse.ecosystem-work-intake.v1",
      "communication_id":communication_id,
      "packet_id":packet["packet_id"],
      "origin":packet["origin"],
      "destination":packet["destination"],
      "requested_action":payload.get("requested_action"),
      "body":payload.get("body"),
      "transition":packet["transition"],
      "state":"QUEUED_FOR_LOCAL_ADMISSION_EVALUATION",
      "execution_authority_inferred":False,
      "carrier_grants_execution_authority":False
    }
    # Recorded in the node's supplied state, never in the source checkout.
    if store is None: raise ValueError("node_state_location_required_from_materializer")
    target=store
    key=node_store_module.intake_key(packet["packet_id"],communication_id)
    try:
        target.put_once(key,record)
    except node_store_module.WriteOnceCollision:
        raise ValueError("work_intake_write_once_collision")
    return {"state":record["state"],"intake_ref":target.locator(key),
            "execution_authority_inferred":False}

def handle_control_message(root:Path, packet:dict[str,Any], registry:dict[str,Any], *,
                           node_state:Any|None=None, epoch:int|None=None)->dict[str,Any]:
    payload=packet.get("payload") or {}
    message_class=payload.get("message_class")
    result={
      "message_received":True,
      "message_class":message_class,
      "communication_id":payload.get("communication_id"),
      "requested_action":payload.get("requested_action"),
      "execution_authority_inferred":False,
      "execution_authority_effect":packet["transition"]["authority_effect"]
    }
    if message_class=="ecosystem.monitor.request":
        # Stamped with the delivering frame's SUPPLIED epoch when it has one,
        # so a monitor answer never reaches the clock default for it.
        result["monitor_status"]=resident_status(root,registry,epoch=epoch)
    elif message_class=="ecosystem.work.request":
        result["work_intake"]=persist_work_request(root,packet,store=node_state)
    elif message_class=="ecosystem.communication":
        result["communication_acknowledged"]=True
    elif message_class in {"ecosystem.monitor.response","ecosystem.work.ack","ecosystem.communication.ack"}:
        result["response_acknowledged"]=True
    return result

#: The request classes this boundary answers, and the acknowledgement each is
#: answered with. Named because the responder, the response builder and the
#: egress boundary all read it; a crossing declaring anything else is consumed
#: and never answered.
RESPONDED_REQUEST_CLASSES={
    "ecosystem.monitor.request":"ecosystem.monitor.response",
    "ecosystem.work.request":"ecosystem.work.ack",
    "ecosystem.communication":"ecosystem.communication.ack",
}

def response_message_class(request_class:str|None)->str:
    return RESPONDED_REQUEST_CLASSES.get(request_class or "","ecosystem.communication.ack")

def build_control_response(request_packet:dict[str,Any], execution_result:dict[str,Any])->dict[str,Any]:
    req_payload=request_packet.get("payload") or {}
    origin_org=request_packet["origin"]["org"]
    local_org=request_packet["destination"]["org"]
    cls=response_message_class(req_payload.get("message_class"))
    payload={
      "communication_id":req_payload.get("communication_id"),
      "message_class":cls,
      "subject":"response:"+str(req_payload.get("subject") or ""),
      "body":{
        "request_packet_id":request_packet["packet_id"],
        "request_sha256":sha(request_packet),
        "responding_organization":local_org,
        "application_result":execution_result.get("application_result"),
        "receipt_terminal":(execution_result.get("reconstruction") or {}).get("terminal_receipt_id")
      },
      "requested_action":None,
      "audience":"ORIGIN",
      "target_organization":origin_org,
      "target_count":1
    }
    return build_packet(
      origin_org=local_org,
      origin_service=organization_slug(local_org)+".org-control",
      destination_org=origin_org,
      destination_service=organization_slug(origin_org)+".org-control",
      payload=payload,
      standing=carried_standing(request_packet),
      transition_reference=str((request_packet.get("transition") or {}).get("reference") or "ecosystem.communication.v1")+".response",
      authority_effect="NONE",
      packet_id=str(req_payload.get("communication_id"))+":response:"+organization_slug(local_org)
    )

# --- Organization receipts for every crossing this node consumes or refuses ---
#: The transition class a consumed federation crossing is recorded under.
CROSSING_CONSUMED_CLASS="ORGANIZATION_FEDERATION_CROSSING_CONSUMED"
#: The transition class a crossing this boundary refused is recorded under. Its
#: own class, so a crossing first refused and later admitted is two transitions
#: rather than an admission reported as the earlier refusal.
CROSSING_REFUSED_CLASS="ORGANIZATION_FEDERATION_CROSSING_REFUSED"
#: Refusals that will not change on a retry: the crossing is refused, recorded
#: and marked. Anything else is FAIL_CLOSED: recorded, left unmarked, retried.
DETERMINISTIC_REFUSALS=("unknown_service","node_standing_refused:","standing-",
                        "PROCESSING_SELECTED_ONLY_BY_ADMITTED_PROCESSING_CAPABILITY_AND_ROUTE_ID",
                        "manifest-declares-","declared-capability-","endpoint_adapter_not_installed",
                        "endpoint-adapter-not-installed","wrong_destination_org","wrong-destination-org")
#: Refusals of custody itself. Nothing can be recorded without it, so the whole
#: pass refuses before any mutation and the frames stay in the mesh.
CUSTODY_REFUSALS=("node_state_location_required_from_materializer",
                  "ledger_location_required_from_materializer",
                  "dispatch_root_is_not_this_kernels_organization")
_crossing_emitters:dict[str,Any]={}

def _own_module(name:str, relative:str)->Any:
    """Load a module from this kernel's own repository, never from a caller's root."""
    own=Path(__file__).resolve().parents[1]
    key=str(own/relative)
    if key not in _crossing_emitters:
        spec=importlib.util.spec_from_file_location(name,own/relative)
        if spec is None or not (own/relative).is_file():
            raise ValueError("organization_emitter_missing:"+relative)
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        _crossing_emitters[key]=module
    return _crossing_emitters[key]

def crossing_custody(repo_root:Path, *, repo_ledger_root:Path|None, org_ledger_root:Path|None)->dict[str,Any]:
    """The organization's own emitters and the ledger locations its materializer supplied.

    Resolved before anything is consumed. Every state transition occurring
    within the organization emits an organization receipt, and a consumed
    crossing is one. The emitters are this kernel's own repository's, so a
    caller's root cannot bring its own; the dispatch root must be this
    kernel's organization; and both ledger locations are supplied, never
    derived. Any of those missing is a refusal before mutation.

    `org_ledger_root` is a POSIX root, admitted only under a declared
    {store: posix} (OL-3: otherwise LedgerStoreKindMismatch, FAIL_CLOSED
    ORGANIZATION_LEDGER_STORE_KIND_MISMATCH, before anything is consumed), or
    the store organization_store() selected, used as is.
    """
    if repo_ledger_root is None or org_ledger_root is None:
        raise ValueError("ledger_location_required_from_materializer")
    own=Path(__file__).resolve().parents[1]
    emitter=_own_module("crossing_repository_ledger",".stegverse/transition-ledger/emit.py")
    organization_ledger=_own_module("crossing_organization_ledger","resident-runtime/aggregate_repo_transition.py")
    organization=load_registry(repo_root)["organization"]
    if Path(repo_root).resolve()!=own or organization!=organization_ledger.C["organization"]:
        raise ValueError("dispatch_root_is_not_this_kernels_organization")
    if organization_ledger._is_store(org_ledger_root):
        organization_root=org_ledger_root
    else:
        organization_ledger.refuse_explicit_posix_root()
        organization_root=Path(org_ledger_root).expanduser().resolve()
    return {"emitter":emitter,"organization_ledger":organization_ledger,
            "repository_store":emitter.ledger_store.PosixLedgerStore(Path(repo_ledger_root).expanduser().resolve()),
            "organization_root":organization_root}

def _record_both(custody:dict[str,Any], name:str, transition_class:str, predecessor:str, successor:str,
                 evidence:dict[str,Any], carried:tuple[str,...], epoch:int|None)->dict[str,Any]:
    """Append the repository receipt, then the organization receipt consuming it.

    Identified by the frame, which is content addressed, so the same frame seen
    again returns the repository receipt already recorded. The organization
    receipt is built from that returned receipt, not from this attempt, so a
    retry whose detail differs (a FAIL_CLOSED reason, say) consumes the same
    source with the same context and the organization ledger returns the
    receipt it already holds instead of refusing a conflict.
    """
    repository_receipt=custody["emitter"].append(
        "ORGANIZATION-FEDERATION-CROSSING-"+hashlib.sha256(name.encode()).hexdigest()[:16],
        transition_class,predecessor,successor,evidence,"NONE",hb_epoch=epoch,
        store=custody["repository_store"],idempotent_on=("frame_sha256","packet_id"))
    recorded=repository_receipt.get("evidence") or {}
    organization_receipt=custody["organization_ledger"].aggregate_transition(
        repository_receipt,org_transition_class="REPO_STATE_PROPAGATION",
        predecessor_org_state_sha256=repository_receipt["predecessor_state_sha256"],
        successor_org_state_sha256=repository_receipt["successor_state_sha256"],
        boundary_evidence={"operation":repository_receipt["transition_class"],
                           **{key:recorded.get(key) for key in carried}},
        authority_effect="NONE",ledger=custody["organization_root"],hb_epoch=epoch)
    return {"repository_receipt_sha256":repository_receipt["receipt_sha256"],
            "organization_receipt_sha256":organization_receipt["receipt_sha256"]}

def record_crossing(custody:dict[str,Any], item:dict[str,Any], result:dict[str,Any], *,
                    service:dict[str,Any]|None, epoch:int|None)->dict[str,Any]|None:
    """Append the repository and organization receipts for one consumed crossing.

    A crossing to a capability address is not recorded here: the receiving
    operation it resolves to records both levels itself.
    """
    if result.get("status")!="CONSUMED":
        return None
    if (service or {}).get("boundary_role")==CAPABILITY_INGRESS_ROLE:
        return None
    packet=result["packet"]; execution=result["execution_result"]; frame=item["frame"]
    name=node_store_module.frame_name(str(item["path"]))
    terminal=(execution.get("reconstruction") or {}).get("terminal_receipt_id")
    predecessor="sha256:"+hashlib.sha256(canon(packet.get("payload"))).hexdigest()
    successor="sha256:"+hashlib.sha256(canon({"packet_id":packet["packet_id"],"terminal_receipt_id":terminal})).hexdigest()
    evidence={"frame_name":name,"frame_sha256":frame.get("frame_sha256"),"packet_id":packet["packet_id"],
              "origin":packet["origin"],"destination":packet["destination"],
              "service_id":execution.get("service_id"),
              "boundary_role":(service or {}).get("boundary_role"),
              "message_class":(packet.get("payload") or {}).get("message_class"),
              "processing_selection":execution.get("processing_selection"),
              "terminal_receipt_id":terminal,"disposition":"ALLOW"}
    return _record_both(custody,name,CROSSING_CONSUMED_CLASS,predecessor,successor,evidence,
                        ("packet_id","service_id","disposition"),epoch)

def refusal_disposition(reason:str)->str:
    return "DENY" if any(marker in reason for marker in DETERMINISTIC_REFUSALS) else "FAIL_CLOSED"

def record_refusal(custody:dict[str,Any], item:dict[str,Any], reason:str, disposition:str, *,
                   service:dict[str,Any]|None, epoch:int|None,
                   actionable:dict[str,Any]|None=None)->dict[str,Any]:
    """Append the repository and organization receipts for a refused crossing.

    The crossing arrived, so its disposition is a transition of this
    organization, recorded like an admission. Identified by the frame, so a
    FAIL_CLOSED retried on every pass is recorded once.
    """
    frame=item["frame"]
    name=node_store_module.frame_name(str(item["path"]))
    packet_id=frame.get("packet_id")
    predecessor="sha256:"+hashlib.sha256(canon({"frame_sha256":frame.get("frame_sha256")})).hexdigest()
    successor="sha256:"+hashlib.sha256(canon({"packet_id":packet_id,"disposition":disposition,
                                                "failed_predicate":reason})).hexdigest()
    evidence={"frame_name":name,"frame_sha256":frame.get("frame_sha256"),"packet_id":packet_id,
              "destination_org":frame.get("destination_org"),
              "service_id":(service or {}).get("service_id"),
              "boundary_role":(service or {}).get("boundary_role"),
              "disposition":disposition,"failed_predicate":reason,
              "retry_entrypoint":None if disposition=="DENY" else "org-kernel/kernel.py::consume_and_respond"}
    carried=("packet_id","disposition","failed_predicate")
    if actionable:
        # A refusal that states its six fields is stored with them, at both
        # levels; its failed_predicate is the one it names, not the bare reason.
        evidence.update({key:actionable[key] for key in SIX_FIELDS if key in actionable})
        carried=("packet_id","disposition")+SIX_FIELDS
    recorded=_record_both(custody,name,CROSSING_REFUSED_CLASS,predecessor,successor,evidence,carried,epoch)
    return {**recorded,"disposition":disposition}

FRAME_REFUSED_QUARANTINED="FRAME_REFUSED_QUARANTINED"
CARRIED_PROVENANCE_UNVERIFIED="CARRIED_PROVENANCE_UNVERIFIED"
CARRIED_NOT_ACCEPTED_BY_DESTINATION="CARRIED_NOT_ACCEPTED_BY_DESTINATION"
HB_REFERENCE_INVALID="HB_REFERENCE_INVALID"
FRAME_INTEGRITY_INVALID="FRAME_INTEGRITY_INVALID"
FRAME_INGEST_FAILED="FRAME_INGEST_FAILED"

def _claims_carried(frame:Any)->bool:
    ref=frame.get("heartbeat_reference") if isinstance(frame,dict) else None
    return isinstance(ref,dict) and ("source" in ref or "head_receipt_sha" in ref)

def _carried_head_verified(frame:dict[str,Any], custody:dict[str,Any])->bool:
    """head_receipt_sha is this organization's current ledger head, recorded derived_from_clock false."""
    ref=frame["heartbeat_reference"]
    ledger=custody["organization_ledger"]
    store=ledger.organization_store(custody["organization_root"])
    head=store.get(ledger.ledger_store.HEAD_KEY) or {}
    sha=head.get("receipt_sha256")
    if not sha or ref.get("head_receipt_sha")!=sha:
        return False
    receipt=store.get(ledger.ledger_store.receipt_key(sha)) or {}
    recorded=receipt.get("hb_reference") if isinstance(receipt.get("hb_reference"),dict) else {}
    return recorded.get("derived_from_clock") is False and supplied_epoch_failure(recorded.get("epoch"),recorded) is None

def _is_clock_reference(ref:Any)->bool:
    """CLOCK: derived_from_clock true, or a bare sampled_unix_ns with no flag (legacy CLOCK)."""
    return isinstance(ref,dict) and (ref.get("derived_from_clock") is True
                                     or ("derived_from_clock" not in ref and "sampled_unix_ns" in ref))

def _frame_quarantine(frame:dict[str,Any], custody:dict[str,Any],
                      registry:dict[str,Any]|None=None)->dict[str,Any]|None:
    """The six-field quarantine of a frame that can never be consumed, or None. No clock is read.

    Every carrier epoch passes the digit/anchor check first, whatever the
    frame's flag. A CLOCK frame (flag true, or a bare sampled_unix_ns) is then
    consumed and lends no epoch (_frame_epoch); its receipts take the marked
    clock fallback until WU-B13 gives the publishers an epoch
    (CLOCK_FLAGGED_FRAMES_CONSUMED_PENDING_WU_B13). An UNMARKED reference, or
    one marked false that still carries sampled_unix_ns, is refused by the
    shared rule; a CARRIED claim must name this organization's verified head. A verified
    one is refused CARRIED_NOT_ACCEPTED_BY_DESTINATION while the registry declares
    accepts_carried_crossings false (B-P36m option 1): the writers cannot yet
    record source/head_receipt_sha downstream, and {epoch, false} reads as SUPPLIED.
    """
    ref=frame.get("heartbeat_reference") if isinstance(frame,dict) else None
    # A field of the wrong type is a malformed frame, whatever it would have
    # meant (F-TYPE): FRAME_INGEST_FAILED, not an integrity or epoch code.
    mistyped=[name for name,kind in (("heartbeat_reference",dict),("frame_sha256",str),("packet_sha256",str),
                                     ("packet_base64",str),("packet_id",str),("destination_org",str))
              if isinstance(frame,dict) and name in frame and not isinstance(frame[name],kind)]
    if mistyped:
        return _quarantine_record(frame,FRAME_INGEST_FAILED,"wrong type: "+", ".join(mistyped),
                                  failed_predicate="FRAME_IS_INGESTED_AS_PUBLISHED:TypeError")
    failure=_frame_epoch_failure(frame)
    if failure is None and _is_clock_reference(ref):
        return None
    if failure is None and isinstance(ref,dict):
        failure=supplied_epoch_failure(ref.get("epoch"),ref)
    if failure is None and _claims_carried(frame):
        if not _carried_head_verified(frame,custody):
            failure=(CARRIED_PROVENANCE_UNVERIFIED,"head_receipt_sha is not this organization's current verified "
                     "ledger head recorded derived_from_clock false")
        elif not (registry or {}).get("accepts_carried_crossings",False):
            failure=(CARRIED_NOT_ACCEPTED_BY_DESTINATION,"this organization's registry declares "
                     "accepts_carried_crossings false; a CARRIED crossing is not accepted here")
    if failure is None:
        return None
    if failure[0]==CARRIED_NOT_ACCEPTED_BY_DESTINATION:
        # Refused at admission, before any write, so no receipt is ever written
        # for a crossing this destination's writers cannot carry.
        record=_quarantine_record(frame,*failure,failed_predicate="DESTINATION_ACCEPTS_CARRIED_CROSSINGS")
        record.update({"required_evidence_or_repair":"re-send with the SUPPLIED epoch",
                       "retry_entrypoint":"the sender's hop: the origin re-publishes the packet in a SUPPLIED frame",
                       "owning_existing_goal":"INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001 (WU-B13, #3183)"})
        return record
    return _quarantine_record(frame,*failure)

def _ingest_failure_quarantine(frame:dict[str,Any], exc:Exception)->dict[str,Any]:
    """Any error ingesting one frame, as its six-field quarantine (B-P36o)."""
    reason=str(exc)
    if isinstance(exc,CarrierEpochRefusal):
        code=str(exc)
    elif "hash_mismatch" in reason:
        code=FRAME_INTEGRITY_INVALID
    elif reason.startswith("heartbeat_"):
        code=HB_EPOCH_INVALID if reason=="heartbeat_epoch_invalid" else HB_REFERENCE_INVALID
    else:
        code=FRAME_INGEST_FAILED
    return _quarantine_record(frame,code,reason or type(exc).__name__,
                              failed_predicate=(HB_EPOCH_PREDICATE if code in (HB_EPOCH_INVALID,HB_EPOCH_NOT_SUPPLIED,
                                                                              HB_REFERENCE_INVALID)
                                                else "FRAME_IS_INGESTED_AS_PUBLISHED:"+type(exc).__name__))

CYCLE_EPOCH_RETRY_ENTRYPOINT="org-kernel/kernel.py::consume_and_respond (hb_epoch=, or federation_cycle --hb-epoch)"
HB_EPOCH_CONFLICT="HB_EPOCH_CONFLICT"

def _pending_epoch(frame:Any, code:str, detail:str)->dict[str,Any]:
    """A non-terminal six-field refusal: nothing written, no marker, offered again next cycle."""
    return {"status":"PENDING","disposition":"FAIL_CLOSED","failure_code":code,"terminal":False,
            "failed_predicate":HB_EPOCH_PREDICATE,"detail":detail,
            "required_evidence_or_repair":"a consume cycle that supplies hb_epoch (federation_cycle --hb-epoch)",
            "retry_entrypoint":CYCLE_EPOCH_RETRY_ENTRYPOINT,"owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
            "next_attempt":"the next cycle that carries a supplied epoch consumes the frame; nothing was written",
            "packet_id":frame.get("packet_id") if isinstance(frame,dict) else None,
            "derived_from_clock":False,"consequence_committed":False}

RESPONSE_ID_COLLISION="RESPONSE_ID_COLLISION"

def _answered(organization:str, request:dict[str,Any], mesh_root:Path|None)->dict[str,Any]|None:
    """The answer this organization already published for this response id, if any.

    Keyed by the response id (communication_id:response:<organization>) and by
    request packet id; `same_request` says whether it answered this exact
    request (its recorded request_sha256, or, for an answer recorded before
    that field, the same request packet id).
    """
    response_id=str((request.get("payload") or {}).get("communication_id"))+":response:"+organization_slug(organization)
    digest=sha(request)
    target=mesh_store(mesh_root)
    for key in target.list_prefix(node_store_module.MESH_FRAME_PREFIX):
        try:
            frame=_read_frame(target,key)
            if not frame or frame.get("origin_org")!=organization:
                continue
            answer=recover_packet(frame)
            body=(answer.get("payload") or {}).get("body") or {}
        except Exception:  # noqa: BLE001 -- an unreadable frame answers nothing
            continue
        if answer.get("packet_id")!=response_id and body.get("request_packet_id")!=request.get("packet_id"):
            continue
        recorded=body.get("request_sha256")
        same=(recorded==digest) if recorded is not None else body.get("request_packet_id")==request.get("packet_id")
        return {"frame":frame,"path":str(target.locator(key)),"already_published":True,"same_request":same}
    return None

FRAME_DISPATCH_IO_FAILED="FRAME_DISPATCH_IO_FAILED"
FRAME_DISPATCH_FAILED="FRAME_DISPATCH_FAILED"

def _dispatch_failure(frame:Any, exc:Exception)->dict[str,Any]:
    """A non-terminal six-field record of this node's own failure on a frame; it stays pending."""
    code=FRAME_DISPATCH_IO_FAILED if isinstance(exc,OSError) else FRAME_DISPATCH_FAILED
    return {"status":"PENDING","disposition":"FAIL_CLOSED","failure_code":code,"terminal":False,
            "failed_predicate":"FRAME_IS_RECORDED_AND_ANSWERED:"+type(exc).__name__,
            "detail":str(exc) or type(exc).__name__,
            "required_evidence_or_repair":"this node's own state or ledger write completes",
            "retry_entrypoint":"org-kernel/kernel.py::consume_and_respond (next pass)",
            "owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
            "next_attempt":"the next pass offers the frame again; the idempotent append completes it",
            "packet_id":frame.get("packet_id") if isinstance(frame,dict) else None,
            "consequence_committed":False}

def _quarantine_record(frame:Any, code:str, detail:str, *, failed_predicate:str=HB_EPOCH_PREDICATE)->dict[str,Any]:
    return {"status":"REFUSED","disposition":"FAIL_CLOSED","failure_code":FRAME_REFUSED_QUARANTINED,
            "terminal":True,"frame_failure_code":code,"failed_predicate":failed_predicate,"detail":detail,
            "required_evidence_or_repair":("the sender re-publishes the packet in a frame whose heartbeat_reference "
                                           "is SUPPLIED (digits >= 32, derived_from_clock false) or a verified CARRIED"),
            "retry_entrypoint":HB_EPOCH_RETRY_ENTRYPOINT,"owning_existing_goal":HB_EPOCH_OWNING_EXISTING_GOAL,
            "next_attempt":"a new frame; this one is quarantined and never offered again",
            "packet_id":frame.get("packet_id") if isinstance(frame,dict) else None,
            "derived_from_clock":False,"consequence_committed":False}

def _frame_epoch_failure(frame:Any)->tuple[str,str]|None:
    """supplied_epoch_failure of the frame's heartbeat_reference.epoch. No clock is read.

    Only the epoch is checked here; whether a frame derived from its sender's
    clock may cross stays where it is decided (dispatch, carrier_epoch).
    """
    ref=frame.get("heartbeat_reference") if isinstance(frame,dict) else None
    return supplied_epoch_failure(ref.get("epoch") if isinstance(ref,dict) else None)

def _frame_epoch(frame:Any)->int|None:
    """The frame's carrier epoch to stamp receipts with, else None. No clock is read.

    Only a SUPPLIED reference qualifies (the shared rule with the reference, so
    derived_from_clock must be exactly false): a frame its sender stamped from
    a clock is never forwarded as if supplied, and its receipts say clock.
    """
    ref=frame.get("heartbeat_reference") if isinstance(frame,dict) else None
    if not isinstance(ref,dict) or supplied_epoch_failure(ref.get("epoch"),ref) is not None:
        return None
    return int(str(ref["epoch"]))

def ingest_recorded(repo_root:Path, item:dict[str,Any], custody:dict[str,Any], registry:dict[str,Any], *,
                    mesh_root:Path|None=None, node_state:Any|None, epoch:int|None,
                    crossing_reference:dict[str,Any]|None=None)->tuple[dict[str,Any],dict[str,Any]|None]:
    """Ingest one frame and record its disposition, admitted or refused.

    A refusal used to leave the consuming pass by exception, recorded nowhere
    and stopping every frame behind it. A refusal of custody itself still
    raises: without it nothing can be recorded. A capability-address crossing
    still raises: its receiving operation records its own refusal at both levels.
    """
    # Without a supplied epoch nothing can be recorded, so nothing is ingested
    # either: the frame is refused six-field, unmarked, and no clock is read
    # to stand in for the epoch (WU-B13 slice g).
    if epoch is None:
        refusal=no_epoch_caller_refusal("org-kernel/kernel.py::ingest_recorded",
                                        retry_entrypoint="org-kernel/kernel.py::consume_and_respond")
        return {"status":"REFUSED","disposition":refusal["disposition"],
                "packet_id":item["frame"].get("packet_id"),
                **{key:refusal[key] for key in SIX_FIELDS}},None
    # A frame whose epoch fails the shared rule is not recovered here: ingest_frame
    # refuses it six-field (CarrierEpochRefusal).
    destination=(None if _frame_epoch_failure(item["frame"]) is not None
                 else (recover_packet(item["frame"]).get("destination") or {}).get("service"))
    service=next((svc for svc in registry["services"] if svc.get("service_id")==destination),None)
    try:
        result=ingest_frame(repo_root,item["frame"],mesh_root=mesh_root,node_state=node_state,
                            crossing_reference=crossing_reference)
    except ValueError as exc:
        reason=str(exc)
        if isinstance(exc,EndpointInputFault):
            raise
        if (any(marker in reason for marker in CUSTODY_REFUSALS)
                or (service or {}).get("boundary_role")==CAPABILITY_INGRESS_ROLE):
            raise
        actionable=getattr(exc,"record",None) if isinstance(getattr(exc,"record",None),dict) else None
        # The stored disposition is the returned one: a refusal that states its
        # own disposition is recorded and returned as that disposition.
        disposition=actionable["disposition"] if actionable else refusal_disposition(reason)
        recorded=record_refusal(custody,item,reason,disposition,service=service,epoch=epoch,actionable=actionable)
        refused={"status":"REFUSED","disposition":disposition,"failed_predicate":reason,
                 "packet_id":item["frame"].get("packet_id")}
        if actionable: refused.update({key:actionable[key] for key in SIX_FIELDS})
        return refused,recorded
    return result,record_crossing(custody,item,result,service=service,epoch=epoch)

def consume_and_respond(repo_root:Path, *, mesh_root:Path|None=None, node_state_root:Path|None=None,
                        repo_ledger_root:Path|None=None, org_ledger_root:Path|None=None,
                        seen:set[str]|None=None, now_ns:int|None=None,
                        hb_epoch:Any=None)->list[dict[str,Any]]:
    """Consume frames addressed to this organization, answer them, and mark them seen.

    `hb_epoch` is the cycle's own supplied epoch. Invalid, nothing is consumed
    (SuppliedEpochRefused, whatever the frames). Supplied, every receipt and
    answer of the cycle is stamped with it and a frame's SUPPLIED epoch is
    provenance only; a frame whose SUPPLIED epoch differs is HB_EPOCH_CONFLICT
    and stays pending. Without it a frame's SUPPLIED epoch is used, and a frame
    that lends none (CLOCK) is refused HB_EPOCH_NOT_SUPPLIED and stays pending,
    with nothing written, for the next cycle that carries an epoch. `now_ns`
    no longer stamps anything.

    Consumption markers and work intake are this node's own state, written to
    the `node_state_root` its materializer supplied -- never into `repo_root`,
    which is the organization's source and is only read. Markers keep their
    key (`federation/seen.d/<sha256(frame_name)>.json`) and record the frame's
    name, so dedup identity is unchanged; a materializer that supplies
    `<checkout>/resident-runtime` as node state keeps markers written there
    before this.

    Every crossing is recorded on the repository and organization ledgers at
    the `repo_ledger_root` and `org_ledger_root` its materializer supplied,
    before its answer is published or its frame marked; without both nothing
    is consumed. A refused crossing is recorded too: DENY is marked, while
    FAIL_CLOSED is left unmarked and offered again on the next pass.
    """
    cycle_epoch=(None if hb_epoch is None else
                 int(supplied_hb_reference(hb_epoch,retry_entrypoint=CYCLE_EPOCH_RETRY_ENTRYPOINT)["epoch"]))
    node_state=addressed_node_state_store(node_state_root)
    custody=crossing_custody(repo_root,repo_ledger_root=repo_ledger_root,org_ledger_root=org_ledger_root)
    registry=load_registry(repo_root)
    organization=registry["organization"]
    durable_seen=federation_seen_frame_names(repo_root,store=node_state)
    effective_seen=set(seen or set())|durable_seen
    out=[]
    for item in scan_addressed_frames(organization,root=mesh_root,seen=effective_seen,include_unreadable=True):
        if item.get("scan_failure") is not None:
            # A file that cannot be read as a frame is quarantined by its name.
            refused=_ingest_failure_quarantine({},item["scan_failure"])
            marker=mark_federation_frame_seen(repo_root,item["path"],{},refused,store=node_state)
            out.append({"path":item["path"],"result":refused,"response_publication":None,
                        "organization_record":None,"seen_marker":str(marker)})
            continue
        # An answer is stamped with the epoch of the frame it answers, checked
        # by the shared rule. Consuming the same frame again then builds the
        # same answer frame, and publishing it is a write-once no-op rather
        # than a second answer stamped by whatever clock this pass read. A
        # frame whose epoch fails the rule is refused six-field by ingest_frame
        # before recovery, and that refusal is recorded below.
        # The guard is total: whatever this one frame raises, it is quarantined
        # and the loop continues (B-P36o, F-TYPE).
        try:
            frame_epoch=_frame_epoch(item["frame"])
            quarantined=_frame_quarantine(item["frame"],custody,registry)
        except Exception as exc:  # noqa: BLE001 -- a frame defect is that frame's quarantine
            frame_epoch,quarantined=None,_ingest_failure_quarantine(item["frame"],exc)
        epoch=cycle_epoch if cycle_epoch is not None else frame_epoch
        if quarantined is None and (cycle_epoch is not None and frame_epoch is not None
                                    and frame_epoch!=cycle_epoch):
            out.append({"path":item["path"],"result":_pending_epoch(item["frame"],HB_EPOCH_CONFLICT,
                        "the cycle's supplied epoch "+str(cycle_epoch)+" differs from the frame's "+str(frame_epoch)),
                        "response_publication":None,"organization_record":None,"seen_marker":None})
            continue
        if quarantined is None and epoch is None:
            out.append({"path":item["path"],"result":_pending_epoch(item["frame"],HB_EPOCH_NOT_SUPPLIED,
                        "the frame lends no epoch (CLOCK) and the cycle supplies none; nothing is stamped"),
                        "response_publication":None,"organization_record":None,"seen_marker":None})
            continue
        crossing_reference=hb_reference(epoch=epoch) if cycle_epoch is not None else None
        if quarantined is None:
            # Any error the frame itself causes -- recovery, integrity, its
            # heartbeat reference, a six-field carrier refusal -- quarantines it
            # rather than stopping the frames behind it (B-P36o). A failure of
            # this node's own ledgers still raises and leaves the frame
            # unmarked, so the next pass completes it.
            try:
                request=recover_packet(item["frame"])
            except Exception as exc:  # noqa: BLE001 -- a frame that cannot be recovered is quarantined
                request,quarantined=None,_ingest_failure_quarantine(item["frame"],exc)
            if (request is not None
                    and (request.get("payload") or {}).get("message_class") in RESPONDED_REQUEST_CLASSES):
                # A different request under a response id already answered is
                # refused before it is consumed; it is never handed that answer.
                prior=_answered(organization,request,mesh_root)
                if prior is not None and not prior["same_request"]:
                    quarantined=_quarantine_record(
                        item["frame"],RESPONSE_ID_COLLISION,
                        "response id "+str(prior["frame"].get("packet_id"))+" already answers another request",
                        failed_predicate="ONE_RESPONSE_ID_ANSWERS_ONE_REQUEST")
        if quarantined is None:
            # Recorded before anything leaves this node: no answer is published
            # and no consumption marker written for a crossing the organization
            # has not recorded. A failed append leaves the frame unmarked, so the
            # next pass offers it again and the idempotent append completes it.
            try:
                result,recorded=ingest_recorded(repo_root,item,custody,registry,mesh_root=mesh_root,
                                                node_state=node_state,epoch=epoch,
                                                crossing_reference=crossing_reference)
            except (CarrierEpochRefusal,EndpointInputFault) as exc:
                quarantined=_ingest_failure_quarantine(item["frame"],exc)
            except Exception as exc:  # noqa: BLE001 -- this node's own failure: the frame stays pending
                if any(marker in str(exc) for marker in CUSTODY_REFUSALS):
                    raise
                # Not terminal: no marker, nothing answered; the next pass offers
                # the frame again and the idempotent append completes it.
                out.append({"path":item["path"],"result":_dispatch_failure(item["frame"],exc),
                            "response_publication":None,"organization_record":None,"seen_marker":None})
                continue
        if quarantined is not None:
            # Terminal: nothing is recorded or answered, no clock is read, and the
            # marker keeps the frame from being offered again (B-P36j).
            marker=mark_federation_frame_seen(repo_root,item["path"],item["frame"],quarantined,store=node_state)
            out.append({"path":item["path"],"result":quarantined,"response_publication":None,
                        "organization_record":None,"seen_marker":str(marker)})
            continue
        if result.get("status")=="REFUSED" and result["disposition"]!="DENY":
            # FAIL_CLOSED: recorded, not marked, offered again on the next pass.
            out.append({"path":item["path"],"result":result,"response_publication":None,
                        "organization_record":recorded,"seen_marker":None})
            continue
        packet=recover_packet(item["frame"])
        payload=packet.get("payload") or {}
        message_class=payload.get("message_class")
        response_publication=None
        try:
            if result.get("status")=="CONSUMED" and message_class in RESPONDED_REQUEST_CLASSES:
                # One answer per request: a pass that published and then failed to
                # mark the frame does not publish a second one (F-REPUB).
                response_publication=_answered(organization,packet,mesh_root)
                if response_publication is None:
                    response=build_control_response(packet,result["execution_result"])
                    response_publication=publish_packet(response,root=mesh_root,epoch=epoch)
            marker=mark_federation_frame_seen(repo_root,item["path"],item["frame"],result,store=node_state)
        except Exception as exc:  # noqa: BLE001 -- this node's own write failed: the frame stays pending
            out.append({"path":item["path"],"result":_dispatch_failure(item["frame"],exc),
                        "response_publication":response_publication,"organization_record":recorded,
                        "seen_marker":None})
            continue
        out.append({"path":item["path"],"result":result,"response_publication":response_publication,
                    "organization_record":recorded,"seen_marker":str(marker)})
    return out

def collect_ecosystem_responses(origin_org:str, communication_id:str, *, mesh_root:Path|None=None)->dict[str,Any]:
    responses=[]
    for item in scan_addressed_frames(origin_org,root=mesh_root):
        packet=recover_packet(item["frame"])
        payload=packet.get("payload") or {}
        if payload.get("communication_id")!=communication_id:
            continue
        if payload.get("message_class") not in {
            "ecosystem.monitor.response","ecosystem.work.ack","ecosystem.communication.ack"}:
            continue
        body=payload.get("body") or {}
        responses.append({
          "organization":body.get("responding_organization") or packet["origin"]["org"],
          "message_class":payload.get("message_class"),
          "request_packet_id":body.get("request_packet_id"),
          "application_result":body.get("application_result"),
          "receipt_terminal":body.get("receipt_terminal"),
          "response_packet_id":packet["packet_id"],
          "frame_sha256":item["frame"].get("frame_sha256")
        })
    dedup={}
    for row in responses:
        dedup[row["organization"]]=row
    rows=[dedup[k] for k in sorted(dedup)]
    return {
      "communication_id":communication_id,
      "response_count":len(rows),
      "organizations":rows
    }

def publish_ecosystem_from_directory(repo_root:Path, *, standing:dict[str,Any], message_class:str, subject:str, body:dict[str,Any],
                                     requested_action:str|None=None, authority_effect:str="NONE",
                                     communication_id:str|None=None, mesh_root:Path|None=None,
                                     now_ns:int|None=None)->dict[str,Any]:
    registry=load_registry(repo_root)
    directory=load_federation_directory(repo_root)
    organizations=[row["organization"] for row in directory["organizations"]]
    origin=registry["organization"]
    return publish_ecosystem_message(
      origin_org=origin,
      origin_service=organization_slug(origin)+".org-control",
      organizations=organizations,
      standing=standing,
      message_class=message_class,
      subject=subject,
      body=body,
      requested_action=requested_action,
      authority_effect=authority_effect,
      communication_id=communication_id,
      root=mesh_root,
      now_ns=now_ns
    )


# --- Federation replay/dedup v1.3.1 additions ---
def federation_seen_frame_names(repo_root:Path, *, store:Any|None=None)->set[str]:
    """Which frames this node has already consumed.

    The marker records the frame's name rather than its key, so markers written
    before state was addressed keep deduplicating the same frames.
    """
    target=store or node_state_store(repo_root)
    names=set()
    for key in target.list_prefix(node_store_module.NODE_SEEN_PREFIX):
        try:
            value=target.get(key)
        except ValueError:
            continue
        if isinstance(value,dict) and isinstance(value.get("frame_name"),str):
            names.add(value["frame_name"])
    return names

def mark_federation_frame_seen(repo_root:Path, frame_path:str, frame:dict[str,Any], result:dict[str,Any],
                               *, store:Any|None=None)->Path:
    """Record that this node consumed a frame, once and atomically.

    A quarantined frame's marker also carries its six-field refusal, so the
    refusal is terminal and the frame is never offered again (B-P36j).
    """
    target=store or node_state_store(repo_root)
    frame_name=node_store_module.frame_name(str(frame_path))
    marker={
      "schema_version":"stegverse.federation-frame-consumption.v1",
      "frame_name":frame_name,
      "frame_sha256":frame.get("frame_sha256"),
      "packet_id":frame.get("packet_id"),
      "destination_org":frame.get("destination_org"),
      "status":result.get("status"),
      "authority_effect":"NONE_CARRIER_ONLY"
    }
    if result.get("failure_code")==FRAME_REFUSED_QUARANTINED:
        marker.update({key:result[key] for key in ("disposition","frame_failure_code",*SIX_FIELDS)})
    key=node_store_module.seen_key(frame_name)
    try:
        target.put_once(key,marker)
    except node_store_module.WriteOnceCollision:
        raise ValueError("federation_seen_marker_collision")
    return Path(target.locator(key))

# --- Resident cycle records, addressed rather than located ---
def resolve_node_state_root(root:Path|str|None)->tuple[Path,str]:
    """Return the node-state location supplied by the materializer."""
    if root is None:
        raise ValueError("node_state_location_required_from_materializer")
    return Path(root).expanduser().resolve(), node_store_module.SUPPLIED

def addressed_node_state_store(root:Path|str|None=None, env:dict[str,str]|None=None)->Any:
    """This node's state at the location supplied by its materializer."""
    if env is not None:
        raise ValueError("host_environment_node_state_binding_forbidden")
    resolved,provenance=resolve_node_state_root(root)
    return PosixStateStore(resolved, provenance=provenance)

def record_federation_cycle(receipt:dict[str,Any], *, root:Path|None=None,
                            store:Any|None=None, env:dict[str,str]|None=None)->Path:
    """Record one resident cycle in this node's own supplied state, addressed by what it reported."""
    target=store or addressed_node_state_store(root,env)
    key=node_store_module.cycle_key(receipt)
    target.put_once(key,receipt)
    return Path(target.locator(key))

def federation_cycles(*, root:Path|None=None, store:Any|None=None,
                      env:dict[str,str]|None=None)->list[dict[str,Any]]:
    """Every cycle this node recorded, in reproducible key order."""
    target=store or addressed_node_state_store(root,env)
    out=[]
    for key in target.list_prefix(node_store_module.NODE_CYCLE_PREFIX):
        value=target.get(key)
        if isinstance(value,dict):
            out.append(value)
    return out
