from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER_PATH = ROOT / "scripts" / "dispatch_resident_execution_requests.py"
SPEC = importlib.util.spec_from_file_location("resident_dispatcher", DISPATCHER_PATH)
assert SPEC and SPEC.loader
DISPATCHER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DISPATCHER)


class StegSocialsBoundedIntrResidentDispatchTests(unittest.TestCase):
    def test_consumer_is_registered_exactly_once(self) -> None:
        matches = [row for row in DISPATCHER.CONSUMERS if row[0] == "stegsocials_bounded_intr_admission"]
        self.assertEqual(
            matches,
            [("stegsocials_bounded_intr_admission", "scripts/consume_stegsocials_bounded_intr_admission_request.py")],
        )

    def test_input_not_materialized_is_non_authorizing_wait_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            consumer = runtime / "scripts" / "consume_stegsocials_bounded_intr_admission_request.py"
            consumer.parent.mkdir(parents=True, exist_ok=True)
            consumer.write_text(
                "import json\nprint(json.dumps({'state':'INPUT_NOT_MATERIALIZED','authority_effect':'NONE'}))\n",
                encoding="utf-8",
            )
            original = DISPATCHER.CONSUMERS
            try:
                DISPATCHER.CONSUMERS = (("stegsocials_bounded_intr_admission", "scripts/consume_stegsocials_bounded_intr_admission_request.py"),)
                receipt = DISPATCHER.dispatch(
                    ROOT,
                    runtime,
                    env={"PATH": "/usr/bin:/bin"},
                    only_consumers=("stegsocials_bounded_intr_admission",),
                )
            finally:
                DISPATCHER.CONSUMERS = original

            self.assertEqual(receipt["state"], "DISPATCH_COMPLETE")
            self.assertEqual(receipt["request_failures"], [])
            self.assertEqual(receipt["outcomes"][0]["state"], "INPUT_NOT_MATERIALIZED")
            self.assertFalse(receipt["request_dispatch_grants_authority"])
            self.assertEqual(receipt["authority_effect"], "NONE_DISPATCH_ONLY")


if __name__ == "__main__":
    unittest.main()
