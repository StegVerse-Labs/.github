from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SPEC = importlib.util.spec_from_file_location(
    "erl_review_portable_dispatch",
    SCRIPTS / "refresh_and_dispatch_resident_requests.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)

TARGET = "erl_ai_economic_transparency_review"


class ERLAIEconomicTransparencyPortableExactDispatchTests(unittest.TestCase):
    def test_exact_er_review_selector_isolated_through_portable_bridge(self):
        self.assertIn(TARGET, MOD.ALLOWED_TARGET_CONSUMERS)
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            runtime.mkdir()

            dispatcher = runtime / MOD.DISPATCHER_REL
            dispatcher.parent.mkdir(parents=True)
            dispatcher.write_text("# refreshed dispatcher\n", encoding="utf-8")
            dispatch_receipt = runtime / MOD.DISPATCH_RECEIPT_REL
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                dispatch_receipt.parent.mkdir(parents=True, exist_ok=True)
                dispatch_receipt.write_text(
                    json.dumps({
                        "schema": "stegverse.resident-request-dispatch/v1",
                        "state": "DISPATCH_COMPLETE",
                        "registered_consumer_count": 1,
                        "consumer_count": 1,
                        "selected_consumers": [TARGET],
                        "selection_scope": "EXACT_SELECTOR",
                        "consumers_visited": 1,
                        "missing_consumers": [],
                        "dispatch_exceptions": [],
                        "request_failures": [],
                        "network_source_fetch_performed": False,
                        "credential_authority": "TV/TVC",
                        "github_token_required": False,
                        "github_token_runtime_authority": "NONE",
                        "heartbeat_grants_execution_authority": False,
                        "request_dispatch_grants_authority": False,
                        "second_machine_required": False,
                        "authority_effect": "NONE_DISPATCH_ONLY",
                    }) + "\n",
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            refresh_receipt = {
                "schema": "stegverse.sovereign-worker-runtime-source-refresh/v1",
                "mutable_runtime_state_preserved": True,
                "network_fetch_performed": False,
                "credential_read_or_acquired": False,
                "authority_effect": "NONE_LOCAL_SOURCE_REFRESH",
            }
            with mock.patch.object(MOD, "refresh", return_value=refresh_receipt):
                result = MOD.refresh_and_dispatch(
                    source,
                    runtime,
                    target_consumer=TARGET,
                    runner=runner,
                    env={"PATH": "/bin", "HOME": td},
                )

            self.assertEqual(result["state"], "REFRESH_AND_DISPATCH_COMPLETE")
            self.assertEqual(result["target_consumer"], TARGET)
            self.assertTrue(result["exact_consumer_selection_observed"])
            self.assertFalse(result["unrelated_consumers_dispatched"])
            self.assertFalse(result["bridge_grants_execution_authority"])
            self.assertFalse(result["bridge_mints_claim_or_fence"])
            self.assertFalse(result["network_source_fetch_performed"])
            self.assertFalse(result["credential_read_or_acquired"])
            self.assertEqual(len(calls), 1)
            command, kwargs = calls[0]
            self.assertEqual(command[command.index("--only-consumer") + 1], TARGET)
            self.assertEqual(kwargs["cwd"], runtime)
            self.assertNotIn("GITHUB_TOKEN", kwargs["env"])


if __name__ == "__main__":
    unittest.main()
