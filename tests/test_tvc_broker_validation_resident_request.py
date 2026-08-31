from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from scripts import consume_tvc_broker_validation_request as consumer


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def request() -> dict:
    return {
        "schema":"stegverse.resident-execution-request/v1",
        "request_id":"RESIDENT-EXEC-TVC-BROKER-VALIDATION-001",
        "state":"REQUESTED",
        "task_id":consumer.TARGET_TASK,
        "mode":consumer.TARGET_MODE,
        "entrypoint":consumer.TARGET_ENTRYPOINT,
        "fresh_fence_minimum_exclusive":consumer.MIN_FENCE,
        "credential_authority":"TV/TVC",
        "github_token_required":False,
        "github_token_runtime_authority":"NONE",
        "heartbeat_grants_execution_authority":False,
        "second_machine_required":False,
        "network_source_fetch_allowed":False,
        "request_granted_authority":False,
        "tvc_root_locator_required":True,
        "credential_material_allowed":False,
        "authority_effect":"NONE_REQUEST_ONLY",
    }


def test_request_contract_is_non_authorizing():
    value = request()
    consumer.validate_request(value)
    assert value["request_granted_authority"] is False
    assert value["github_token_required"] is False
    assert value["network_source_fetch_allowed"] is False
    assert value["credential_material_allowed"] is False


def test_missing_exact_tvc_root_is_retryable_handoff_ready(tmp_path, monkeypatch):
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    source.mkdir()
    runtime.mkdir()
    write_json(runtime / consumer.REQUEST_REL, request())
    monkeypatch.setattr(consumer, "exact_local_tvc_root", lambda values: (None, None))
    receipt = consumer.consume(
        source,
        runtime,
        env={"HOME":str(tmp_path),"PATH":"/usr/bin"},
    )
    assert receipt["state"] == "HANDOFF_READY"
    assert receipt["runtime_execution_attempted"] is False
    assert receipt["terminal_validation_observed"] is False
    assert receipt["second_machine_required"] is False
    assert consumer.previously_consumed(runtime, request(), consumer.stable_hash(request())) is False


def test_exact_local_root_invokes_only_targeted_existing_bridge(tmp_path, monkeypatch):
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    tvc = tmp_path / "TVC"
    source.mkdir()
    runtime.mkdir()
    tvc.mkdir()
    write_json(runtime / consumer.REQUEST_REL, request())
    entrypoint = runtime / consumer.TARGET_ENTRYPOINT
    entrypoint.parent.mkdir(parents=True, exist_ok=True)
    entrypoint.write_text("# bridge\n", encoding="utf-8")
    monkeypatch.setattr(consumer, "exact_local_tvc_root", lambda values: (tvc, f"{tvc}:{consumer.EXPECTED_HEAD}"))
    monkeypatch.setattr(consumer, "terminal_validation", lambda runtime_root: True)
    observed = {}
    def runner(command, **kwargs):
        observed["command"] = command
        observed["env"] = kwargs["env"]
        return SimpleNamespace(returncode=0, stdout="{}\n", stderr="")
    receipt = consumer.consume(
        source,
        runtime,
        runner=runner,
        env={
            "HOME":str(tmp_path),
            "PATH":"/usr/bin",
            "STEGVERSE_TVC_ROOT":str(tvc),
            "GITHUB_TOKEN":"forbidden",
            "TVC_EPHEMERAL_GITHUB_TOKEN":"forbidden",
        },
    )
    assert receipt["state"] == "COMPLETED"
    assert receipt["runtime_execution_attempted"] is True
    assert receipt["terminal_validation_observed"] is True
    assert observed["command"][-2:] == ["--task-id", consumer.TARGET_TASK]
    assert "GITHUB_TOKEN" not in observed["env"]
    assert "TVC_EPHEMERAL_GITHUB_TOKEN" not in observed["env"]
    assert observed["env"]["STEGVERSE_TVC_ROOT"] == str(tvc)



