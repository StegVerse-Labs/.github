from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_independent_ecosystem_chat_parent.py"
spec = importlib.util.spec_from_file_location("independent_ecosystem_chat_parent", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class IndependentEcosystemChatParentExecutorTests(unittest.TestCase):
    def load(self, relative: Path | str) -> dict:
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_current_registration_and_authorization_are_claimable(self) -> None:
        mod.validate_registered_executor(ROOT)
        auth = self.load(mod.AUTH_PATH)
        self.assertEqual(auth["authority_domain"], "INDEPENDENT_TASK_CONTROL")
        self.assertEqual(auth["minimum_fencing_token_exclusive"], 24)
        self.assertFalse(auth["heartbeat_required_for_admission"])
        self.assertFalse(auth["heartbeat_grants_execution_authority"])
        self.assertFalse(auth["g18_terminalization_required"])
        self.assertFalse(auth["recovery_reacquisition_allowed"])
        self.assertFalse(auth["github_token_required"])
        self.assertFalse(auth["render_required"])

    def test_fresh_parent_claim_is_strictly_greater_than_terminal_g22_and_registry_floor(self) -> None:
        registry = copy.deepcopy(self.load(mod.REGISTRY_PATH))
        fragment = self.load(mod.FRAGMENT_PATH)
        existing_max = mod.max_projected_fence(registry)

        task, fence = mod.acquire_parent_claim(registry, fragment, reference_epoch=0)

        self.assertGreater(fence, 24)
        self.assertGreater(fence, existing_max)
        self.assertEqual(registry["generation"], fence)
        self.assertEqual(task["state"], "ACTIVE")
        self.assertEqual(task["executor_binding"], "BOUND")
        self.assertEqual(task["worker_id"], mod.WORKER_ID)
        self.assertTrue(task["claim_id"].endswith(f"-G{fence}"))
        self.assertEqual(task["heartbeat_timing"]["fencing_token"], fence)
        self.assertEqual(task["heartbeat_timing"]["start_epoch"], 0)
        self.assertTrue(task["independent_task_control"]["heartbeat_reference_only"])
        self.assertFalse(task["independent_task_control"]["heartbeat_granted_authority"])
        self.assertFalse(task["independent_task_control"]["g18_authority_used"])
        self.assertFalse(task["independent_task_control"]["g20_authority_reused"])
        self.assertFalse(task["independent_task_control"]["g22_recovery_authority_reused"])
        self.assertFalse(task["independent_task_control"]["recovery_reacquired"])

    def test_current_or_newer_parent_claim_blocks_duplicate_acquisition(self) -> None:
        registry = copy.deepcopy(self.load(mod.REGISTRY_PATH))
        fragment = self.load(mod.FRAGMENT_PATH)
        current = mod.task_by_id(registry, mod.TASK_ID)
        self.assertIsNotNone(current)
        assert current is not None
        current.update(
            {
                "state": "ACTIVE",
                "claim_id": "SHWP-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-G27",
                "worker_id": mod.WORKER_ID,
                "worker_instance_id": f"{mod.WORKER_ID}-REF0-G27",
                "executor_binding": "BOUND",
                "heartbeat_timing": {"fencing_token": 27, "expected_next_transition": "TVC_LOCAL_MODEL_ROUTE_ADMISSION"},
            }
        )
        with self.assertRaisesRegex(RuntimeError, "current or newer parent claim"):
            mod.acquire_parent_claim(registry, fragment, reference_epoch=0)

    def test_nonterminal_attempt_releases_claim_for_fresh_retry(self) -> None:
        registry = copy.deepcopy(self.load(mod.REGISTRY_PATH))
        fragment = self.load(mod.FRAGMENT_PATH)
        task, fence = mod.acquire_parent_claim(registry, fragment, reference_epoch=0)
        claim = task["claim_id"]

        released = mod.release_parent_claim(
            registry,
            response_state="HANDOFF_READY",
            transition_id="TVC_LOCAL_ROUTE_CAPSULE_NOT_MATERIALIZED",
            evidence_refs=[str(mod.BASE_RECEIPT)],
        )

        self.assertEqual(released["state"], "HANDOFF_READY")
        self.assertEqual(released["executor_binding"], "AUTHORIZED")
        self.assertIsNone(released["claim_id"])
        self.assertIsNone(released["worker_id"])
        self.assertIsNone(released["worker_instance_id"])
        self.assertIsNone(released["heartbeat_timing"])
        self.assertEqual(released["independent_task_control"]["last_released_claim_id"], claim)
        self.assertEqual(released["independent_task_control"]["last_released_fencing_token"], fence)
        self.assertFalse(released["independent_task_control"]["terminal_verified"])

    def test_completion_cannot_be_claimed_without_terminal_verification(self) -> None:
        registry = copy.deepcopy(self.load(mod.REGISTRY_PATH))
        fragment = self.load(mod.FRAGMENT_PATH)
        mod.acquire_parent_claim(registry, fragment, reference_epoch=0)
        with self.assertRaisesRegex(RuntimeError, "completion requires independently verified terminal evidence"):
            mod.release_parent_claim(
                registry,
                response_state="COMPLETED",
                transition_id="MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTED",
                evidence_refs=[],
                terminal_verified=False,
            )

    def test_verified_completion_releases_parent_authority_terminally(self) -> None:
        registry = copy.deepcopy(self.load(mod.REGISTRY_PATH))
        fragment = self.load(mod.FRAGMENT_PATH)
        mod.acquire_parent_claim(registry, fragment, reference_epoch=0)
        released = mod.release_parent_claim(
            registry,
            response_state="COMPLETED",
            transition_id="MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTED",
            evidence_refs=[str(mod.ACTIVATION_RECEIPT)],
            terminal_verified=True,
        )
        self.assertEqual(released["state"], "COMPLETED")
        self.assertEqual(released["executor_binding"], "UNBOUND")
        self.assertTrue(released["archive_eligible"])
        self.assertIsNone(released["claim_id"])
        self.assertIsNone(released["worker_id"])
        self.assertTrue(released["independent_task_control"]["terminal_verified"])

    def test_scope_denial_releases_claim_before_error_propagation(self) -> None:
        registry = copy.deepcopy(self.load(mod.REGISTRY_PATH))
        fragment = self.load(mod.FRAGMENT_PATH)
        claimed, fence = mod.acquire_parent_claim(registry, fragment, reference_epoch=0)
        claim_id = claimed["claim_id"]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "control").mkdir(parents=True)
            registry_path = root / mod.REGISTRY_PATH
            registry_path.write_text(json.dumps(registry) + "\n", encoding="utf-8")
            (root / "protected-source.txt").write_text("before", encoding="utf-8")
            before = mod.snapshot_protected_tree(root)
            (root / "protected-source.txt").write_text("after", encoding="utf-8")

            scope_error = mod.release_attempt_guarded(
                root,
                registry_path=registry_path,
                before=before,
                response_state="COMPLETED",
                transition_id="MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTED",
                evidence_refs=[],
                terminal_verified=True,
            )

            self.assertIsInstance(scope_error, RuntimeError)
            released_registry = json.loads(registry_path.read_text(encoding="utf-8"))
            released = mod.task_by_id(released_registry, mod.TASK_ID)
            self.assertIsNotNone(released)
            assert released is not None
            self.assertEqual(released["state"], "HANDOFF_READY")
            self.assertEqual(released["executor_binding"], "AUTHORIZED")
            self.assertIsNone(released["claim_id"])
            self.assertIsNone(released["worker_id"])
            self.assertEqual(released["independent_task_control"]["last_released_claim_id"], claim_id)
            self.assertEqual(released["independent_task_control"]["last_released_fencing_token"], fence)
            self.assertFalse(released["independent_task_control"]["terminal_verified"])
            self.assertEqual(released["transition_history"][-1]["transition_id"], "OUT_OF_SCOPE_MUTATION_DENIED")

    def test_clean_environment_forwards_only_nonsecret_locators_and_no_hosted_markers(self) -> None:
        source = {
            "PATH": "/bin",
            "HOME": "/home/stegverse",
            "LANG": "C.UTF-8",
            "STEGVERSE_MICRO_NODE_RUNTIME_ROOT": "/srv/stegverse/micro-node-runtime",
            "STEGVERSE_TVC_ROOT": "/srv/stegverse/TVC",
            "STEGVERSE_LLM_ADAPTER_ROOT": "/srv/stegverse/LLM-adapter",
            "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT": "/srv/stegverse/master-records/orchestration",
            "GITHUB_TOKEN": "forbidden",
            "GH_TOKEN": "forbidden",
            "GITHUB_ACTIONS": "true",
            "RENDER": "true",
            "CLOUDFLARE_API_TOKEN": "forbidden",
            "UNRELATED_SECRET": "forbidden",
        }
        env = mod.clean_exec_env(source)
        self.assertEqual(env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "TV/TVC")
        self.assertEqual(env["STEGVERSE_LOCAL_MODEL_CREDENTIAL_REQUIREMENT"], "NONE")
        for name in mod.FORBIDDEN_AUTH_ENV | mod.HOSTED_MARKERS:
            self.assertNotIn(name, env)
        self.assertNotIn("UNRELATED_SECRET", env)
        for name in mod.NONSECRET_LOCATORS:
            self.assertIn(name, env)

    def test_protected_tree_ignores_only_admitted_registry_and_receipt_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "control").mkdir(parents=True)
            (root / mod.RECEIPT_ROOT).mkdir(parents=True)
            (root / "source.txt").write_text("A", encoding="utf-8")
            (root / mod.REGISTRY_PATH).write_text("{}\n", encoding="utf-8")
            (root / mod.BASE_RECEIPT).write_text("{}\n", encoding="utf-8")
            before = mod.snapshot_protected_tree(root)
            (root / mod.REGISTRY_PATH).write_text('{"generation": 23}\n', encoding="utf-8")
            (root / mod.BASE_RECEIPT).write_text('{"state": "ACTIVE"}\n', encoding="utf-8")
            after_allowed = mod.snapshot_protected_tree(root)
            mod.assert_protected_tree_unchanged(before, after_allowed)
            (root / "source.txt").write_text("B", encoding="utf-8")
            after_forbidden = mod.snapshot_protected_tree(root)
            with self.assertRaisesRegex(RuntimeError, "out-of-scope repository paths"):
                mod.assert_protected_tree_unchanged(before, after_forbidden)

    def test_terminal_finalization_requires_exact_chain_and_persistent_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / mod.RECEIPT_ROOT).mkdir(parents=True)
            proof_path = root / mod.RECEIPT_ROOT / "proof.json"
            proof = {
                "predicates": {
                    "real_model_process_observed": True,
                    "private_endpoint_only": True,
                }
            }
            route = {"receipt_hash": "route-hash"}
            execution = {
                "state": "EXECUTED",
                "measured_usage": {"input_tokens": 1, "output_tokens": 1},
                "provider_usage_event": {"event_sha256": "usage-hash"},
            }
            base = {
                "local_model_proof_path": str(proof_path),
                "live_model_endpoint": "http://127.0.0.1:7777",
            }
            proof_path.write_text(json.dumps(proof), encoding="utf-8")
            (root / mod.BASE_RECEIPT).write_text(json.dumps(base), encoding="utf-8")
            (root / mod.ROUTE_RECEIPT).write_text(json.dumps(route), encoding="utf-8")
            (root / mod.LLM_EXECUTION_RECEIPT).write_text(json.dumps(execution), encoding="utf-8")
            reconstruction = {
                "provider_usage_reconstruction_pass": True,
                "transition_reconstruction_pass": True,
                "same_execution": True,
                "reconstruction_receipt_hash": "mr-hash",
            }
            reconstruction_result = {
                "state": "COMPLETE",
                "reconstruction_receipt": reconstruction,
                "va_conversational_runtime": {"state": "COMPLETE"},
            }
            task = {
                "claim_id": "SHWP-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-G23",
                "heartbeat_timing": {"fencing_token": 23},
            }
            with mock.patch.object(mod, "route_receipt_verified", return_value=True), \
                 mock.patch.object(mod, "execution_receipt_verified", return_value=True), \
                 mock.patch.object(mod, "find_master_records_root", return_value=root), \
                 mock.patch.object(mod, "reconstruct_same_execution", return_value=reconstruction_result), \
                 mock.patch.object(mod, "reconstruction_receipt_verified", return_value=True):
                terminal, activation = mod.finalize_same_execution(root, task, 0)
            self.assertTrue(terminal)
            self.assertEqual(activation["state"], "PASS")
            self.assertTrue(activation["same_execution"])
            self.assertTrue(activation["persistent_conversational_runtime_ready"])
            saved = json.loads((root / mod.BASE_RECEIPT).read_text(encoding="utf-8"))
            self.assertTrue(saved["completed"])
            self.assertEqual(saved["transition_id"], "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTED")
            self.assertFalse(saved["github_token_required"])
            self.assertFalse(saved["third_party_inference_required"])

    def test_source_does_not_use_process_adapter_sandbox_or_recovery_authority(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("ProcessWorkerAdapter", source)
        self.assertNotIn("run_independent_orphan_recovery", source)
        self.assertIn("clean_exec_env", source)
        self.assertIn("release_attempt_guarded", source)
        self.assertIn("reconstruct_same_execution", source)
        self.assertIn("minimum_fencing_token_exclusive", (ROOT / mod.AUTH_PATH).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
