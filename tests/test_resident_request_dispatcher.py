from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "dispatch_resident_execution_requests",
    ROOT / "scripts/dispatch_resident_execution_requests.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class ResidentRequestDispatcherTests(unittest.TestCase):
    def test_failed_request_does_not_starve_later_consumers(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            for _name, rel in mod.CONSUMERS:
                path = runtime / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# consumer\n", encoding="utf-8")

            states = [
                {"state": "ATTEMPT_RECORDED"},
                {"state": "FAIL_CLOSED"},
                {"state": "ATTEMPT_RECORDED"},
                {"state": "NO_REQUEST"},
                {"state": "ALREADY_CONSUMED"},
            ]
            calls = []

            def runner(command, **kwargs):
                idx = len(calls)
                calls.append((command, kwargs))
                return SimpleNamespace(
                    returncode=1 if idx == 1 else 0,
                    stdout=json.dumps(states[idx]) + "\n",
                    stderr="",
                )

            receipt = mod.dispatch(
                source,
                runtime,
                runner=runner,
                env={
                    "PATH": "/bin",
                    "HOME": "/home/stegverse",
                    "STEGVERSE_SOVEREIGN_NODE": "1",
                    "STEGVERSE_LLM_ADAPTER_ROOT": "/srv/stegverse/llm-adapter",
                    "GITHUB_TOKEN": "forbidden",
                    "CLOUDFLARE_API_TOKEN": "forbidden",
                },
            )
            self.assertEqual(receipt["state"], "DISPATCH_COMPLETE")
            self.assertEqual(len(calls), len(mod.CONSUMERS))
            self.assertIn("g18", receipt["request_failures"])
            self.assertFalse(receipt["request_failure_blocks_later_requests"])
            self.assertFalse(receipt["request_dispatch_grants_authority"])
            self.assertFalse(receipt["github_token_required"])
            self.assertFalse(receipt["second_machine_required"])
            for _command, kwargs in calls:
                self.assertNotIn("GITHUB_TOKEN", kwargs["env"])
                self.assertNotIn("CLOUDFLARE_API_TOKEN", kwargs["env"])

    def test_missing_consumer_is_reported_without_hiding_later_visits(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            for _name, rel in mod.CONSUMERS[1:]:
                path = runtime / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# consumer\n", encoding="utf-8")

            calls = []
            def runner(command, **kwargs):
                calls.append(command)
                return SimpleNamespace(returncode=0, stdout='{"state":"NO_REQUEST"}\n', stderr="")

            receipt = mod.dispatch(source, runtime, runner=runner, env={"PATH": "/bin"})
            self.assertEqual(receipt["state"], "DISPATCH_INCOMPLETE")
            self.assertEqual(receipt["missing_consumers"], ["ecosystem_chat"])
            self.assertEqual(len(calls), len(mod.CONSUMERS) - 1)
            self.assertTrue((runtime / mod.RECEIPT_REL).is_file())

    def test_hosted_environment_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            with self.assertRaises(RuntimeError):
                mod.dispatch(
                    base / "source",
                    base / "runtime",
                    env={"PATH": "/bin", "GITHUB_ACTIONS": "true"},
                )


if __name__ == "__main__":
    unittest.main()