def test_missing_exact_root_invokes_existing_tvc_progression_then_validation(tmp_path, monkeypatch):
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    control = tmp_path / "TVC-control"
    exact = tmp_path / "TVC-exact"
    source.mkdir()
    runtime.mkdir()
    control.mkdir()
    exact.mkdir()
    write_json(runtime / consumer.REQUEST_REL, request())
    entrypoint = runtime / consumer.TARGET_ENTRYPOINT
    entrypoint.parent.mkdir(parents=True, exist_ok=True)
    entrypoint.write_text("# bridge\n", encoding="utf-8")

    calls = {"exact": 0}
    def exact_root(values):
        calls["exact"] += 1
        if calls["exact"] == 1:
            return None, "not-yet-materialized"
        return exact, f"{exact}:{consumer.EXPECTED_HEAD}"

    monkeypatch.setattr(consumer, "exact_local_tvc_root", exact_root)
    monkeypatch.setattr(consumer, "local_tvc_control_root", lambda values: (control, f"{control}:PROGRESSION_READY"))
    monkeypatch.setattr(
        consumer,
        "run_tvc_private_source_progression",
        lambda control_root, runner, env: {
            "command":["python","-m",consumer.TVC_PROGRESSION_MODULE],
            "returncode":0,
            "result":{"state":"TVC_PR92_BROKER_VALIDATED","result":"PASS"},
            "result_observed":True,
            "credential_value_exposed":False,
            "consumer_credential_used":False,
            "consumer_network_source_fetch_performed":False,
            "tvc_private_source_service_may_perform_provider_read":True,
            "authority_effect":"EXISTING_TVC_PRIVATE_SOURCE_AUTHORITY_ONLY",
        },
    )
    monkeypatch.setattr(consumer, "terminal_validation", lambda runtime_root: True)
    observed = {}
    def runner(command, **kwargs):
        observed["command"] = list(command)
        observed["env"] = dict(kwargs["env"])
        return SimpleNamespace(returncode=0, stdout="{}\n", stderr="")

    receipt = consumer.consume(
        source,
        runtime,
        runner=runner,
        env={
            "HOME":str(tmp_path),
            "PATH":"/usr/bin",
            "STEGVERSE_TVC_CONTROL_ROOT":str(control),
            "GITHUB_TOKEN":"forbidden",
            "TVC_EPHEMERAL_GITHUB_TOKEN":"forbidden",
        },
    )
    assert receipt["state"] == "COMPLETED"
    assert receipt["private_source_progression_attempted"] is True
    assert receipt["private_source_progression"]["result"]["state"] == "TVC_PR92_BROKER_VALIDATED"
    assert receipt["observed_tvc_root"] == str(exact)
    assert receipt["network_source_fetch_performed_by_consumer"] is False
    assert receipt["terminal_validation_observed"] is True
    assert observed["command"][-2:] == ["--task-id", consumer.TARGET_TASK]
    assert "GITHUB_TOKEN" not in observed["env"]
    assert "TVC_EPHEMERAL_GITHUB_TOKEN" not in observed["env"]


def test_progression_credential_absence_remains_retryable(tmp_path, monkeypatch):
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    control = tmp_path / "TVC-control"
    source.mkdir()
    runtime.mkdir()
    control.mkdir()
    write_json(runtime / consumer.REQUEST_REL, request())
    monkeypatch.setattr(consumer, "exact_local_tvc_root", lambda values: (None, "missing"))
    monkeypatch.setattr(consumer, "local_tvc_control_root", lambda values: (control, f"{control}:PROGRESSION_READY"))
    monkeypatch.setattr(
        consumer,
        "run_tvc_private_source_progression",
        lambda control_root, runner, env: {
            "command":["python","-m",consumer.TVC_PROGRESSION_MODULE],
            "returncode":2,
            "result":{"state":"BLOCKED_CREDENTIAL_NOT_OBSERVED"},
            "result_observed":True,
            "credential_value_exposed":False,
            "consumer_credential_used":False,
            "consumer_network_source_fetch_performed":False,
            "tvc_private_source_service_may_perform_provider_read":True,
            "authority_effect":"EXISTING_TVC_PRIVATE_SOURCE_AUTHORITY_ONLY",
        },
    )
    receipt = consumer.consume(
        source,
        runtime,
        env={"HOME":str(tmp_path),"PATH":"/usr/bin","STEGVERSE_TVC_CONTROL_ROOT":str(control)},
    )
    assert receipt["state"] == "HANDOFF_READY"
    assert receipt["private_source_progression_attempted"] is True
    assert receipt["private_source_progression"]["result"]["state"] == "BLOCKED_CREDENTIAL_NOT_OBSERVED"
    assert receipt["runtime_execution_attempted"] is False
    assert receipt["second_machine_required"] is False
    assert receipt["network_source_fetch_performed_by_consumer"] is False



