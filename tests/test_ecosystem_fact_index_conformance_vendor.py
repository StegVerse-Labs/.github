"""Vendored LLM-adapter fact-index conformance vector, checked as data only.

RT-ECOSYSTEM-CHAT-LOCAL-ANSWER-001 is a definition with no runner, and its fact
index is referenced from LLM-adapter#426 rather than vendored, so no case is
executed here: the cases execute in the declared runtime's CI, which the
execution_evidence_ref cites. These tests pin the vector, verify every file it
pins, check the cases against the vector's own rules, bind it to the shard's
FACT_INDEX dependency and check that the cited execution covers this vector.
Nothing here is runtime evidence or authority.
"""
import hashlib
import json
import unittest
from pathlib import Path

from scripts import materialize_reusable_task_construct as constructor

ROOT = Path(__file__).resolve().parents[1]
VECTOR_DIR = ROOT / "tests/fixtures/ecosystem_fact_index_conformance"
MANIFEST_SHA256 = "b5929144b5384805edaedd774b378edbed74205b70188d726d693532125520d6"
TASK_ID = "RT-ECOSYSTEM-CHAT-LOCAL-ANSWER-001"
EXECUTED_IN_DECLARED_RUNTIME_CI = "EXECUTED_IN_DECLARED_RUNTIME_CI_LABS_HOLDS_DATA_ONLY"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class VendoredVectorDigestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = load(VECTOR_DIR / "conformance-vector.json")

    def test_manifest_digest_is_pinned(self):
        self.assertEqual(sha256(VECTOR_DIR / "conformance-vector.json"), MANIFEST_SHA256)

    def test_vendor_record_matches_pinned_manifest(self):
        vendor = load(VECTOR_DIR / "VENDOR.json")
        self.assertEqual(vendor["manifest_sha256"], MANIFEST_SHA256)
        self.assertEqual(vendor["source_repository"], self.manifest["subject"]["repository"])
        self.assertEqual(vendor["subject_module"], self.manifest["subject"]["module"])
        self.assertEqual(vendor["vector_id"], self.manifest["vector_id"])
        self.assertRegex(vendor["source_commit"], r"^[0-9a-f]{40}$")

    def test_every_pinned_file_matches_its_digest(self):
        pinned = self.manifest["source_fixtures"] + self.manifest["refusal_fixtures"]
        self.assertEqual(len(pinned), 9)
        for entry in pinned:
            with self.subTest(fixture=entry["id"]):
                self.assertEqual(sha256(VECTOR_DIR / entry["fixture"]), entry["sha256"])

    def test_no_code_is_vendored(self):
        files = {p.relative_to(VECTOR_DIR).as_posix() for p in VECTOR_DIR.rglob("*") if p.is_file()}
        self.assertFalse({f for f in files if not f.endswith((".json", ".md"))})


class VendoredVectorCaseTests(unittest.TestCase):
    def setUp(self):
        self.manifest = load(VECTOR_DIR / "conformance-vector.json")
        self.cases = self.manifest["cases"]

    def test_case_set_is_six_allow_and_seventeen_fail_closed(self):
        self.assertEqual(len(self.cases), 23)
        self.assertEqual(len({c["id"] for c in self.cases}), 23)
        dispositions = [c["expected_disposition"] for c in self.cases]
        self.assertEqual(dispositions.count("ALLOW"), 6)
        self.assertEqual(dispositions.count("FAIL_CLOSED"), 17)

    def test_each_case_follows_the_vector_rules(self):
        rule = self.manifest["rules"]["disposition"]
        self.assertEqual(self.manifest["rules"]["fail_closed_required_fields"], constructor.resolve_reusable_task(
            constructor.load_registry(), TASK_ID)["non_allow_record_fields"])
        for case in self.cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(case["expected_disposition"], rule[case["expected_status"]])
                if case["expected_disposition"] == "ALLOW":
                    self.assertTrue(case["expected_answers"])
                else:
                    self.assertTrue(case["expected_failure_code"])
                    self.assertTrue(case["expected_failed_predicate"])

    def test_every_allow_citation_names_a_pinned_source_line_holding_the_key(self):
        sources = {(s["repository"], s["revision"], s["path"]): s for s in self.manifest["source_fixtures"]}
        for case in self.cases:
            for answer in case.get("expected_answers", []):
                with self.subTest(case=case["id"], key=answer["key"]):
                    head, path, line = answer["citation"].rsplit(":", 2)
                    repository, revision = head.rsplit("@", 1)
                    source = sources[(repository, revision, path)]
                    lines = (VECTOR_DIR / source["fixture"]).read_bytes().decode("utf-8").split("\n")
                    self.assertIn(json.dumps(answer["key"]), lines[int(line) - 1])

    def test_refusal_cases_reference_pinned_fixtures(self):
        ids = {f["id"] for f in self.manifest["source_fixtures"] + self.manifest["refusal_fixtures"]}
        for case in self.cases:
            for source in case.get("sources", []):
                with self.subTest(case=case["id"]):
                    self.assertIn(source.get("source_fixture") or source.get("refusal_fixture"), ids)


