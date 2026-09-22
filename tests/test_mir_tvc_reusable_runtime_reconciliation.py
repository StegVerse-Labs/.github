import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TASK_DEF = ROOT / "source-bundles/reusable-task-registry.d/RT-TVC-RUNTIME-BOUNDARY-OBSERVATION-001.json"
MANIFEST = ROOT / "manifests/reusable-task-invocations/MIR-TVC-PROVIDER-ROUNDTRIP-001.TVC-CAPABILITY-RUNTIME-002.json"
RUNNER = ROOT / "scripts/reconcile_tvc_runtime_boundary_reusable.py"
CONSTRUCTOR = ROOT / "scripts/materialize_reusable_task_construct.py"
TRIGGER = ROOT / "scripts/trigger_reusable_task.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def intr_lane(direction: str):
    char = "a" if direction == "request" else "b"
    terminal = "sha256:" + char * 64
    receipt = {
        "boundary_verification": "VERIFIED",
        "authority_transfer": False,
        "receipt_hash": terminal,
    }
    source = "StegVerse-org/StegVerse-SDK" if direction == "request" else "TVC:ProviderOperationBroker"
    destination = "TVC:ProviderOperationBroker" if direction == "request" else "StegVerse-org/StegVerse-SDK"
    return {
        "component_id": "RTC-INTERLOCK-INTR-TRANSPORT-008",
        "intent": {
            "protocol": "InTr",
            "source": {"boundary": "STEGOS_ECOSYSTEM", "subsystem": source},
            "destination": {"boundary": "STEGOS_ECOSYSTEM", "subsystem": destination},
        },
        "receipts": [receipt],
        "transport_result": {
            "state": "TRANSPORT_COMPLETE",
            "component_id": "RTC-INTERLOCK-INTR-TRANSPORT-008",
            "terminal_receipt_hash": terminal,
        },
    }


class MirTvcReusableRuntimeReconciliationTests(unittest.TestCase):
    def test_registered_runner_is_local_and_materialized(self):
        definition = json.loads(TASK_DEF.read_text(encoding="utf-8"))
        self.assertEqual(definition["runner_templates"], ["scripts/reconcile_tvc_runtime_boundary_reusable.py"])
        self.assertTrue(RUNNER.is_file())

    def test_runner_predicates_end_after_real_intr_and_before_master_records(self):
        definition = json.loads(TASK_DEF.read_text(encoding="utf-8"))
        self.assertEqual(
            definition["completion_predicates"],
            [
                "QUALIFYING_REAL_PROVIDER_OPERATION_RECEIPT_CHAIN_OBSERVED",
                "READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND_DERIVED",
                "CANONICAL_INTR_TRANSPORT_CHAIN_RETAINED",
            ],
        )
        self.assertEqual(
            definition["post_runner_lifecycle_predicates"],
            ["INTERLOCK_INTR_RECEIPT_ADMITTED", "MASTER_RECORDS_CUSTODY_ACCEPTED", "MASTER_RECORDS_RECONSTRUCTION_CONFIRMED"],
        )

    def test_checked_in_manifest_matches_constructor(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        constructor = load_module("mir_tvc_reusable_constructor", CONSTRUCTOR)
        args = type("Args", (), {
            "reusable_task_id": manifest["reusable_task_id"],
            "invocation_id": manifest["invocation_id"],
            "parameters_json": json.dumps(manifest["parameters"], sort_keys=True, separators=(",", ":")),
            "task_id": manifest["task_id"],
            "cosv_task_vector": manifest["cosv_task_vector"],
        })()
        rebuilt = constructor.build_manifest(args)
        self.assertEqual(rebuilt, manifest)

    def test_real_receipt_requires_claim_allow_use_receipt_and_both_intr_chains(self):
        runner = load_module("mir_tvc_reusable_runner", RUNNER)
        receipt = {
            "schema": "stegverse.mir-tvc-provider-roundtrip-receipt/v1",
            "state": "COMPLETED_PROVIDER_OPERATION_RECEIPT",
            "goal_task_id": "MIR-TVC-PROVIDER-ROUNDTRIP-001",
            "claim_id": "CLAIM-MIR-G7",
            "fencing_token": 7,
            "provider_operation_completed": True,
            "allow_operation_result_observed": True,
            "use_receipt_observed": True,
            "ready_state": "READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND",
            "secret_values_exported": False,
            "protected_values_exposed": False,
            "credential_material_retained": False,
            "provider_operation_result": {
                "decision": "ALLOW_OPERATION_RESULT",
                "use_receipt": {"receipt_id": "real-use-receipt"},
            },
            "intr_transport": {
                "component_id": "RTC-INTERLOCK-INTR-TRANSPORT-008",
                "request": intr_lane("request"),
                "response": intr_lane("response"),
            },
        }
        runner.qualified_real_receipt(
            receipt,
            tracking_task_id="MIR-TVC-PROVIDER-ROUNDTRIP-001",
            expected_ready_state="READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND",
        )
        bad = dict(receipt)
        bad["intr_transport"] = dict(receipt["intr_transport"])
        bad["intr_transport"]["response"] = None
        with self.assertRaises(RuntimeError):
            runner.qualified_real_receipt(
                bad,
                tracking_task_id="MIR-TVC-PROVIDER-ROUNDTRIP-001",
                expected_ready_state="READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND",
            )


    def test_trigger_stops_before_master_records_without_explicit_intr_admission(self):
        source = TRIGGER.read_text(encoding="utf-8")
        self.assertIn('BOUNDARY_INTR_ADMISSION = "INTERLOCK_INTR_ADMISSION_REQUIRED"', source)
        self.assertIn('"INTERLOCK_INTR_RECEIPT_ADMITTED" in post_runner_lifecycle_predicates', source)
        self.assertIn('"AUTHENTIC_EXPLICIT_INTERLOCK_INTR_ADMISSION_RECEIPT"', source)
        admission_index = source.index('if "INTERLOCK_INTR_RECEIPT_ADMITTED" in post_runner_lifecycle_predicates')
        master_index = source.index('custody_request = lifecycle.build_custody_request')
        self.assertLess(admission_index, master_index)


if __name__ == "__main__":
    unittest.main()
