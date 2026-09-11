from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str, name: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_submission_input_rejects_non_loopback(tmp_path: Path):
    mod = load("scripts/submit_erl_active_research_intr_binding.py", "erl_submit_loopback")
    binding = tmp_path / "binding.json"
    binding.write_text("{}\n")
    body = {
        "schema": mod.INPUT_SCHEMA,
        "state": "READY",
        "task_id": mod.TASK_ID,
        "binding_ref": "binding.json",
        "ingress_url": "https://example.com/intr/materialization",
        "tvc_relay_authorization_id": "TVC-AUTH-EXISTING",
        "transport_origin": "TVC_RELAY_EGRESS",
        "request_grants_execution_authority": False,
        "provider_operation_authorized": False,
        "authority_effect": "NONE_INPUT_ONLY",
    }
    value = {**body, "input_hash": mod.sha_uri(body)}
    with pytest.raises(RuntimeError, match="loopback"):
        mod.validate_input(value, tmp_path)


def test_post_exact_uses_tvc_relay_headers_only():
    mod = load("scripts/submit_erl_active_research_intr_binding.py", "erl_submit_headers")
    captured = {}

    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return b"{}"

    def opener(req, timeout):
        captured["url"] = req.full_url
        captured["headers"] = {k.lower(): v for k, v in req.header_items()}
        captured["body"] = req.data
        captured["timeout"] = timeout
        return Response()

    mod.post_exact({"schema": "x"}, "http://127.0.0.1:7777/intr/materialization", "TVC-AUTH-EXISTING", opener=opener)
    assert captured["headers"]["x-stegverse-transport"] == "InTr"
    assert captured["headers"]["x-stegverse-transport-origin"] == "TVC_RELAY_EGRESS"
    assert captured["headers"]["x-stegverse-authorization-id"] == "TVC-AUTH-EXISTING"
    assert len(captured["headers"]["x-stegverse-payload-sha256"]) == 64


def test_profile_admission_requires_two_verified_upstream_hops():
    mod = load("scripts/submit_erl_active_research_intr_binding.py", "erl_submit_admission")
    request = {
        "materialization_id": "INTR-MAT-0123456789abcdef01234567",
        "operation_id": "ERL-ACTIVE-RESEARCH-TEST",
        "packet_id": "INTR-0123456789abcdef01234567",
        "payload_hash": "sha256:" + "a" * 64,
    }
    binding = {"x": 1}
    hop1 = {
        "schema": "stegverse.intr.hop_receipt/v1", "hop_index": 1,
        "packet_id": request["packet_id"], "payload_hash": request["payload_hash"],
        "prior_receipt_hash": None, "boundary_verification": "VERIFIED",
        "transition_state": "FORWARDED", "authority_transfer": False,
        "receipt_hash": "sha256:" + "1" * 64,
    }
    hop2 = {**hop1, "hop_index": 2, "prior_receipt_hash": hop1["receipt_hash"], "receipt_hash": "sha256:" + "2" * 64}
    terminal = {
        "boundary_path": ["DEVICE_SYSTEM", "KV"],
        "downstream_owner_ref": "StegVerse-Labs/continuity-vault-kit#79",
        "prior_transport_receipt_hash": hop2["receipt_hash"],
        "operation_id": request["operation_id"], "packet_id": request["packet_id"], "payload_hash": request["payload_hash"],
    }
    response = {
        "schema": mod.PROFILE_SCHEMA,
        "state": "PROFILE_ADMITTED_TERMINAL_MATERIALIZATION_PENDING",
        "materialization_id": request["materialization_id"],
        "operation_id": request["operation_id"], "packet_id": request["packet_id"], "payload_hash": request["payload_hash"],
        "transport_payload_sha256": mod.sha_uri(mod.canonical(binding)),
        "hop_receipts": [hop1, hop2], "terminal_materialization_request": terminal,
        "terminal_runtime_receipt_present": False, "provider_operation_reexecution_authorized": False,
        "credential_authority": "TV/TVC", "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_PROFILE_ADMISSION_ONLY",
    }
    mod.validate_admission(response, request, binding)
    bad = json.loads(json.dumps(response)); bad["hop_receipts"][1]["prior_receipt_hash"] = "sha256:" + "f" * 64
    with pytest.raises(RuntimeError, match="lineage"):
        mod.validate_admission(bad, request, binding)


def test_route_installer_normalizes_payload_hash_uri():
    mod = load("scripts/install_erl_active_research_universal_intr_route.py", "erl_route_normalize")
    source = (
        mod.IMPORT_BLOCK
        + 'def x():\n    pass\n'
        + 'def profile():\n    return {"profiles": ["HIL:Ingress", "SV002:PublicObservation", "ERL:ActiveResearch"],}\n'
        + 'ThreadingHTTPServer\n'
        + mod.OLD_ERL_ROUTE
    )
    transformed = mod.transform(source)
    assert 'transport_payload_sha256="sha256:"+' in transformed
    assert mod.OLD_ERL_ROUTE not in transformed


def test_request_wiring_registers_submission_consumer_and_submitter_copy():
    mod = load("scripts/install_erl_resident_request_wiring.py", "erl_wiring_submission")
    dispatcher = (
        'NONSECRET_ENV = (\n    "STEGVERSE_GOOGLE_DRIVE_CLIENT_ID", "STEGVERSE_OWNER_BINDING_DIGEST", "STEGVERSE_STEGFIN_SOURCE_ROOT",\n)\n'
        'CONSUMERS = (\n    ("stegos_kv_intr_chain", "scripts/consume_stegos_kv_intr_chain_request.py"),\n)\n'
    )
    out = mod.transform_dispatcher(dispatcher)
    assert "erl_active_research_intr_submission" in out
    materializer = 'COPY_FILES = (\n    "scripts/consume_stegos_kv_intr_chain_request.py",\n)\nrequired = (\n        target_root / "scripts" / "consume_stegos_kv_intr_chain_request.py",\n)\n'
    mout = mod.transform_materializer(materializer)
    assert "submit_erl_active_research_intr_binding.py" in mout
