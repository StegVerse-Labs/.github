#!/usr/bin/env python3
"""Bounded DEVICE_KV read/write extension for the owner's Personal Contact Profile."""
from __future__ import annotations
import base64, importlib.util, json, os, tempfile
from pathlib import Path
from typing import Any, Mapping

RECORD_CLASS="PERSONAL_CONTACT_PROFILE"
PROFILE_SCHEMA="stegverse.kv.personal-contact-profile/v1"
CANONICAL_PATH=Path("_Entities/Self/Personal_Contact_Profile.json")
DATA_PREFIX="data:application/vnd.stegverse.personal-contact-profile+json;base64,"
ALLOWED_PROFILE_KEYS={"schema","display_name","legal_name","date_of_birth","phone_numbers","postal_addresses","email_addresses","authority_effect"}
FORBIDDEN_TOKENS=("password","secret","token","credential","private_key","seed","mnemonic","access_key","refresh_key")

class PersonalProfileDeviceKVError(ValueError): pass

def _require(ok:bool,reason:str)->None:
    if not ok: raise PersonalProfileDeviceKVError(reason)

def _contains_forbidden(value:Any)->bool:
    if isinstance(value,dict):
        for k,v in value.items():
            if any(t in str(k).lower() for t in FORBIDDEN_TOKENS): return True
            if _contains_forbidden(v): return True
    elif isinstance(value,list):
        return any(_contains_forbidden(v) for v in value)
    return False

def _load_profile_module(source_root:Path):
    p=(source_root/"runtime/personal_contact_profile.py").resolve()
    _require(p.is_file(),"personal_contact_profile_source_missing")
    spec=importlib.util.spec_from_file_location("stegverse_personal_contact_profile",p)
    _require(spec is not None and spec.loader is not None,"personal_contact_profile_loader_unavailable")
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    _require(hasattr(m,"validate_profile") and hasattr(m,"new_profile"),"personal_contact_profile_entrypoint_missing")
    return m

def is_personal_profile_request(req:Mapping[str,Any])->bool:
    q=req.get("kv_request")
    return isinstance(q,dict) and q.get("record_class")==RECORD_CLASS

def validate_request(query:Mapping[str,Any],*,node_id:str)->dict[str,Any]:
    _require(isinstance(query,dict),"profile_request_object_required")
    common={"schema_version","operation","request_id","requester","purpose","record_class","requested_scope","minimum_necessary_justification","authority_ref","disclosure_mode"}
    op=query.get("operation")
    allowed=common|({"candidate_writeback"} if op=="COMMIT_CANDIDATE" else set())
    _require(set(query)==allowed,"profile_request_field_set_invalid")
    _require(query.get("schema_version")=="kv.interlock.request.v1","profile_request_schema_invalid")
    _require(op in {"REQUEST","COMMIT_CANDIDATE"},"profile_request_operation_invalid")
    _require(query.get("requester")=={"module":"Site","component":"MyKVPersonalInfo"},"profile_requester_invalid")
    _require(query.get("record_class")==RECORD_CLASS,"profile_record_class_invalid")
    _require(query.get("authority_ref")=="stegos-node://"+node_id,"profile_node_binding_invalid")
    _require(query.get("disclosure_mode")=="BOUNDED_CONTEXT","profile_disclosure_mode_invalid")
    _require(isinstance(query.get("request_id"),str) and query["request_id"],"profile_request_id_required")
    _require(isinstance(query.get("purpose"),str) and query["purpose"],"profile_purpose_required")
    _require(isinstance(query.get("minimum_necessary_justification"),str) and query["minimum_necessary_justification"],"profile_minimum_necessary_required")
    if op=="REQUEST":
        _require(query.get("requested_scope")==["personal_profile"],"profile_read_scope_invalid")
    else:
        _require(query.get("requested_scope")==["personal_profile_update"],"profile_write_scope_invalid")
        cw=query.get("candidate_writeback")
        _require(isinstance(cw,dict) and set(cw)=={"candidate_type","payload_ref","requested_destination"},"profile_candidate_invalid")
        _require(cw.get("candidate_type")=="PERSONAL_CONTACT_PROFILE_REPLACE","profile_candidate_type_invalid")
        _require(cw.get("requested_destination")==CANONICAL_PATH.as_posix(),"profile_destination_invalid")
        _require(isinstance(cw.get("payload_ref"),str) and cw["payload_ref"].startswith(DATA_PREFIX),"profile_payload_ref_invalid")
    return dict(query)

