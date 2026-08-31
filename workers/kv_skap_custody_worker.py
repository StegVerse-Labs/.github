#!/usr/bin/env python3
"""Recovery worker for an already-admitted KV -> SKAP custody materialization."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts.consume_kv_skap_custody_materialization_request import consume_one

ENV_ID="STEGVERSE_KV_SKAP_MATERIALIZATION_ID"

def main()->int:
    mid=str(os.environ.get(ENV_ID) or "").strip()
    if not mid:
        print(json.dumps({"state":"BLOCKED","reason":"kv_skap_materialization_id_missing","authority_effect":"NONE"},sort_keys=True))
        return 1
    runtime=Path(os.environ.get("STEGVERSE_RUNTIME_ROOT") or ROOT).expanduser().resolve()
    try:
        result=consume_one(ROOT,runtime,mid)
    except Exception as exc:
        print(json.dumps({"state":"BLOCKED","reason":str(exc),"authority_effect":"NONE"},sort_keys=True))
        return 1
    print(json.dumps({"state":"COMPLETED","transition_id":"KV_SKAP_CIPHERTEXT_CUSTODY_OBSERVED","materialization_id":mid,"result_hash":result.get("result_hash"),"authority_effect":"NONE"},sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
