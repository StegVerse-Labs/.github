#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess
from pathlib import Path
from typing import Any

EXPECTED_HEAD="b5288f9910ada26c6ab2e9bca3f7701afaae2cef"
MATERIALIZATION_ID="tvc-pr92-validation-b5288f99"
DEST=Path("/var/lib/stegverse/private-source-read/materialized")/MATERIALIZATION_ID
REQUEST=Path("/run/stegverse/tvc-private-source-read/request.json")
EXECUTION_RECEIPT=Path("/var/lib/stegverse/private-source-read/latest-execution-receipt.json")
SERVICE="stegtvc-private-source-read.service"

def _git_head(root:Path)->str|None:
    if not (root/".git").is_dir(): return None
    p=subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],capture_output=True,text=True,check=False,timeout=20,env={"PATH":os.environ.get("PATH","/usr/bin:/bin"),"GIT_TERMINAL_PROMPT":"0"})
    v=p.stdout.strip().lower()
    return v if p.returncode==0 else None

def bootstrap(*,runner=subprocess.run)->dict[str,Any]:
    existing=_git_head(DEST)
    if existing==EXPECTED_HEAD:
        return {"schema":"stegverse.tvc-validation-source-bootstrap/v1","state":"READY","source_root":str(DEST),"source_head":existing,"source_reused":True,"credential_authority":"TV/TVC","credential_material_observed":False,"authority_effect":"NONE_SOURCE_BOOTSTRAP_ONLY"}
    if existing:
        return {"schema":"stegverse.tvc-validation-source-bootstrap/v1","state":"BLOCKED","reason":"EXISTING_MATERIALIZATION_IDENTITY_MISMATCH","observed_head":existing,"expected_head":EXPECTED_HEAD,"credential_material_observed":False,"authority_effect":"NONE"}
    req={"caller_repository":"StegVerse-Labs/.github","source_repository":"StegVerse-Labs/TVC","consumer_task":"SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001","reference_mode":"IMMUTABLE_COMMIT","exact_ref":"commit:"+EXPECTED_HEAD,"exact_sha":EXPECTED_HEAD,"materialization_id":MATERIALIZATION_ID,"ttl_seconds":600}
    try:
        REQUEST.parent.mkdir(parents=True,exist_ok=True)
        REQUEST.write_text(json.dumps(req,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        os.chmod(REQUEST,0o600)
    except PermissionError:
        return {"schema":"stegverse.tvc-validation-source-bootstrap/v1","state":"HANDOFF_READY","reason":"PRIVATE_SOURCE_REQUEST_PATH_NOT_WRITABLE_BY_CURRENT_RUNTIME","credential_material_observed":False,"authority_effect":"NONE"}
    try:
        p=runner(["systemctl","start",SERVICE],capture_output=True,text=True,check=False,timeout=360)
    except (OSError,subprocess.TimeoutExpired) as exc:
        return {"schema":"stegverse.tvc-validation-source-bootstrap/v1","state":"HANDOFF_READY","reason":"PRIVATE_SOURCE_SERVICE_NOT_EXECUTABLE:"+type(exc).__name__,"credential_material_observed":False,"authority_effect":"NONE"}
    finally:
        REQUEST.unlink(missing_ok=True)
    head=_git_head(DEST)
    receipt=None
    if EXECUTION_RECEIPT.is_file():
        try: receipt=json.loads(EXECUTION_RECEIPT.read_text(encoding="utf-8"))
        except Exception: receipt=None
    ok=(p.returncode==0 and head==EXPECTED_HEAD and isinstance(receipt,dict) and receipt.get("state")=="COMPLETE" and receipt.get("credential_authority")=="TV/TVC" and receipt.get("authorized_exact_sha")==EXPECTED_HEAD and receipt.get("observed_exact_sha")==EXPECTED_HEAD and receipt.get("credential_value_exposed") is False and receipt.get("credential_persisted") is False)
    return {"schema":"stegverse.tvc-validation-source-bootstrap/v1","state":"READY" if ok else "HANDOFF_READY","reason":None if ok else "PRIVATE_SOURCE_BOOTSTRAP_NOT_YET_PROVEN","service_returncode":p.returncode,"source_root":str(DEST) if head else None,"source_head":head,"expected_head":EXPECTED_HEAD,"execution_receipt_observed":isinstance(receipt,dict),"credential_authority":"TV/TVC","credential_material_observed":False,"github_token_runtime_authority":"NONE","authority_effect":"NONE_SOURCE_BOOTSTRAP_ONLY"}

if __name__=="__main__":
    print(json.dumps(bootstrap(),sort_keys=True))
