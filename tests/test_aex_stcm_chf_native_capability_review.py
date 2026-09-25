"""Source-only consistency and negative controls for the pinned original CHF/math capability audit.

These tests never treat source classification as a native CHF consequence result,
an installed SDK manifest route, or an authentic resident execution receipt.
"""
import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data/aex-stcm-chf-native-math-capability-review.json"
CENSUS = ROOT / "data/aex-native-math-processing-census.json"


class OriginalNativeMathCapabilityReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        cls.census = json.loads(CENSUS.read_text(encoding="utf-8"))
        cls.rows = {r["repository"]: r for r in cls.census["entries"]}

    def test_original_stcm_synthetic_native_execution_is_explicit(self):
        native = self.audit["STCM"]
        self.assertEqual(native["exact_original_callable"],
                         "tools/closure-harness/lineage_gate.py::gated_close")
        self.assertEqual(native["native_source_test"]["workflow_conclusion"], "success")
        self.assertEqual(native["native_same_specimen_status"],
                         "SYNTHETIC_ONE_SIDED_VERIFIED")
        self.assertIn("constructed synthetic prior",
                      native["native_source_test"]["positive"])
        self.assertEqual(native["sdk_manifest_invocation"], "NOT_ESTABLISHED")

    def test_original_chf_threshold_and_ready_checks_are_not_native_math(self):
        surfaces = {
            s["path"]: s for s in self.audit["CHF"]["inspected_original_surfaces"]
        }
        self.assertIn("DATA_DECLARATION", surfaces["tools/check_chf_thresholds.py"]["kind"])
        self.assertIn("FLAGS_CLASSIFIER", surfaces["validators/c.py"]["kind"])
        self.assertIn("NOT_PER_SPECIMEN", surfaces["validators/c.py"]["kind"])
        self.assertEqual(self.audit["CHF"]["same_specimen_mathematical_output"],
                         "BOUNDED_ORIGINAL_DECLARED_THRESHOLD_SYNTHETIC_VERIFIED_FULL_HORIZON_NOT_ESTABLISHED")
        self.assertEqual(self.audit["CHF"]["required_original_native_callable"]["status"],
                         "FOUR_SYMBOLIC_INEQUALITIES_NATIVE_IMPLEMENTED_FULL_HORIZON_NOT_ESTABLISHED")

    def test_census_uses_original_owner_and_same_task_vector(self):
        self.assertEqual(self.audit["math_cosv"], "10111110111000")
        self.assertEqual(self.audit["adjacent_cosv"], "10111010112000")
        self.assertEqual(self.rows["Admissible-Existence/CHF"]["owner"],
                         "NATIVE_SOURCE_REPOSITORY")
        self.assertEqual(self.rows["Admissible-Existence/CHF"]["same_specimen_math_status"],
                         "BOUNDED_DECLARED_THRESHOLD_NATIVE_EVALUATION_VERIFIED_FULL_HORIZON_NOT_ESTABLISHED")
        self.assertEqual(self.rows["Admissible-Existence/STCM"]["same_specimen_math_status"],
                         "STCM_SYNTHETIC_ONLY_ORIGINAL_CALLABLE_VERIFIED")

    def test_all_four_published_sdk_capabilities_exclude_native_math(self):
        sdk = self.audit["SDK"]
        self.assertEqual(
            set(sdk["published_processor_capabilities"]),
            {"governance", "ecosystem_diagnostic", "purpose_bound_worker", "atomic_task_worker"},
        )
        self.assertEqual(sdk["native_math_published_binding"], "NOT_ESTABLISHED")

    def test_missing_chf_cannot_be_promoted_by_contract_ci(self):
        forged = copy.deepcopy(self.audit)
        forged["CHF"]["same_specimen_mathematical_output"] = "VERIFIED"
        with self.assertRaises(AssertionError):
            self.assertEqual(forged["CHF"]["same_specimen_mathematical_output"],
                             "BOUNDED_ORIGINAL_DECLARED_THRESHOLD_SYNTHETIC_VERIFIED_FULL_HORIZON_NOT_ESTABLISHED")
        self.assertEqual(forged["CHF"]["original_owner_hosted_evidence"]["classification"],
                         "ORIGINAL_REPO_DECLARATION_AND_CONTRACT_VALIDATION_NOT_NUMERIC_WITNESS")

    def test_new_original_chf_callable_is_exact_bounded_four_thresholds(self):
        original = self.audit["CHF"]["bounded_original_native_threshold_evaluator"]
        self.assertEqual(original["native_callable"],
                         "tools/evaluate_chf_specimen_thresholds.py::evaluate_specimen")
        self.assertEqual(original["original_owner_pr"], "Admissible-Existence/CHF#5")
        self.assertEqual(original["validation_workflow_run"], 36095046140)
        self.assertEqual(original["common_source_sha256"],
                         "sha256:fa95f04d35e51df5892a35dc2dd28e823696334082320c60df29d06c50bead02")
        self.assertEqual(original["full_horizon"], "NOT_ESTABLISHED")
        self.assertEqual(original["sdk_native_manifest"], "NOT_ESTABLISHED")
        self.assertEqual(len(original["four_synthetic_controls"]), 4)

    def test_unobserved_runtime_and_physical_heat_remain_unobserved(self):
        self.assertEqual(self.audit["runtime"]["authenticated_resident_gate"],
                         "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED")
        self.assertEqual(self.audit["runtime"]["master_records"],
                         "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED")
        self.assertEqual(self.audit["physical_heat_measurement"], "NOT_OBSERVED")
        self.assertEqual(self.audit["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
