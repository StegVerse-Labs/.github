from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "control/resident-execution-request.d/sdk-tt-richard-seam-authentic-runtime-001.json"
CONSUMER = ROOT / "scripts/consume_sdk_tt_richard_seam_authentic_runtime_request.py"
DISPATCHER = ROOT / "scripts/dispatch_resident_execution_requests.py"

def load_consumer():
    spec = importlib.util.spec_from_file_location("test3_resident_consumer", CONSUMER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_test3_request_identity_and_authority_boundary():
    value=json.loads(REQUEST.read_text(encoding="utf-8"))
    assert value["task_id"]=="SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001"
    assert value["cosv_profile"]=="task.v1"
    assert value["cosv_task_vector"]=="20010000110000"
    assert value["argv"]==["--task-id","SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001","--cosv-task-vector","20010000110000"]
    assert value["github_token_required"] is False
    assert value["github_token_runtime_authority"]=="NONE"
    assert value["second_machine_required"] is False
    assert value["request_granted_authority"] is False
    assert value["authority_effect"]=="NONE_REQUEST_ONLY"

def test_consumer_requires_exact_request_and_strips_github_authority():
    module=load_consumer()
    value=json.loads(REQUEST.read_text(encoding="utf-8"))
    module.validate_request(value)
    env=module.clean_env({
        "PATH":"/usr/bin",
        "GITHUB_TOKEN":"secret",
        "GH_TOKEN":"secret2",
        "STEGVERSE_TV_ROOT":"/tv",
        "STEGVERSE_MASTER_RECORDS_ENDPOINT":"http://127.0.0.1:8765",
        "STEGVERSE_MASTER_RECORDS_TOKEN":"mr-token",
        "STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS":"12",
        "MASTER_RECORDS_DB":"/srv/stegverse/master-records.sqlite",
        "MASTER_RECORDS_RECEIPT_KEY":"receipt-key",
        "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS":"true",
    })
    assert "GITHUB_TOKEN" not in env and "GH_TOKEN" not in env
    assert env["STEGVERSE_MASTER_RECORDS_ENDPOINT"]=="http://127.0.0.1:8765"
    assert env["STEGVERSE_MASTER_RECORDS_TOKEN"]=="mr-token"
    assert env["MASTER_RECORDS_DB"]=="/srv/stegverse/master-records.sqlite"
    assert env["MASTER_RECORDS_RECEIPT_KEY"]=="receipt-key"
    assert env["MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS"]=="true"
    assert env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]=="NONE"
    assert env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]=="TV/TVC"

def test_consumer_requires_exact_cosv_pointer_binding():
    source=CONSUMER.read_text(encoding="utf-8")
    assert 'pointer.get("task_id") == TARGET_TASK' in source
    assert 'pointer.get("vector") == TARGET_VECTOR' in source
    assert 'pointer.get("binding_verified") is True' in source
    assert 'pointer.get("authority_effect") == "NONE"' in source

def test_dispatcher_has_exactly_one_test3_selector():
    source=DISPATCHER.read_text(encoding="utf-8")
    row='("sdk_tt_richard_seam_authentic_runtime", "scripts/consume_sdk_tt_richard_seam_authentic_runtime_request.py")'
    assert source.count(row)==1


def test_dispatcher_preserves_test3_master_records_custody_binding():
    spec = importlib.util.spec_from_file_location("test3_dispatcher", DISPATCHER)
    assert spec is not None and spec.loader is not None
    dispatcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dispatcher)
    env = dispatcher.clean_exec_env({
        "PATH": "/usr/bin",
        "HOME": "/home/stegverse",
        "STEGVERSE_MASTER_RECORDS_ENDPOINT": "http://127.0.0.1:8765",
        "STEGVERSE_MASTER_RECORDS_TOKEN": "mr-token",
        "STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS": "12",
        "MASTER_RECORDS_DB": "/srv/stegverse/master-records.sqlite",
        "MASTER_RECORDS_RECEIPT_KEY": "receipt-key",
        "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS": "true",
        "GITHUB_TOKEN": "forbidden",
    })
    assert env["STEGVERSE_MASTER_RECORDS_ENDPOINT"] == "http://127.0.0.1:8765"
    assert env["STEGVERSE_MASTER_RECORDS_TOKEN"] == "mr-token"
    assert env["MASTER_RECORDS_DB"] == "/srv/stegverse/master-records.sqlite"
    assert env["MASTER_RECORDS_RECEIPT_KEY"] == "receipt-key"
    assert env["MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS"] == "true"
    assert "GITHUB_TOKEN" not in env
