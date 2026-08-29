from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "hil_intr_profiled_ingress",
    ROOT / "workers/hil_intr_profiled_ingress.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_profile_uses_shared_gateway_without_authority_inflation():
    profile = mod.build_profile(tls_enabled=False)
    assert profile["schema"] == "stegverse.hil-intr-materialization-ingress-profile/v1"
    assert profile["state"] == "ACTIVE_SOVEREIGN_INTR_INGRESS"
    assert profile["profile_path"] == "/intr/profile"
    assert profile["materialization_path"] == "/intr/materialization"
    assert profile["public_tls_terminated_by"] == "STEGVERSE_SHARED_SERVICE_GATEWAY"
    assert profile["event_triggered"] is True
    assert profile["always_on_receiver_required"] is False
    assert profile["second_user_device_required"] is False
    assert profile["g18_required"] is False
    assert profile["runtime_execution_attempted"] is False
    assert profile["hil_receiver_readiness_claimed"] is False
    assert profile["hil_custody_claimed"] is False
    assert profile["credential_authority"] == "TV/TVC"
    assert profile["github_token_runtime_authority"] == "NONE"
    assert profile["execution_authority"] == "NONE"
    assert profile["authority_effect"] == "NONE_DISCOVERY_EVIDENCE_ONLY"


def test_profile_wrapper_preserves_existing_post_handler():
    assert issubclass(mod.ProfiledIngressHandler, mod.ingress.IngressHandler)
    assert mod.ProfiledIngressHandler.do_POST is mod.ingress.IngressHandler.do_POST
