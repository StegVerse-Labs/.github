"""Source composition only; fixtures never establish live provider evidence."""
import argparse
import copy
import json
import unittest

from scripts.compose_ecosystem_chat_task import compose, FIRST, SECOND
from scripts import materialize_reusable_task_construct as constructor


def specification(mode="single", providers=("chatgpt",)):
    return {
        "invocation_id": "offline-composition-fixture",
        "task_id": "EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001",
        "cosv_task_vector": "10100000103000",
        "request_hash": "a" * 64,
        "routing_mode": mode,
        "sources": [{"source_id": f"source-{i}", "provider": p,
                     "model": "explicit-fixture-model", "interaction_mode": "browser_session",
                     "operation_ref": "fixture:existing-owner-operation", "required": i == 0}
                    for i, p in enumerate(providers)],
    }


class ChatCompositionTests(unittest.TestCase):
    def test_all_provider_parameters_reuse_same_roundtrip_without_forced_adapter(self):
        spec = specification("parallel", ("chatgpt", "claude", "grok", "gemini", "other"))
        result = compose(spec)
        nodes = result["parameters"]["nodes"]
        operations = [n for n in nodes if n["node_id"].endswith("-operation")]
        self.assertEqual(len(operations), 5)
        self.assertEqual({n["manifest"]["reusable_task_id"] for n in operations}, {"RT-EPHEMERAL-LLM-ROUNDTRIP-001"})
        self.assertEqual([n["manifest"]["parameters"]["source"]["canonical_provider"] for n in operations], ["openai", "anthropic", "xai", "google", "other"])
        self.assertTrue(all("adapter_ref" not in n["manifest"]["parameters"]["source"] for n in operations))
        self.assertFalse(result["parameters"]["execution_available"])
        self.assertEqual(result["runner_plan"]["materialization_refs"], [])

    def test_fallback_and_cleanup_cover_failure_cancellation_and_skips(self):
        result = compose(specification("fallback", ("openai", "anthropic")))
        nodes = {n["node_id"]: n for n in result["parameters"]["nodes"]}
        self.assertEqual(nodes["source-1-lease"]["depends_on"], ["source-0-close"])
        self.assertIn("FALLBACK_ADMITTED", nodes["source-1-lease"]["run_condition"])
        self.assertTrue(nodes["source-0-close"]["all_terminal_paths"])
        self.assertIn("CANCELLATION", nodes["source-0-close"]["run_condition"])
        self.assertIn("SKIPPED", nodes["collect"]["run_condition"])
        seen = set()
        for node in nodes.values():
            self.assertTrue(set(node["depends_on"]) <= seen)
            seen.add(node["node_id"])

    def test_manifest_determinism_and_parameter_tamper_binding(self):
        spec = specification()
        one = compose(spec)
        self.assertEqual(one, compose(copy.deepcopy(spec)))
        spec["sources"][0]["model"] = "different-model"
        self.assertNotEqual(one["manifest_hash"], compose(spec)["manifest_hash"])
        for node in one["parameters"]["nodes"]:
            child = dict(node["manifest"])
            digest = child.pop("manifest_hash")
            self.assertEqual(digest, constructor.sha256_json(child))

    def test_adapter_only_when_translation_reason_is_declared(self):
        spec = specification()
        spec["sources"][0].update(interaction_mode="provider_api", adapter_ref="fixture:existing-adapter")
        with self.assertRaisesRegex(ValueError, "translation_reason"):
            compose(spec)
        spec["sources"][0]["translation_reason"] = "project provider-native wire fields"
        self.assertTrue(compose(spec)["parameters"]["source_only"])

    def test_missing_or_wrong_canonical_identity_cannot_be_materialized(self):
        spec = specification()
        spec["cosv_task_vector"] = "00000000000000"
        with self.assertRaisesRegex(SystemExit, "binding mismatch"):
            compose(spec)
        spec["task_id"] = FIRST
        with self.assertRaisesRegex(SystemExit, "binding mismatch"):
            compose(spec)

    def test_local_proposals_are_not_treated_as_registered_or_runtime(self):
        spec = specification("parallel", ("chatgpt", "claude"))
        spec["scenario"] = "local_collaboration"
        for source, participant in zip(spec["sources"], (FIRST, SECOND)):
            source.update(participant_task_id=participant, participant_cosv="00000000000000", interaction_mode="local_tool")
        with self.assertRaisesRegex(SystemExit, "binding mismatch"):
            compose(spec)

    def test_unsupported_modes_secrets_duplicate_sources_and_implicit_custody_rejected(self):
        for mode in ("sequential", "challenge", "unknown"):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                compose(specification(mode))
        for mutate in (
            lambda s: s["sources"][0].update(api_key="fixture-secret"),
            lambda s: s.update(custody_mode="immediate_master_records"),
            lambda s: s.update(request_hash="not-a-hash"),
            lambda s: s["sources"][0].update(interaction_mode="implicit"),
            lambda s: s["sources"][0].update(required="false"),
        ):
            spec = specification()
            mutate(spec)
            with self.assertRaises(ValueError):
                compose(spec)
        spec = specification("parallel", ("openai", "anthropic"))
        spec["sources"][1]["source_id"] = spec["sources"][0]["source_id"]
        with self.assertRaisesRegex(ValueError, "unique"):
            compose(spec)


