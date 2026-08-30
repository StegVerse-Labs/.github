from pathlib import Path
import ast, json

ROOT=Path(__file__).resolve().parents[1]

def test_tvc_pr92_bootstrap_is_exact_and_credential_neutral():
    src=(ROOT/"scripts/bootstrap_tvc_pr92_validation_source.py").read_text()
    assert 'EXPECTED_HEAD="b5288f9910ada26c6ab2e9bca3f7701afaae2cef"' in src
    assert 'source_repository":"StegVerse-Labs/TVC"' in src
    assert 'reference_mode":"IMMUTABLE_COMMIT"' in src
    assert 'systemctl","start",SERVICE' in src
    assert "TVC_EPHEMERAL_GITHUB_TOKEN" not in src
    assert "GITHUB_TOKEN" not in src
    ast.parse(src)

def test_request_authorizes_only_existing_private_source_service_delegation():
    req=json.loads((ROOT/"control/resident-execution-request.d/tvc-repository-broker-validation-001.json").read_text())
    assert req["private_source_bootstrap_allowed"] is True
    assert req["private_source_bootstrap_service"]=="stegtvc-private-source-read.service"
    assert req["private_source_bootstrap_credential_transport"]=="SYSTEMD_LOADCREDENTIAL"
    assert req["credential_material_allowed"] is False
    assert req["github_token_runtime_authority"]=="NONE"

def test_consumer_uses_bootstrap_only_when_exact_root_absent():
    src=(ROOT/"scripts/consume_tvc_broker_validation_request.py").read_text()
    assert "bootstrap_tvc_pr92_validation_source" in src
    assert 'if tvc_root is None:' in src
    assert 'bootstrap_receipt.get("state") == "READY"' in src


def test_consumer_terminal_state_is_bound_to_exact_bundle_digest():
    src=(ROOT/"scripts/consume_tvc_broker_validation_request.py").read_text()
    assert 'EXPECTED_BUNDLE_SHA256 = _HANDOFF_EXECUTION["expected_source_bundle_sha256"]' in src
    assert 'result.get("source_bundle_sha256") == EXPECTED_BUNDLE_SHA256' in src
