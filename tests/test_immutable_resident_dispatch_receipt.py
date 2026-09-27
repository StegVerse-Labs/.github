"""Source-level regression for immutable resident dispatch custody (not runtime proof)."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "scripts/dispatch_resident_execution_requests.py"
spec = importlib.util.spec_from_file_location("resident_dispatch_under_test", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ImmutableDispatchReceiptTests(unittest.TestCase):
    def test_distinct_receipts_survive_latest_rotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = {"state": "DISPATCH_INCOMPLETE", "outcomes": [{"consumer": "canonical_work_coordination", "state": "DENY"}]}
            second = {"state": "DISPATCH_COMPLETE", "outcomes": [{"consumer": "canonical_work_coordination", "state": "COMPLETED"}]}
            first_path = module.retain_immutable_dispatch_receipt(root, first)
            first_bytes = first_path.read_bytes()
            second_path = module.retain_immutable_dispatch_receipt(root, second)
            self.assertNotEqual(first_path, second_path)
            self.assertEqual(first_path.read_bytes(), first_bytes)
            self.assertEqual(json.loads(second_path.read_text()), second)
            self.assertEqual(json.loads((root / module.RECEIPT_REL).read_text()), second)
            self.assertEqual(module.retain_immutable_dispatch_receipt(root, first), first_path)

    def test_symlink_at_immutable_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = {"state": "DISPATCH_INCOMPLETE"}
            original = module.retain_immutable_dispatch_receipt(root, receipt)
            original.unlink()
            target = root / "outside.json"
            target.write_text("untouched")
            original.symlink_to(target)
            with self.assertRaises(RuntimeError):
                module.retain_immutable_dispatch_receipt(root, receipt)
            self.assertEqual(target.read_text(), "untouched")


if __name__ == "__main__":
    unittest.main()
