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
            (runtime / "scripts").mkdir(parents=True, exist_ok=True)
            for _name, rel in mod.CONSUMERS:
                path = runtime / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# consumer\n", encoding="utf-8")

            states = [
                {"state": "ATTEMPT_RECORDED"},
                {"state": "FAIL_CLOSED"},
                {"state": "ATTEMPT_RECORDED"},
            ] + [{"state": "NO_REQUEST"}] * (len(mod.CONSUMERS) - 3)
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
                    "STEGVERSE_STEGINDEX_SOURCE_ROOT": "/srv/stegverse/StegIndex",
                    "GITHUB_TOKEN": "forbidden",
                    "CLOUDFLARE_API_TOKEN": "forbidden",
                },
            )
            self.assertEqual(receipt["state"], "DISPATCH_COMPLETE")
            self.assertEqual(receipt["selection_scope"], "ALL_REGISTERED")
            self.assertEqual(receipt["consumer_count"], len(mod.CONSUMERS))
            self.assertEqual(len(calls), len(mod.CONSUMERS))
            self.assertIn("g18", receipt["request_failures"])
            self.assertFalse(receipt["request_failure_blocks_later_requests"])
            self.assertFalse(receipt["request_dispatch_grants_authority"])
            self.assertFalse(receipt["github_token_required"])
            self.assertFalse(receipt["second_machine_required"])
            for _command, kwargs in calls:
                self.assertEqual(kwargs["env"].get("STEGVERSE_STEGINDEX_SOURCE_ROOT"), "/srv/stegverse/StegIndex")
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

    def test_exact_selector_visits_only_requested_consumer(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            target = "cross_framework_current_basis_v04"
            rel = dict(mod.CONSUMERS)[target]
            consumer = runtime / rel
            consumer.parent.mkdir(parents=True, exist_ok=True)
            consumer.write_text("# current-basis consumer\n", encoding="utf-8")
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                return SimpleNamespace(returncode=0, stdout='{"state":"ATTEMPT_RECORDED"}\n', stderr="")

            receipt = mod.dispatch(
                source,
                runtime,
                runner=runner,
                env={"PATH": "/bin", "HOME": td},
                only_consumers=(target,),
            )
            self.assertEqual(receipt["state"], "DISPATCH_COMPLETE")
            self.assertEqual(receipt["selection_scope"], "EXACT_SELECTOR")
            self.assertEqual(receipt["selected_consumers"], [target])
            self.assertEqual(receipt["consumer_count"], 1)
            self.assertEqual(receipt["consumers_visited"], 1)
            self.assertEqual(len(calls), 1)
            self.assertEqual(Path(calls[0][0][1]), consumer)

    def test_unknown_selector_fails_before_any_consumer_is_invoked(self) -> None:
        calls = []
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            with self.assertRaisesRegex(RuntimeError, "unknown resident consumer selector"):
                mod.dispatch(
                    base / "source",
                    base / "runtime",
                    runner=lambda *args, **kwargs: calls.append((args, kwargs)),
                    env={"PATH": "/bin"},
                    only_consumers=("not_registered",),
                )
        self.assertEqual(calls, [])

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
