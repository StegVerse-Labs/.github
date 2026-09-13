import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_completion_evidence_v1.py"


def mod():
    spec = importlib.util.spec_from_file_location("cev1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CompletionEvidenceV1Tests(unittest.TestCase):
    def test_legacy_completion_is_not_reportable(self):
        module = mod()
        record = {"completion": {"claimed": True, "validated": True}}
        module.validate(Path("legacy.json"), record)
        self.assertEqual(module.classify(record), "LEGACY_UNQUALIFIED_NON_AUTHORITATIVE")

    def test_v1_requires_evidence_class(self):
        module = mod()
        record = {
            "completion_evidence_contract_version": "v1",
            "completion": {"claimed": True, "validated": True},
        }
        with self.assertRaises(SystemExit):
            module.validate(Path("x.json"), record)

    def test_v1_rejects_weaker_terminal_class(self):
        module = mod()
        record = {
            "completion_evidence_contract_version": "v1",
            "completion": {
                "claimed": True,
                "validated": True,
                "evidence_class": "CI_VALIDATED",
                "terminal_evidence_class": "SANDBOX_RUNTIME_OBSERVED",
                "evidence_refs": ["run:1"],
            },
        }
        with self.assertRaises(SystemExit):
            module.validate(Path("x.json"), record)

    def test_v1_accepts_terminal_evidence(self):
        module = mod()
        record = {
            "completion_evidence_contract_version": "v1",
            "completion": {
                "claimed": True,
                "validated": True,
                "evidence_class": "MASTER_RECORDS_RECONSTRUCTED",
                "terminal_evidence_class": "SANDBOX_RUNTIME_OBSERVED",
                "evidence_refs": ["mr:1"],
            },
        }
        module.validate(Path("x.json"), record)
        self.assertEqual(module.classify(record), "QUALIFIED_TERMINAL_SATISFIED")

    def test_end_to_end_flag_requires_end_to_end(self):
        module = mod()
        record = {
            "completion_evidence_contract_version": "v1",
            "completion": {
                "claimed": True,
                "validated": True,
                "evidence_class": "MASTER_RECORDS_RECONSTRUCTED",
                "evidence_refs": ["mr:1"],
                "end_to_end_complete": True,
            },
        }
        with self.assertRaises(SystemExit):
            module.validate(Path("x.json"), record)


if __name__ == "__main__":
    unittest.main()