def test_terminal_validation_continues_into_current_base_compatibility(tmp_path, monkeypatch):
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    exact = tmp_path / "TVC-exact"
    control = tmp_path / "TVC-control"
    source.mkdir()
    runtime.mkdir()
    exact.mkdir()
    control.mkdir()
    admission_script = control / consumer.TVC_ADMISSION_SCRIPT
    admission_script.parent.mkdir(parents=True, exist_ok=True)
    admission_script.write_text("# admission\n", encoding="utf-8")

    value = request()
    value["request_id"] = "RESIDENT-EXEC-TVC-BROKER-VALIDATION-003"
    value["admission_compatibility_requested"] = True
    write_json(runtime / consumer.REQUEST_REL, value)
    entrypoint = runtime / consumer.TARGET_ENTRYPOINT
    entrypoint.parent.mkdir(parents=True, exist_ok=True)
    entrypoint.write_text("# bridge\n", encoding="utf-8")

    monkeypatch.setattr(consumer, "exact_local_tvc_root", lambda values: (exact, f"{exact}:{consumer.EXPECTED_HEAD}"))
    monkeypatch.setattr(consumer, "local_tvc_control_root", lambda values: (control, f"{control}:PROGRESSION_READY"))
    monkeypatch.setattr(consumer, "terminal_validation", lambda runtime_root: True)
    monkeypatch.setattr(
        consumer,
        "run_tvc_admission_compatibility",
        lambda control_root, runner, env: {
            "command":["python","-m",consumer.TVC_ADMISSION_MODULE],
            "returncode":0,
            "result":{
                "state":"TVC_PR92_BROKER_ADMISSION_ELIGIBLE",
                "validated_exact_sha":consumer.EXPECTED_HEAD,
                "source_bundle_file_count":16,
                "source_bundle_sha256":consumer.EXPECTED_BUNDLE_SHA256,
                "credential_used":False,
                "network_access_performed":False,
                "repository_writeback_performed":False,
                "merge_performed":False,
            },
            "result_observed":True,
            "admission_eligible":True,
            "consumer_credential_used":False,
            "consumer_network_access_performed":False,
            "repository_writeback_performed":False,
            "merge_performed":False,
            "authority_effect":"EXISTING_TVC_ADMISSION_COMPATIBILITY_AUTHORITY_ONLY",
        },
    )

    def runner(command, **kwargs):
        return SimpleNamespace(returncode=0, stdout="{}\n", stderr="")

    receipt = consumer.consume(
        source,
        runtime,
        runner=runner,
        env={
            "HOME":str(tmp_path),
            "PATH":"/usr/bin",
            "STEGVERSE_TVC_CONTROL_ROOT":str(control),
        },
    )
    assert receipt["state"] == "COMPLETED"
    assert receipt["terminal_validation_observed"] is True
    assert receipt["admission_compatibility_requested"] is True
    assert receipt["admission_compatibility_observed"] is True
    assert receipt["admission_compatibility"]["admission_eligible"] is True
    assert receipt["admission_compatibility"]["result"]["merge_performed"] is False


