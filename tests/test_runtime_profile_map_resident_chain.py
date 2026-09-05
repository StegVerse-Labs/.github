from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_runtime_profile_map_resident_chain.py"
spec = importlib.util.spec_from_file_location("runtime_profile_chain_validator", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_current_source_chain_validates() -> None:
    result = module.validate(ROOT)
    assert result["state"] == "SOURCE_CHAIN_VALID"
    assert result["stage_count"] == 5
    assert result["runtime_execution_observed"] is False
    assert result["execution_authority_granted"] is False


def test_missing_dispatch_binding_fails_closed(tmp_path: Path) -> None:
    dispatcher = tmp_path / "scripts" / "dispatch_resident_execution_requests.py"
    dispatcher.parent.mkdir(parents=True)
    dispatcher.write_text("CONSUMERS = ()\n", encoding="utf-8")
    for selector, request_rel, consumer_rel in module.STAGES:
        request = tmp_path / request_rel
        request.parent.mkdir(parents=True, exist_ok=True)
        request.write_text(json.dumps({
            "schema": "stegverse.resident-execution-request/v1",
            "state": "REQUESTED",
            "entrypoint": consumer_rel,
            "credential_authority": "TV/TVC",
            "github_token_required": False,
            "github_token_runtime_authority": "NONE",
            "heartbeat_grants_execution_authority": False,
            "oscillator_grants_execution_authority": False,
            "second_machine_required": False,
            "network_source_fetch_allowed": False,
            "request_granted_authority": False,
            "authority_effect": "NONE_REQUEST_ONLY",
        }), encoding="utf-8")
        consumer = tmp_path / consumer_rel
        consumer.parent.mkdir(parents=True, exist_ok=True)
        consumer.write_text("# consumer\n", encoding="utf-8")
    try:
        module.validate(tmp_path)
    except RuntimeError as exc:
        assert "dispatcher binding mismatch" in str(exc)
    else:
        raise AssertionError("expected fail-closed dispatcher mismatch")
