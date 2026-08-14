from __future__ import annotations

import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "workers" / "local_source_generation_executor_worker.py"
spec = importlib.util.spec_from_file_location("local_source_generation_executor", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def config() -> dict:
    return {
        "source_generation_capability_id": "stegverse:capability:formalism-source-generation:v1",
        "local_model_capability_id": "stegverse:capability:sovereign-local-model:v1",
        "maximum_prompt_bytes": 524288,
        "maximum_file_count": 32,
        "maximum_total_bytes": 1048576,
        "secret_name_fragments": ["TOKEN", "SECRET", "PASSWORD", "API_KEY", "GITHUB_", "GH_", "OPENAI_"],
    }


def activation() -> dict:
    return {
        "schema": "stegverse.local-source-generation-activation-envelope/v0.1",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": False,
        "non_tv_tvc_secret_or_token_used": False,
        "source_generation": {
            "capability_id": "stegverse:capability:formalism-source-generation:v1",
            "capability_version": "1.0.0",
            "phase": "ACTIVATED",
            "existence_hash": "a" * 64,
            "activation_proof_ref": "receipt:source-generation:activation",
            "integration_evidence_refs": ["integration:source-generation"],
            "authority_ref": "StegVerse-Labs/StegCore:management/admissible-existence-capability-registry.json",
        },
        "local_model": {
            "capability_id": "stegverse:capability:sovereign-local-model:v1",
            "capability_version": "1.0.0",
            "phase": "ACTIVATED",
            "existence_hash": "b" * 64,
            "activation_proof_ref": "receipt:local-model:activation",
            "integration_evidence_refs": ["integration:local-model"],
            "runtime_proof_ref": "receipt:local-model:runtime",
        },
    }


def manifest() -> dict:
    return {
        "schema": "stegverse.owner-implementation-work-manifest/v0.1",
        "claim_state": "READY_FOR_SEPARATE_OWNER_ADMISSION",
        "delta_id": "DELTA-1",
        "owner_repository": "StegVerse-Labs/StegCore",
        "kind": "RUNTIME_IMPLEMENTATION",
        "objective": "Implement bounded example",
        "authority_ceiling": ["no_authority_expansion"],
        "proposed_paths": ["EXAMPLE_MIRROR_HANDOFF.md", "src/stegcore/example.py"],
    }


def test_dual_activation_is_required():
    prepared, error = module.validate_activation(config(), activation())
    assert error is None
    assert prepared is not None

    value = activation()
    value["source_generation"]["phase"] = "ADMISSIBLE"
    prepared, error = module.validate_activation(config(), value)
    assert prepared is None
    assert error == "SOURCE_GENERATION_CAPABILITY_NOT_ACTIVATED"

    value = activation()
    value["local_model"]["phase"] = "ADMISSIBLE"
    prepared, error = module.validate_activation(config(), value)
    assert prepared is None
    assert error == "LOCAL_MODEL_CAPABILITY_NOT_ACTIVATED"


def test_activation_proof_runtime_proof_and_tvtvc_are_required():
    value = activation()
    value["credential_authority"] = "OTHER"
    assert module.validate_activation(config(), value)[1] == "ACTIVATION_CREDENTIAL_AUTHORITY_INVALID"

    value = activation()
    value["source_generation"]["activation_proof_ref"] = ""
    assert module.validate_activation(config(), value)[1] == "GENERATOR_ACTIVATION_PROOF_MISSING"

    value = activation()
    value["local_model"]["runtime_proof_ref"] = ""
    assert module.validate_activation(config(), value)[1] == "LOCAL_MODEL_RUNTIME_PROOF_MISSING"


def test_child_environment_is_minimal_and_secret_free(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "must-not-flow")
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-flow")
    monkeypatch.setenv("PATH", "/usr/bin")
    env = module.sanitized_child_env(tmp_path)
    assert env["PATH"] == "/usr/bin"
    assert env["PYTHONPATH"] == str(tmp_path)
    assert "GITHUB_TOKEN" not in env
    assert "OPENAI_API_KEY" not in env
    assert module.child_env_is_secret_free(config(), env) is True


def test_request_binds_exact_local_source_hashes(tmp_path: Path):
    (tmp_path / "src/stegcore").mkdir(parents=True)
    (tmp_path / "src/stegcore/example.py").write_text("VALUE = 1\n", encoding="utf-8")
    request, error = module.build_request(config(), manifest(), tmp_path, "c" * 40)
    assert error is None
    assert request is not None
    assert request["expected_base_sha"] == "c" * 40
    rows = {row["path"]: row for row in request["source_files"]}
    assert rows["EXAMPLE_MIRROR_HANDOFF.md"]["exists"] is False
    assert rows["EXAMPLE_MIRROR_HANDOFF.md"]["source_sha256"] is None
    assert rows["src/stegcore/example.py"]["source_sha256"] == module.sha_text("VALUE = 1\n")
    assert rows["src/stegcore/example.py"]["content_utf8"] == "VALUE = 1\n"


def test_unsafe_or_unadmitted_paths_fail_closed(tmp_path: Path):
    value = manifest()
    value["proposed_paths"] = ["EXAMPLE_MIRROR_HANDOFF.md", "../escape.py"]
    assert module.build_request(config(), value, tmp_path, "d" * 40)[1] == "OWNER_PATH_SCOPE_INVALID"


def test_structured_response_is_strictly_scoped_and_handoff_first(tmp_path: Path):
    (tmp_path / "src/stegcore").mkdir(parents=True)
    (tmp_path / "src/stegcore/example.py").write_text("VALUE = 1\n", encoding="utf-8")
    request, error = module.build_request(config(), manifest(), tmp_path, "e" * 40)
    assert error is None and request is not None
    response = {
        "schema": "stegverse.local-source-generation-response/v0.1",
        "delta_id": "DELTA-1",
        "owner_repository": "StegVerse-Labs/StegCore",
        "new_branch": "feat/delta-1",
        "commit_message": "Implement delta 1",
        "files": [
            {"path": "EXAMPLE_MIRROR_HANDOFF.md", "content_utf8": "# Example\n"},
            {"path": "src/stegcore/example.py", "content_utf8": "VALUE = 2\n"},
        ],
    }
    files, error = module.validate_model_response(config(), manifest(), request, response)
    assert error is None and files is not None
    assert files[0]["path"] == "EXAMPLE_MIRROR_HANDOFF.md"
    assert files[1]["expected_source_sha256"] == module.sha_text("VALUE = 1\n")
    assert files[1]["replacement_sha256"] == module.sha_text("VALUE = 2\n")

    bad = json.loads(json.dumps(response))
    bad["files"][1]["path"] = "src/stegcore/outside.py"
    assert module.validate_model_response(config(), manifest(), request, bad)[1] == "SOURCE_GENERATION_RESPONSE_PATH_OR_CONTENT_INVALID"

    bad = json.loads(json.dumps(response))
    bad["files"] = [bad["files"][1], bad["files"][0]]
    assert module.validate_model_response(config(), manifest(), request, bad)[1] == "SOURCE_GENERATION_HANDOFF_NOT_FIRST"


def test_chat_fallback_never_accepts_unstructured_text():
    value = {"choices": [{"message": {"content": "not-json"}}], "usage": {"total_tokens": 3}}
    parsed, error, meta = module.extract_response(value)
    assert parsed is None
    assert error == "LOCAL_MODEL_STRUCTURED_OUTPUT_INVALID"
    assert meta["route"] == "chat"


def test_direct_structured_response_is_preferred():
    value = {"schema": "stegverse.local-source-generation-response/v0.1", "delta_id": "D", "owner_repository": "R", "files": []}
    parsed, error, meta = module.extract_response(value)
    assert error is None
    assert parsed == value
    assert meta["route"] == "structured"
