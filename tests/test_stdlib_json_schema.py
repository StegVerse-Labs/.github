"""scripts/stdlib_json_schema.py: the standard-library validator that replaces jsonschema (StegVerse-org/.github#166).

Known-good and known-bad fixtures for every implemented keyword, refusal (six fields) of every unimplemented
keyword or form, and the agreement corpus: every instance the schema-only consumer tests judge, with the verdict
those tests asserted under jsonschema.Draft202012Validator. This file checks the stdlib validator against the
corpus; StegVerse-org/.github's full-suite job, where jsonschema is installed, checks jsonschema against the same
pinned corpus bytes. `python3 tests/test_stdlib_json_schema.py --write` regenerates the corpus.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import stdlib_json_schema as S  # noqa: E402

CORPUS = ROOT / "tests" / "fixtures" / "stdlib-json-schema" / "agreement-corpus.json"
CORPUS_SCHEMA = "stegverse.stdlib-json-schema-agreement-corpus/v1"
CONSUMER_SCHEMAS = ("schemas/hil-explanation-trial-record.v1.schema.json", "schemas/user-facing-explanation.v1.schema.json")
# Consumer schemas outside this repository, by keyword (StegVerse-org/.github#166): the validator also judges
# StegVerse-org/.github orchestration/schemas/task-registry.schema.json, vendored there from StegVerse-Labs/repo-standards
# schemas/task-registry.schema.json @e46a8a5a68c7009a3939d9e3c7cef307cd03ceca (sha256 d3a6460b45e1fb24...762976ec), whose
# cosv.exact_metrics uses minProperties. Its agreement with jsonschema is re-derived in StegVerse-org/.github CI
# (tests/test_stdlib_json_schema_agreement.py, committed registry and violations).
EXTERNAL_CONSUMER_KEYWORDS = {"minProperties": "StegVerse-org/.github orchestration/schemas/task-registry.schema.json"}
D = S.DRAFT_2020_12

# keyword -> (schema, known-good instances, known-bad instances). Edge cases follow jsonschema: booleans are not
# numbers, 1.0 is an integer, true != 1, 1 == 1.0.
KEYWORDS = {
    "type": ({"type": ["integer", "null"]}, [1, 1.0, None, -7], [True, 1.5, "1", [], {}]),
    "enum": ({"enum": ["A", 1, None, {"k": [1]}]}, ["A", 1, 1.0, None, {"k": [1.0]}], ["a", True, 2, {"k": [True]}]),
    "const": ({"const": {"a": [1, "x"]}}, [{"a": [1, "x"]}, {"a": [1.0, "x"]}], [{"a": [True, "x"]}, {"a": [1]}, []]),
    "properties": ({"properties": {"n": {"type": "string"}}}, [{"n": "x"}, {}, {"m": 1}, 5], [{"n": 1}]),
    "required": ({"required": ["a", "b"]}, [{"a": 1, "b": None}, "not an object"], [{"a": 1}, {}]),
    "additionalProperties": ({"properties": {"a": {}}, "additionalProperties": False}, [{"a": 1}, {}, [1]],
                             [{"a": 1, "b": 2}, {"b": 2}]),
    "items": ({"items": {"type": "string"}}, [[], ["a", "b"], "str"], [["a", 1], [None]]),
    "minItems": ({"minItems": 2}, [[1, 2], [1, 2, 3], {}], [[], [1]]),
    "uniqueItems": ({"uniqueItems": True}, [[1, True], [{"a": 1}, {"a": 2}], []], [[1, 1.0], [{"a": 1}, {"a": 1.0}]]),
    "contains": ({"contains": {"const": "R"}}, [["x", "R"], ["R"], "R"], [[], ["x"]]),
    "minLength": ({"minLength": 2}, ["ab", "\u00e9\u00e9", 5], ["", "a", "\u00e9"]),
    "pattern": ({"pattern": "^sha256:[0-9a-f]{4}$"}, ["sha256:00ff", 3], ["sha256:00FF", "xsha256:00ff", "sha256:00f"]),
    "minimum": ({"minimum": 1}, [1, 1.5, "0", True], [0, 0.99, -1]),
    "maximum": ({"maximum": 1}, [1, 0.5, "9", False], [1.01, 2]),
    "minProperties": ({"minProperties": 2}, [{"a": 1, "b": 2}, {"a": 1, "b": 2, "c": 3}, [1], "ab"], [{}, {"a": 1}]),
    "maxProperties": ({"maxProperties": 1}, [{}, {"a": 1}, [1, 2]], [{"a": 1, "b": 2}]),
    "allOf": ({"allOf": [{"type": "integer"}, {"minimum": 3}]}, [3, 9], [2, 3.5, "3"]),
    "anyOf": ({"anyOf": [{"type": "string"}, {"minimum": 3}]}, ["x", 3, None], [2, 0.5]),
    "not": ({"not": {"const": "DENY"}}, ["ALLOW", None], ["DENY"]),
    "if": ({"if": {"properties": {"k": {"const": "A"}}, "required": ["k"]}, "then": {"required": ["a"]}},
           [{"k": "A", "a": 1}, {"k": "B"}, {}], [{"k": "A"}]),
    "then": ({"if": {"type": "string"}, "then": {"minLength": 3}}, ["abc", 5, None], ["ab"]),
}
# annotations: never decide validity (format is annotation-only in Draft 2020-12 without a format checker).
ANNOTATIONS = {
    "$schema": ({"$schema": D, "type": "string"}, ["x"], [1]),
    "$id": ({"$id": "https://stegverse.invalid/s.json", "type": "string"}, ["x"], [1]),
    "$comment": ({"$comment": "c", "type": "string"}, ["x"], [1]),
    "title": ({"title": "t", "type": "string"}, ["x"], [1]),
    "description": ({"description": "d", "type": "string"}, ["x"], [1]),
    "format": ({"type": "string", "format": "date-time"}, ["2026-10-23T00:00:00Z", "not a date-time"], [1]),
}
UNSUPPORTED = {
    "else": {"if": {"type": "string"}, "then": {"minLength": 1}, "else": {"type": "integer"}},
    "$ref": {"$defs": {"a": {"type": "string"}}, "$ref": "#/$defs/a"},
    "prefixItems": {"prefixItems": [{"type": "string"}]},
    "oneOf": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
    "patternProperties": {"patternProperties": {"^x": {"type": "string"}}},
    "nested_unsupported": {"properties": {"a": {"properties": {"b": {"maxLength": 3}}}}},
    "items_as_array": {"items": [{"type": "string"}]},
    "embedded_schema_dialect": {"properties": {"a": {"$schema": D, "type": "string"}}},
    "draft_07_dialect": {"$schema": "http://json-schema.org/draft-07/schema#", "type": "string"},
    "unknown_type_name": {"type": "any"},
    "pattern_does_not_compile": {"pattern": "("},
    "negative_minLength": {"minLength": -1},
    "boolean_as_minimum": {"minimum": True},
    "empty_anyOf": {"anyOf": []},
}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def build_corpus() -> dict:
    """Every instance the schema-only consumer tests judge, with the verdict each asserted."""
    th = _load("_corpus_hil", ROOT / "tests" / "test_hil_explanation_experiment.py")
    tu = _load("_corpus_ufe", ROOT / "tests" / "test_user_facing_explanation.py")
    hil, ufe = CONSUMER_SCHEMAS
    cases = []

    def add(schema: str, source: str, label: str, inst, valid: bool) -> None:
        cases.append({"schema_path": schema, "schema_sha256": _sha(schema), "source_test": source, "label": label,
                      "instance": json.loads(json.dumps(inst)), "expected_valid": valid})
    so = th.SchemaOnlyConsumers()
    src = "tests/test_hil_explanation_experiment.py::SchemaOnlyConsumers::test_jsonschema_rejects_contradictory_trials"
    for name, inst in so.mutations().items():
        add(hil, src, name, inst, False)
    for i, inst in enumerate(so.valid_records()):
        add(hil, src, f"valid_record_{i}", inst, True)
    src = ("tests/test_hil_explanation_experiment.py::ActualObservationOnlyThroughTicketedIntake::"
           "test_validation_binds_locator_to_evidence_class")
    add(hil, src, "good", th.trial(), True)
    for name, inst in {"synthetic_with_owner_locator": th.trial(evidence_locator="owner-vault://x"),
                       "actual_with_synthetic_locator": th.trial(evidence_class="ACTUAL_OBSERVATION",
                                                                 evidence_locator="synthetic://x#" + th.D64),
                       "actual_without_digest": th.trial(evidence_class="ACTUAL_OBSERVATION",
                                                         evidence_locator="owner-vault://x")}.items():
        add(hil, src, name, inst, False)
    src = "tests/test_user_facing_explanation.py::VerifiedReceiptLocatorSchema::test_verified_receipt_locator_is_required_by_jsonschema"
    valid, mutations = tu.VerifiedReceiptLocatorSchema().mutations()
    add(ufe, src, "valid", valid, True)
    for name, inst in mutations.items():
        add(ufe, src, f"ref={name}", inst, False)
    src = "tests/test_user_facing_explanation.py::SchemaOnlyConsumers::test_jsonschema_rejects_contradictory_artifacts"
    for name, inst in tu.SchemaOnlyConsumers().mutations().items():
        add(ufe, src, name, inst, False)
    for p in tu.FIXTURES:
        add(ufe, src, f"fixture:{p.stem}", tu.build(p.stem), True)
    kw = [{"keyword": k, "kind": "assertion", "schema": {"$schema": D, **s}, "good": g, "bad": b}
          for k, (s, g, b) in KEYWORDS.items()]
    kw += [{"keyword": k, "kind": "annotation", "schema": s if "$schema" in s else {"$schema": D, **s}, "good": g,
            "bad": b} for k, (s, g, b) in ANNOTATIONS.items()]
    return {"schema": CORPUS_SCHEMA, "validator": "scripts/stdlib_json_schema.py", "dialect": D,
            "verdict_source": "each schema case's expected_valid is the verdict its source test asserted under "
                              "jsonschema.Draft202012Validator; StegVerse-org/.github CI re-derives it with jsonschema",
            "schema_cases": cases, "keyword_cases": kw,
            "unsupported": [{"label": k, "schema": {"$schema": D, **v} if "$schema" not in v else v}
                            for k, v in UNSUPPORTED.items()]}


def canonical(v) -> bytes:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class Corpus(unittest.TestCase):
    def test_the_committed_corpus_is_what_the_consumer_tests_judge(self):
        self.assertEqual(canonical(json.loads(CORPUS.read_text(encoding="utf-8"))), canonical(build_corpus()),
                         "regenerate: python3 tests/test_stdlib_json_schema.py --write")

    def test_every_recorded_verdict_is_the_stdlib_verdict(self):
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(corpus["schema_cases"]), 40)
        validators = {p: S.Validator(json.loads((ROOT / p).read_text(encoding="utf-8"))) for p in CONSUMER_SCHEMAS}
        for c in corpus["schema_cases"]:
            with self.subTest(case=c["label"], schema=c["schema_path"]):
                self.assertEqual(c["schema_sha256"], _sha(c["schema_path"]))
                self.assertEqual(validators[c["schema_path"]].is_valid(c["instance"]), c["expected_valid"])

    def test_the_implemented_keywords_are_exactly_the_consumer_schemas_keywords(self):
        used = set()
        for p in CONSUMER_SCHEMAS:
            used |= S.keywords(json.loads((ROOT / p).read_text(encoding="utf-8")))
        self.assertEqual(used | set(EXTERNAL_CONSUMER_KEYWORDS), set(S.SUPPORTED))
        self.assertFalse(used & set(EXTERNAL_CONSUMER_KEYWORDS), "a keyword used here needs no external record")


class Keywords(unittest.TestCase):
    def test_each_keyword_has_known_good_and_known_bad_fixtures(self):
        self.assertEqual(set(KEYWORDS), set(S.ASSERTIONS))
        self.assertEqual(set(ANNOTATIONS), set(S.ANNOTATIONS))
        for k, (schema, good, bad) in {**KEYWORDS, **ANNOTATIONS}.items():
            with self.subTest(keyword=k):
                self.assertTrue(good and bad)
                self.assertIn(k, S.keywords(schema))
                v = S.Validator({"$schema": D, **schema})
                for g in good:
                    self.assertTrue(v.is_valid(g), f"{k} rejected known-good {g!r}")
                for b in bad:
                    self.assertFalse(v.is_valid(b), f"{k} accepted known-bad {b!r}")
                    self.assertTrue(v.errors(b))

    def test_boolean_schemas(self):
        self.assertTrue(S.Validator({"properties": {"a": True}}).is_valid({"a": "x"}))
        self.assertFalse(S.Validator({"properties": {"a": False}}).is_valid({"a": 1}))
        self.assertTrue(S.Validator({"properties": {"a": False}}).is_valid({}))


class FailClosed(unittest.TestCase):
    def test_every_unimplemented_keyword_or_form_is_refused_with_six_fields(self):
        for label, schema in UNSUPPORTED.items():
            with self.subTest(label=label):
                with self.assertRaises(S.SchemaUnsupported) as ctx:
                    S.Validator(schema)
                item = ctx.exception.item
                self.assertEqual(item["disposition"], "FAIL_CLOSED")
                for f in ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
                          "owning_existing_goal", "next_attempt"):
                    self.assertTrue(item[f], f)

    def test_a_refused_schema_judges_no_instance(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "s.json").write_text(json.dumps(UNSUPPORTED["else"]), encoding="utf-8")
            (Path(d) / "i.json").write_text(json.dumps("anything"), encoding="utf-8")
            out = subprocess.run([sys.executable, str(ROOT / "scripts" / "stdlib_json_schema.py"), "validate",
                                  "--schema", str(Path(d) / "s.json"), "--instance", str(Path(d) / "i.json")],
                                 capture_output=True, text=True)
        self.assertEqual(out.returncode, 2, out.stderr)
        self.assertEqual(json.loads(out.stdout)["failure_code"], "SCHEMA_KEYWORD_UNSUPPORTED")

    def test_the_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "s.json").write_text(json.dumps({"$schema": D, "type": "string"}), encoding="utf-8")
            for inst, code in (("x", 0), (1, 1)):
                (Path(d) / "i.json").write_text(json.dumps(inst), encoding="utf-8")
                out = subprocess.run([sys.executable, str(ROOT / "scripts" / "stdlib_json_schema.py"), "validate",
                                      "--schema", str(Path(d) / "s.json"), "--instance", str(Path(d) / "i.json")],
                                     capture_output=True, text=True)
                self.assertEqual(out.returncode, code, out.stdout)


if __name__ == "__main__":
    if "--write" in sys.argv:
        CORPUS.write_text(json.dumps(build_corpus(), indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                          encoding="utf-8")
        print(CORPUS)
    else:
        unittest.main()
