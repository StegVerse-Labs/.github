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
from urllib.parse import urlparse
from urllib.request import Request, urlopen

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
        raise KVPublisherReturnError("SDK return binding unavailable for Master Records custody") from exc
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
        require_predecessor_master_records_closure,
        submit_state_receipt,
    )
    predecessor_receipt_sha256=request.get("predecessor_master_records_receipt_sha256")
    prior_ref,predecessor_evidence=require_predecessor_master_records_closure(
        predecessor_receipt_sha256,
        successor_transition_id=transition_id,
    )
    if prior_ref is None:
        raise KVPublisherReturnError("RTC-SDK-RETURN-006 canonical predecessor Master Records closure required")
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
      proof_ceiling="MASTER_RECORDS_VALIDATED_SDK_RETURN_BINDING_ONLY",
    )
    mr=submit_state_receipt(state_receipt)
    if not (
        mr.get("state")=="RECORDED"
        and mr.get("reconstruction_status")=="PASS"
        and mr.get("required_evidence_validation_status")=="PASS"
        and mr.get("receipt_sha256")==mr.get("reconstructed_receipt_sha256")
    ):
        raise KVPublisherReturnError("SDK return binding Master Records custody not closed")
    return {
      "state":mr.get("state"),
      "reconstruction_status":mr.get("reconstruction_status"),
      "required_evidence_validation_status":mr.get("required_evidence_validation_status"),
      "receipt_sha256":mr.get("receipt_sha256"),
      "reconstructed_receipt_sha256":mr.get("reconstructed_receipt_sha256"),
      "required_evidence_count":mr.get("required_evidence_count"),
      "authority_effect":"NONE_CUSTODY_RECONSTRUCTION_ONLY",
    }

