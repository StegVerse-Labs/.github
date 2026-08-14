from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "workers" / "admissible_source_generation_capability_worker.py"
spec = importlib.util.spec_from_file_location("source_generation_capability", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

validate_generation_result = module.validate_generation_result
build_source_packet = module.build_source_packet


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def config() -> dict:
    return {
        "capability_id": "stegverse:capability:formalism-source-generation:v1",
        "capability_version": "1.0.0",
        "require_activated_capability": True,
        "require_activation_proof": True,
        "require_integration_evidence": True,
        "require_runtime_proof": True,
        "require_teardown_or_reconstruction_evidence": True,
        "allowed_lifetime_classes": ["ONE_SHOT_OPERATION", "SHORT_LIVED_WORKER"],
        "maximum_file_count": 32,
        "maximum_total_bytes": 1048576,
    }


def manifest() -> dict:
    return {
        "schema": "stegverse.owner-implementation-work-manifest/v0.1",
        "claim_state": "READY_FOR_SEPARATE_OWNER_ADMISSION",
        "delta_id": "delta-1",
        "owner_repository": "StegVerse-Labs/StegCore",
        "proposed_paths": [
            "EXAMPLE_MIRROR_HANDOFF.md",
            "src/stegcore/example.py",
        ],
    }


def result() -> dict:
    handoff = "# handoff\n"
    source = "VALUE = 1\n"
    return {
        "schema": "stegverse.local-source-generation-result/v0.1",
        "delta_id": "delta-1",
        "owner_repository": "StegVerse-Labs/StegCore",
        "base_ref": "main",
        "expected_base_sha": "a" * 40,
        "new_branch": "feat/example",
        "commit_message": "Implement example",
        "generator_capability_id": "stegverse:capability:formalism-source-generation:v1",
        "generator_capability_version": "1.0.0",
        "generator_existence_hash": "b" * 64,
        "generator_phase": "ACTIVATED",
        "generator_activation_proof_ref": "receipt:source-generation:activation",
        "generator_integration_evidence_refs": ["integration:source-generation"],
        "generator_authority_ref": "ae:formalism-source-generation:v1",
        "generator_profile_ref": "profile:least-stable-source-generation:v1",
        "local_model_capability_id": "stegverse:capability:sovereign-local-model:v1",
        "local_model_phase": "ACTIVATED",
        "local_model_activation_proof_ref": "receipt:local-model:activation",
        "model_runtime_proof_ref": "receipt:local-model:runtime-proof",
        "execution_identity": "exec:source-generation:1",
        "lifetime_class": "ONE_SHOT_OPERATION",
        "persistent_execution_used": False,
        "teardown_or_reconstruction_evidence_ref": "receipt:teardown:1",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": False,
        "non_tv_tvc_secret_or_token_used": False,
        "consumer_credential_present": False,
        "files": [
            {
                "path": "EXAMPLE_MIRROR_HANDOFF.md",
                "content_utf8": handoff,
                "expected_source_sha256": None,
                "replacement_sha256": sha(handoff),
            },
            {
                "path": "src/stegcore/example.py",
                "content_utf8": source,
                "expected_source_sha256": "c" * 64,
                "replacement_sha256": sha(source),
            },
        ],
    }


def codes(error: str | None) -> str:
    return error or ""


def test_valid_activated_one_shot_result_emits_exact_packet():
    prepared, error = validate_generation_result(config(), manifest(), result())
    assert error is None
    assert prepared is not None
    packet = build_source_packet(config(), prepared)
    assert packet["schema"] == "stegverse.owner-source-generation-packet/v0.1"
    assert packet["source_generation_authorized"] is True
    assert packet["generator_phase"] == "ACTIVATED"
    assert packet["local_model_phase"] == "ACTIVATED"
    assert packet["persistent_execution_used"] is False
    assert packet["credential_authority"] == "TV/TVC"
    assert packet["github_token_runtime_authority"] is False
    assert packet["consumer_credential_present"] is False
    assert packet["non_tv_tvc_secret_or_token_used"] is False


def test_declared_or_admissible_capability_cannot_generate_source():
    value = result()
    value["generator_phase"] = "ADMISSIBLE"
    prepared, error = validate_generation_result(config(), manifest(), value)
    assert prepared is None
    assert codes(error) == "GENERATOR_CAPABILITY_NOT_ACTIVATED"


def test_model_availability_does_not_replace_local_model_activation():
    value = result()
    value["local_model_phase"] = "ADMISSIBLE"
    value["model_available"] = True
    prepared, error = validate_generation_result(config(), manifest(), value)
    assert prepared is None
    assert codes(error) == "LOCAL_MODEL_NOT_ACTIVATED"


def test_activation_requires_proof_and_integration_evidence():
    value = result()
    value["generator_activation_proof_ref"] = ""
    prepared, error = validate_generation_result(config(), manifest(), value)
    assert prepared is None
    assert codes(error) == "GENERATOR_ACTIVATION_PROOF_MISSING"

    value = result()
    value["generator_integration_evidence_refs"] = []
    prepared, error = validate_generation_result(config(), manifest(), value)
    assert prepared is None
    assert codes(error) == "GENERATOR_INTEGRATION_EVIDENCE_MISSING"


def test_persistent_execution_fails_closed():
    value = result()
    value["persistent_execution_used"] = True
    prepared, error = validate_generation_result(config(), manifest(), value)
    assert prepared is None
    assert codes(error) == "PERSISTENT_EXECUTION_NOT_ADMITTED"


def test_unadmitted_lifetime_fails_closed():
    value = result()
    value["lifetime_class"] = "PERSISTENT_STATEFUL_MICRONODE"
    prepared, error = validate_generation_result(config(), manifest(), value)
    assert prepared is None
    assert codes(error) == "LIFETIME_CLASS_NOT_ADMITTED"


def test_teardown_or_reconstruction_evidence_required():
    value = result()
    value["teardown_or_reconstruction_evidence_ref"] = ""
    prepared, error = validate_generation_result(config(), manifest(), value)
    assert prepared is None
    assert codes(error) == "TEARDOWN_OR_RECONSTRUCTION_EVIDENCE_MISSING"


def test_non_tvtvc_or_consumer_credential_fails_closed():
    value = result()
    value["non_tv_tvc_secret_or_token_used"] = True
    prepared, error = validate_generation_result(config(), manifest(), value)
    assert prepared is None
    assert codes(error) == "NON_TV_TVC_SECRET_OR_TOKEN_USED"

    value = result()
    value["consumer_credential_present"] = True
    prepared, error = validate_generation_result(config(), manifest(), value)
    assert prepared is None
    assert codes(error) == "CONSUMER_CREDENTIAL_PRESENT"


def test_path_scope_and_handoff_first_are_enforced():
    value = result()
    value["files"][1]["path"] = "src/stegcore/not-admitted.py"
    prepared, error = validate_generation_result(config(), manifest(), value)
    assert prepared is None
    assert codes(error).startswith("PATH_NOT_ADMITTED:")

    value = result()
    value["files"] = [value["files"][1], value["files"][0]]
    prepared, error = validate_generation_result(config(), manifest(), value)
    assert prepared is None
    assert codes(error) == "HANDOFF_NOT_FIRST_GENERATED_FILE"


def test_replacement_hash_mismatch_fails_closed():
    value = result()
    value["files"][0]["replacement_sha256"] = "0" * 64
    prepared, error = validate_generation_result(config(), manifest(), value)
    assert prepared is None
    assert codes(error).startswith("REPLACEMENT_SHA_MISMATCH:")
