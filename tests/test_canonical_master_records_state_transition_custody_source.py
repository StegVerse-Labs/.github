from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_custody_client_and_reusable_task_are_primary() -> None:
    client = (ROOT / "workers/canonical_state_transition_custody.py").read_text()
    reusable = (ROOT / "source-bundles/reusable-task-registry.d/RT-CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001.json").read_text()
    assert "stegverse.canonical-state-transition-receipt/v1" in client
    assert "CANONICAL_MASTER_RECORDS_CUSTODY_SURFACE_UNAVAILABLE" in client
    assert "reconstruction_status" in client
    assert "RT-INTR-GOVERNED-TRANSITION-001" in reusable
    assert "RT-INTR-EVIDENCE-CUSTODY-001" in reusable
    assert "Task-specific probes may compare conformance but must not replace this path" in reusable


def test_mir_event_creation_does_not_require_workercoordinator_claim() -> None:
    driver = (ROOT / "scripts/execute_mir_event_driven_roundtrip.py").read_text()
    request = (ROOT / "control/resident-execution-request.d/mir-roundtrip-egress-authenticity-001.json").read_text()
    consumer = (ROOT / "scripts/consume_mir_roundtrip_egress_authenticity_request.py").read_text()
    assert "build_materialization_request" in driver
    assert "persist_materialization_request" in driver
    assert '"claim_or_fence_minted": False' in driver
    assert '"request_grants_execution_authority": False' in driver
    assert "CanonicalTransitionCustody" in driver
    assert '"workercoordinator_claim_required_for_event_creation": false' in request
    assert '"requires_current_workercoordinator_claim_fence": false' in request
    assert "scripts/execute_mir_event_driven_roundtrip.py" in request
    assert "refresh_and_execute_resident_task.py" not in consumer


def test_temporary_probe_is_disabled_comparator_only() -> None:
    adapter = (ROOT / "control/process-worker-adapters.d/mir-roundtrip-egress-authenticity-001.json").read_text()
    assert '"enabled": false' in adapter
    assert "CONFORMANCE_COMPARATOR_ONLY" not in adapter  # role is described in notes, not promoted as an execution state
    assert "Comparator only" in adapter


def test_inventory_demotes_task_specific_fanout() -> None:
    inventory = (ROOT / "reports/canonical-master-records-state-transition-custody-inventory-20260917.json").read_text()
    assert "NEW_CANONICAL_PER_STATE_TRANSITION_CUSTODY_API" in inventory
    assert "TEMPORARY_CONFORMANCE_COMPARATOR_ONLY" in inventory
    assert "RETAIN_AS_LEGACY_COMPARATOR_NOT_PRIMARY_CANONICAL_CUSTODY" in inventory


def test_required_transition_evidence_is_part_of_canonical_source_contract() -> None:
    client = (ROOT / "workers/canonical_state_transition_custody.py").read_text()
    contract = (ROOT / "control/canonical-master-records-state-transition-custody-contract.json").read_text()
    reusable = (ROOT / "source-bundles/reusable-task-registry.d/RT-CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001.json").read_text()
    assert "required_evidence_manifest" in client
    assert "CANONICAL_MASTER_RECORDS_REQUIRED_EVIDENCE_NOT_VALIDATED" in client
    assert "every_required_transition_evidence_item_is_submitted_to_master_records" in contract
    assert "transition_custody_pass_requires_all_required_evidence_pass" in contract
    assert "ALL_REQUIRED_TRANSITION_EVIDENCE_MASTER_RECORDS_VALIDATED" in reusable
    assert "Specialized lane validators may produce semantic validation artifacts" in reusable


def test_canonical_custody_goal_is_projected_into_monolithic_registry() -> None:
    import json
    registry = json.loads((ROOT / "data/canonical-task-registry.json").read_text())
    task = next(
        row for row in registry["tasks"]
        if row.get("task_id") == "CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001"
    )
    assert task["coordination_state"] == "ACTIVE"
    assert task["required_evidence_validation"]["manifest_field"] == "required_evidence_manifest"
    assert task["required_evidence_validation"]["progression_gate"] == [
        "state=RECORDED",
        "reconstruction_status=PASS",
        "required_evidence_validation_status=PASS",
    ]


def test_first_mir_transition_carries_materialization_as_required_evidence() -> None:
    driver = (ROOT / "scripts/execute_mir_event_driven_roundtrip.py").read_text()
    assert '"MIR_EVENT_MATERIALIZATION_REQUEST_QUEUED:materialization-request"' in driver
    assert '"evidence_type": "MIR_MATERIALIZATION_REQUEST"' in driver
    assert '"origin_transition_id": "MIR_EVENT_MATERIALIZATION_REQUEST_QUEUED"' in driver
    assert '"content": materialization' in driver
    assert 'required_evidence_manifest=[materialization_evidence]' in driver


def test_required_evidence_contract_is_non_deferrable() -> None:
    import json
    contract = json.loads((ROOT / "control/canonical-master-records-state-transition-custody-contract.json").read_text())
    reusable = json.loads((ROOT / "source-bundles/reusable-task-registry.d/RT-CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001.json").read_text())
    semantics = contract["required_evidence_semantics"]
    assert "WAIT_OR_DEFER_CONDITION" in semantics["validation_execution_semantics"]
    assert "FIRST_DETERMINISTIC_SOURCE_OR_RUNTIME_BOUNDARY" in semantics["no_wait_on_missing_runtime_receipt"]
    assert "never a wait/defer condition" in reusable["reuse_instructions"]
