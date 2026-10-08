"""Master Records boundary migration: readers accept the new organization-record
names and the legacy names; writers emit only the new names."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "scripts"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stegagents = load("compat_stegagents_worker", "workers/stegagents_governed_runtime_worker.py")
fanout = load("compat_endpoint_fanout_worker", "workers/endpoint_fanout_sovereign_runtime_worker.py")
lifecycle = load("compat_reusable_task_lifecycle", "workers/reusable_task_lifecycle.py")
custody = load("compat_canonical_state_transition_custody", "workers/canonical_state_transition_custody.py")
profile_map = load("compat_validate_runtime_profile_map", "scripts/validate_runtime_profile_map.py")
first_round = load("compat_sv_dn1_sdk_first_round_worker", "workers/sv_dn1_sdk_first_round_worker.py")
manifest_ingress = load("compat_manifest_state_transition_intr_ingress", "workers/manifest_state_transition_intr_ingress.py")
shwp_consumer = load("compat_consume_shwp_manifest_invocation", "scripts/consume_shwp_manifest_invocation.py")
shwp_bootstrap = load("compat_shwp_manifest_intr_event_bootstrap", "workers/shwp_manifest_intr_event_bootstrap.py")
first_round_chain = load("compat_run_sv_dn1_first_round_chain", "scripts/run_sv_dn1_first_round_chain.py")


@pytest.mark.parametrize("field", ["master_records_organization_record_status", "record_status", "master_records_custody_status"])
def test_stegagents_governance_record_status_accepts_new_and_legacy(field: str) -> None:
    assert stegagents.organization_record_status({field: "RECORDED"}) == "RECORDED"
    assert stegagents.organization_record_status({}) is None


def test_stegagents_new_name_wins_over_legacy() -> None:
    governance = {"master_records_organization_record_status": "RECORDED", "master_records_custody_status": "FAILED"}
    assert stegagents.organization_record_status(governance) == "RECORDED"


@pytest.mark.parametrize("field", ["master_records_organization_record_status", "master_records_custody_status"])
def test_stegagents_purpose_result_validates_with_either_status_field(field: str) -> None:
    profile = stegagents._profile(stegagents.PURPOSE_TASK_ID)
    result = {
        "state": "GOVERNED_PURPOSE_BOUND_WORKER_RETURNED",
        "execution_authority": False,
        "self_authorization_allowed": False,
        "provider_operation_required": False,
        "credential_authority": "TV/TVC",
        "credential_material_present": False,
        "records_only": True,
        "worker_live_after_close": False,
        "continued_authority_after_retirement": False,
        "governance": {
            "chain_verified": True,
            "transaction_identity_continuous": True,
            field: "RECORDED",
            "external_side_effect": False,
        },
        "master_records_reconstruction": {"operation_transition_custody_status": "RECORDED", "operation_receipt_ids": ["OR1"]},
        "purpose_bound_worker_result": {
            "callable_retained": False,
            "executor_reference_retained": False,
            "lifecycle_receipts": [{"phase": p} for p in ("MATERIALIZED", "INVOCATION_STARTED", "TASK_COMPLETED", "RETIRED")],
        },
    }
    stegagents._validate_result(profile, result)
    result["governance"].pop(field)
    with pytest.raises(RuntimeError, match="organization record missing"):
        stegagents._validate_result(profile, result)


@pytest.mark.parametrize("field", ["record_status", "master_records_organization_record_status", "custody_status"])
def test_endpoint_fanout_reads_continuity_vault_kit_record_status(field: str) -> None:
    assert fanout.master_records_record_status({field: "TEST_ONLY_RECORDED"}) == "TEST_ONLY_RECORDED"
    assert fanout.master_records_record_status(None) is None


def test_endpoint_fanout_new_names_win_over_legacy() -> None:
    result = {"master_records_organization_record_status": "RECORDED", "custody_status": "FAILED"}
    assert fanout.master_records_record_status(result) == "RECORDED"


def test_stegagents_short_new_name_wins_over_legacy() -> None:
    governance = {"record_status": "RECORDED", "master_records_custody_status": "FAILED"}
    assert stegagents.organization_record_status(governance) == "RECORDED"


def test_endpoint_fanout_reader_has_no_bare_legacy_literal() -> None:
    source = (ROOT / "workers/endpoint_fanout_sovereign_runtime_worker.py").read_text(encoding="utf-8")
    assert source.count('"custody_status"') == 1  # only the LEGACY_ constant


def test_reusable_task_request_emits_organization_record_names() -> None:
    manifest = {"invocation_id": "I1", "reusable_task_id": "RT1", "manifest_hash": "sha256:" + "0" * 64}
    request = lifecycle.build_custody_request(
        manifest=manifest, trigger_receipt={}, runner_result={}, runner_expiry={}, residual_recording={},
    )
    assert request["schema"] == "stegverse.reusable-task-master-records-organization-record-request/v1"
    assert request["record_requested"] is True
    assert "custody_requested" not in request
    assert lifecycle.LEGACY_ORGANIZATION_RECORD_REQUEST_SCHEMA == "stegverse.reusable-task-master-records-custody-request/v1"


@pytest.mark.parametrize("field", ["master_records_organization_record_ordinal", "master_records_custody_ordinal"])
def test_reconstruction_ordinal_accepts_new_and_legacy(field: str) -> None:
    assert custody.organization_record_ordinal({field: 7}) == 7


@pytest.mark.parametrize("module_name", ["master_records_organization_record_api", "master_records_custody_api"])
def test_local_binding_finds_new_or_legacy_master_records_api_module(tmp_path: Path, module_name: str) -> None:
    services = tmp_path / "services"
    services.mkdir()
    (services / f"{module_name}.py").write_text("", encoding="utf-8")
    assert custody._organization_record_api_module(tmp_path) == module_name


def test_local_binding_prefers_new_master_records_api_module(tmp_path: Path) -> None:
    services = tmp_path / "services"
    services.mkdir()
    for name in ("master_records_organization_record_api", "master_records_custody_api"):
        (services / f"{name}.py").write_text("", encoding="utf-8")
    assert custody._organization_record_api_module(tmp_path) == "master_records_organization_record_api"
    assert custody._organization_record_api_module(tmp_path / "missing") is None


def _runtime_map(value: str) -> dict:
    data = json.loads((ROOT / "control/runtime-profile-map.json").read_text(encoding="utf-8"))
    data["authority"]["observed_reality_authority"] = value
    return data


@pytest.mark.parametrize("value", ["ORGANIZATION", "MASTER_RECORDS"])
def test_runtime_profile_map_accepts_organization_and_legacy_observed_reality(value: str) -> None:
    assert profile_map.validate(_runtime_map(value))["state"] == "PASS"


def test_runtime_profile_map_rejects_other_observed_reality_authority() -> None:
    with pytest.raises(Exception, match="observed reality authority drift"):
        profile_map.validate(_runtime_map("INTERLOCK_INTR"))


def test_runtime_profile_map_writers_emit_organization() -> None:
    data = json.loads((ROOT / "control/runtime-profile-map.json").read_text(encoding="utf-8"))
    assert data["authority"]["observed_reality_authority"] == "ORGANIZATION"
    for rel in ("scripts/build_runtime_profile_map.py", "scripts/build_runtime_profile_map_custody_package.py",
                "scripts/build_canonical_work_intr_request.py"):
        source = (ROOT / rel).read_text(encoding="utf-8")
        assert '"observed_reality_authority": "ORGANIZATION"' in source
        assert '"observed_reality_authority": "MASTER_RECORDS"' not in source


@pytest.mark.parametrize("field", ["master_records_organization_record_status", "master_records_custody_status"])
def test_sdk_result_record_status_readers_accept_new_and_legacy(field: str) -> None:
    assert first_round.organization_record_status({field: "RECORDED"}) == "RECORDED"
    assert manifest_ingress.organization_record_status({field: "RECORDED"}) == "RECORDED"
    receipt = {field: "RECORDED"}
    assert first_round_chain._receipt_field(receipt, "master_records_organization_record_status") == "RECORDED"


def test_sdk_mcp_validation_program_accepts_new_and_legacy_status() -> None:
    source = (ROOT / "workers/sdk_mcp_canonical_validation_worker.py").read_text(encoding="utf-8")
    namespace: dict = {}
    start = source.index("ORGANIZATION_RECORD_STATUS_FIELD =")
    end = source.index("root = Path.home()", start)
    exec(source[start:end], namespace)
    for field in ("master_records_organization_record_status", "master_records_custody_status"):
        assert namespace["organization_record_status"]({field: "RECORDED"}) == "RECORDED"


@pytest.mark.parametrize("field", [
    "organization_master_records_organization_record_observed",
    "organization_master_records_closure_observed",
])
def test_organization_record_observed_readers_accept_new_and_legacy(field: str) -> None:
    for module in (shwp_consumer, shwp_bootstrap):
        assert module.organization_record_observed({field: False}) is False
        assert module.organization_record_observed({field: True}) is True
        assert module.organization_record_observed({}) is None


# --- Part B: in-repository identifiers renamed to organization-record names ---

disposition = load("compat_sv002_adversarial_disposition", "scripts/evaluate_sv002_adversarial_disposition.py")
observation = load("compat_sv002_adversarial_observation", "scripts/evaluate_sv002_adversarial_observation.py")


def test_predecessor_reconstruction_helper_keeps_legacy_name() -> None:
    new = custody.require_predecessor_master_records_organization_record
    assert getattr(custody, "require_predecessor_master_records_closure") is new
    assert custody.require_predecessor_master_records_organization_record(None, successor_transition_id="T") == (None, [])


@pytest.mark.parametrize("field", ["master_records_organization_record_valid", "master_records_custody_valid"])
def test_sv002_disposition_accepts_new_and_legacy_record_field(field: str) -> None:
    case = {"output_correct": True, "authorized_execution": True, "observation_valid": True,
            field: True, "reconstruction_valid": True, "receipt_lineage_valid": True}
    assert disposition.disposition(case)["disposition"] == "OBSERVED"
    case[field] = False
    assert disposition.disposition(case)["reason"] == "CUSTODY_NOT_ESTABLISHED"


@pytest.mark.parametrize("field", ["master_records_organization_record", "master_records_custody"])
def test_sv002_observation_accepts_new_and_legacy_record_field(field: str) -> None:
    inputs = {field: "PASS", "reconstruction_state": "PASS", "authorized_execution": True, "observation_valid": True}
    assert observation.evaluate(inputs)["disposition"] == "OBSERVED"
    inputs[field] = "SUBSTITUTED"
    assert observation.evaluate(inputs)["disposition"] == "FAIL_CLOSED"


def test_dispatcher_accepts_legacy_wait_states() -> None:
    source = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text(encoding="utf-8")
    assert "*LEGACY_ACCEPTED_WAIT_STATES," in source
    assert '"WAITING_FOR_MASTER_RECORDS_ORGANIZATION_RECORD"' in source


@pytest.mark.parametrize("rel,legacy", [
    ("scripts/consume_organization_custody_readback_request.py", "intr_master_records_closure"),
    ("scripts/consume_organization_custody_readback_request.py", "predecessor_master_records_closure"),
    ("scripts/consume_universal_governance_enforced_reference_request.py", "master_records_custody_accepted"),
    ("workers/mir_tvc_provider_roundtrip_worker.py", "master_records_custody_ref"),
    ("heartbeat_runtime/worker_runtime_legacy.py", "project_active_only_after_master_records_closure"),
    ("scripts/validate_heartbeat_runtime_separation.py", "PASSIVE_CUSTODY_AND_QUERYABLE_EVIDENCE"),
])
def test_renamed_readers_keep_one_legacy_constant(rel: str, legacy: str) -> None:
    source = (ROOT / rel).read_text(encoding="utf-8")
    assert source.count(f'"{legacy}"') == 1
    line = next(l for l in source.splitlines() if f'"{legacy}"' in l)
    assert line.startswith("LEGACY_")


def test_org_transition_submission_emits_organization_record_names() -> None:
    source = (ROOT / "resident-runtime/submit_org_transition_to_master_records.py").read_text(encoding="utf-8")
    for new in ("ORGANIZATION_RECORD_ORGANIZATION_TRANSITION", "ecosystem.transition.organization-record.v1", "PUBLISHED_FOR_ORGANIZATION_RECORD"):
        assert new in source
    for old in ("CUSTODY_ORGANIZATION_TRANSITION", "ecosystem.transition.custody.v1", "PUBLISHED_FOR_CUSTODY"):
        assert f'"{old}"' not in source


def test_organization_batch_submission_emits_organization_record_authority_effect() -> None:
    source = (ROOT / "workers/canonical_state_transition_custody.py").read_text(encoding="utf-8")
    assert 'authority_effect="NONE_ORGANIZATION_RECORD_ONLY"' in source
    assert '"NONE_CUSTODY_ONLY"' not in source


# --- Owner-approved identifier renames (destination record, runtime profile map, transition ledger) ---

coordination_graph = load("compat_coordination_graph", "heartbeat_runtime/coordination_graph.py")
universal_worker_source = (ROOT / "workers/universal_governance_enforced_reference_worker.py").read_text(encoding="utf-8")


def test_reusable_task_request_emits_destination_record_accepted() -> None:
    manifest = {"invocation_id": "I1", "reusable_task_id": "RT1", "manifest_hash": "sha256:" + "0" * 64}
    request = lifecycle.build_custody_request(
        manifest=manifest, trigger_receipt={}, runner_result={}, runner_expiry={}, residual_recording={},
    )
    assert request["destination_record_accepted"] is False
    assert "destination_custody_accepted" not in request


@pytest.mark.parametrize("field", ["destination_record_accepted", "destination_custody_accepted"])
def test_destination_record_accepted_reader_accepts_new_and_legacy(field: str) -> None:
    assert lifecycle.destination_record_accepted({field: True}) is True
    assert lifecycle.destination_record_accepted({field: False}) is False
    assert lifecycle.destination_record_accepted({}) is None


def test_destination_record_accepted_new_name_wins_over_legacy() -> None:
    record = {"destination_record_accepted": False, "destination_custody_accepted": True}
    assert lifecycle.destination_record_accepted(record) is False


@pytest.mark.parametrize("rel", ["workers/reusable_task_lifecycle.py", "workers/universal_governance_enforced_reference_worker.py"])
def test_destination_record_readers_keep_one_legacy_constant(rel: str) -> None:
    source = (ROOT / rel).read_text(encoding="utf-8")
    assert source.count('"destination_custody_accepted"') == 1
    line = next(l for l in source.splitlines() if '"destination_custody_accepted"' in l)
    assert line.startswith("LEGACY_")
    assert '"destination_record_accepted"' in source


@pytest.mark.parametrize("field", ["destination_record_accepted", "destination_custody_accepted"])
def test_universal_worker_reads_destination_record_accepted_new_and_legacy(field: str) -> None:
    namespace: dict = {}
    for line in universal_worker_source.splitlines():
        if line.startswith(("DESTINATION_RECORD_ACCEPTED_FIELD =", "LEGACY_DESTINATION_RECORD_ACCEPTED_FIELD =")):
            exec(line, namespace)
    expr = 'effect.get(DESTINATION_RECORD_ACCEPTED_FIELD, effect.get(LEGACY_DESTINATION_RECORD_ACCEPTED_FIELD))'
    assert expr in universal_worker_source
    assert eval(expr, {**namespace, "effect": {field: True}}) is True


RUNTIME_PROFILE_MAP_CONSUMPTION_SCHEMA = "stegverse.runtime-profile-map-organization-record-consumption/v1"


def _runtime_profile_map_predicate() -> dict:
    data = json.loads((ROOT / "control/cross-task-coordination.d/runtime-profile-map-lifecycle-predicates.json").read_text(encoding="utf-8"))
    return next(p for p in data["predicates"] if p.get("required_schema", "").startswith("stegverse.runtime-profile-map-organization-record"))


@pytest.mark.parametrize("schema", [RUNTIME_PROFILE_MAP_CONSUMPTION_SCHEMA, "stegverse.runtime-profile-map-custody-consumption/v1"])
def test_runtime_profile_map_predicate_accepts_new_and_legacy_consumption_schema(schema: str) -> None:
    predicate = _runtime_profile_map_predicate()
    assert predicate["required_schema"] == RUNTIME_PROFILE_MAP_CONSUMPTION_SCHEMA
    evidence = {"schema": schema}
    reasons = coordination_graph._evidence_rejection_reasons(predicate, evidence, coordination_graph._now(None))
    assert "SCHEMA_MISMATCH" not in reasons
    evidence["schema"] = "stegverse.other/v1"
    assert "SCHEMA_MISMATCH" in coordination_graph._evidence_rejection_reasons(predicate, evidence, coordination_graph._now(None))


def test_runtime_profile_map_writers_emit_organization_record_schema_ids() -> None:
    consumer = (ROOT / "control/resident-execution-request.d/consume-runtime-profile-map-custody.py").read_text(encoding="utf-8")
    assert f'CONSUMPTION_SCHEMA = "{RUNTIME_PROFILE_MAP_CONSUMPTION_SCHEMA}"' in consumer
    assert "runtime-profile-map-custody-consumption" not in consumer
    builder = (ROOT / "scripts/build_runtime_profile_map_custody_package.py").read_text(encoding="utf-8")
    assert '"schema": "stegverse.runtime-profile-map-organization-record-package/v1"' in builder
    assert "runtime-profile-map-custody-package/v1" not in builder


@pytest.mark.parametrize("schema", [
    "stegverse.runtime-profile-map-organization-record-package/v1",
    "stegverse.runtime-profile-map-custody-package/v1",
])
def test_runtime_profile_map_package_schema_accepts_new_and_legacy(schema: str) -> None:
    contract = json.loads((ROOT / "schemas/runtime-profile-map-custody-package.schema.json").read_text(encoding="utf-8"))
    assert schema in contract["properties"]["schema"]["enum"]


def test_org_transition_submission_targets_organization_transition_ledger() -> None:
    source = (ROOT / "resident-runtime/submit_org_transition_to_master_records.py").read_text(encoding="utf-8")
    assert 'destination_service="organization.ecosystem-transition-ledger"' in source
    assert "master-records.ecosystem-transition-ledger" not in source


def test_master_records_owner_keys_use_record_owner_names() -> None:
    handoff = json.loads((ROOT / "handoffs/VACC-LONGITUDINAL-CONTINUITY-001.json").read_text(encoding="utf-8"))
    assert handoff["record_owner"] == "master-records/orchestration#15"
    assert "custody_owner" not in handoff
    intake = json.loads((ROOT / "control/repository-hygiene-ref-retirement-admin-intake-20260924.json").read_text(encoding="utf-8"))
    assert "master_records_organization_record_owner" in intake
    assert "master_records_custody_owner" not in intake
