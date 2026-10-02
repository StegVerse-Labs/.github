import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.legacy.py"
SPEC = importlib.util.spec_from_file_location("canonical_work_legacy_attempt_test", LEGACY)
consumer = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(consumer)


class CanonicalWorkAttemptCorrelationTests(unittest.TestCase):
    def test_stale_completed_receipt_is_not_already_consumed_for_new_attempt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            runtime = root / "runtime"
            source.mkdir()
            runtime.mkdir()
            spec = {
                "request_rel": Path("control/request.json"),
                "consumption_rel": Path("receipts/consumption.latest.json"),
                "bootstrap_runtime_rel": Path("runtime/bootstrap"),
                "task_id": "STEGVERSE-CANONICAL-WORK-COORDINATION-001",
            }
            request_path = runtime / spec["request_rel"]
            request_path.parent.mkdir(parents=True)
            request_path.write_text(json.dumps({"request_id": "request-1"}) + "\n")
            consumption_path = runtime / spec["consumption_rel"]
            consumption_path.parent.mkdir(parents=True)
            old_bootstrap = root / "old-bootstrap.json"
            old_bootstrap.write_text("{}\n")
            consumption_path.write_text(json.dumps({
                "schema": "stegverse.canonical-work-bootstrap-request-consumption/v1",
                "state": "COMPLETED",
                "request_sha256": "same-request",
                "task_id": spec["task_id"],
                "bootstrap_receipt_ref": str(old_bootstrap),
                "execution_attempt_id": "attempt-old",
                "disposition": "ALLOW",
            }) + "\n")

            def runner(command, **kwargs):
                bootstrap = runtime / spec["bootstrap_runtime_rel"] / "receipts/sovereign-host/canonical-work-event-bootstrap.latest.json"
                bootstrap.parent.mkdir(parents=True, exist_ok=True)
                bootstrap.write_text("{}\n")
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps({
                        "state": "INGRESS_CONSUMPTION_AND_PROJECTION_OBSERVED",
                        "task_id": spec["task_id"],
                        "governed_disposition": "DENY",
                        "governed_disposition_authority": "INTERLOCK_INTR",
                        "governed_disposition_evidence_refs": [str(bootstrap)],
                    }),
                    stderr="",
                )

            with mock.patch.object(consumer, "validate_spec"), \
                 mock.patch.object(consumer, "resolve_local_canonical_source", return_value=source), \
                 mock.patch.object(consumer, "ensure_request_materialized", return_value={}), \
                 mock.patch.object(consumer, "validate_request"), \
                 mock.patch.object(consumer, "stable_hash", return_value="same-request"), \
                 mock.patch.object(consumer, "materialize", return_value=[]), \
                 mock.patch.object(consumer, "ensure_task_identity_materialized", return_value={}):
                result = consumer.consume_for_spec(
                    source, runtime, spec, runner=runner, env={},
                    execution_attempt_id="attempt-new",
                )

            self.assertEqual(result["state"], "COMPLETED")
            self.assertNotEqual(result["state"], "ALREADY_CONSUMED")
            self.assertEqual(result["execution_attempt_id"], "attempt-new")
            self.assertEqual(result["disposition"], "DENY")

    def test_same_attempt_preserves_idempotent_already_consumed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            runtime = root / "runtime"
            source.mkdir()
            runtime.mkdir()
            spec = {
                "request_rel": Path("control/request.json"),
                "consumption_rel": Path("receipts/consumption.latest.json"),
                "bootstrap_runtime_rel": Path("runtime/bootstrap"),
                "task_id": "STEGVERSE-CANONICAL-WORK-COORDINATION-001",
            }
            request_path = runtime / spec["request_rel"]
            request_path.parent.mkdir(parents=True)
            request_path.write_text(json.dumps({"request_id": "request-1"}) + "\n")
            bootstrap = root / "bootstrap.json"
            bootstrap.write_text("{}\n")
            consumption_path = runtime / spec["consumption_rel"]
            consumption_path.parent.mkdir(parents=True)
            consumption_path.write_text(json.dumps({
                "state": "COMPLETED",
                "request_sha256": "same-request",
                "bootstrap_receipt_ref": str(bootstrap),
                "execution_attempt_id": "attempt-1",
                "disposition": "ALLOW",
            }) + "\n")

            with mock.patch.object(consumer, "validate_spec"), \
                 mock.patch.object(consumer, "resolve_local_canonical_source", return_value=source), \
                 mock.patch.object(consumer, "ensure_request_materialized", return_value={}), \
                 mock.patch.object(consumer, "validate_request"), \
                 mock.patch.object(consumer, "stable_hash", return_value="same-request"):
                result = consumer.consume_for_spec(
                    source, runtime, spec, env={}, execution_attempt_id="attempt-1"
                )
            self.assertEqual(result["state"], "ALREADY_CONSUMED")
            self.assertEqual(result["execution_attempt_id"], "attempt-1")


if __name__ == "__main__":
    unittest.main()