def _submit_rtc008_materialization(request:dict[str,Any], *, env:Mapping[str,str]|None=None, opener=urlopen)->dict[str,Any]:
    """Submit the exact prepared RTC008 request to the existing shared InTr listener.

    This consumes an already-issued TVC relay authorization identifier. It does
    not create a credential, listener, runtime, scheduler, dispatcher, custody
    store, or transition authority.
    """
    values=dict(os.environ if env is None else env)
    ingress_url=str(values.get(MIR_RTC008_INGRESS_ENV) or "").strip()
    authorization_id=str(values.get(MIR_RTC008_AUTH_ENV) or "").strip()
    if not ingress_url:
        raise KVPublisherReturnError("RTC008 shared Universal InTr ingress URL missing")
    if not authorization_id:
        raise KVPublisherReturnError("RTC008 existing TVC relay authorization missing")
    parsed=urlparse(ingress_url)
    if parsed.scheme!="http" or (parsed.hostname or "").lower() not in {"127.0.0.1","localhost","::1"} or parsed.path!="/intr/materialization":
        raise KVPublisherReturnError("RTC008 ingress URL must be existing loopback /intr/materialization")
    if parsed.username is not None or parsed.password is not None:
        raise KVPublisherReturnError("RTC008 ingress URL credentials forbidden")
    raw=canonical(request)
    req=Request(
        ingress_url,
        data=raw,
        method="POST",
        headers={
          "Content-Type":"application/json",
          "X-StegVerse-Transport":"InTr",
          "X-StegVerse-Transport-Origin":"TVC_RELAY_EGRESS",
          "X-StegVerse-Authorization-Id":authorization_id,
          "X-StegVerse-Payload-SHA256":hashlib.sha256(raw).hexdigest(),
        },
    )
    with opener(req,timeout=10.0) as response:
        payload=response.read()
    admitted=json.loads(payload.decode("utf-8"))
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
      "master_records_state":"RECORDED",
      "master_records_reconstruction_status":"PASS",
      "master_records_required_evidence_validation_status":"PASS",
      "rtc008_evidence_complete":True,
      "far_side_transition_observed":False,
      "caller_consequence_observed":False,
    }
    for key,value in expected.items():
        if admitted.get(key)!=value:
            raise KVPublisherReturnError("RTC008 admission mismatch:"+key)
    if admitted.get("master_records_receipt_sha256")!=admitted.get("master_records_reconstructed_receipt_sha256"):
        raise KVPublisherReturnError("RTC008 Master Records digest mismatch")
    return admitted


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
    from llm_adapter.southbound_sdk_return import prepare_sdk_return_for_intr
    transition=prepare_sdk_return_for_intr(binding_bytes,transition_id="RTC-STEGVERSE-EGRESS-007")
    if transition.get("state")!="FINAL_STEGVERSE_SIDE_TRANSITION_PREPARED" or transition.get("final_stegverse_transition_surface_reached") is not True:
        raise KVPublisherReturnError("RTC-STEGVERSE-EGRESS-007 transition not prepared")
    handoff=transition.get("intr_handoff")
    if not isinstance(handoff,dict):
        raise KVPublisherReturnError("RTC-STEGVERSE-EGRESS-007 InTr handoff missing")

    workers_root=ROOT/"workers"
    if str(workers_root) not in sys.path: sys.path.insert(0,str(workers_root))
    from canonical_state_transition_custody import build_state_receipt, submit_state_receipt
    transition_hash=sha(transition)
    required_evidence=[
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
      prior_state_ref_or_hash=rtc006_master_records.get("receipt_sha256"),
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
      proof_ceiling="MASTER_RECORDS_VALIDATED_FINAL_STEGVERSE_EGRESS_PREPARATION_ONLY",
    )
    mr=submit_state_receipt(state_receipt)
    if not (
        mr.get("state")=="RECORDED"
        and mr.get("reconstruction_status")=="PASS"
        and mr.get("required_evidence_validation_status")=="PASS"
        and mr.get("receipt_sha256")==mr.get("reconstructed_receipt_sha256")
    ):
        raise KVPublisherReturnError("RTC-STEGVERSE-EGRESS-007 Master Records custody not closed")

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
    })
    rtc008_request["predecessor_master_records_digest_equal"]=(
      rtc008_request["predecessor_master_records_receipt_sha256"]
      == rtc008_request["predecessor_master_records_reconstructed_receipt_sha256"]
    )
    rtc008_request.pop("request_hash",None)
    rtc008_request["request_hash"]=sha(rtc008_request)
    prepared={**prepared,"materialization_request":rtc008_request}
    rtc008=_submit_rtc008_materialization(rtc008_request)
    return {
      "rtc007_transition":transition,
      "rtc007_master_records":{
        "state":mr.get("state"),
        "reconstruction_status":mr.get("reconstruction_status"),
        "required_evidence_validation_status":mr.get("required_evidence_validation_status"),
        "receipt_sha256":mr.get("receipt_sha256"),
        "reconstructed_receipt_sha256":mr.get("reconstructed_receipt_sha256"),
      },
      "rtc008_materialization_prepared":prepared,
      "rtc008_admission":rtc008,
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
      "rtc008_master_records_state":continuation["rtc008_admission"]["master_records_state"],
      "rtc008_master_records_reconstruction_status":continuation["rtc008_admission"]["master_records_reconstruction_status"],
      "rtc008_master_records_required_evidence_validation_status":continuation["rtc008_admission"]["master_records_required_evidence_validation_status"],
      "rtc008_master_records_receipt_sha256":continuation["rtc008_admission"]["master_records_receipt_sha256"],
      "rtc008_master_records_reconstructed_receipt_sha256":continuation["rtc008_admission"]["master_records_reconstructed_receipt_sha256"],
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

def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument("--runtime-root",type=Path,required=True); parser.add_argument("--materialization-id",required=True); args=parser.parse_args()
    try: result=consume(args.runtime_root.expanduser().resolve(),args.materialization_id)
    except Exception as exc:
        result={"schema":"stegverse.publisher-return-materialization-consumption/v1","state":"BLOCKED","reason":str(exc),"return_transport_observed":False,"sdk_return_binding_observed":False,"canonical_kv_mutation_performed":False,"authority_effect":"NONE"}
    print(json.dumps(result,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