def test_repository_authority_handoff_is_nonsecret_and_tvc_owned(tmp_path):
    control = tmp_path / "TVC-control"
    control.mkdir()
    activator = control / consumer.TVC_REPOSITORY_AUTHORITY_ACTIVATOR
    activator.parent.mkdir(parents=True, exist_ok=True)
    activator.write_text("# activator\n", encoding="utf-8")
    observed = {}
    def runner(command, **kwargs):
        observed["command"] = list(command)
        observed["env"] = dict(kwargs["env"])
        request_id = command[command.index("--request-id") + 1]
        return SimpleNamespace(
            returncode=2,
            stdout=json.dumps({
                "state":"BLOCKED_CREDENTIAL_NOT_OBSERVED",
                "request_id":request_id,
                "credential_value_exposed":False,
                "authority_effect":"NONE",
            }) + "\n",
            stderr="",
        )
    result = consumer.run_tvc_repository_authority_handoff(
        control,
        request_id="RESIDENT-EXEC-TVC-BROKER-VALIDATION-003",
        runner=runner,
        env={"PATH":"/usr/bin","HOME":str(tmp_path)},
    )
    assert result["request_staged_or_owned"] is True
    assert result["downstream_request_id"].endswith("-repository-authority")
    assert "TVC_EPHEMERAL_GITHUB_TOKEN" not in observed["env"]
    assert "GITHUB_TOKEN" not in observed["env"]
    assert result["repository_write_authority"] is False
    assert result["credential_value_exposed"] is False


def test_terminal_validation_compatibility_hands_off_to_repository_authority(tmp_path, monkeypatch):
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    exact = tmp_path / "TVC-exact"
    control = tmp_path / "TVC-control"
    for p in (source, runtime, exact, control): p.mkdir()
    value = request()
    value["request_id"] = "RESIDENT-EXEC-TVC-BROKER-VALIDATION-003"
    value["admission_compatibility_requested"] = True
    value["repository_authority_continuation_requested"] = True
    write_json(runtime / consumer.REQUEST_REL, value)
    entrypoint = runtime / consumer.TARGET_ENTRYPOINT
    entrypoint.parent.mkdir(parents=True, exist_ok=True)
    entrypoint.write_text("# bridge\n", encoding="utf-8")
    admission_script = control / consumer.TVC_ADMISSION_SCRIPT
    admission_script.parent.mkdir(parents=True, exist_ok=True)
    admission_script.write_text("# admission\n", encoding="utf-8")

    monkeypatch.setattr(consumer, "exact_local_tvc_root", lambda values: (exact, f"{exact}:{consumer.EXPECTED_HEAD}"))
    monkeypatch.setattr(consumer, "local_tvc_control_root", lambda values: (control, f"{control}:PROGRESSION_READY"))
    monkeypatch.setattr(consumer, "terminal_validation", lambda runtime_root: True)
    monkeypatch.setattr(consumer, "run_tvc_admission_compatibility", lambda control_root, runner, env: {
        "returncode":0,"result_observed":True,"admission_eligible":True,
        "result":{"state":"TVC_PR92_BROKER_ADMISSION_ELIGIBLE"},
        "credential_value_exposed":False,"consumer_credential_used":False,
        "consumer_network_access_performed":False,"repository_writeback_performed":False,
        "merge_performed":False,"authority_effect":"EXISTING_TVC_ADMISSION_COMPATIBILITY_AUTHORITY_ONLY",
    })
    monkeypatch.setattr(consumer, "run_tvc_repository_authority_handoff", lambda control_root, request_id, runner, env: {
        "returncode":2,"result_observed":True,"request_staged_or_owned":True,
        "downstream_request_id":request_id+"-repository-authority",
        "result":{"state":"BLOCKED_CREDENTIAL_NOT_OBSERVED","request_id":request_id+"-repository-authority","credential_value_exposed":False},
        "credential_value_exposed":False,"consumer_credential_used":False,"repository_write_authority":False,
        "authority_effect":"NONE_HANDOFF_ONLY",
    })
    receipt = consumer.consume(source, runtime, runner=lambda command, **kwargs: SimpleNamespace(returncode=0,stdout="{}\n",stderr=""), env={"HOME":str(tmp_path),"PATH":"/usr/bin","STEGVERSE_TVC_CONTROL_ROOT":str(control)})
    assert receipt["state"] == "COMPLETED"
    assert receipt["admission_compatibility_observed"] is True
    assert receipt["repository_authority_continuation_requested"] is True
    assert receipt["repository_authority_handoff_observed"] is True
    assert receipt["repository_authority_handoff"]["repository_write_authority"] is False


