from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_independent_ecosystem_chat_parent.py"
spec = importlib.util.spec_from_file_location("independent_ecosystem_chat_parent_same_device", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def process_proof() -> dict:
    return {
        "endpoint": "http://127.0.0.1:7777",
        "endpoint_transport": "PRIVATE_LOOPBACK_HTTP",
        "predicates": {
            "real_model_process_observed": True,
            "private_endpoint_only": True,
            "browser_service_worker_runtime_observed": False,
            "device_local_intercepted_endpoint": False,
            "network_egress_required": False,
            "real_inference_response_observed": True,
        },
    }


def device_proof() -> dict:
    return {
        "endpoint": mod.DEVICE_LOCAL_MODEL_ENDPOINT,
        "endpoint_transport": "SERVICE_WORKER_LOCAL_INTERCEPT",
        "service_worker_scope": "https://stegverse.org/stegos-bootstrap/",
        "predicates": {
            "real_model_process_observed": False,
            "private_endpoint_only": False,
            "browser_service_worker_runtime_observed": True,
            "device_local_intercepted_endpoint": True,
            "network_egress_required": False,
            "real_inference_response_observed": True,
        },
    }


def test_process_runtime_surface_remains_accepted() -> None:
    surface = mod.classify_sovereign_runtime_surface(process_proof())
    assert surface["sovereign_runtime_execution_surface_observed"] is True
    assert surface["runtime_execution_surface"] == "PRIVATE_PROCESS"
    assert surface["real_model_process_observed"] is True
    assert surface["private_endpoint_only"] is True
    assert surface["device_local_runtime_observed"] is False


def test_current_iphone_service_worker_surface_is_accepted_without_falsifying_process_predicates() -> None:
    surface = mod.classify_sovereign_runtime_surface(device_proof())
    assert surface["sovereign_runtime_execution_surface_observed"] is True
    assert surface["runtime_execution_surface"] == "CURRENT_USER_IPHONE_SERVICE_WORKER"
    assert surface["real_model_process_observed"] is False
    assert surface["private_endpoint_only"] is False
    assert surface["browser_service_worker_runtime_observed"] is True
    assert surface["device_local_intercepted_endpoint"] is True
    assert surface["network_egress_required"] is False
    assert surface["device_local_runtime_observed"] is True


def test_partial_device_surface_fails_closed() -> None:
    proof = device_proof()
    proof["predicates"]["real_inference_response_observed"] = False
    surface = mod.classify_sovereign_runtime_surface(proof)
    assert surface["sovereign_runtime_execution_surface_observed"] is False
    assert surface["runtime_execution_surface"] == "UNVERIFIED"


def test_wrong_service_worker_endpoint_fails_closed() -> None:
    proof = device_proof()
    proof["endpoint"] = "https://example.invalid/local-model"
    surface = mod.classify_sovereign_runtime_surface(proof)
    assert surface["sovereign_runtime_execution_surface_observed"] is False


def test_source_uses_aggregate_surface_for_terminal_activation() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert '"sovereign_runtime_execution_surface_observed"' in text
    assert '"device_local_runtime_observed"' in text
    assert '"runtime_execution_surface"' in text
    required = text.split("required_true = (", 1)[1].split(")", 1)[0]
    assert '"sovereign_runtime_execution_surface_observed"' in required
    assert '"real_model_process_observed"' not in required
    assert '"private_endpoint_only"' not in required