def _decode_candidate(query:Mapping[str,Any])->dict[str,Any]:
    encoded=query["candidate_writeback"]["payload_ref"][len(DATA_PREFIX):]
    try: raw=base64.b64decode(encoded.encode("ascii"),validate=True)
    except Exception as exc: raise PersonalProfileDeviceKVError("profile_payload_base64_invalid") from exc
    _require(0<len(raw)<=256*1024,"profile_payload_size_invalid")
    try: profile=json.loads(raw.decode("utf-8"))
    except Exception as exc: raise PersonalProfileDeviceKVError("profile_payload_json_invalid") from exc
    _require(isinstance(profile,dict),"profile_payload_object_required")
    _require(set(profile).issubset(ALLOWED_PROFILE_KEYS),"profile_payload_fields_invalid")
    _require(profile.get("schema")==PROFILE_SCHEMA,"profile_schema_invalid")
    _require(profile.get("authority_effect")=="NONE","profile_authority_effect_invalid")
    _require(not _contains_forbidden(profile),"profile_secret_like_field_forbidden")
    return profile

def _atomic_write(path:Path,data:bytes)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile("wb",dir=path.parent,delete=False) as h:
        h.write(data);tmp=h.name
    os.replace(tmp,path)

def execute(*,query:Mapping[str,Any],node_id:str,kv_source_root:Path,kv_data_root:Path)->dict[str,Any]:
    q=validate_request(query,node_id=node_id)
    module=_load_profile_module(kv_source_root)
    target=(kv_data_root/CANONICAL_PATH).resolve()
    root=kv_data_root.resolve()
    _require(root in target.parents,"profile_destination_escape")
    prior_hash=None
    if target.is_file():
        import hashlib
        prior_hash="sha256:"+hashlib.sha256(target.read_bytes()).hexdigest()
    if q["operation"]=="REQUEST":
        if target.is_file():
            try: profile=json.loads(target.read_text(encoding="utf-8"))
            except Exception as exc: raise PersonalProfileDeviceKVError("profile_read_invalid_json") from exc
        else:
            profile=module.new_profile()
        errors=module.validate_profile(profile)
        _require(not errors,"profile_read_validation_failed:"+";".join(errors))
        _require(not _contains_forbidden(profile),"profile_read_secret_like_field_forbidden")
        return {"schema":"stegverse.device-kv.personal-profile-response/v1","state":"PROFILE_READ","request_id":q["request_id"],"record_class":RECORD_CLASS,"canonical_path":CANONICAL_PATH.as_posix(),"profile":profile,"credential_material_present":False,"provider_operation_authorized":False,"authority_effect":"NONE"}
    profile=_decode_candidate(q)
    errors=module.validate_profile(profile)
    _require(not errors,"profile_write_validation_failed:"+";".join(errors))
    raw=(json.dumps(profile,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf-8")
    _atomic_write(target,raw)
    readback=target.read_bytes()
    _require(readback==raw,"profile_exact_readback_mismatch")
    import hashlib
    new_hash="sha256:"+hashlib.sha256(readback).hexdigest()
    return {"schema":"stegverse.device-kv.profile-update-response/v1","state":"PROFILE_PERSISTED","request_id":q["request_id"],"record_class":RECORD_CLASS,"canonical_path":CANONICAL_PATH.as_posix(),"prior_profile_hash":prior_hash,"profile_hash":new_hash,"exact_readback_verified":True,"credential_material_present":False,"provider_operation_authorized":False,"authority_effect":"NONE"}
