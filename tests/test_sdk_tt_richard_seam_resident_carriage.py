from __future__ import annotations

import importlib.util
import json
import subprocess
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


def test_consumer_drives_bounded_two_cycle_test3_one_shot(tmp_path):
    module = load_consumer()
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    source.mkdir()
    (runtime / "control/resident-execution-request.d").mkdir(parents=True)
    (runtime / "scripts").mkdir(parents=True)
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    (runtime / module.REQUEST_REL).write_text(json.dumps(request), encoding="utf-8")
    (runtime / module.TARGET_ENTRYPOINT).write_text("# fixture\n", encoding="utf-8")
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        result = {
            "mode": module.TARGET_MODE,
            "task_id": module.TARGET_TASK,
            "runtime_execution_attempted": True,
            "network_fetch_performed": False,
            "github_token_runtime_authority": "NONE",
            "credential_authority": "TV/TVC",
            "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
            "cosv_task_pointer": {
                "task_id": module.TARGET_TASK,
                "vector": module.TARGET_VECTOR,
                "binding_verified": True,
                "authority_effect": "NONE",
            },
        }
        if len(calls) == 2:
            close_path = runtime / module.CLOSE_LATEST_REL
            close_path.parent.mkdir(parents=True, exist_ok=True)
            close_path.write_text(json.dumps({
                "state": "AUTHENTIC_TASK_CLOSED_WORKER_RETIRED_RECORDS_ONLY",
                "task_id": module.TARGET_TASK,
            }), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(result) + "\n", stderr="")

    receipt = module.consume(source, runtime, runner=runner, env={"PATH": "/usr/bin", "HOME": "/home/stegverse"})
    assert receipt["state"] == "ATTEMPT_RECORDED"
    assert receipt["targeted_cycle_count"] == 2
    assert receipt["bounded_cycle_limit"] == 2
    assert len(calls) == 2
    assert all(module.TARGET_TASK in call for call in calls)


def test_native_runtime_prioritizes_exact_test3_selector_before_global_dispatch():
    source = (ROOT / "scripts/run_worker_runtime.py").read_text(encoding="utf-8")
    function_start = source.index("def dispatch_local_resident_requests(")
    function_end = source.index("\ndef maybe_dispatch_machine_continuation(", function_start)
    body = source[function_start:function_end]
    priority = body.index('"--only-consumer", TEST3_CONSUMER_SELECTOR')
    global_dispatch = body.index('"--runtime-root", str(root),\n        ],', priority + 1)
    assert priority < global_dispatch
    assert 'test3_request = root / TEST3_REQUEST_REL' in body
    assert '"priority_test3_dispatch": priority_result' in body


def test_existing_org_ledger_root_survives_targeted_custody_chain():
    module = load_consumer()
    values = {"PATH": "/usr/bin", "STEGVERSE_ORG_LEDGER_ROOT": "/srv/stegverse/org-ledgers/StegVerse-Labs"}
    assert module.clean_env(values)["STEGVERSE_ORG_LEDGER_ROOT"] == values["STEGVERSE_ORG_LEDGER_ROOT"]
    spec = importlib.util.spec_from_file_location("test3_dispatcher_org", DISPATCHER)
    dispatcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dispatcher)
    assert dispatcher.clean_exec_env(values)["STEGVERSE_ORG_LEDGER_ROOT"] == values["STEGVERSE_ORG_LEDGER_ROOT"]
    refresh = (ROOT / "scripts/refresh_and_execute_resident_task.py").read_text(encoding="utf-8")
    assert '"STEGVERSE_ORG_LEDGER_ROOT"' in refresh.split("NONSECRET_FORWARD =", 1)[1].split("Runner =", 1)[0]
    adapter = json.loads((ROOT / "control/process-worker-adapters.d/stegagents-governed-runtime-001.json").read_text())
    assert "STEGVERSE_ORG_LEDGER_ROOT" in adapter["adapters"][0]["env_allowlist"]