class LocalAnswerDefinitionTests(unittest.TestCase):
    ID = "RT-ECOSYSTEM-CHAT-LOCAL-ANSWER-001"

    def definition(self):
        return constructor.resolve_reusable_task(constructor.load_registry(), self.ID)

    def test_local_answer_is_answer_only_without_runner_or_llm(self):
        d = self.definition()
        self.assertEqual(d["authority_effect"], "NONE_ANSWER_ONLY")
        self.assertEqual(d["runner_templates"], [])
        self.assertIn("NO_LLM_ROUNDTRIP_OR_MODEL_OUTPUT", d["completion_predicates"])
        self.assertIn("UNANSWERABLE_QUESTION_FAIL_CLOSED_SIX_FIELDS_NO_LLM_FALLBACK", d["failure_semantics"])
        self.assertEqual(d["non_allow_record_fields"], ["failure_code", "failed_predicate", "required_evidence_or_repair",
                                                        "retry_entrypoint", "owning_existing_goal", "next_attempt"])
        llm = {"RT-EPHEMERAL-LLM-ROUNDTRIP-001", "RT-STEGBROWSER-LLM-LEASE-001", "RT-ECOSYSTEM-CHAT-ANSWER-001"}
        self.assertFalse(llm & set(d["composes"]))

    def test_unresolved_dependencies_stay_out_of_composes_and_fail_closed(self):
        d = self.definition()
        ids = {t["reusable_task_id"] for t in constructor.load_registry()["tasks"]}
        self.assertTrue(set(d["composes"]) <= ids)
        for dep in d["dependency_refs"]:
            self.assertNotIn(dep.get("reusable_task_id"), ids)
            self.assertTrue(dep["failure_code"])
            self.assertIn(dep["state"], {"OWNER_GATED_PENDING_MERGE_FAIL_CLOSED", "OWNER_GATED_PENDING_LABS_PORT"})
            self.assertRegex(dep["source_ref"], r"^[\w.-]+/[\w.-]+#\d+@[0-9a-f]{40}:\S+\.py$")
            self.assertFalse(dep["vendored"])

    def test_local_answer_manifest_materializes_without_runner(self):
        manifest = constructor.build_manifest(argparse.Namespace(
            reusable_task_id=self.ID, invocation_id="offline-local-answer-fixture", task_id=None,
            cosv_task_vector=None, parameters_json=json.dumps({"request_hash": "b" * 64})))
        self.assertEqual(manifest["runner_plan"]["materialization_refs"], [])
        self.assertEqual(manifest["construct"]["gtg"]["authority_effect_from_reusable_definition"], "NONE_ANSWER_ONLY")
        self.assertFalse(manifest["construct"]["rtg"]["allow_authority"])


if __name__ == "__main__":
    unittest.main()
