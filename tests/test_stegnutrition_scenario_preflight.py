from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def _entrypoint_module():
    path = ROOT / "workers/stegnutrition_continuation_entrypoint.py"
    spec = importlib.util.spec_from_file_location("stegnutrition_scenario_preflight_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _passing_result() -> dict:
    return {
        "state": "PASS",
        "execution": "LOCAL_ONLY",
        "github_token_required": False,
        "hosted_inference_required": False,
        "authority_effect": "NONE",
        "scenario_count_positive": True,
        "usda_bound": True,
        "photo_portion_interval_bound": True,
        "evidence_ids_bound": True,
        "failed_quality_gate_rejected": True,
        "missing_nutrition_rejected": True,
        "real_semantic_accuracy_qualified_by_this_verifier": False,
    }


def test_scenario_verifier_is_a_required_current_surface() -> None:
    entrypoint = _entrypoint_module()
    assert entrypoint.SCENARIO_VERIFIER == "scripts/verify_scenario_provider_no_network.py"
    assert entrypoint.SCENARIO_VERIFIER in entrypoint.CURRENT_REQUIRED_SURFACES


def test_scenario_preflight_accepts_only_local_no_token_non_authorizing_result(tmp_path: Path) -> None:
    entrypoint = _entrypoint_module()
    with mock.patch.object(entrypoint, "_run_json_verifier", return_value=_passing_result()) as run:
        entrypoint._run_scenario_provider_preflight(tmp_path)
    run.assert_called_once_with(
        tmp_path,
        "scripts/verify_scenario_provider_no_network.py",
        label="scenario provider verifier",
    )


def test_scenario_preflight_rejects_overstated_real_semantic_qualification(tmp_path: Path) -> None:
    entrypoint = _entrypoint_module()
    result = _passing_result()
    result["real_semantic_accuracy_qualified_by_this_verifier"] = True
    with mock.patch.object(entrypoint, "_run_json_verifier", return_value=result):
        try:
            entrypoint._run_scenario_provider_preflight(tmp_path)
        except entrypoint.ReceiptContractError as exc:
            assert "overstated real semantic qualification" in str(exc)
        else:
            raise AssertionError("scenario preflight must reject synthetic mechanics as real semantic qualification")


def test_scenario_preflight_rejects_hosted_or_token_requiring_path(tmp_path: Path) -> None:
    entrypoint = _entrypoint_module()
    result = _passing_result()
    result["hosted_inference_required"] = True
    with mock.patch.object(entrypoint, "_run_json_verifier", return_value=result):
        try:
            entrypoint._run_scenario_provider_preflight(tmp_path)
        except entrypoint.ReceiptContractError as exc:
            assert "hosted inference" in str(exc)
        else:
            raise AssertionError("hosted inference must fail closed")


def test_scenario_preflight_rejects_missing_binding_predicate(tmp_path: Path) -> None:
    entrypoint = _entrypoint_module()
    result = _passing_result()
    result["evidence_ids_bound"] = False
    with mock.patch.object(entrypoint, "_run_json_verifier", return_value=result):
        try:
            entrypoint._run_scenario_provider_preflight(tmp_path)
        except entrypoint.ReceiptContractError as exc:
            assert "evidence_ids_bound" in str(exc)
        else:
            raise AssertionError("missing scenario binding predicate must fail closed")