def test_compatibility_requested_prevents_early_consumption(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    value = request()
    value["request_id"] = "RESIDENT-EXEC-TVC-BROKER-VALIDATION-003"
    value["admission_compatibility_requested"] = True
    digest = consumer.stable_hash(value)
    write_json(runtime / consumer.CONSUMPTION_REL, {
        "request_id":value["request_id"],
        "request_sha256":digest,
        "terminal_validation_observed":True,
        "admission_compatibility_observed":False,
    })
    monkeypatch.setattr(consumer, "terminal_validation", lambda runtime_root: True)
    assert consumer.previously_consumed(runtime, value, digest) is False
    retained = json.loads((runtime / consumer.CONSUMPTION_REL).read_text())
    retained["admission_compatibility_observed"] = True
    write_json(runtime / consumer.CONSUMPTION_REL, retained)
    assert consumer.previously_consumed(runtime, value, digest) is True


def test_repository_authority_requested_prevents_early_consumption(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    value = request()
    value["admission_compatibility_requested"] = True
    value["repository_authority_continuation_requested"] = True
    digest = consumer.stable_hash(value)
    write_json(runtime / consumer.CONSUMPTION_REL, {
        "request_id":value["request_id"],
        "request_sha256":digest,
        "terminal_validation_observed":True,
        "admission_compatibility_observed":True,
        "repository_authority_handoff_observed":False,
    })
    monkeypatch.setattr(consumer, "terminal_validation", lambda runtime_root: True)
    assert consumer.previously_consumed(runtime, value, digest) is False
    retained = json.loads((runtime / consumer.CONSUMPTION_REL).read_text())
    retained["repository_authority_handoff_observed"] = True
    write_json(runtime / consumer.CONSUMPTION_REL, retained)
    assert consumer.previously_consumed(runtime, value, digest) is True


def test_only_terminal_pass_marks_request_consumed(tmp_path):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    value = request()
    digest = consumer.stable_hash(value)
    write_json(runtime / consumer.CONSUMPTION_REL, {
        "request_id":value["request_id"],
        "request_sha256":digest,
        "terminal_validation_observed":True,
    })
    assert consumer.previously_consumed(runtime, value, digest) is False

    write_json(runtime / consumer.VALIDATION_RECEIPT_REL, {
        "state":"COMPLETED",
        "result":{
            "reason":"TVC_BROKER_VALIDATION_PASS",
            "expected_tvc_head":consumer.EXPECTED_HEAD,
            "source_head":consumer.EXPECTED_HEAD,
            "source_bundle_file_count":16,
            "source_bundle_sha256":consumer.EXPECTED_BUNDLE_SHA256,
        },
        "credential_authority":"TV/TVC",
        "authority_effect":"NONE_VALIDATION_ONLY",
    })
    assert consumer.previously_consumed(runtime, value, digest) is True


def test_private_source_candidate_is_builtin():
    assert str(consumer.PRIVATE_SOURCE_CANDIDATE) == "/var/lib/stegverse/private-source-read/materialized/tvc-pr92-broker-validation-b5288f99"
    assert consumer.TVC_PROGRESSION_MODULE == "scripts.advance_tvc_pr92_broker_validation"
    assert consumer.TVC_ADMISSION_MODULE == "scripts.evaluate_github_repository_operation_broker_admission"
    assert str(consumer.TVC_REPOSITORY_AUTHORITY_ACTIVATOR) == "scripts/activate_sv_dn1_repository_authority_request.py"


def test_hosted_environment_rejected():
    try:
        consumer.clean_env({"GITHUB_ACTIONS":"true","HOME":"/tmp","PATH":"/usr/bin"})
    except RuntimeError as exc:
        assert "hosted environment" in str(exc)
    else:
        raise AssertionError("hosted environment should be rejected")
