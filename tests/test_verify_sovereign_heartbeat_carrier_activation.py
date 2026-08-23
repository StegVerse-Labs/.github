import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_sovereign_heartbeat_carrier_activation.py"
spec = importlib.util.spec_from_file_location("carrier_activation_verifier", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class SovereignHeartbeatActivationVerifierTests(unittest.TestCase):
    def valid_receipt(self):
        return dict(mod.EXPECTED)

    def run_main(self, path: Path):
        output = StringIO()
        with redirect_stdout(output):
            code = mod.main([str(path)])
        return code, json.loads(output.getvalue())

    def test_accepts_exact_terminal_carrier_only_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "carrier-activation.latest.json"
            path.write_text(json.dumps(self.valid_receipt()), encoding="utf-8")
            code, result = self.run_main(path)
            self.assertEqual(code, 0)
            self.assertTrue(result["verified"])
            self.assertEqual(result["failures"], [])
            self.assertEqual(result["authority_effect"], "NONE")
            self.assertFalse(result["runtime_authority_granted"])

    def test_rejects_absent_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "carrier-activation.latest.json"
            code, result = self.run_main(path)
            self.assertEqual(code, 1)
            self.assertFalse(result["verified"])
            self.assertIn("activation receipt is absent", result["failures"])
            self.assertEqual(result["authority_effect"], "NONE")

    def test_rejects_worker_start_or_wrong_runtime(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "carrier-activation.latest.json"
            receipt = self.valid_receipt()
            receipt["worker_start_attempted"] = True
            receipt["canonical_runtime"] = "heartbeat_runtime.engine_v12.HeartbeatRuntime"
            path.write_text(json.dumps(receipt), encoding="utf-8")
            code, result = self.run_main(path)
            self.assertEqual(code, 1)
            self.assertFalse(result["verified"])
            failures = "\n".join(result["failures"])
            self.assertIn("worker_start_attempted", failures)
            self.assertIn("canonical_runtime", failures)

    def test_rejects_missing_terminal_invariant(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "carrier-activation.latest.json"
            receipt = self.valid_receipt()
            del receipt["heartbeat_progression_dependency"]
            path.write_text(json.dumps(receipt), encoding="utf-8")
            code, result = self.run_main(path)
            self.assertEqual(code, 1)
            self.assertIn("missing required field: heartbeat_progression_dependency", result["failures"])


if __name__ == "__main__":
    unittest.main()
