import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_sv002_adversarial_disposition.py"
spec = importlib.util.spec_from_file_location("sv002_adv", P)
MOD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MOD)

class SV002AdversarialDispositionTests(unittest.TestCase):
    def base(self):
        return {
            "output_correct": True,
            "authorized_execution": True,
            "observation_valid": True,
            "master_records_custody_valid": True,
            "reconstruction_valid": True,
            "receipt_lineage_valid": True,
        }

    def test_correct_output_does_not_erase_unauthorized_path(self):
        c = self.base()
        c["authorized_execution"] = False
        r = MOD.disposition(c)
        self.assertEqual(r["disposition"], "CONTRADICTED")
        self.assertEqual(r["reason"], "CORRECT_OUTPUT_UNAUTHORIZED_OR_UNESTABLISHED_PATH")

    def test_execution_host_cannot_replace_custody(self):
        c = self.base()
        c["master_records_custody_valid"] = False
        r = MOD.disposition(c)
        self.assertEqual(r["disposition"], "NOT_ESTABLISHED")

    def test_bad_lineage_fails_closed(self):
        c = self.base()
        c["receipt_lineage_valid"] = False
        r = MOD.disposition(c)
        self.assertEqual(r["disposition"], "FAIL_CLOSED")

if __name__ == "__main__":
    unittest.main()
