#!/usr/bin/env python3
"""Validate Publisher return transport and dispatch the verified next-owner transition.

The existing reverse InTr carrier is shared by ordinary KV Publisher returns and
MIR returns addressed to StegVerse-SDK. Owner selection is already performed by
the verified Publisher transition; this consumer preserves that selection and
never grants transport, credential, governance, publication, or egress authority.
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys
from pathlib import Path
from typing import Any, Mapping

ROOT=Path(__file__).resolve().parents[1]
REQUEST_DIR=Path("intr-materialization")
INGRESS_DIR=Path("receipts/sovereign-network/kv-publisher-return-ingress")
PAYLOAD_DIR=Path("intr-payloads/kv-publisher-return")
RECEIPT_DIR=Path("receipts/sovereign-host/kv-publisher-return-import")
SDK_RECEIPT_DIR=Path("receipts/sovereign-host/sdk-publisher-return-materialization")
SDK_BINDING_DIR=Path("sdk-publisher-return-bindings")
DESTINATION={"boundary":"KV","subsystem":"KnowledgeVault:DocumentImport"}
KV_DOWNSTREAM_OWNER="StegVerse-Labs/continuity-vault-kit"
SDK_DOWNSTREAM_OWNER="StegVerse-org/StegVerse-SDK"
RETURN_SCHEMA="stegverse.publisher.artifact-return/v1"
MIR_ROUNDTRIP_BINDING_PROFILE="stegverse.publisher.mir-roundtrip-binding/v1"
SDK_COMPLETION_CAPSULE_PROFILE="stegverse.sdk.downstream-completion-capsule/v1"
HOSTED_ENV=("GITHUB_ACTIONS","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
CREDENTIAL_ENV=("GITHUB_TOKEN","GH_TOKEN","STEGVERSE_GITHUB_TOKEN","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN")
POST_SDK_FALSE_FLAGS=("final_stegverse_side_egress_transition_observed","interlock_intr_egress_observed","far_side_transition_observed","authentic_external_mir_endpoint_substitution_observed","communication_complete")
MIR_RTC008_INGRESS_ENV="STEGVERSE_UNIVERSAL_INTR_INGRESS_URL"
MIR_RTC008_AUTH_ENV="STEGVERSE_TVC_RELAY_AUTHORIZATION_ID"
MIR_RTC008_RECEIPT_SCHEMA="stegverse.mir-southbound-intr-materialization-ingress/v1"
# A failed consumption is a typed FAIL_CLOSED on the append of its own diagnostic,
# not a passive "unknown" first failed transition (StegVerse-Labs/.github#3012
# K2), matching CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001
# publisher_return_failure_observation.actual_first_failed_transition. The
# upstream *_observed fields stay UNKNOWN as typed evidence of what this
# diagnostic cannot reconstruct; they assert no RTC006-RTC009 outcome.
FAILURE_APPEND_TRANSITION="PUBLISHER_RETURN_CONSUMPTION_FAILURE_OBSERVATION"
FAILURE_APPEND_PREDICATE="ORGANIZATION_RECEIPT_APPENDED_UNDER_LOCK:"+FAILURE_APPEND_TRANSITION
FAILURE_RETRY_ENTRYPOINT="scripts/consume_kv_publisher_return_materialization_request.py"

def _failure_disposition(materialization_id:str)->dict[str,Any]:
    return {
        "disposition":"FAIL_CLOSED",
        "consequence_committed":False,
        "failure_code":"ORGANIZATION_RECEIPT_NOT_APPENDED",
        "failed_predicate":FAILURE_APPEND_PREDICATE,
        "satisfying_edge":"the owning lane's manifest-directed append of "+FAILURE_APPEND_TRANSITION+" to the Organization ledger root under ORGANIZATION_LEDGER_LOCK, read back by resident-runtime/organization_batch_custody.py::verified_organization_receipt",
        "required_evidence_or_repair":"Repair the recorded failure_class/reason_code and re-invoke the same materialization; the verified Organization receipt of the diagnostic append satisfies "+FAILURE_APPEND_PREDICATE+".",
        "retry_entrypoint":FAILURE_RETRY_ENTRYPOINT,
        "owning_existing_goal":"CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001",
        "next_attempt":"NEXT_MANIFEST_DIRECTED_ATTEMPT_OF_"+FAILURE_APPEND_TRANSITION,
        "evidence_refs":[f"MATERIALIZATION_REQUEST:{REQUEST_DIR.as_posix()}/{materialization_id}.json"],
        "first_failed_governed_transition":FAILURE_APPEND_PREDICATE,
    }

class _PublisherReturnOwnerMatcher:
    """Compatibility matcher used by the existing universal-ingress discriminator.

    It lets the already-installed Publisher-return ingress recognize both verified
    next-owner states without introducing a second ingress endpoint or transport
    plane. Request validation below still binds the exact owner string.
    """
    allowed=frozenset({KV_DOWNSTREAM_OWNER,SDK_DOWNSTREAM_OWNER})
    def __eq__(self,other:object)->bool:return isinstance(other,str) and other in self.allowed
    def __ne__(self,other:object)->bool:return not self.__eq__(other)
    def __repr__(self)->str:return "PublisherReturnOwnerMatcher(KV|SDK)"

DOWNSTREAM_OWNER=_PublisherReturnOwnerMatcher()

class KVPublisherReturnError(ValueError): pass

def canonical(value:Any)->bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")
def sha(value:Any)->str:
    raw=value if isinstance(value,bytes) else canonical(value)
    return "sha256:"+hashlib.sha256(raw).hexdigest()
def load(path:Path)->Any:
    return json.loads(path.read_text(encoding="utf-8"))
def scrubbed_env(env=None):
    child=dict(os.environ if env is None else env)
    for key in HOSTED_ENV+CREDENTIAL_ENV: child.pop(key,None)
    child["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC"
    child["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"
    return child
def source_root(env_name:str,repo_name:str,required:str)->Path|None:
    candidates=[]
    if os.environ.get(env_name): candidates.append(Path(os.environ[env_name]).expanduser())
    try:
        roots=json.loads(os.environ.get("STEGVERSE_REPO_ROOTS_JSON","") or "{}")
    except Exception:
        roots={}
    if isinstance(roots,dict):
        for key in (f"StegVerse-org/{repo_name}",f"StegVerse-Labs/{repo_name}",repo_name):
            value=roots.get(key)
            if isinstance(value,str) and value.strip():
                candidates.append(Path(value).expanduser())
    candidates += [ROOT.parent/repo_name,ROOT/repo_name,ROOT/"StegVerse-Labs"/repo_name,ROOT.parent.parent/repo_name]
    for item in candidates:
        resolved=item.resolve()
        if (resolved/required).is_file(): return resolved
    return None


class KVOrganizationReceiptRefused(KVPublisherReturnError):
    """A successor gate refused: the Organization receipt did not verify.

    Carries the typed DENY or FAIL_CLOSED refusal from the existing
    Organization ledger verifier; nothing is committed.
    """
    def __init__(self, message:str, refusal:Mapping[str,Any]):
        super().__init__(message+":"+str(refusal.get("disposition"))+":"+str(refusal.get("failed_predicate")))
        self.refusal=dict(refusal)


# Basis of each verified readback, keyed by the receipt digest it is a function of.
READBACK_CUSTODY_BASES:dict[str,str]={}


def _organization_receipt_gate(result:Any, *, transition_id:str, message:str, record_refusal:bool=False)->str:
    """Verified Organization receipt digest for this exact state receipt, else a typed refusal.

    The Organization ledger append is the transition's runtime reality.
    Master Records reconstruction fields are evidence only and never consulted.
    `record_refusal` is set where the gate sits inside the transition this
    consumer just attempted: the refusal is appended as its non-ALLOW record.
    """
    from importlib import import_module
    resident=str(ROOT/"resident-runtime")
    if resident not in sys.path:
        sys.path.insert(0,resident)
    custody=import_module("organization_batch_custody")
    try:
        row=custody.verified_organization_record(
            None,dict(result) if isinstance(result,Mapping) else result,expected_transition_id=transition_id)
    except custody.OrganizationReceiptRefused as exc:
        refusal=exc.refusal()
        if record_refusal:
            from canonical_state_transition_custody import record_organization_receipt_refusal
            refusal=record_organization_receipt_refusal(
                refusal,gated_transition_id=transition_id,
                state_receipt_sha256=result.get("receipt_sha256") if isinstance(result,Mapping) else None)
        raise KVOrganizationReceiptRefused(message,refusal) from exc
    # The readback is never custody authority; its basis is kept for the report.
    READBACK_CUSTODY_BASES[row["receipt_sha256"]]=custody.readback_custody_basis(row)
    return row["receipt_sha256"]


def require_organization_recorded_predecessor(predecessor:Any, *, predecessor_transition_id:str, successor_transition_id:str)->str:
    """The predecessor transition is real when its verified Organization receipt exists.

    Master Records reconstruction of the predecessor is optional evidence and
    never a precondition for the successor.
    """
    return _organization_receipt_gate(predecessor,transition_id=predecessor_transition_id,
                                      message=successor_transition_id+" predecessor Organization record refused")

def validate_request(request:dict[str,Any])->None:
    expected={
      "schema":"stegverse.universal-intr-materialization-request/v1",
      "state":"QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
      "transport_schema":"stegverse.universal-intr-transport/v1",
      "transport_protocol":"InTr",
      "destination":DESTINATION,
      "event_triggered":True,
      "always_on_receiver_required":False,
      "second_user_device_required":False,
      "receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
      "exact_packet_transport_retry_allowed":True,
      "blind_consequence_retry_allowed":False,
      "interlock_required":True,
      "request_grants_execution_authority":False,
      "claim_or_fence_minted":False,
      "transport_grants_execution_authority":False,
      "credential_authority":"TV/TVC",
      "github_token_runtime_authority":"NONE",
      "authority_transfer":False,
      "authority_effect":"NONE_REQUEST_ONLY",
    }
    for key,value in expected.items():
        if request.get(key)!=value: raise KVPublisherReturnError("materialization_"+key+"_mismatch")
    owner=request.get("downstream_owner_ref")
    if owner not in {KV_DOWNSTREAM_OWNER,SDK_DOWNSTREAM_OWNER}:
        raise KVPublisherReturnError("materialization_downstream_owner_ref_mismatch")
    if request.get("boundary_path")!=["STEGOS_ECOSYSTEM","DEVICE_SYSTEM","KV"]:
        raise KVPublisherReturnError("materialization_boundary_path_invalid")
    body=dict(request); claimed=body.pop("request_hash",None)
    if claimed!=sha(body): raise KVPublisherReturnError("materialization_request_hash_mismatch")

def _verify_common_return_transport(runtime:Path,materialization_id:str,request:dict[str,Any])->tuple[bytes,dict[str,Any],list[dict[str,Any]],str]:
    ingress=load(runtime/INGRESS_DIR/f"{materialization_id}.json")
    if ingress.get("schema")!="stegverse.kv-publisher-return-materialization-ingress/v1" or ingress.get("state")!="INGRESS_ADMITTED":
        raise KVPublisherReturnError("return_ingress_not_admitted")
    for key in ("materialization_id","request_hash","transport_intent_hash","payload_hash","operation_id","packet_id"):
        if ingress.get(key)!=request.get(key): raise KVPublisherReturnError("return_ingress_binding_mismatch:"+key)
    raw_path=runtime/PAYLOAD_DIR/f"{materialization_id}.bin"
    intent_path=runtime/PAYLOAD_DIR/f"{materialization_id}.intent.json"
    receipts_path=runtime/PAYLOAD_DIR/f"{materialization_id}.receipts.json"
    if not raw_path.is_file() or not intent_path.is_file() or not receipts_path.is_file():
        raise KVPublisherReturnError("return_transport_sidecars_missing")
    raw=raw_path.read_bytes(); intent=load(intent_path); receipts=load(receipts_path)
    if sha(raw)!=request["payload_hash"]: raise KVPublisherReturnError("return_payload_hash_mismatch")
    if sha(intent)!=request["transport_intent_hash"]: raise KVPublisherReturnError("return_intent_hash_mismatch")
    if intent.get("packet_id")!=request["packet_id"] or intent.get("operation_id")!=request["operation_id"]:
        raise KVPublisherReturnError("return_intent_identity_mismatch")
    if intent.get("source")!={"boundary":"STEGOS_ECOSYSTEM","subsystem":"Publisher:Export"} or intent.get("destination")!=DESTINATION:
        raise KVPublisherReturnError("return_intent_endpoint_mismatch")
    if intent.get("boundary_path")!=["STEGOS_ECOSYSTEM","DEVICE_SYSTEM","KV"]:
        raise KVPublisherReturnError("return_intent_path_mismatch")
    if not isinstance(receipts,list) or len(receipts)!=2:
        raise KVPublisherReturnError("return_receipt_chain_incomplete")
    stegos=source_root("STEGVERSE_STEGOS_ROOT","StegOS","stegos/universal_intr_transport.py")
    if stegos is None: raise KVPublisherReturnError("local_stegos_source_materialization_required")
    if str(stegos) not in sys.path: sys.path.insert(0,str(stegos))
    from stegos.universal_intr_transport import validate_transport_intent, validate_receipt_chain
    validate_transport_intent(intent); validate_receipt_chain(intent,receipts)
    terminal=receipts[-1].get("receipt_hash")
    if not isinstance(terminal,str) or not terminal: raise KVPublisherReturnError("return_transport_terminal_receipt_missing")
    return raw,intent,receipts,terminal

def extract_sdk_materialization_inputs(returned:dict[str,Any])->tuple[dict[str,Any],str,dict[str,Any]]:
    """Recover only continuity inputs already carried by the verified MIR return."""
    if returned.get("schema")!=RETURN_SCHEMA: raise KVPublisherReturnError("Publisher return schema mismatch")
    binding=returned.get("roundtrip_binding")
    if not isinstance(binding,dict) or binding.get("profile")!=MIR_ROUNDTRIP_BINDING_PROFILE:
        raise KVPublisherReturnError("SDK-owned return requires MIR roundtrip binding")
    if binding.get("publisher_transition_observed") is not True:
        raise KVPublisherReturnError("Publisher MIR transition not observed")
    if binding.get("sdk_return_binding_observed") is not False:
        raise KVPublisherReturnError("SDK return binding already promoted")
    for field in POST_SDK_FALSE_FLAGS:
        if binding.get(field) is not False:
            raise KVPublisherReturnError("downstream predicate prematurely promoted:"+field)
    if binding.get("authority_effect")!="NONE": raise KVPublisherReturnError("MIR binding authority effect invalid")
    sdk_state=binding.get("sdk_processor_state")
    if not isinstance(sdk_state,dict) or sdk_state.get("state")!="SDK_MANIFEST_SELECTED_PROCESSING_EXECUTED" or sdk_state.get("processor_result_observed") is not True:
        raise KVPublisherReturnError("carried SDK processor state invalid")
    manifest=sdk_state.get("manifest")
    if not isinstance(manifest,dict): raise KVPublisherReturnError("original admitted manifest missing from SDK processor state")
    processor_result=sdk_state.get("processor_result")
    if not isinstance(processor_result,dict): raise KVPublisherReturnError("original SDK processor result missing")
    receipt_id=str(processor_result.get("manifest_receipt_id") or "").strip()
    if not receipt_id: raise KVPublisherReturnError("original manifest_receipt_id missing")
    capsule=binding.get("downstream_completion_capsule")
    if not isinstance(capsule,dict) or capsule.get("profile")!=SDK_COMPLETION_CAPSULE_PROFILE:
        raise KVPublisherReturnError("original downstream completion capsule missing")
    return manifest,receipt_id,capsule

def _record_sdk_return_binding_custody(
    runtime:Path,
    materialization_id:str,
    request:dict[str,Any],
    terminal:str,
    output_path:Path,
    materialization:dict[str,Any],
)->dict[str,Any]:
    try:
        binding=load(output_path)
    except Exception as exc:
        raise KVPublisherReturnError("SDK return binding unavailable for Master Records organization record") from exc
    expected_binding_hash=str(materialization.get("output_sha256") or "")
    actual_binding_hash=sha(binding)
    if not expected_binding_hash or actual_binding_hash!=expected_binding_hash:
        raise KVPublisherReturnError("SDK return binding custody hash mismatch")
    transition_id="RTC-SDK-RETURN-006"
    materialization_hash=sha(materialization)
    required_evidence=[
      {
        "evidence_id":"sdk-publisher-return-binding",
        "evidence_type":"SDK_PUBLISHER_RETURN_BINDING",
        "origin_transition_id":transition_id,
        "encoding":"canonical-json",
        "sha256":actual_binding_hash.split(":",1)[1],
        "content":binding,
      },
      {
        "evidence_id":"sdk-publisher-return-materialization-receipt",
        "evidence_type":"SDK_PUBLISHER_RETURN_MATERIALIZATION_RECEIPT",
        "origin_transition_id":transition_id,
        "encoding":"canonical-json",
        "sha256":materialization_hash.split(":",1)[1],
        "content":materialization,
      },
    ]
    workers_root=ROOT/"workers"
    if str(workers_root) not in sys.path:
        sys.path.insert(0,str(workers_root))
    from canonical_state_transition_custody import (
        build_state_receipt,
        require_predecessor_master_records_organization_record,
        submit_state_receipt,
    )
    predecessor_receipt_sha256=request.get("predecessor_master_records_receipt_sha256")
    prior_ref,predecessor_evidence=require_predecessor_master_records_organization_record(
        predecessor_receipt_sha256,
        successor_transition_id=transition_id,
    )
    if prior_ref is None:
        raise KVPublisherReturnError("RTC-SDK-RETURN-006 canonical predecessor Master Records organization record required")
    required_evidence=list(predecessor_evidence)+required_evidence
    state_receipt=build_state_receipt(
      transition_id=transition_id,
      transition_sequence=1,
      subject_or_correlation_id=str(request.get("operation_id") or materialization_id),
      transition_outcome="EXECUTED",
      prior_state_ref_or_hash=prior_ref,
      resulting_state_ref_or_hash=actual_binding_hash,
      governance_decision_ref_where_applicable=None,
      transition_evidence={
        "state":"SDK_RETURN_BINDING_MATERIALIZED_READY_FOR_FINAL_STEGVERSE_EGRESS",
        "materialization_id":materialization_id,
        "request_hash":request.get("request_hash"),
        "return_transport_terminal_receipt_hash":terminal,
        "return_downstream_owner_ref":SDK_DOWNSTREAM_OWNER,
        "sdk_return_binding_ref":str(output_path.relative_to(runtime)),
        "sdk_return_binding_sha256":actual_binding_hash,
        "authority_effect":"NONE",
      },
      required_evidence_manifest=required_evidence,
      proof_scope="RTC_SDK_RETURN_006_ONLY",
      proof_ceiling="ORGANIZATION_RECORDED_SDK_RETURN_BINDING_ONLY",
    )
    mr=submit_state_receipt(state_receipt)
    # Organization ledger record is the transition's reality; Master Records
    # reconstruction fields are evidence only and never gate it.
    organization_receipt_sha256=_organization_receipt_gate(
        mr,transition_id=transition_id,message="SDK return binding Organization record not recorded",
        record_refusal=True)
    return {
      "state":mr.get("state"),
      "organization_receipt_sha256":organization_receipt_sha256,
      "organization_readback_custody_basis":READBACK_CUSTODY_BASES.get(organization_receipt_sha256),
      "reconstruction_status":mr.get("reconstruction_status"),
      "required_evidence_validation_status":mr.get("required_evidence_validation_status"),
      "receipt_sha256":mr.get("receipt_sha256"),
      "reconstructed_receipt_sha256":mr.get("reconstructed_receipt_sha256"),
      "required_evidence_count":mr.get("required_evidence_count"),
      "authority_effect":"NONE_CUSTODY_RECONSTRUCTION_ONLY",
    }

def _submit_rtc008_materialization(request:dict[str,Any], *, runtime_root:Path, env:Mapping[str,str]|None=None, admit=None)->dict[str,Any]:
    """Admit the exact prepared RTC008 request through the existing InTr ingress.

    The existing write-once ingress admission (admit_mir_southbound) persists
    the exact request into the durable queue and returns its admission receipt.
    It is invoked in-process on this node's runtime root: no listener, socket,
    timeout or receiver liveness is a predicate of the transition
    (DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION). Downstream far-side
    materialization is a later, separately manifested transition. This consumes
    an already-issued TVC relay authorization identifier. It does not create a
    credential, listener, runtime, scheduler, dispatcher, custody store, or
    transition authority.
    """
    values=dict(os.environ if env is None else env)
    authorization_id=str(values.get(MIR_RTC008_AUTH_ENV) or "").strip()
    if not authorization_id:
        raise KVPublisherReturnError("RTC008 existing TVC relay authorization missing")
    if admit is None:
        if str(ROOT) not in sys.path:
            sys.path.insert(0,str(ROOT))
        from workers.universal_intr_profiled_ingress import admit_mir_southbound as admit
    raw=canonical(request)
    headers={
      "Content-Type":"application/json",
      "X-StegVerse-Transport":"InTr",
      "X-StegVerse-Transport-Origin":"TVC_RELAY_EGRESS",
      "X-StegVerse-Authorization-Id":authorization_id,
      "X-StegVerse-Payload-SHA256":hashlib.sha256(raw).hexdigest(),
    }
    try:
        admitted=admit(runtime_root=Path(runtime_root),body=raw,headers=headers)
    except ValueError as exc:
        raise KVPublisherReturnError("RTC008 InTr admission refused:"+str(exc)) from exc
    if not isinstance(admitted,dict):
        raise KVPublisherReturnError("RTC008 ingress response object required")
    expected={
      "schema":MIR_RTC008_RECEIPT_SCHEMA,
      "state":"INGRESS_ADMITTED",
      "materialization_id":request.get("materialization_id"),
      "request_hash":request.get("request_hash"),
      "transport_intent_hash":request.get("transport_intent_hash"),
      "payload_hash":request.get("payload_hash"),
      "operation_id":request.get("operation_id"),
      "packet_id":request.get("packet_id"),
      "transport_origin":"TVC_RELAY_EGRESS",
      "transport_authorization_id":authorization_id,
      "rtc008_evidence_complete":True,
      "write_once_persisted":True,
      "runtime_execution_attempted":False,
      "far_side_transition_observed":False,
      "caller_consequence_observed":False,
    }
    for key,value in expected.items():
        if admitted.get(key)!=value:
            raise KVPublisherReturnError("RTC008 admission mismatch:"+key)
    digest=admitted.get("intr_admission_receipt_sha256")
    if not isinstance(digest,str) or len(digest)!=64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise KVPublisherReturnError("RTC008 exact ingress admission digest missing")
    # Any master_records_* fields in the admission are reconstruction evidence
    # only; InTr admission is the transition authority and is not gated on them.
    return admitted


def rtc008_ingress_projection(admitted:Mapping[str,Any])->dict[str,Any]:
    """What RTC008 establishes: INGRESS_ADMITTED into the existing write-once queue.

    The queued request is materialized later by a separately manifested
    transition; RTC008 downstream execution and RTC009 far-side consequence are
    never claimed here.
    """
    return {
      "rtc008_ingress_state":admitted["state"],
      "rtc008_request_hash":admitted["request_hash"],
      "rtc008_queue_ref":admitted["queue_ref"],
      "rtc008_write_once_persisted":admitted["write_once_persisted"],
      "rtc008_intr_admission_receipt_sha256":admitted["intr_admission_receipt_sha256"],
      "rtc008_downstream_execution_observed":False,
      "rtc009_far_side_transition_observed":False,
    }

def _prepare_rtc007_continuation(
    runtime:Path,
    materialization_id:str,
    request:dict[str,Any],
    output_path:Path,
    sdk_binding_sha256:str,
    rtc006_master_records:dict[str,Any],
)->dict[str,Any]:
    binding_bytes=output_path.read_bytes()
    if sha(binding_bytes)!=sdk_binding_sha256:
        raise KVPublisherReturnError("RTC-SDK-RETURN-006 exact binding changed before RTC-STEGVERSE-EGRESS-007")
    llm=source_root("STEGVERSE_LLM_ADAPTER_ROOT","LLM-adapter","llm_adapter/southbound_sdk_return.py")
    if llm is None:
        raise KVPublisherReturnError("local_LLM_adapter_source_materialization_required")
    if str(llm) not in sys.path: sys.path.insert(0,str(llm))
    from llm_adapter.southbound_sdk_return import prepare_sdk_return_for_intr, admit_intr_egress
    transition=prepare_sdk_return_for_intr(binding_bytes,transition_id="RTC-STEGVERSE-EGRESS-007")
    if transition.get("state")!="FINAL_STEGVERSE_SIDE_TRANSITION_PREPARED" or transition.get("final_stegverse_transition_surface_reached") is not True:
        raise KVPublisherReturnError("RTC-STEGVERSE-EGRESS-007 transition not prepared")
    handoff=transition.get("intr_handoff")
    if not isinstance(handoff,dict):
        raise KVPublisherReturnError("RTC-STEGVERSE-EGRESS-007 InTr handoff missing")

    workers_root=ROOT/"workers"
    if str(workers_root) not in sys.path: sys.path.insert(0,str(workers_root))
    from canonical_state_transition_custody import (
        build_state_receipt,
        require_predecessor_master_records_organization_record,
        submit_state_receipt,
    )
    prior_ref, predecessor_evidence = require_predecessor_master_records_organization_record(
        rtc006_master_records.get("receipt_sha256"),
        successor_transition_id="RTC-STEGVERSE-EGRESS-007",
    )
    if prior_ref is None:
        raise KVPublisherReturnError("RTC-STEGVERSE-EGRESS-007 canonical predecessor receipt required")
    # The predecessor is real once the Organization ledger recorded it; any
    # Master Records reconstruction in predecessor_evidence is evidence only.
    require_organization_recorded_predecessor(rtc006_master_records,predecessor_transition_id="RTC-SDK-RETURN-006",
                                              successor_transition_id="RTC-STEGVERSE-EGRESS-007")
    transition_hash=sha(transition)
    required_evidence=[
      *predecessor_evidence,
      {
        "evidence_id":"rtc007-southbound-final-transition",
        "evidence_type":"RTC_STEGVERSE_EGRESS_007_TRANSITION",
        "origin_transition_id":"RTC-STEGVERSE-EGRESS-007",
        "encoding":"canonical-json",
        "sha256":transition_hash.split(":",1)[1],
        "content":transition,
      },
      {
        "evidence_id":"rtc007-sdk-return-binding",
        "evidence_type":"SDK_PUBLISHER_RETURN_BINDING",
        "origin_transition_id":"RTC-STEGVERSE-EGRESS-007",
        "encoding":"canonical-json",
        "sha256":sdk_binding_sha256.split(":",1)[1],
        "content":load(output_path),
      },
    ]
    state_receipt=build_state_receipt(
      transition_id="RTC-STEGVERSE-EGRESS-007",
      transition_sequence=2,
      subject_or_correlation_id=str(request.get("operation_id") or materialization_id),
      transition_outcome="EXECUTED",
      prior_state_ref_or_hash=prior_ref,
      resulting_state_ref_or_hash=transition_hash,
      governance_decision_ref_where_applicable=None,
      transition_evidence={
        "state":transition.get("state"),
        "transition_surface":transition.get("transition_surface"),
        "destination_profile":transition.get("destination_profile"),
        "sdk_binding_sha256":transition.get("sdk_binding_sha256"),
        "authority_effect":"NONE",
      },
      required_evidence_manifest=required_evidence,
      proof_scope="RTC_STEGVERSE_EGRESS_007_ONLY",
      proof_ceiling="ORGANIZATION_RECORDED_FINAL_STEGVERSE_EGRESS_PREPARATION_ONLY",
    )
    mr=submit_state_receipt(state_receipt)
    # Organization ledger record is the transition's reality; Master Records
    # reconstruction fields are evidence only and never gate it.
    organization_receipt_sha256=_organization_receipt_gate(
        mr,transition_id="RTC-STEGVERSE-EGRESS-007",message="RTC-STEGVERSE-EGRESS-007 Organization record not recorded",
        record_refusal=True)

    stegos=source_root("STEGVERSE_STEGOS_ROOT","StegOS","stegos/mir_southbound_intr_consumer.py")
    if stegos is None:
        raise KVPublisherReturnError("local_StegOS_source_materialization_required_for_RTC008")
    if str(stegos) not in sys.path: sys.path.insert(0,str(stegos))
    from stegos.mir_southbound_intr_consumer import prepare_mir_southbound_materialization
    prepared=prepare_mir_southbound_materialization(
        handoff,
        payload_ref="runtime://"+str(output_path.relative_to(runtime)),
    )
    rtc008_request=dict(prepared["materialization_request"])
    rtc008_request.update({
      "predecessor_transition_id":"RTC-STEGVERSE-EGRESS-007",
      "predecessor_master_records_state":mr.get("state"),
      "predecessor_master_records_reconstruction_status":mr.get("reconstruction_status"),
      "predecessor_master_records_required_evidence_validation_status":mr.get("required_evidence_validation_status"),
      "predecessor_master_records_receipt_sha256":mr.get("receipt_sha256"),
      "predecessor_master_records_reconstructed_receipt_sha256":mr.get("reconstructed_receipt_sha256"),
      "predecessor_organization_receipt_sha256":organization_receipt_sha256,
    })
    # Claim reconstructed-digest equality only when a reconstruction exists.
    rtc008_request["predecessor_master_records_digest_equal"]=bool(
      rtc008_request["predecessor_master_records_reconstructed_receipt_sha256"]
      and rtc008_request["predecessor_master_records_receipt_sha256"]
      == rtc008_request["predecessor_master_records_reconstructed_receipt_sha256"]
    )
    rtc008_request.pop("request_hash",None)
    rtc008_request["request_hash"]=sha(rtc008_request)
    prepared={**prepared,"materialization_request":rtc008_request}
    rtc008=_submit_rtc008_materialization(rtc008_request,runtime_root=runtime)
    llm_admission=admit_intr_egress(
        transition,
        disposition="ALLOW",
        egress_receipt_hash=rtc008["intr_admission_receipt_sha256"],
        admitted_sdk_binding_sha256=handoff["sdk_binding_sha256"],
    )
    if llm_admission.get("state")!="EGRESS_ADMITTED" or llm_admission.get("sdk_binding_sha256")!=handoff["sdk_binding_sha256"] or llm_admission.get("egress_receipt_hash")!=rtc008["intr_admission_receipt_sha256"]:
        raise KVPublisherReturnError("RTC008 LLM Adapter canonical admission projection invalid")
    return {
      "rtc007_transition":transition,
      "rtc007_master_records":{
        "state":mr.get("state"),
        "organization_receipt_sha256":organization_receipt_sha256,
        "organization_readback_custody_basis":READBACK_CUSTODY_BASES.get(organization_receipt_sha256),
        "reconstruction_status":mr.get("reconstruction_status"),
        "required_evidence_validation_status":mr.get("required_evidence_validation_status"),
        "receipt_sha256":mr.get("receipt_sha256"),
        "reconstructed_receipt_sha256":mr.get("reconstructed_receipt_sha256"),
      },
      "rtc008_materialization_prepared":prepared,
      "rtc008_admission":rtc008,
      "rtc008_llm_adapter_admission":llm_admission,
      "rtc008_admission_observed":True,
      "rtc009_far_side_transition_observed":False,
      "caller_consequence_observed":False,
      "communication_complete":False,
      "authority_effect":"NONE_CONTINUATION_REQUEST_ONLY",
    }

def _consume_sdk_owner(runtime:Path,materialization_id:str,request:dict[str,Any],raw:bytes,terminal:str)->dict[str,Any]:
    try: returned=json.loads(raw.decode("utf-8"))
    except Exception as exc: raise KVPublisherReturnError("Publisher return JSON invalid") from exc
    manifest,manifest_receipt_id,capsule=extract_sdk_materialization_inputs(returned)
    sdk=source_root("STEGVERSE_SDK_ROOT","StegVerse-SDK","stegverse/publisher_return_materialization.py")
    if sdk is None: raise KVPublisherReturnError("local_StegVerse_SDK_source_materialization_required")
    if str(sdk) not in sys.path: sys.path.insert(0,str(sdk))
    from stegverse.publisher_return_materialization import materialize_publisher_return_binding
    output_path=runtime/SDK_BINDING_DIR/f"{materialization_id}.json"
    materialization=materialize_publisher_return_binding(
        manifest=manifest,
        manifest_receipt_id=manifest_receipt_id,
        publisher_return_bytes=raw,
        downstream_completion_capsule=capsule,
        output_path=output_path,
        overwrite=False,
    )
    if materialization.get("sdk_return_binding_observed") is not True:
        raise KVPublisherReturnError("SDK return binding materialization not observed")
    master_records=_record_sdk_return_binding_custody(
        runtime,materialization_id,request,terminal,output_path,materialization
    )
    continuation=_prepare_rtc007_continuation(
        runtime,materialization_id,request,output_path,materialization["output_sha256"],master_records
    )
    for field in ("final_stegverse_transition_observed","interlock_intr_egress_observed","far_side_transition_observed","authentic_external_mir_endpoint_substitution_observed","communication_complete"):
        if materialization.get(field) is not False:
            raise KVPublisherReturnError("SDK materialization promoted downstream predicate:"+field)
    out=runtime/SDK_RECEIPT_DIR; out.mkdir(parents=True,exist_ok=True)
    result={
      "schema":"stegverse.sdk-publisher-return-intr-materialization-consumption/v1",
      "state":"SDK_RETURN_BINDING_MATERIALIZED_READY_FOR_FINAL_STEGVERSE_EGRESS",
      "materialization_id":materialization_id,
      "request_hash":request["request_hash"],
      "return_transport_observed":True,
      "return_transport_terminal_receipt_hash":terminal,
      "return_downstream_owner_ref":SDK_DOWNSTREAM_OWNER,
      "manifest_receipt_id":manifest_receipt_id,
      "sdk_return_binding_ref":str(output_path.relative_to(runtime)),
      "sdk_return_binding_sha256":materialization["output_sha256"],
      "sdk_return_binding_schema":materialization["binding_schema"],
      "communication_state":materialization["communication_state"],
      "sdk_return_binding_observed":True,
      "master_records_state":master_records["state"],
      "master_records_reconstruction_status":master_records["reconstruction_status"],
      "master_records_required_evidence_validation_status":master_records["required_evidence_validation_status"],
      "master_records_receipt_sha256":master_records["receipt_sha256"],
      "master_records_reconstructed_receipt_sha256":master_records["reconstructed_receipt_sha256"],
      "master_records_required_evidence_count":master_records["required_evidence_count"],
      "rtc007_transition_sha256":sha(continuation["rtc007_transition"]),
      "rtc007_master_records_state":continuation["rtc007_master_records"]["state"],
      "rtc007_master_records_reconstruction_status":continuation["rtc007_master_records"]["reconstruction_status"],
      "rtc007_master_records_required_evidence_validation_status":continuation["rtc007_master_records"]["required_evidence_validation_status"],
      "rtc007_master_records_receipt_sha256":continuation["rtc007_master_records"]["receipt_sha256"],
      "rtc007_master_records_reconstructed_receipt_sha256":continuation["rtc007_master_records"]["reconstructed_receipt_sha256"],
      "rtc008_materialization_request":continuation["rtc008_materialization_prepared"]["materialization_request"],
      "rtc008_ingress_receipt":continuation["rtc008_admission"],
      "rtc008_llm_adapter_admission":continuation["rtc008_llm_adapter_admission"],
      "rtc008_llm_adapter_admission_sha256":sha(continuation["rtc008_llm_adapter_admission"]),
      **rtc008_ingress_projection(continuation["rtc008_admission"]),
      "final_stegverse_side_egress_transition_observed":True,
      "interlock_intr_egress_observed":True,
      "far_side_transition_observed":False,
      "return_record_durably_recorded":False,
      "final_allowed_transport_exit_transition_observed":False,
      "successful_data_transport_round_trip_identified":False,
      "authentic_external_mir_endpoint_substitution_observed":False,
      "communication_complete":False,
      "publication_authorized":False,
      "release_authorized":False,
      "execution_authorized":False,
      "credential_authority":"TV/TVC",
      "github_token_runtime_authority":"NONE",
      "authority_effect":"NONE",
    }
    receipt_path=out/f"{materialization_id}.json"; receipt_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    latest=out/"latest.json"; latest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result

def _consume_kv_owner(runtime:Path,materialization_id:str,request:dict[str,Any],raw:bytes,terminal:str)->dict[str,Any]:
    try: returned=json.loads(raw.decode("utf-8"))
    except Exception as exc: raise KVPublisherReturnError("Publisher return JSON invalid") from exc
    if returned.get("schema")!=RETURN_SCHEMA: raise KVPublisherReturnError("Publisher return schema mismatch")
    export_id=returned.get("source_export_id")
    if not isinstance(export_id,str) or not export_id: raise KVPublisherReturnError("source export id missing")
    bundle_root=Path(os.environ.get("STEGVERSE_KV_DOCUMENT_EXPORT_BUNDLE_ROOT",str(runtime/"private-kv-document-exports"))).expanduser().resolve()
    bundle_path=bundle_root/f"{export_id}.json"
    if not bundle_path.is_file(): raise KVPublisherReturnError("private source export bundle unavailable")
    source_bundle=load(bundle_path)
    kv=source_root("STEGVERSE_KV_SOURCE_ROOT","continuity-vault-kit","runtime/document_intr_transfer.py")
    if kv is None: raise KVPublisherReturnError("local_KV_source_materialization_required")
    if str(kv) not in sys.path: sys.path.insert(0,str(kv))
    from runtime.document_intr_transfer import validate_artifact_return, build_import_receipt
    candidate=validate_artifact_return(raw,source_bundle=source_bundle)
    import_receipt=build_import_receipt(candidate,return_transport_terminal_receipt_hash=terminal)
    out=runtime/RECEIPT_DIR; out.mkdir(parents=True,exist_ok=True)
    candidate_path=out/f"{materialization_id}.candidate.json"; receipt_path=out/f"{materialization_id}.receipt.json"
    candidate_path.write_text(json.dumps(candidate,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    receipt_path.write_text(json.dumps(import_receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    result={
      "schema":"stegverse.kv-publisher-return-materialization-consumption/v1",
      "state":"VALIDATED_IMPORT_CANDIDATE_NOT_COMMITTED",
      "materialization_id":materialization_id,"request_hash":request["request_hash"],
      "return_transport_observed":True,"return_transport_terminal_receipt_hash":terminal,
      "return_downstream_owner_ref":KV_DOWNSTREAM_OWNER,
      "source_export_id":candidate["source_export_id"],"source_export_sha256":candidate["source_export_sha256"],
      "candidate_ref":str(candidate_path.relative_to(runtime)),"import_receipt_ref":str(receipt_path.relative_to(runtime)),
      "canonical_kv_mutation_performed":False,"publication_authorized":False,"release_authorized":False,
      "execution_authorized":False,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","authority_effect":"NONE",
    }
    latest=out/"latest.json"; latest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result

def consume(runtime:Path,materialization_id:str)->dict[str,Any]:
    request=load(runtime/REQUEST_DIR/f"{materialization_id}.json"); validate_request(request)
    raw,_intent,_receipts,terminal=_verify_common_return_transport(runtime,materialization_id,request)
    owner=request["downstream_owner_ref"]
    if owner==SDK_DOWNSTREAM_OWNER:
        return _consume_sdk_owner(runtime,materialization_id,request,raw,terminal)
    if owner==KV_DOWNSTREAM_OWNER:
        return _consume_kv_owner(runtime,materialization_id,request,raw,terminal)
    raise KVPublisherReturnError("unsupported Publisher return owner")

def retain_blocked_consumption(runtime:Path,materialization_id:str,exc:Exception)->dict[str,Any]:
    """Persist a non-authorizing diagnostic for the exact failed invocation.

    This is observation of a failed consumer attempt, not proof that RTC006,
    RTC007, RTC008, RTC009, or any other governed transition failed or closed.
    Existing SDK/KV receipt namespaces remain the only storage destinations.
    """
    if not materialization_id or materialization_id in {".",".."} or "/" in materialization_id or chr(92) in materialization_id:
        raise KVPublisherReturnError("materialization_id_invalid_for_diagnostic")
    request_path=runtime/REQUEST_DIR/f"{materialization_id}.json"
    request=None
    if request_path.is_file():
        try:
            loaded=load(request_path)
            if isinstance(loaded,dict):
                request=loaded
        except (ValueError,OSError):
            pass
    owner=request.get("downstream_owner_ref") if request is not None else None
    destination=SDK_RECEIPT_DIR if owner==SDK_DOWNSTREAM_OWNER else RECEIPT_DIR
    out=runtime/destination
    out.mkdir(parents=True,exist_ok=True)
    reason=str(exc) if isinstance(exc,KVPublisherReturnError) else type(exc).__name__
    record={
        "schema":"stegverse.publisher-return-consumption-failure-observation/v1",
        "state":"BLOCKED",
        "materialization_id":materialization_id,
        "request_present":request is not None,
        "request_hash":request.get("request_hash") if request is not None else None,
        "downstream_owner_ref":owner,
        "failure_class":type(exc).__name__,
        "reason_code":reason[:256],
        **_failure_disposition(materialization_id),
        "rtc008_admission_observed":"UNKNOWN_NOT_AUTHENTICALLY_RECONSTRUCTED",
        "rtc009_far_side_transition_observed":"UNKNOWN_NOT_AUTHENTICALLY_RECONSTRUCTED",
        "caller_consequence_observed":"UNKNOWN_NOT_AUTHENTICALLY_RECONSTRUCTED",
        "master_records_organization_record_claimed":False,
        "credential_material_present":False,
        "execution_authority":"NONE",
        "authority_effect":"NONE_DIAGNOSTIC_ONLY",
    }
    if isinstance(getattr(exc,"refusal",None),dict):
        record["organization_receipt_refusal"]=exc.refusal
    record["diagnostic_sha256"]=sha(record)
    raw=json.dumps(record,sort_keys=True,indent=2).encode("utf-8")+bytes([10])
    receipt_path=out/f"{materialization_id}.{record['diagnostic_sha256'].split(':',1)[1]}.blocked.json"
    if receipt_path.exists():
        if receipt_path.read_bytes()!=raw:
            raise KVPublisherReturnError("diagnostic_write_once_collision")
    else:
        with receipt_path.open("xb") as stream:
            stream.write(raw)
    (out/"latest.blocked.json").write_bytes(raw)
    return {**record,"diagnostic_receipt_ref":str(receipt_path.relative_to(runtime))}


def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument("--runtime-root",type=Path,required=True); parser.add_argument("--materialization-id",required=True); args=parser.parse_args()
    runtime=args.runtime_root.expanduser().resolve()
    try:
        result=consume(runtime,args.materialization_id)
    except Exception as exc:
        try:
            result=retain_blocked_consumption(runtime,args.materialization_id,exc)
        except Exception as diagnostic_exc:
            result={
              "schema":"stegverse.publisher-return-consumption-failure-observation/v1",
              "state":"BLOCKED",
              "materialization_id":args.materialization_id,
              "failure_class":type(exc).__name__,
              "diagnostic_retention":"FAILED",
              "diagnostic_retention_failure_class":type(diagnostic_exc).__name__,
              **_failure_disposition(materialization_id),
              "authority_effect":"NONE_DIAGNOSTIC_ONLY",
            }
    print(json.dumps(result,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
