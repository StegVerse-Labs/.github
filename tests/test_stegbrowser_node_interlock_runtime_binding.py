from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_stegbrowser_runtime_consumption_reusable.py"
WORKER = ROOT / "workers/stegbrowser_manifest_intr_ingress.py"
RT = ROOT / "source-bundles/reusable-task-registry.d/RT-STEGBROWSER-RUNTIME-CONSUMPTION-001.json"
REQUEST = ROOT / "control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json"


def test_runner_validates_receipt_one_before_existing_materializer():
    source = RUNNER.read_text()
    assert "validate_node_genesis_receipt" in source
    assert '"stegos.node_handoff_receipt.v1"' in source
    assert "registered_stegverse_node_receipt_one_required" in source
    assert "SovereignLocalEventRuntimeAdapter.materialize" in source
    assert "bound_lease_request" in source
    assert "node_interlock_lease_runtime_correlation_failed" in source


def test_canonical_registered_node_selector_is_invocation_bound_and_fail_closed():
    request = json.loads(REQUEST.read_text())
    path_parameters = request["reusable_task_binding"]["path_parameters"]
    assert path_parameters["node_binding_ref"] == "CANONICAL_REGISTERED_STEGVERSE_NODE_BINDING"
    source = RUNNER.read_text()
    assert 'CANONICAL_NODE_SELECTOR = "CANONICAL_REGISTERED_STEGVERSE_NODE_BINDING"' in source
    assert 'STEGVERSE_STEGBROWSER_NODE_BINDING_REF' in source
    assert 'STEGVERSE_SOVEREIGN_NODE_MARKER' in source
    assert 'Path.home() / ".stegverse" / "node.json"' in source
    assert 'Path("/etc/stegverse/node.json")' in source
    assert "canonical_registered_stegverse_node_receipt_one_not_available" in source
    assert "build_node_genesis_receipt" not in source


def test_lease_state_identity_binds_manifest_node_interlock_goal_cosv():
    source = RUNNER.read_text()
    for token in (
        '"goal_task_id": GOAL_ID',
        '"cosv_task_vector": COSV',
        '"manifest_sha256": manifest_sha256',
        '"node_id": node["node_id"]',
        '"interlock_id": node["interlock_id"]',
        '"registration_receipt_sha256": node["registration_receipt_sha256"]',
        'kwargs["state_root_binding"] = "sha256:" + basis_sha256',
    ):
        assert token in source


def test_a4_packet_binds_exact_node_lease_runtime_correlation():
    source = WORKER.read_text()
    for token in (
        '"node_id": binding["node_id"]',
        '"interlock_id": binding["interlock_id"]',
        '"registration_receipt_sha256": binding["registration_receipt_sha256"]',
        '"lease_id": binding["lease_id"]',
        '"runtime_id": binding["runtime_id"]',
        'and receipt.get("payload_hash") == expected["payload_hash"]',
        'and receipt.get("ingress_packet_sha256") == sha256_uri(expected)',
    ):
        assert token in source


def test_reusable_task_has_no_external_host_discovery_repair():
    source = RT.read_text()
    assert '"node_binding_ref"' in source
    assert "NODE_INTERLOCK_LEASE_RUNTIME_BINDING_RECEIPT_RETAINED" in source
    assert "do not discover an external host or create a Node" in source
    assert "duplicate materializer" in source
