import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "review_worker",
    ROOT / "workers" / "erl_ai_economic_transparency_review_worker.py",
)
review_worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review_worker)

class TestERLAIEconomicTransparencyReviewWorker(unittest.TestCase):
    def write_json(self, root, rel, value):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def build_source(self, root, bad_rating=False):
        package = {
            "review_scope":"FINALIZED_CONSUMER_NON_ACCOUNT_ATTRIBUTED_SURFACES_ONLY",
            "providers":["openai","anthropic","deepseek"],
            "forbidden_promotions":["provider-wide transparency ranking"]
        }
        self.write_json(root, "assessments/reviews/ai-economic-transparency-consumer-surface-independent-review-package.2026-09-03.json", package)

        findings=[]
        reviews=[]
        for provider in ["openai","anthropic","deepseek"]:
            rating = 4 if bad_rating and provider == "openai" else 5
            obs = {
                "surface_class":"CONSUMER_NON_ACCOUNT_ATTRIBUTED",
                "rating_scope":"SURFACE_SPECIFIC",
                "protocol_complete":True,
                "disclosure_burden_rating":rating,
                "reconstructable_actual_cost":False,
                "literal_request_cost_usd":None,
                "scale_scenarios":[
                    {"equivalent_requests":1000,"state":"UNBOUNDED_UNKNOWN","known_total_cost_usd":None,"lower_bound_usd":None,"upper_bound_usd":None},
                    {"equivalent_requests":100000,"state":"UNBOUNDED_UNKNOWN","known_total_cost_usd":None,"lower_bound_usd":None,"upper_bound_usd":None},
                    {"equivalent_requests":1000000,"state":"UNBOUNDED_UNKNOWN","known_total_cost_usd":None,"lower_bound_usd":None,"upper_bound_usd":None},
                ],
                "activation_authorized":False,
            }
            self.write_json(root, f"research-data/ai-economic-transparency/{provider}-consumer-surface-observation.2026-09-03.json", obs)
            findings.append({
                "provider":provider,
                "surface_class":"CONSUMER_NON_ACCOUNT_ATTRIBUTED",
                "disclosure_burden_rating":rating,
                "scale_sensitivity_state":"UNBOUNDED_UNKNOWN",
            })
            reviews.append({"provider":provider,"result":"NO_MATERIAL_CONTRADICTION"})

        self.write_json(root, "research-data/ai-economic-transparency/candidate-results.consumer-surfaces.2026-09-03.json", {
            "state":"CANDIDATE_RESULTS_PENDING_INDEPENDENT_REVIEW",
            "provider_wide_ranking_authorized":False,
            "findings":findings,
        })
        self.write_json(root, "assessments/reviews/ai-economic-transparency-consumer-surface-contradiction-review.2026-09-03.json", {
            "state":"COMPLETE",
            "provider_reviews":reviews,
        })
        self.write_json(root, "schemas/ai-economic-transparency-observation.schema.json", {"fixture":True})
        standard = root / "standards" / "ai-economic-transparency.v1.md"
        standard.parent.mkdir(parents=True, exist_ok=True)
        standard.write_text("fixture", encoding="utf-8")

    def test_bundle_manifest_verification_rejects_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self.build_source(root)
            manifest = {
                "schema":"stegverse.erl.ai-economic-transparency-review-input-bundle/v1",
                "files":[
                    {"relative_path": rel, "sha256":"sha256:deadbeef"}
                    for rel in review_worker.REQUIRED_RELATIVE_PATHS
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            old_root = review_worker.BUNDLED_REVIEW_ROOT
            old_manifest = review_worker.BUNDLE_MANIFEST
            try:
                review_worker.BUNDLED_REVIEW_ROOT = root.resolve()
                review_worker.BUNDLE_MANIFEST = manifest_path
                ok, errors = review_worker.verify_bundle_manifest(root.resolve())
                self.assertFalse(ok)
                self.assertTrue(any("hash mismatch" in e for e in errors))
            finally:
                review_worker.BUNDLED_REVIEW_ROOT = old_root
                review_worker.BUNDLE_MANIFEST = old_manifest

    def test_approve_when_all_fixed_review_checks_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self.build_source(root)
            result = review_worker.evaluate(root)
            self.assertEqual(result["recommendation"], "APPROVE")
            self.assertTrue(all(c["passed"] for c in result["checks"]))

    def test_revise_when_rating_does_not_match_fixed_rule(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self.build_source(root, bad_rating=True)
            result = review_worker.evaluate(root)
            self.assertEqual(result["recommendation"], "REVISE")
            self.assertTrue(any(not c["passed"] for c in result["checks"]))

if __name__ == "__main__":
    unittest.main()