def _setup_test3_target(tmp_path, module, *, old_close=None):
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    source.mkdir()
    (runtime / "control/resident-execution-request.d").mkdir(parents=True)
    (runtime / "scripts").mkdir(parents=True)
    (runtime / module.REQUEST_REL).write_text(REQUEST.read_text(), encoding="utf-8")
    (runtime / module.TARGET_ENTRYPOINT).write_text("# fixture\n", encoding="utf-8")
    if old_close is not None:
        close = runtime / module.CLOSE_LATEST_REL
        close.parent.mkdir(parents=True, exist_ok=True)
        close.write_text(json.dumps(old_close), encoding="utf-8")
    return source, runtime


def _test3_result(module, *, verified=True):
    return {
        "mode": module.TARGET_MODE, "task_id": module.TARGET_TASK,
        "runtime_execution_attempted": True,
        "network_fetch_performed": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
        "cosv_task_pointer": {
            "task_id": module.TARGET_TASK, "vector": module.TARGET_VECTOR,
            "binding_verified": verified, "authority_effect": "NONE",
        },
    }


def test_first_failed_targeted_cycle_is_not_masked_by_second_retry(tmp_path):
    module = load_consumer()
    source, runtime = _setup_test3_target(tmp_path, module)
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(
            command, 7, stdout=json.dumps(_test3_result(module)) + "\n", stderr="fixture-only",
        )

    receipt = module.consume(source, runtime, runner=runner, env={"PATH": "/usr/bin"})
    assert len(calls) == 1
    assert receipt["state"] == "FAIL_CLOSED"
    assert receipt["first_failed_cycle"] == {
        "cycle_index": 0, "boundary": "PROCESS_EXIT_NONZERO", "returncode": 7,
    }
    assert receipt["targeted_cycles"][0]["cycle_valid"] is False
    assert receipt["fresh_close_snapshot_seen"] is False


def test_missing_exact_pointer_fails_before_second_cycle(tmp_path):
    module = load_consumer()
    source, runtime = _setup_test3_target(tmp_path, module)
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(
            command, 0, stdout=json.dumps(_test3_result(module, verified=False)) + "\n", stderr="",
        )

    receipt = module.consume(source, runtime, runner=runner, env={"PATH": "/usr/bin"})
    assert len(calls) == 1
    assert receipt["state"] == "FAIL_CLOSED"
    assert receipt["first_failed_cycle"]["boundary"] == "TARGETED_RESULT_OR_COSV_POINTER_INVALID"


def test_stale_close_pointer_does_not_terminate_fresh_attempt(tmp_path):
    module = load_consumer()
    previous = {
        "state": "AUTHENTIC_TASK_CLOSED_WORKER_RETIRED_RECORDS_ONLY",
        "task_id": module.TARGET_TASK,
        "worker_claim": {"claim_id": "STALE-OLD-CLAIM", "fencing_token": 1},
    }
    source, runtime = _setup_test3_target(tmp_path, module, old_close=previous)
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(
            command, 0, stdout=json.dumps(_test3_result(module)) + "\n", stderr="",
        )

    receipt = module.consume(source, runtime, runner=runner, env={"PATH": "/usr/bin"})
    assert len(calls) == 2
    assert receipt["state"] == "ATTEMPT_RECORDED"
    assert receipt["first_failed_cycle"] is None
    assert receipt["fresh_close_snapshot_seen"] is False
    assert receipt["authority_effect"] == "NONE_REQUEST_CONSUMPTION_ONLY"


