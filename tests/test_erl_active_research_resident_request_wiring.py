from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(rel: str, name: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resident_request_is_non_authorizing_and_exact_path():
    request = json.loads((ROOT / "control/resident-execution-request.d/erl-active-research-intr-runtime-binding-001.json").read_text())
    assert request["task_id"] == "SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001"
    assert request["cosv_task_vector"] == "40000100100000"
    assert request["canonical_boundary_path"] == ["EXTERNAL_SYSTEM", "STEGOS_ECOSYSTEM", "DEVICE_SYSTEM", "KV"]
    assert request["terminal_runtime_owner_task"] == "SHWP-DEVICE-KV-INTR-OBSERVATION-001"
    assert request["terminal_downstream_owner_ref"] == "StegVerse-Labs/continuity-vault-kit#79"
    assert request["provider_operation_reexecution_authorized"] is False
    assert request["request_granted_authority"] is False
    assert request["heartbeat_grants_execution_authority"] is False
    assert request["github_token_runtime_authority"] == "NONE"
    assert request["second_machine_required"] is False


def test_wiring_transform_is_idempotent_and_reuses_existing_runtime():
    mod = load_module("scripts/install_erl_resident_request_wiring.py", "erl_request_wiring")
    dispatcher = (
        'NONSECRET_ENV = (\n'
        '    "STEGVERSE_GOOGLE_DRIVE_CLIENT_ID", "STEGVERSE_OWNER_BINDING_DIGEST", "STEGVERSE_STEGFIN_SOURCE_ROOT",\n'
        ')\nCONSUMERS = (\n'
        '    ("stegos_kv_intr_chain", "scripts/consume_stegos_kv_intr_chain_request.py"),\n'
        ')\n'
    )
    transformed = mod.transform_dispatcher(dispatcher)
    assert 'erl_active_research_intr_runtime_binding' in transformed
    assert 'STEGVERSE_ERL_ROOT' in transformed
    assert 'STEGVERSE_ERL_ACTIVE_RESEARCH_DISPATCH_PATH' in transformed
    assert mod.transform_dispatcher(transformed) == transformed

    materializer = (
        'COPY_FILES = (\n'
        '    "scripts/consume_stegos_kv_intr_chain_request.py",\n'
        ')\nrequired = (\n'
        '        target_root / "scripts" / "consume_stegos_kv_intr_chain_request.py",\n'
        ')\n'
    )
    transformed_m = mod.transform_materializer(materializer)
    assert 'prepare_erl_active_research_intr_runtime_source.py' in transformed_m
    assert 'install_erl_resident_request_wiring.py' in transformed_m
    assert mod.transform_materializer(transformed_m) == transformed_m


def test_preparation_includes_request_wiring_installer():
    text = (ROOT / "scripts/prepare_erl_active_research_intr_runtime_source.py").read_text()
    assert "install_erl_resident_request_wiring.py" in text
    assert "REQUEST_WIRING_INSTALLER" in text


def test_consumer_no_request_is_non_authorizing(tmp_path: Path):
    mod = load_module(
        "control/resident-execution-request.d/consume-erl-active-research-intr-runtime-binding.py",
        "erl_request_consumer",
    )
    result = mod.consume(ROOT, tmp_path, env={"PATH": "/usr/bin"})
    assert result["state"] == "NO_REQUEST"
    assert result["runtime_execution_attempted"] is False
    assert result["authority_effect"] == "NONE"


def test_consumer_requires_source_preparation_before_inputs(tmp_path: Path):
    mod = load_module(
        "control/resident-execution-request.d/consume-erl-active-research-intr-runtime-binding.py",
        "erl_request_consumer_prep",
    )
    request_src = ROOT / "control/resident-execution-request.d/erl-active-research-intr-runtime-binding-001.json"
    request_dst = tmp_path / mod.REQUEST_REL
    request_dst.parent.mkdir(parents=True, exist_ok=True)
    request_dst.write_bytes(request_src.read_bytes())
    prep = tmp_path / mod.PREP
    prep.parent.mkdir(parents=True, exist_ok=True)
    prep.write_text("print('x')\n")

    class Result:
        returncode = 1
        stdout = ""
        stderr = "not prepared"

    result = mod.consume(ROOT, tmp_path, runner=lambda *a, **k: Result(), env={"PATH": "/usr/bin"})
    assert result["state"] == "SOURCE_PREPARATION_REQUIRED"
    assert result["transport_submission_attempted"] is False
    assert result["provider_operation_attempted"] is False
    assert result["authority_effect"] == "NONE_WAIT_STATE"
