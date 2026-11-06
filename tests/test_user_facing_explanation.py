"""Universal user-facing explanation contract: builder, schema, sanitization, non-authority."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import user_facing_explanation as U  # noqa: E402

FIXTURES = sorted((ROOT / "data" / "user-facing-explanation" / "fixtures.d").glob("*.json"))
SCHEMA = json.loads((ROOT / "schemas" / "user-facing-explanation.v1.schema.json").read_text(encoding="utf-8"))


def fixture(stem: str) -> dict:
    return json.loads(next(p for p in FIXTURES if p.stem == stem).read_text(encoding="utf-8"))


def build(stem: str) -> dict:
    f = fixture(stem)
    return U.validate_explanation(U.build_explanation(f["outcome"], surface=f["surface"]))


class FixturesBuildAndValidate(unittest.TestCase):
    def test_non_allow_outcomes_carry_the_actionable_disposition(self):
        for p in FIXTURES:
            a = build(p.stem)
            ad = a["outcome"]["actionable_disposition"]
            if a["outcome"]["disposition"] == "ALLOW":
                self.assertIsNone(ad)
            else:
                self.assertEqual(set(ad), set(U.ACTIONABLE_FIELDS))
                self.assertIn(ad["failed_predicate"], a["outcome"]["predicates"])
                text = U.render_prose(a)
                self.assertIn("What resolves this:", text)
                self.assertIn("Next attempt:", text)

    def test_outcome_classes_present(self):
        # Task Registry invariant: every transition, ALLOW or not, has a receipt. There is no authorized-but-pending
        # class; the missing-evidence fixture is a step that did not take place (FAILED_CLOSED).
        classes = {build(p.stem)["outcome"]["outcome_class"] for p in FIXTURES}
        self.assertEqual(classes, {"SUCCESS_VERIFIED", "DENIED", "FAILED_CLOSED", "UNOBSERVED"})

    def test_artifact_keys_match_schema_exactly(self):
        for p in FIXTURES:
            a = build(p.stem)
            self.assertEqual(set(a) - {"produced_at"}, set(SCHEMA["required"]) | {"remediation_draft"})
            self.assertEqual(a["schema"], "stegverse.user-facing-explanation/v1")
            self.assertEqual(a["ecosystem_identifier"], "STEGVERSE")

    def test_authorization_and_execution_are_separate_facts(self):
        s = build("01-success-verified")
        self.assertTrue(s["authorization"]["authorized"] and s["execution"]["executed"])
        self.assertEqual(s["execution"]["execution_state"], "VERIFIED")
        for stem in ("02-denied", "03-fail-closed", "04-missing-evidence", "05-unobserved-runtime"):
            a = build(stem)
            self.assertFalse(a["authorization"]["authorized"])
            self.assertFalse(a["execution"]["executed"])
            self.assertEqual(a["execution"]["execution_state"], "NOT_EXECUTED")

    def test_prose_is_primary_and_complete(self):
        for p in FIXTURES:
            text = U.render_prose(build(p.stem))
            for heading in ("What happened:", "Why:", "Outcome:", "What was authorized:", "What was executed:", "What evidence exists:", "What you can safely do next:", "Limitations:"):
                self.assertIn(heading, text)
            self.assertNotIn("{", text)
        self.assertIn("Failing closed is the designed behaviour", U.render_prose(build("03-fail-closed")))
        self.assertIn("did not take place", U.render_prose(build("04-missing-evidence")))
        self.assertIn("not success, not failure", U.render_prose(build("05-unobserved-runtime")).lower())

    def test_lower_case_producer_predicates_are_copied_verbatim(self):
        f = fixture("03-fail-closed")
        a = U.validate_explanation(U.build_explanation(dict(f["outcome"], predicate="snapshot_position_field_missing:value_usd", predicates=None, failed_predicate="snapshot_position_field_missing:value_usd"), surface=f["surface"]))
        self.assertEqual(a["outcome"]["predicate"], "snapshot_position_field_missing:value_usd")
        self.assertIn("snapshot_position_field_missing:value_usd", a["prose"]["what_was_authorized"])

    def test_predicate_preserved_exactly(self):
        a = build("03-fail-closed")
        self.assertEqual(a["outcome"]["predicate"], "AUTHORIZED_DEVICE_INDEPENDENT_KV_INGRESS_NOT_BOUND_TO_WORKSPACE")
        self.assertIn("AWAITING_SOVEREIGN_INTR_INGRESS", a["outcome"]["predicates"])
        self.assertIn(a["outcome"]["predicate"], a["prose"]["what_was_authorized"])

    def test_non_authority_blocks(self):
        for p in FIXTURES:
            a = build(p.stem)
            self.assertEqual(a["authority"], {"authority_effect": "NONE", "explanation_is_non_authoritative": True, "canonical_record_mutation": False, "alternate_governance_path": False})
            self.assertEqual(a["sanitization"], {"secrets_present": False, "personal_data_minimized": True, "invented_evidence": False})
            self.assertEqual(a["recognition_probe"]["literal"], "STEGVERSE_ECOSYSTEM_KNOWLEDGE_PROBE_V1")
            self.assertEqual(a["recognition_probe"]["status"], "CANDIDATE_NOT_CANONICAL")
            self.assertTrue(a["llm_interpretation"]["self_contained"])
            self.assertTrue(any("not" in s.lower() and "authoriz" in s.lower() for s in a["llm_interpretation"]["prohibited_assumptions"]))

    def test_remediation_draft_is_unsubmitted_and_non_authorizing(self):
        d = build("02-denied")["remediation_draft"]
        self.assertEqual({k: d[k] for k in ("submitted", "manifest_admitted", "authority_effect", "non_authorizing")}, {"submitted": False, "manifest_admitted": False, "authority_effect": "NONE_REQUEST_ONLY", "non_authorizing": True})
        self.assertIn("unsubmitted remediation draft", " ".join(build("02-denied")["prose"]["what_you_can_safely_do_next"]))
        self.assertIsNone(build("03-fail-closed")["remediation_draft"])

    def test_personal_data_minimized_by_whitelist(self):
        f = fixture("03-fail-closed")
        record = dict(f["outcome"], owner_email="person@example.invalid", home_address="1 Example Street", notes={"free": "text"})
        a = U.validate_explanation(U.build_explanation(record, surface=f["surface"]))
        self.assertNotIn("example.invalid", json.dumps(a))
        self.assertNotIn("Example Street", json.dumps(a))

    def test_published_examples_do_not_drift(self):
        out = subprocess.run([sys.executable, "scripts/render_user_facing_explanation_examples.py", "--check"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("USER_FACING_EXPLANATION_EXAMPLES_PASS", out.stdout)


class Refusals(unittest.TestCase):
    def refuse(self, record: dict, code: str, surface: dict | None = None):
        with self.assertRaises(U.ExplanationError) as ctx:
            U.build_explanation(record, surface=surface or {"repository": "r", "surface_id": "s"})
        self.assertTrue(str(ctx.exception).startswith(code), str(ctx.exception))

    def test_refusals(self):
        base = fixture("03-fail-closed")["outcome"]
        self.refuse(dict(base, api_token="x"), "secret_material_present:api_token")
        self.refuse(dict(base, evidence=[{"kind": "SOURCE_REF", "ref": "Bearer abcdef", "description": "d"}]), "secret_material_present")
        self.refuse(dict(base, disposition="ALLOW", consequence_observation="OBSERVED"), "allow_requires_receipt")
        # ALLOW without its receipt does not exist: no observation, or no receipt-class evidence, is refused.
        receipt = [{"kind": "RECEIPT_REF", "ref": "receipt:1", "description": "d"}]
        self.refuse(dict(base, disposition="ALLOW", consequence_observation="NOT_AUTHENTICALLY_OBSERVED", evidence=receipt), "allow_requires_receipt")
        self.refuse(dict(base, disposition="ALLOW", consequence_observation="UNKNOWN", evidence=receipt), "allow_requires_receipt")
        self.refuse(dict(base, consequence_observation="OBSERVED"), "non_allow_cannot_observe_consequence")
        self.refuse(dict(base, remediation_draft={"submitted": True}), "remediation_draft_must_be_unsubmitted")
        self.refuse(dict(base, remediation_draft={"submitted": False, "manifest_admitted": True}), "remediation_draft_must_not_be_admitted")
        self.refuse(dict(base, remediation_draft={"submitted": False, "manifest_admitted": False, "authority_effect": "EXECUTE"}), "remediation_draft_must_be_non_authorizing")
        self.refuse(dict(base, remediation_draft={"submitted": False, "manifest_admitted": False, "authority_effect": "NONE", "disposition": "ALLOW"}), "remediation_draft_must_not_carry_allow")
        self.refuse(dict(base, predicate="not a predicate"), "predicate_invalid")
        self.refuse(dict(base, disposition="MAYBE"), "disposition_invalid")
        self.refuse(dict(base, requested_action=""), "requested_action_required")
        self.refuse(dict(base, authority_source="GITHUB"), "authority_source_invalid")
        self.refuse(dict(base, evidence=[{"kind": "RECEIPT_REF", "ref": None, "description": "d"}]), "evidence_ref_required_for_kind")
        self.refuse(base, "secret_material_present", surface={"repository": "r", "surface_id": "s", "session_cookie": "x"})
        # Organization Role conformance item 5: a non-ALLOW record without its six actionable fields is not a finding.
        for key in U.ACTIONABLE_FIELDS:
            self.refuse({k: v for k, v in base.items() if k != key}, "non_allow_requires_" + key)
            self.refuse(dict(base, **{key: "  "}), "non_allow_requires_" + key)
        self.refuse(dict(base, failed_predicate="not a predicate"), "failed_predicate_invalid")
        # A failed condition named apart from the outcome predicate is listed with the predicates.
        named = U.validate_explanation(U.build_explanation(dict(base, failed_predicate="PREREQUISITE_ESTABLISHED"), surface=fixture("03-fail-closed")["surface"]))
        self.assertIn("PREREQUISITE_ESTABLISHED", named["outcome"]["predicates"])
        self.assertEqual(named["outcome"]["actionable_disposition"]["failed_predicate"], "PREREQUISITE_ESTABLISHED")

    def test_text_that_displays_as_something_else_is_refused(self):
        # Right-to-left override, isolate, zero-width, NUL, line separator and a lone surrogate, in each
        # free-text place a producer controls; the builder and the validator both refuse them.
        base = fixture("03-fail-closed")["outcome"]
        hidden = ["\u202e", "\u2066", "\u200b", "\u0000", "\u2028", "\ud800"]
        for ch in hidden:
            self.refuse(dict(base, requested_action="Act" + ch + "ion"), "text_not_displayable:requested_action")
            self.refuse(dict(base, why="ok " + ch + "hidden"), "text_not_displayable:why")
            self.refuse(dict(base, evidence=[{"kind": "SOURCE_REF", "ref": "kv:" + ch + "x", "description": "d"}]), "text_not_displayable:evidence[0].ref")
            self.refuse(dict(base, evidence=[{"kind": "SOURCE_REF", "ref": "kv:x", "description": "d" + ch}]), "text_not_displayable:evidence[0].description")
            self.refuse(base, "text_not_displayable:surface_id", surface={"repository": "r", "surface_id": "s" + ch})
            artifact = build("01-success-verified")
            artifact["evidence"][0]["description"] = "Receipt" + ch
            with self.assertRaises(U.ExplanationError) as ctx:
                U.validate_explanation(artifact)
            self.assertTrue(str(ctx.exception).startswith("text_not_displayable:evidence[0].description"), str(ctx.exception))

    def test_layout_whitespace_and_non_latin_text_are_not_refused(self):
        base = fixture("03-fail-closed")["outcome"]
        for text in ("line one\nline two", "tab\tseparated", "crlf\r\nend", "Grüße — café", "日本語の説明", "عربي"):
            U.validate_explanation(U.build_explanation(dict(base, why=text), surface={"repository": "r", "surface_id": "s"}))

    def test_ordinary_words_near_secret_prefixes_are_not_refused(self):
        a = build("01-success-verified")
        for text in ("No Bearer credentials are shown here.", "task-runner ask-flow risk-score",
                     "The ghost_ ledger and akia notes", "xox is not a token"):
            b = json.loads(json.dumps(a))
            b["evidence"][0]["description"] = text
            U.validate_explanation(b)

    def test_validate_rejects_mutated_artifacts(self):
        a = build("01-success-verified")
        for mutate, code in (
            (lambda x: x["authority"].__setitem__("authority_effect", "EXECUTE"), "schema:const:$.authority.authority_effect"),
            (lambda x: x["sanitization"].__setitem__("secrets_present", True), "schema:const:$.sanitization.secrets_present"),
            (lambda x: x.__setitem__("extra", 1), "schema:additionalProperties:$.extra"),
            (lambda x: x["outcome"].__setitem__("disposition", "DENY"), "schema:const:$.authorization.authorized"),
            (lambda x: x["execution"].__setitem__("executed", True) or x["execution"].__setitem__("consequence_observation", "UNKNOWN"), "schema:const:$.execution.consequence_observation"),
            (lambda x: x["evidence"].append({"kind": "RECEIPT_REF", "ref": "ghp_" + "a" * 30, "description": "d", "sanitized": True}), "secret_material_present"),
            (lambda x: x["evidence"][0].__setitem__("description", "see token ghp_" + "a" * 36), "secret_material_present"),
            (lambda x: x["evidence"][0].__setitem__("description", "Authorization: Bearer " + "b" * 32), "secret_material_present"),
            (lambda x: x["evidence"][0].__setitem__("ref", "https://example.test/?t=github_pat_" + "c" * 40), "secret_material_present"),
            (lambda x: x["evidence"][0].__setitem__("description", "key AKIA" + "D" * 16 + " in log"), "secret_material_present"),
            (lambda x: x["evidence"][0].__setitem__("description", "slack xoxb-" + "1" * 24), "secret_material_present"),
            (lambda x: x["evidence"][0].__setitem__("description", "openai sk-" + "e" * 24), "secret_material_present"),
        ):
            b = json.loads(json.dumps(a))
            mutate(b)
            with self.assertRaises(U.ExplanationError) as ctx:
                U.validate_explanation(b)
            self.assertTrue(str(ctx.exception).startswith(code), str(ctx.exception))

    def test_cli_prose_and_fail_closed(self):
        f = next(p for p in FIXTURES if p.stem == "03-fail-closed")
        tmp = ROOT / "tests" / "_ufe_tmp_outcome.json"
        tmp.write_text(json.dumps(json.loads(f.read_text(encoding="utf-8"))["outcome"]), encoding="utf-8")
        try:
            out = subprocess.run([sys.executable, "scripts/user_facing_explanation.py", "--outcome", str(tmp), "--surface-repository", "StegVerse-Labs/Site", "--surface-id", "workspace", "--prose"], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertTrue(out.stdout.startswith("What happened:"))
            tmp.write_text(json.dumps({"disposition": "ALLOW", "predicate": "X", "requested_action": "a", "access_token": "t"}), encoding="utf-8")
            out = subprocess.run([sys.executable, "scripts/user_facing_explanation.py", "--outcome", str(tmp), "--surface-repository", "r", "--surface-id", "s"], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(out.returncode, 2)
            self.assertEqual(json.loads(out.stdout)["predicate"], "EXPLANATION_NOT_BUILDABLE")
        finally:
            tmp.unlink(missing_ok=True)


class VerifiedReceiptLocatorSchema(unittest.TestCase):
    """Schema-only consumers must not accept verified execution without a usable evidence locator."""

    def mutations(self):
        import copy
        valid = build("01-success-verified")
        out = {}
        for invalid_ref in (None, "", "   "):
            mutated = copy.deepcopy(valid)
            for entry in mutated["evidence"]:
                if entry["kind"] in ("RECEIPT_REF", "PROVENANCE_REF", "DIGEST"):
                    entry["ref"] = invalid_ref
            out[repr(invalid_ref)] = mutated
        return valid, out

    def test_verified_receipt_locator_is_required_by_schema_check(self):
        valid, mutations = self.mutations()
        U.schema_check(valid, SCHEMA)
        for name, mutated in mutations.items():
            with self.assertRaises(U.ExplanationError, msg=name):
                U.schema_check(mutated, SCHEMA)
            with self.assertRaises(U.ExplanationError, msg=name):
                U.validate_explanation(mutated)

    def test_verified_receipt_locator_is_required_by_jsonschema(self):
        from stdlib_json_schema import Validator  # stdlib, never skipped; jsonschema agreement runs in org CI
        validator = Validator(SCHEMA)
        valid, mutations = self.mutations()
        self.assertTrue(validator.is_valid(valid))
        for name, mutated in mutations.items():
            self.assertFalse(validator.is_valid(mutated), f"schema-only consumer accepted unusable receipt locator {name}")


class SchemaOnlyConsumers(unittest.TestCase):
    """Repair for .github#3106 review finding EXPLANATION_SCHEMA_CROSS_FIELD_CONSISTENCY: a consumer that
    validates only against the JSON Schema (no builder) must still be unable to accept an artifact whose
    fields contradict each other. Each mutation below is checked with the dependency-free schema_check
    and with the standard-library schema validator (scripts/stdlib_json_schema.py) as well."""

    def mutations(self):
        den = build("02-denied")
        suc = build("01-success-verified")
        fc = build("03-fail-closed")
        unk = build("05-unobserved-runtime")
        def m(base, fn):
            x = json.loads(json.dumps(base)); fn(x); return x
        return {
            "deny_verified_observed": m(den, lambda x: (x["execution"].__setitem__("execution_state", "VERIFIED"), x["execution"].__setitem__("consequence_observation", "OBSERVED"))),
            "deny_success_class": m(den, lambda x: x["outcome"].__setitem__("outcome_class", "SUCCESS_VERIFIED")),
            "deny_observation_observed": m(den, lambda x: x["outcome"].__setitem__("observation_state", "OBSERVED")),
            "deny_authorized_true": m(den, lambda x: x["authorization"].__setitem__("authorized", True)),
            "deny_execution_not_verified": m(den, lambda x: x["execution"].__setitem__("execution_state", "NOT_VERIFIED")),
            "authorized_not_verified_class": m(den, lambda x: x["outcome"].__setitem__("outcome_class", "AUTHORIZED_NOT_VERIFIED")),
            "deny_class_failed_closed": m(den, lambda x: x["outcome"].__setitem__("outcome_class", "FAILED_CLOSED")),
            "fail_closed_observation_unknown": m(fc, lambda x: x["outcome"].__setitem__("observation_state", "UNKNOWN")),
            "unknown_class_denied": m(unk, lambda x: x["outcome"].__setitem__("outcome_class", "DENIED")),
            "success_without_receipt_evidence": m(suc, lambda x: x.__setitem__("evidence", [{"kind": "SOURCE_REF", "ref": "x", "description": "d", "sanitized": True}])),
            "success_executed_false": m(suc, lambda x: x["execution"].__setitem__("executed", False)),
            "allow_not_executed_success_class": m(suc, lambda x: (x["execution"].__setitem__("executed", False), x["execution"].__setitem__("execution_state", "NOT_VERIFIED"), x["execution"].__setitem__("consequence_observation", "UNKNOWN"), x["outcome"].__setitem__("observation_state", "UNKNOWN"))),
            "allow_without_execution": m(suc, lambda x: (x["execution"].__setitem__("executed", False), x["execution"].__setitem__("execution_state", "NOT_EXECUTED"), x["execution"].__setitem__("consequence_observation", "NOT_AUTHENTICALLY_OBSERVED"), x["outcome"].__setitem__("observation_state", "NOT_AUTHENTICALLY_OBSERVED"))),
            "observation_state_mismatch": m(fc, lambda x: x["outcome"].__setitem__("observation_state", "UNKNOWN")),
            "non_allow_without_actionable": m(fc, lambda x: x["outcome"].__setitem__("actionable_disposition", None)),
            "non_allow_actionable_missing_field": m(den, lambda x: x["outcome"]["actionable_disposition"].pop("next_attempt")),
            "allow_with_actionable": m(suc, lambda x: x["outcome"].__setitem__("actionable_disposition", dict(fc["outcome"]["actionable_disposition"]))),
        }

    def test_schema_check_rejects_contradictory_artifacts(self):
        for name, inst in self.mutations().items():
            with self.assertRaises(U.ExplanationError, msg=name):
                U.schema_check(inst, SCHEMA)

    def test_jsonschema_rejects_contradictory_artifacts(self):
        from stdlib_json_schema import Validator  # stdlib, never skipped; jsonschema agreement runs in org CI
        validator = Validator(SCHEMA)
        for name, inst in self.mutations().items():
            self.assertFalse(validator.is_valid(inst), name)
        for p in FIXTURES:
            self.assertTrue(validator.is_valid(build(p.stem)), p.stem)

    def test_schema_check_and_jsonschema_agree_on_fixtures(self):
        for p in FIXTURES:
            U.schema_check(build(p.stem), SCHEMA)


if __name__ == "__main__":
    unittest.main()



class ReasonCatalogStandard(unittest.TestCase):
    """Compatibility requirement 7: one plain-language reason per returnable predicate."""

    GOOD = {"SNAPSHOT_SOURCE_NOT_AUTHENTICATED": "the snapshot was not observed through an authenticated session, the only accepted source"}

    def test_conforming_catalog_and_prefix_predicates(self):
        self.assertEqual(U.check_reason_catalog(self.GOOD, {"SNAPSHOT_SOURCE_NOT_AUTHENTICATED"}), [])
        self.assertEqual(U.check_reason_catalog({"field_missing": "a required field is missing from the record"}, ["field_missing:value_usd", "field_missing:asset"]), [])
        self.assertEqual(U.reason_key("CHECKPOINT_MALFORMED:digest"), "CHECKPOINT_MALFORMED")

    def test_violations_are_named(self):
        bad = {"A_B": "Because the SNAPSHOT_STATE check failed.", "ORPHAN": "short", "lower_case": "the reason mentions snapshot_digest_mismatch inside it"}
        out = U.check_reason_catalog(bad, {"A_B", "MISSING_ONE", "lower_case"})
        for code in ("predicate_without_reason:MISSING_ONE", "reason_without_returnable_predicate:ORPHAN", "reason_too_short_or_untrimmed:ORPHAN", "reason_must_start_lower_case:A_B", "reason_must_not_end_with_full_stop:A_B", "reason_restates_a_predicate:A_B", "reason_restates_a_predicate:lower_case"):
            self.assertIn(code, out)
        self.assertEqual(U.check_reason_catalog([], set()), ["reasons_not_a_mapping"])

    def test_reason_renders_as_the_why_of_a_conforming_artifact(self):
        reason = self.GOOD["SNAPSHOT_SOURCE_NOT_AUTHENTICATED"]
        record = {"disposition": "FAIL_CLOSED", "predicate": "SNAPSHOT_SOURCE_NOT_AUTHENTICATED", "requested_action": "Project the snapshot", "authority_source": "NONE", "why": reason,
                  "failure_code": "SNAPSHOT_SOURCE_NOT_AUTHENTICATED", "failed_predicate": "SNAPSHOT_SOURCE_NOT_AUTHENTICATED", "required_evidence_or_repair": "an authenticated snapshot source",
                  "retry_entrypoint": "the projection producer", "owning_existing_goal": "EXAMPLE-GOAL-001", "next_attempt": "project again from an authenticated source"}
        artifact = U.validate_explanation(U.build_explanation(record, surface={"repository": "StegVerse-Labs/example", "surface_id": "example"}))
        self.assertEqual(artifact["prose"]["why"], "Because " + reason + ".")
