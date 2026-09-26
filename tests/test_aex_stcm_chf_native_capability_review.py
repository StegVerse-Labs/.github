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

    def test_published_generic_source_native_math_is_bounded_not_universal(self):
        sdk = self.audit["SDK"]
        self.assertEqual(
            set(sdk["published_processor_capabilities"]),
            {"governance", "ecosystem_diagnostic", "purpose_bound_worker", "atomic_task_worker", "native_source_math"},
        )
        self.assertEqual(sdk["native_math_published_binding"], "INSTALLED_GENERIC_ADAPTER_NOT_PRIVATE_SOURCE_PACKAGE_UNLESS_OWNER_INSTALLED")
        self.assertFalse(sdk["generic_native_math"]["private_source_package_bundled_in_public_sdk"])
        self.assertEqual(sdk["generic_native_math"]["new_adapter_regressions_success"], 5)

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
        self.assertEqual(original["sdk_native_manifest"], "SDK_MANIFEST_INVOKABLE_BOUNDED_PRIVATE_ORIGINAL_SOURCE_3_SYNTHETIC_CASES")
        self.assertEqual(self.audit["CHF"]["original_source_sdk_invocation"]["hosted_validation_run"], 36231939908)
        self.assertEqual(self.census["native_math_manifest_invocations_verified"], 7)
        self.assertEqual(self.census["authentic_governed_math_runs_verified"], 0)
        self.assertTrue(all(r["sdk_manifest_invocation"] == "NOT_ESTABLISHED" for r in self.census["entries"] if r["repository"] not in {"Admissible-Existence/CHF", "Admissible-Existence/ET", "Admissible-Existence/HPS"}))
        self.assertEqual(len(original["four_synthetic_controls"]), 4)

    def test_unobserved_runtime_and_physical_heat_remain_unobserved(self):
        self.assertEqual(self.audit["runtime"]["authenticated_resident_gate"],
                         "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED")
        self.assertEqual(self.audit["runtime"]["master_records"],
                         "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED")
        self.assertEqual(self.audit["physical_heat_measurement"], "NOT_OBSERVED")
        self.assertEqual(self.audit["authority_effect"], "NONE")



    def test_exact_original_native_and_sdk_pre_enrichment_sha_are_distinct(self):
        observed = self.audit["CHF"]["original_source_sdk_invocation"]
        expected_native = {
            "positive": "40765ba64002847bb58d83a1d1745758be3f8b087beb58283f73b5ff479a2e3c",
            "below_absorption": "40c855e6f41de8afa4faf195d34f8598795c9d172ea676802b891c4a5ba6b052",
            "unknown_observability": "c97596105a3de44ecc473cf97c04005923439291c79bf4057453ba397bb247ea",
        }
        self.assertEqual(observed["native_result_sha256"], expected_native)
        self.assertEqual(len(set(observed["sdk_pre_enrichment_processor_sha256"].values())), 3)
        self.assertTrue(all(observed["sdk_pre_enrichment_processor_sha256"][case] != sha for case, sha in expected_native.items()))
        self.assertEqual(observed["full_horizon"], "NOT_ESTABLISHED")
        self.assertEqual(observed["physical_heat"], "NOT_OBSERVED")
        self.assertFalse(observed["production_or_general_distribution_proven"])


    def test_original_private_et_native_and_sdk_lineage_is_bounded(self):
        et = self.audit["ET"]
        row = self.rows["Admissible-Existence/ET"]
        self.assertEqual(et["original_core_git_blob"], "b520bae77ea5cedda95672c5529a2bc5fefc7b33")
        self.assertEqual(et["original_owner_hosted_run"], 36233578328)
        self.assertTrue(et["original_native_source_unchanged"])
        self.assertEqual(row["sdk_manifest_invocation"], "SDK_MANIFEST_INVOKABLE_BOUNDED_PRIVATE_ORIGINAL_SOURCE_1_SYNTHETIC_CASE")
        hashes = [et["original_native_result_sha256"].removeprefix("sha256:"),
                  et["sdk_manifest_sha256"], et["sdk_request_sha256"],
                  et["sdk_pre_enrichment_result_sha256"]]
        self.assertTrue(all(len(x) == 64 for x in hashes))
        self.assertEqual(len(set(hashes)), 4)
        self.assertEqual(et["full_et_mathematical_completeness"], "NOT_ESTABLISHED")
        self.assertEqual(et["governed_runtime"], "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED")
        self.assertEqual(self.census["authentic_governed_math_runs_verified"], 0)


    def test_private_hps_source_only_scores_do_not_grant_standing(self):
        hps = self.audit["HPS"]
        row = self.rows["Admissible-Existence/HPS"]
        self.assertEqual(hps["original_native_git_blob"], "91c205bae95d23b20e3814fcd58b5fdb0d603959")
        self.assertEqual(hps["hosted_validation_run"], 36233899275)
        self.assertEqual(row["sdk_manifest_invocation"], "SDK_MANIFEST_INVOKABLE_BOUNDED_PRIVATE_ORIGINAL_SOURCE_3_SYNTHETIC_SCORE_CLASSES")
        self.assertEqual([r["source_class"] for r in hps["cases"]], ["RESTORED", "DEGRADED", "FAILED"])
        for case in hps["cases"]:
            digests = [case[field] for field in ("native_result_sha256", "sdk_manifest_sha256", "sdk_request_sha256", "sdk_pre_enrichment_result_sha256")]
            self.assertTrue(all(len(digest) == 64 for digest in digests))
            self.assertEqual(len(set(digests)), 4)
        self.assertIs(hps["source_score_is_spe_standing"], False)
        self.assertEqual(hps["execution_authority_effect"], "NONE")
        self.assertEqual(hps["governed_runtime"], "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED")
        self.assertEqual(self.census["authentic_governed_math_runs_verified"], 0)

if __name__ == "__main__":
    unittest.main()