class LocalAnswerBindingTests(unittest.TestCase):
    def setUp(self):
        self.definition = constructor.resolve_reusable_task(constructor.load_registry(), TASK_ID)
        self.manifest = load(VECTOR_DIR / "conformance-vector.json")
        self.fact_index = next(d for d in self.definition["dependency_refs"] if d["role"] == "FACT_INDEX")

    def test_vector_covers_the_pinned_fact_index_module(self):
        vendor = load(VECTOR_DIR / "VENDOR.json")
        self.assertIn(f"StegVerse-Labs/.github:{TASK_ID}", self.manifest["consumers"])
        self.assertTrue(self.fact_index["source_ref"].endswith(":" + self.manifest["subject"]["module"]))
        self.assertEqual(self.fact_index["source_blob"], vendor["subject_module_blob"])
        ref = self.fact_index["conformance_vector_ref"]
        self.assertEqual(ref["path"], VECTOR_DIR.relative_to(ROOT).as_posix() + "/conformance-vector.json")
        self.assertEqual(ref["sha256"], MANIFEST_SHA256)
        self.assertEqual(ref["source_commit"], vendor["source_commit"])

    def test_cases_stay_unexecuted_while_the_fact_index_is_unresolved(self):
        # No runner and an unvendored fact index: no case runs in Labs, and the
        # cases execute only in the declared runtime's CI, cited by the evidence
        # ref. When the dependency resolves this test fails, and the 23 cases
        # must then run through the registered runner.
        self.assertEqual(self.definition["runner_templates"], [])
        self.assertFalse(self.fact_index["vendored"])
        self.assertEqual(self.fact_index["failure_code"], "FACT_INDEX_DEPENDENCY_NOT_ON_MAIN")
        self.assertEqual(self.fact_index["conformance_vector_ref"]["execution"], EXECUTED_IN_DECLARED_RUNTIME_CI)

    def test_execution_evidence_ref_covers_the_vendored_vector(self):
        vendor = load(VECTOR_DIR / "VENDOR.json")
        ref = vendor["execution_evidence_ref"]
        self.assertEqual(vendor["execution"], EXECUTED_IN_DECLARED_RUNTIME_CI)
        self.assertEqual(self.fact_index["conformance_vector_ref"]["execution_evidence_ref"], ref)
        self.assertEqual(ref["vector_manifest_sha256"], sha256(VECTOR_DIR / "conformance-vector.json"))
        self.assertEqual(ref["vector_manifest_sha256"], vendor["manifest_sha256"])
        self.assertEqual(ref["case_count"], len(self.manifest["cases"]))
        self.assertEqual(ref["repository"], vendor["source_repository"])
        self.assertEqual(f"{ref['repository']}#{ref['pr']}", vendor["source_pr"])
        self.assertRegex(ref["commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(ref["conclusion"], "success")
        self.assertEqual(ref["run_url"], f"https://github.com/{ref['repository']}/actions/runs/{ref['run_id']}")


if __name__ == "__main__":
    unittest.main()
