"""Source composition only; fixtures never establish live provider evidence."""
import copy
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
        with self.assertRaisesRegex(SystemExit, "resolve exactly once"):
            compose(spec)

    def test_local_proposals_are_not_treated_as_registered_or_runtime(self):
        spec = specification("parallel", ("chatgpt", "claude"))
        spec["scenario"] = "local_collaboration"
        for source, participant in zip(spec["sources"], (FIRST, SECOND)):
            source.update(participant_task_id=participant, participant_cosv="00000000000000", interaction_mode="local_tool")
        with self.assertRaisesRegex(SystemExit, "resolve exactly once"):
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


if __name__ == "__main__":
    unittest.main()
