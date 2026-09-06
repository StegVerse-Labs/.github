from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from heartbeat_runtime.engine_v11 import HeartbeatRuntime as HeartbeatRuntimeV11

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers" / "sovereign_runtime_activation_worker.py"
RESOLVER = ROOT / "workers" / "sovereign_node_repository_resolution_worker.py"


class SovereignRuntimeActivationEscalationTests(unittest.TestCase):
    def invocation(self) -> dict:
        return {
            "schema": "stegverse.worker-invocation/v0.1",
            "heartbeat_epoch": 29,
            "task": {
                "task_id": "SHWP-DURABLE-RUNTIME-ACTIVATION",
                "claim_id": "SHWP-SHWP-DURABLE-RUNTIME-ACTIVATION-G18",
                "worker_id": "sovereign-runtime-activation-worker",
                "worker_instance_id": "sovereign-runtime-activation-worker-HB15-G18",
                "heartbeat_timing": {"fencing_token": 18},
            },
            "handoff": {"execution": {
                "required_capabilities": ["runtime_observation", "continuous_process_execution", "durable_state_reconstruction", "bounded_repository_mutation"],
                "allowed_paths": ["receipts/sovereign-runtime-activation/**", "receipts/heartbeat-transition-continuity/**"],
            }},
        }

    def resolver_invocation(self) -> dict:
        return {
            "schema": "stegverse.worker-invocation/v0.1", "heartbeat_epoch": 31,
            "task": {"task_id": "ESCALATE-SHWP-DURABLE-RUNTIME-ACTIVATION-test", "claim_id": "SHWP-ESCALATE-SHWP-DURABLE-RUNTIME-ACTIVATION-test-G21", "worker_id": "sovereign-node-repository-resolution-worker-v1", "worker_instance_id": "sovereign-node-repository-resolution-worker-v1-HB31-G21", "heartbeat_timing": {"fencing_token": 21}},
            "handoff": {"execution": {"required_capabilities": ["repository_resolution", "sandbox_validation"], "allowed_paths": ["receipts/sovereign-runtime-activation/**"]}},
            "scope": {"required_capabilities": ["repository_resolution", "sandbox_validation"], "allowed_paths": ["receipts/sovereign-runtime-activation/**"]},
        }

    def _materialize_worker_source(self, root: Path) -> None:
        source = ROOT / "workers" / "sovereign_runtime_activation_worker.py"
        target = root / "workers" / "sovereign_runtime_activation_worker.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())

    def test_missing_v13_bootstrap_emits_exact_sovereign_surface_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self._materialize_worker_source(root)
            env = {"PATH": os.environ.get("PATH", ""), "HOME": str(root / "home"), "XDG_STATE_HOME": str(root / "state")}
            completed = subprocess.run(
                [sys.executable, str(root / "workers" / "sovereign_runtime_activation_worker.py")],
                cwd=root,
                input=json.dumps(self.invocation()) + "\n",
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            response = json.loads(completed.stdout)
            self.assertEqual(response["state"], "BLOCKED")
            self.assertEqual(response["transition_id"], "SOVEREIGN_RUNTIME_ELIGIBLE_SURFACE_REQUIRED")
            self.assertEqual(
                response["expected_next_transition"],
                "RETRY_EXISTING_G18_NATIVE_THEN_SAME_HOST_EPHEMERAL_RECOVERY",
            )
            blocker = response["blocker"]
            self.assertEqual(blocker["dependency_class"], "PHYSICAL_RESOURCE_SOVEREIGN_NODE_ELIGIBILITY")
            self.assertFalse(blocker["physical_additional_machine_required"])
            self.assertFalse(blocker["always_on_external_host_required"])
            self.assertFalse(blocker["heartbeat_activation_blocked"])
            self.assertFalse(blocker["same_host_ephemeral_fallback_attempted"])
            self.assertEqual(
                blocker["same_host_ephemeral_fallback_reason"],
                "CANONICAL_BOOTSTRAP_SOURCE_REQUIRED_FIRST",
            )
            self.assertNotIn("GITHUB_TOKEN", completed.stdout)

    def test_hosted_environment_is_not_used_as_sovereign_runtime_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self._materialize_worker_source(root)
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": str(root / "home"),
                "XDG_STATE_HOME": str(root / "state"),
                "GITHUB_ACTIONS": "true",
            }
            completed = subprocess.run(
                [sys.executable, str(root / "workers" / "sovereign_runtime_activation_worker.py")],
                cwd=root,
                input=json.dumps(self.invocation()) + "\n",
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            response = json.loads(completed.stdout)
            self.assertEqual(response["state"], "BLOCKED")
            receipt = json.loads(
                (root / "receipts" / "sovereign-runtime-activation" / "SHWP-DURABLE-RUNTIME-ACTIVATION.json").read_text()
            )
            self.assertFalse(receipt["bootstrap_attempt"]["attempted"])
            self.assertEqual(
                receipt["bootstrap_attempt"]["reason"],
                "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_RUNTIME_EVIDENCE",
            )
            self.assertFalse(receipt["bootstrap_attempt"]["same_host_ephemeral_fallback"]["attempted"])
            self.assertEqual(receipt["canonical_carrier_runtime"], "heartbeat_runtime.engine_v13.HeartbeatRuntime")
            self.assertFalse(receipt["heartbeat_dependency"])
            self.assertFalse(receipt["third_party_runtime_required"])
            self.assertFalse(receipt["physical_additional_machine_required"])

    def test_carrier_remains_release_priority_and_current_downstream_is_governed(self) -> None:
        from heartbeat_runtime.engine_v2 import HeartbeatRuntime as HeartbeatRuntimeV2
        handoff = json.loads((ROOT / "handoffs" / "SHWP-DURABLE-RUNTIME-ACTIVATION.json").read_text())
        self.assertEqual(handoff["task"]["priority"], "release")
        self.assertLess(HeartbeatRuntimeV2.PRIORITY["release"], HeartbeatRuntimeV2.PRIORITY["critical"])
        self.assertEqual(handoff["authority"]["credential_authority"], "TV/TVC")
        self.assertEqual(handoff["authority"]["github_token_production_authority"], "NONE")
        downstream = " ".join(handoff["release_downstream"])
        self.assertIn("HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009", downstream)
        self.assertIn("RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28", downstream)
        self.assertIn("SHWP-ECOSYSTEM-CHAT-INFERENCE-001", downstream)
        self.assertEqual(handoff["constraint"]["operational_state"], "SUPERSEDED_AS_DOWNSTREAM_BLOCKER")
        self.assertEqual(handoff["constraint"]["class"], "STALE_REGISTRY_PROJECTION_ONLY")
        self.assertEqual(handoff["constraint"]["condition"], "G18_FENCE18_STILL_PROJECTED_BUT_MAY_NOT_GATE_RELEASE_OR_DOWNSTREAM_EXECUTION")
        self.assertFalse(handoff["constraint"]["solution_required"])
        self.assertFalse(handoff["constraint"]["downstream_execution_blocked"])
        self.assertEqual(handoff["completion"]["resident_request_resolution_task_id"], "RESOLVE-G18-RESIDENT-REQUEST-CONSUMPTION-001")
        self.assertFalse(handoff["completion"]["resident_request_resolution_runtime_observed"])
        self.assertFalse(handoff["constraint"]["heartbeat_activation_blocked"])

    def test_g18_adapter_passes_only_nonsecret_runtime_environment(self) -> None:
        adapters = json.loads((ROOT / "control" / "process-worker-adapters.json").read_text())
        adapter = next(row for row in adapters["adapters"] if row["adapter_ref"] == "process:sovereign-runtime-activation-v1")
        allowlist = set(adapter["env_allowlist"])
        self.assertIn("STEGVERSE_HEARTBEAT_ROOT", allowlist)
        for name in ("GITHUB_TOKEN", "GH_TOKEN", "ZEROEX_API_KEY", "WALLET_PRIVATE_KEY", "TVC_TOKEN"):
            self.assertNotIn(name, allowlist)


    def test_v13_resolver_adapter_allows_local_source_and_state_overrides_without_credentials(self) -> None:
        adapters = json.loads((ROOT / "control" / "process-worker-adapters.json").read_text())
        adapter = next(row for row in adapters["adapters"] if row["adapter_ref"] == "process:sovereign-node-repository-resolution-v1")
        allowlist = set(adapter["env_allowlist"])
        self.assertIn("STEGVERSE_HEARTBEAT_SOURCE_ROOT", allowlist)
        self.assertIn("STEGVERSE_HEARTBEAT_ROOT", allowlist)
        for name in ("GITHUB_TOKEN", "GH_TOKEN", "ZEROEX_API_KEY", "WALLET_PRIVATE_KEY", "TVC_TOKEN"):
            self.assertNotIn(name, allowlist)
        notes = " ".join(adapter["notes"])
        self.assertIn("derive the existing v0.4 declaration", notes)
        self.assertNotIn("may not manufacture a node declaration", notes)

    def test_g18_handoff_records_merged_v13_execution_repair_not_candidate(self) -> None:
        handoff = json.loads((ROOT / "handoffs" / "SHWP-DURABLE-RUNTIME-ACTIVATION.json").read_text())
        repairs = handoff["released_repairs"]
        self.assertNotIn("g18_v13_runtime_execution_candidate", repairs)
        merged = repairs["g18_v13_runtime_execution"]
        self.assertEqual(merged["pull_request"], 344)
        self.assertEqual(merged["merge_commit"], "72e9315e557fdcc6e9d5c94c370993da6a2f7f88")
        self.assertEqual(set(merged["validation_runs"]), {33138207869, 33138207844})
        self.assertEqual(merged["runtime_effect"], "SOURCE_ONLY_NO_SOVEREIGN_RUNTIME_RECEIPT_CLAIM")

    def test_v11_resolution_successor_inherits_release_priority_from_legacy_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "handoffs").mkdir(parents=True)
            parent_handoff = {
                "schema": "stegverse.executable-handoff/v0.1",
                "state": "BLOCKED",
                "goal": {"goal_id": "SHWP-DURABLE-RUNTIME-ACTIVATION", "authority_ceiling": [], "successor_policy": "INHERIT_OR_NARROW", "max_successor_depth": 4},
                "task": {"task_id": "SHWP-DURABLE-RUNTIME-ACTIVATION", "repository": "StegVerse-Labs/.github", "canonical_owner_ref": "StegVerse-Labs/.github#12", "derivation_depth": 0, "priority": "release"},
                "authority": {"authority_source": "test", "policy_version": "test"},
                "execution": {"required_capabilities": [], "allowed_paths": [], "allowed_services": [], "max_actions": 3, "max_retries": 3, "external_cost_ceiling_usd": 0, "runtime_window_beats": 32},
                "continuity": {"checkpoint_ref": "checkpoints/parent.json"},
            }
            (root / "handoffs" / "parent.json").write_text(json.dumps(parent_handoff), encoding="utf-8")
            parent = {"task_id": "SHWP-DURABLE-RUNTIME-ACTIVATION", "goal_id": parent_handoff["goal"]["goal_id"], "state": "BLOCKED", "handoff_ref": "handoffs/parent.json", "executor_binding": "BOUND", "worker_id": None, "worker_instance_id": None, "claim_id": None, "heartbeat_timing": None, "last_checkpoint_ref": "checkpoints/parent.json", "archive_eligible": False, "archive_reason_codes": [], "evidence_refs": []}
            registry = {"generation": 18, "workers": [], "tasks": [parent]}
            contract = {"trigger_type": "CONDITIONAL_CONSTRAINT", "dependency_class": "EXECUTION_OPPORTUNITY", "problem_statement": "Bounded successor transition could not execute on this opportunity.", "solution_required": True, "workaround_candidates": ["retry bounded transition"], "next_solution_action": "execute bounded transition", "resolvable_by_current_worker": False, "escalation_target": "SOVEREIGN_RUNTIME_OWNER", "required_capabilities": ["repository_resolution", "sandbox_validation"], "completion_evidence": ["successor evidence"]}
            runtime = HeartbeatRuntimeV11(root); events: list[dict] = []
            task_id = runtime._admit_resolution_task(registry, parent, 30, events, "resolution-contract:test", contract)
            generated = json.loads((root / "handoffs" / "generated" / f"{task_id}.json").read_text())
            self.assertEqual(generated["task"]["priority"], "release")
            self.assertTrue(any(event.get("event_type") == "resolution_priority_inherited" for event in events))

    def test_repository_resolution_worker_is_uniquely_profile_eligible(self) -> None:
        fragment = json.loads((ROOT / "control" / "worker-registry.d" / "sovereign-node-repository-resolution-v1.json").read_text())
        worker_row = fragment["workers"][0]
        self.assertEqual(worker_row["capabilities"], ["repository_resolution", "sandbox_validation"])
        profiles = json.loads((ROOT / "control" / "worker-capability-profiles.json").read_text())
        profile = next(row for row in profiles["profiles"] if row["profile_id"] == "sovereign-resolution-worker-v1")
        self.assertEqual(set(profile["allowed_capabilities"]), {"repository_resolution", "sandbox_validation"})
        adapters = json.loads((ROOT / "control" / "process-worker-adapters.json").read_text())
        matching = [row for row in adapters["adapters"] if set(row.get("capabilities") or []) == {"repository_resolution", "sandbox_validation"} and row.get("enabled") is True]
        self.assertEqual([row["adapter_ref"] for row in matching], ["process:sovereign-node-repository-resolution-v1"])

    def test_repository_resolver_escalates_without_node_and_completes_with_authorized_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); base_env = {"PATH": os.environ.get("PATH", ""), "HOME": str(root / "home"), "XDG_STATE_HOME": str(root / "state")}
            blocked = subprocess.run([sys.executable, str(RESOLVER)], cwd=tmp, input=json.dumps(self.resolver_invocation()) + "\n", text=True, capture_output=True, env=base_env, check=False)
            self.assertEqual(blocked.returncode, 0, blocked.stderr)
            blocked_response = json.loads(blocked.stdout)
            self.assertEqual(blocked_response["state"], "BLOCKED")
            self.assertEqual(blocked_response["blocker"]["escalation_target"], "COMPONENT_AUTHORITY")
            declared_env = dict(base_env); declared_env["STEGVERSE_SOVEREIGN_NODE"] = "1"
            completed = subprocess.run([sys.executable, str(RESOLVER)], cwd=tmp, input=json.dumps(self.resolver_invocation()) + "\n", text=True, capture_output=True, env=declared_env, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["transition_id"], "SOVEREIGN_NODE_DECLARATION_RESOLVED")


if __name__ == "__main__":
    unittest.main()
