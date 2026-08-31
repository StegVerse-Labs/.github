from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


consumer = load("bootstrap_intr_consumer", "scripts/consume_bootstrap_v1_intr_bundle_delivery_request.py")
dispatcher = load("resident_dispatcher", "scripts/dispatch_resident_execution_requests.py")
refresher = load("resident_refresher", "scripts/refresh_sovereign_worker_runtime_source.py")


def request() -> dict:
    return {
        "schema": "stegverse.resident-execution-request/v1",
        "request_id": "RESIDENT-EXEC-BOOTSTRAP-V1-INTR-BUNDLE-DELIVERY-001",
        "state": "REQUESTED",
        "task_id": consumer.TARGET_TASK,
        "mode": consumer.TARGET_MODE,
        "entrypoint": consumer.TARGET_ENTRYPOINT,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE_FOR_PUBLIC_BUNDLE_DELIVERY",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "package_execution_authority": False,
        "sdk_admission_authority": False,
        "release_activation_authority": False,
        "publication_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }


class BootstrapV1InTrResidentWiringTests(unittest.TestCase):
    def test_request_contract_is_non_authorizing(self) -> None:
        value = request()
        consumer.validate_request(value)
        self.assertFalse(value["request_granted_authority"])
        self.assertFalse(value["network_source_fetch_allowed"])
        self.assertFalse(value["package_execution_authority"])
        self.assertFalse(value["release_activation_authority"])

    def test_dispatcher_and_refresh_include_delivery_consumer(self) -> None:
        mapping = dict(dispatcher.CONSUMERS)
        self.assertEqual(
            mapping["bootstrap_v1_intr_bundle_delivery"],
            "scripts/consume_bootstrap_v1_intr_bundle_delivery_request.py",
        )
        static = {path.as_posix() for path in refresher.STATIC_FILES}
        self.assertIn("scripts/serve_bootstrap_v1_intr_bundle_delivery.py", static)
        self.assertIn("scripts/consume_bootstrap_v1_intr_bundle_delivery_request.py", static)

    def test_consumer_retries_until_authentic_delivery_transition(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            runtime.mkdir()
            path = runtime / consumer.REQUEST_REL
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(request()) + "\n", encoding="utf-8")
            entry = runtime / consumer.TARGET_ENTRYPOINT
            entry.parent.mkdir(parents=True, exist_ok=True)
            entry.write_text("# fixture\n", encoding="utf-8")

            waiting = lambda *args, **kwargs: SimpleNamespace(
                returncode=0,
                stdout='{"transition_id":"BOOTSTRAP_V1_INTR_BUNDLE_RECEIVER_READY"}\n',
                stderr="",
            )
            first = consumer.consume(source, runtime, runner=waiting, env={"HOME": str(base), "PATH": "/usr/bin"})
            self.assertEqual(first["state"], "ATTEMPT_RECORDED")
            self.assertFalse(first["terminal_delivery_observed"])

            terminal = lambda *args, **kwargs: SimpleNamespace(
                returncode=0,
                stdout='{"transition_id":"BOOTSTRAP_V1_INTR_BUNDLE_DELIVERY_OBSERVED"}\n',
                stderr="",
            )
            second = consumer.consume(source, runtime, runner=terminal, env={"HOME": str(base), "PATH": "/usr/bin"})
            self.assertEqual(second["state"], "COMPLETED")
            self.assertTrue(second["terminal_delivery_observed"])


if __name__ == "__main__":
    unittest.main()
