from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = importlib.util.spec_from_file_location(
    "chain_authorization_mapping",
    ROOT / "scripts/continue_stegverse001_evidence_chain.py",
)
M = importlib.util.module_from_spec(S)
assert S.loader
S.loader.exec_module(M)


def test_current_iphone_canonical_authorization_source_maps_true():
    source = {
        "authorized_execution_source": "EXTERNAL_WORKERCOORDINATOR_TVC_BOUND_ENVELOPE",
        "state": "COMPLETED",
    }
    assert M.authorized_execution_state(source) is True


def test_legacy_explicit_authorized_execution_true_remains_supported():
    assert M.authorized_execution_state({"authorized_execution": True}) is True


def test_explicit_denial_remains_false_even_with_correct_output():
    source = {
        "authorized_execution": False,
        "authorized_execution_source": "UNAUTHORIZED_OTHER_SOURCE",
        "state": "COMPLETED",
    }
    assert M.authorized_execution_state(source) is False


def test_unknown_source_does_not_infer_authority():
    source = {"state": "COMPLETED", "authorized_execution_source": "UNKNOWN"}
    assert M.authorized_execution_state(source) == "NOT_ESTABLISHED"


def test_exact_canonical_source_constant_is_pinned():
    assert M.CANONICAL_CURRENT_IPHONE_AUTHORIZATION_SOURCE == "EXTERNAL_WORKERCOORDINATOR_TVC_BOUND_ENVELOPE"
