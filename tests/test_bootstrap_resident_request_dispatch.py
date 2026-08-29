from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]

BOOT_SPEC = importlib.util.spec_from_file_location(
    "bootstrap_sovereign_runtime",
    ROOT / "scripts/bootstrap_sovereign_runtime.py",
)
assert BOOT_SPEC and BOOT_SPEC.loader
boot = importlib.util.module_from_spec(BOOT_SPEC)
BOOT_SPEC.loader.exec_module(boot)

INSTALL_SPEC = importlib.util.spec_from_file_location(
    "install_sovereign_heartbeat_service",
    ROOT / "scripts/install_sovereign_heartbeat_service.py",
)
assert INSTALL_SPEC and INSTALL_SPEC.loader
install = importlib.util.module_from_spec(INSTALL_SPEC)
INSTALL_SPEC.loader.exec_module(install)


class BootstrapResidentDispatchTests(unittest.TestCase):
    def test_bootstrap_source_contract_requires_dispatcher_and_consumers(self) -> None:
        required = {path.as_posix() for path in boot.REQUIRED_SOURCE_FILES}
        for rel in (
            "scripts/dispatch_resident_execution_requests.py",
            "scripts/consume_resident_execution_request.py",
            "scripts/consume_g18_resident_execution_request.py",
            "scripts/consume_hil_resident_execution_request.py",
            "scripts/consume_ara_graph_resident_execution_request.py",
            "scripts/consume_sv_dn1_resident_execution_request.py",
        ):
            self.assertIn(rel, required)

    def test_native_materialization_copies_dispatcher_execution_dependencies(self) -> None:
        copied = set(install.COPY_FILES)
        for rel in (
            "scripts/dispatch_resident_execution_requests.py",
            "scripts/refresh_and_execute_resident_task.py",
            "scripts/refresh_sovereign_worker_runtime_source.py",
            "scripts/run_independent_ecosystem_chat_parent.py",
            "scripts/consume_resident_execution_request.py",
            "scripts/consume_g18_resident_execution_request.py",
            "scripts/consume_hil_resident_execution_request.py",
            "scripts/consume_ara_graph_resident_execution_request.py",
            "scripts/run_sv_dn1_first_round_chain.py",
            "scripts/consume_sv_dn1_resident_execution_request.py",
        ):
            self.assertIn(rel, copied)

    def test_post_bootstrap_dispatch_uses_runtime_dispatcher_and_no_authority(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            proof = base / "proof.json"
            dispatcher = runtime / "scripts/dispatch_resident_execution_requests.py"
            dispatcher.parent.mkdir(parents=True)
            dispatcher.write_text("# dispatcher\n", encoding="utf-8")
            receipt_path = runtime / "receipts/sovereign-host/resident-request-dispatch.latest.json"
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                receipt_path.parent.mkdir(parents=True, exist_ok=True)
                receipt_path.write_text(json.dumps({
                    "schema": "stegverse.resident-request-dispatch/v1",
                    "state": "DISPATCH_COMPLETE",
                    "consumer_count": 5,
                    "consumers_visited": 5,
                    "request_failures": ["g18"],
                    "request_failure_blocks_later_requests": False,
                    "credential_authority": "TV/TVC",
                    "github_token_required": False,
                    "request_dispatch_grants_authority": False,
                }) + "\n", encoding="utf-8")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            result = boot._dispatch_resident_requests(
                source,
                runtime,
                proof_path=proof,
                env={
                    "PATH": "/bin",
                    "HOME": "/home/stegverse",
                    "GITHUB_TOKEN": "forbidden",
                    "TVC_TOKEN": "forbidden",
                },
                runner=runner,
            )
            self.assertTrue(result["attempted"])
            self.assertEqual(result["state"], "DISPATCH_COMPLETE")
            self.assertEqual(result["consumer_count"], 5)
            self.assertEqual(result["consumers_visited"], 5)
            self.assertIn("g18", result["request_failures"])
            self.assertFalse(result["request_failure_blocks_later_requests"])
            self.assertFalse(result["github_token_required"])
            self.assertFalse(result["request_dispatch_grants_authority"])
            self.assertEqual(result["authority_effect"], "NONE")
            self.assertEqual(len(calls), 1)
            _command, kwargs = calls[0]
            self.assertNotEqual(kwargs["env"].get("GITHUB_TOKEN"), "forbidden")
            self.assertNotEqual(kwargs["env"].get("TVC_TOKEN"), "forbidden")

    def test_missing_runtime_dispatcher_is_not_faked_as_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            result = boot._dispatch_resident_requests(
                base / "source",
                base / "runtime",
                proof_path=base / "proof.json",
                env={"PATH": "/bin"},
                runner=lambda *_args, **_kwargs: None,
            )
            self.assertFalse(result["attempted"])
            self.assertEqual(result["state"], "NOT_AVAILABLE")
            self.assertEqual(result["reason"], "RESIDENT_REQUEST_DISPATCHER_NOT_MATERIALIZED")


if __name__ == "__main__":
    unittest.main()
