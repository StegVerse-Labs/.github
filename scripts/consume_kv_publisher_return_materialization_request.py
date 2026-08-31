#!/usr/bin/env python3
"""Validate Publisher->KV return transport and create a non-mutating KV import candidate."""
from __future__ import annotations
import argparse, hashlib, json, os, sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
REQUEST_DIR=Path("intr-materialization")
INGRESS_DIR=Path("receipts/sovereign-network/kv-publisher-return-ingress")
PAYLOAD_DIR=Path("intr-payloads/kv-publisher-return")
RECEIPT_DIR=Path("receipts/sovereign-host/kv-publisher-return-import")
DESTINATION={"boundary":"KV","subsystem":"KnowledgeVault:DocumentImport"}
DOWNSTREAM_OWNER="StegVerse-Labs/continuity-vault-kit"
RETURN_SCHEMA="stegverse.publisher.artifact-return/v1"
HOSTED_ENV=("GITHUB_ACTIONS","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
CREDENTIAL_ENV=("GITHUB_TOKEN","GH_TOKEN","STEGVERSE_GITHUB_TOKEN","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN")

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
      "downstream_owner_ref":DOWNSTREAM_OWNER,
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
    if request.get("boundary_path")!=["STEGOS_ECOSYSTEM","DEVICE_SYSTEM","KV"]:
        raise KVPublisherReturnError("materialization_boundary_path_invalid")
    body=dict(request); claimed=body.pop("request_hash",None)
    if claimed!=sha(body): raise KVPublisherReturnError("materialization_request_hash_mismatch")

def consume(runtime:Path,materialization_id:str)->dict[str,Any]:
    request=load(runtime/REQUEST_DIR/f"{materialization_id}.json"); validate_request(request)
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
    raw=raw_path.read_bytes()
    intent=load(intent_path)
    receipts=load(receipts_path)
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
    kv=source_root("STEGVERSE_KV_SOURCE_ROOT","continuity-vault-kit","runtime/document_intr_transfer.py")
    if stegos is None or kv is None: raise KVPublisherReturnError("local_source_materialization_required")
    if str(stegos) not in sys.path: sys.path.insert(0,str(stegos))
    if str(kv) not in sys.path: sys.path.insert(0,str(kv))
    from stegos.universal_intr_transport import validate_transport_intent, validate_receipt_chain
    validate_transport_intent(intent); validate_receipt_chain(intent,receipts)
    try: returned=json.loads(raw.decode("utf-8"))
    except Exception as exc: raise KVPublisherReturnError("Publisher return JSON invalid") from exc
    if returned.get("schema")!=RETURN_SCHEMA: raise KVPublisherReturnError("Publisher return schema mismatch")
    export_id=returned.get("source_export_id")
    if not isinstance(export_id,str) or not export_id: raise KVPublisherReturnError("source export id missing")
    bundle_root=Path(os.environ.get("STEGVERSE_KV_DOCUMENT_EXPORT_BUNDLE_ROOT",str(runtime/"private-kv-document-exports"))).expanduser().resolve()
    bundle_path=bundle_root/f"{export_id}.json"
    if not bundle_path.is_file(): raise KVPublisherReturnError("private source export bundle unavailable")
    source_bundle=load(bundle_path)
    from runtime.document_intr_transfer import validate_artifact_return, build_import_receipt
    candidate=validate_artifact_return(raw,source_bundle=source_bundle)
    terminal=receipts[-1].get("receipt_hash")
    import_receipt=build_import_receipt(candidate,return_transport_terminal_receipt_hash=terminal)
    out=runtime/RECEIPT_DIR
    out.mkdir(parents=True,exist_ok=True)
    candidate_path=out/f"{materialization_id}.candidate.json"
    receipt_path=out/f"{materialization_id}.receipt.json"
    candidate_path.write_text(json.dumps(candidate,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    receipt_path.write_text(json.dumps(import_receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    result={
      "schema":"stegverse.kv-publisher-return-materialization-consumption/v1",
      "state":"VALIDATED_IMPORT_CANDIDATE_NOT_COMMITTED",
      "materialization_id":materialization_id,
      "request_hash":request["request_hash"],
      "return_transport_observed":True,
      "return_transport_terminal_receipt_hash":terminal,
      "source_export_id":candidate["source_export_id"],
      "source_export_sha256":candidate["source_export_sha256"],
      "candidate_ref":str(candidate_path.relative_to(runtime)),
      "import_receipt_ref":str(receipt_path.relative_to(runtime)),
      "canonical_kv_mutation_performed":False,
      "publication_authorized":False,
      "release_authorized":False,
      "execution_authorized":False,
      "credential_authority":"TV/TVC",
      "github_token_runtime_authority":"NONE",
      "authority_effect":"NONE",
    }
    latest=out/"latest.json"; latest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result

def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument("--runtime-root",type=Path,required=True); parser.add_argument("--materialization-id",required=True); args=parser.parse_args()
    try: result=consume(args.runtime_root.expanduser().resolve(),args.materialization_id)
    except Exception as exc:
        result={"schema":"stegverse.kv-publisher-return-materialization-consumption/v1","state":"BLOCKED","reason":str(exc),"return_transport_observed":False,"canonical_kv_mutation_performed":False,"authority_effect":"NONE"}
    print(json.dumps(result,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