def test_first_failed_richard_consumption_is_immutable_after_later_attempt(tmp_path):
    module = load_consumer()
    source, runtime = _setup_test3_target(tmp_path, module)
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        code = 7 if len(calls) == 1 else 0
        return subprocess.CompletedProcess(
            command, code, stdout=json.dumps(_test3_result(module)) + "\n", stderr="",
        )

    first = module.consume(source, runtime, runner=runner, env={"PATH": "/usr/bin"})
    assert first["state"] == "FAIL_CLOSED"
    immutable = runtime / module.IMMUTABLE_CONSUMPTION_DIR_REL / (
        first["receipt_body_sha256"].split(":", 1)[1] + ".json"
    )
    original = immutable.read_bytes()
    second = module.consume(source, runtime, runner=runner, env={"PATH": "/usr/bin"})
    assert second["state"] == "ATTEMPT_RECORDED"
    assert immutable.read_bytes() == original
    assert json.loads(original)["first_failed_cycle"]["boundary"] == "PROCESS_EXIT_NONZERO"
    latest = json.loads((runtime / module.CONSUMPTION_REL).read_text())
    assert latest["receipt_body_sha256"] == second["receipt_body_sha256"]


def test_richard_dispatch_visit_closes_only_with_exact_master_records_readback(tmp_path, monkeypatch):
    import hashlib
    import sys
    import types

    spec = importlib.util.spec_from_file_location("richard_dispatch_custody_test", DISPATCHER)
    dispatcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dispatcher)
    source, runtime = _setup_test3_target(tmp_path, load_consumer())
    consumer = runtime / "scripts/consume_sdk_tt_richard_seam_authentic_runtime_request.py"
    consumer.write_text("# inert consumer fixture\n")
    result = {"state": "ATTEMPT_RECORDED", "first_failed_cycle": {
        "cycle_index": 0, "boundary": "PROCESS_EXIT_NONZERO", "returncode": 7,
    }}
    receipt_calls = []

    def sha(value):
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()

    def build(**kwargs):
        assert kwargs["proof_scope"] == "RICHARD_TEST3_DISPATCH_VISIT_ONLY"
        assert kwargs["required_evidence_manifest"][0]["content"]["first_failed_cycle"] == result["first_failed_cycle"]
        return kwargs

    reconstructed_digest = ["sha256:" + "a" * 64]
    def submit(receipt):
        receipt_calls.append(receipt)
        return {
            "state": "RECORDED", "reconstruction_status": "PASS",
            "required_evidence_validation_status": "PASS",
            "receipt_sha256": "sha256:" + "a" * 64,
            "reconstructed_receipt_sha256": reconstructed_digest[0],
        }

    monkeypatch.setitem(sys.modules, "canonical_state_transition_custody",
                        types.SimpleNamespace(build_state_receipt=build, sha256_uri=sha, submit_state_receipt=submit))

    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(result) + "\n", stderr="")

    closed = dispatcher.dispatch(source, runtime, runner=runner, env={"PATH": "/usr/bin"},
                                 only_consumers=(dispatcher.RICHARD_SELECTOR,))
    assert closed["state"] == "DISPATCH_COMPLETE"
    assert closed["richard_dispatch_master_records"]["state"] == "RECORDED"
    assert closed["richard_dispatch_master_records"]["first_failed_cycle"] == result["first_failed_cycle"]
    assert len(receipt_calls) == 1

    reconstructed_digest[0] = "sha256:" + "b" * 64
    rejected = dispatcher.dispatch(source, runtime, runner=runner, env={"PATH": "/usr/bin"},
                                   only_consumers=(dispatcher.RICHARD_SELECTOR,))
    assert rejected["state"] == "DISPATCH_INCOMPLETE"
    assert rejected["richard_dispatch_master_records"]["state"] == "BOUNDARY"
    assert rejected["exact_selector_failure"] is True

    request = json.loads((runtime / load_consumer().REQUEST_REL).read_text())
    request["cosv_task_vector"] = "00000000000000"
    (runtime / load_consumer().REQUEST_REL).write_text(json.dumps(request))
    unknown = dispatcher.dispatch(source, runtime, runner=runner, env={"PATH": "/usr/bin"},
                                  only_consumers=(dispatcher.RICHARD_SELECTOR,))
    assert unknown["state"] == "DISPATCH_INCOMPLETE"
    assert unknown["richard_dispatch_master_records"]["reason"] == "RICHARD_DISPATCH_REQUEST_IDENTITY_INVALID"
