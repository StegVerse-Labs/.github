from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_worker_runtime.py"

spec = importlib.util.spec_from_file_location("run_worker_runtime", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class FakeRuntime:
    def __init__(self, root: Path, *, on_acquire=None, authorized: bool = True):
        self.root = root
        self.registry_path = root / "control" / "worker-registry.json"
        self.locked = False
        self.lock_acquisitions = 0
        self.on_acquire = on_acquire
        self.authorized = authorized

    def _acquire(self):
        if self.locked:
            raise RuntimeError("fake worker lock already held")
        self.locked = True
        self.lock_acquisitions += 1
        if self.on_acquire is not None:
            self.on_acquire()

    def _release_lock(self):
        if not self.locked:
            raise RuntimeError("fake worker lock not held")
        self.locked = False

    def _load(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def _handoff(self, task):
        if task.get("task_id") != module.G18_TASK_ID:
            raise AssertionError("unexpected handoff lookup")
        return {"activation": {"executor_binding": "AUTHORIZED", "authorization_ref": "canonical-g18"}}

    def _execution_authorized(self, _handoff):
        return self.authorized


def seed_hb29(root: Path, *, claim_id: str = module.G18_CLAIM_ID, fence: int = module.G18_FENCE):
    (root / "control").mkdir(parents=True, exist_ok=True)
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "receipts" / "heartbeat-transition-continuity").mkdir(parents=True, exist_ok=True)
    (root / "control" / "heartbeat-state.json").write_text(
        json.dumps({"schema": "stegverse.org-heartbeat-state/v1", "epoch": 29, "generation": 29}),
        encoding="utf-8",
    )
    (root / "scripts" / "advance_heartbeat_transition.py").write_text("# canonical producer test stub\n", encoding="utf-8")
    (root / "control" / "worker-registry.json").write_text(
        json.dumps({
            "schema": "stegverse.heartbeat-worker-registry/v0.1",
            "generation": 23,
            "tasks": [
                {
                    "task_id": module.G18_TASK_ID,
                    "state": "BLOCKED",
                    "executor_binding": "BOUND",
                    "worker_id": module.G18_WORKER_ID,
                    "worker_instance_id": "sovereign-runtime-activation-worker-HB15-G18",
                    "claim_id": claim_id,
                    "authorized_policy_version": module.G18_POLICY,
                    "handoff_ref": "handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json",
                    "heartbeat_timing": {"fencing_token": fence},
                },
                {
                    "task_id": "UNRELATED-ACTIVE-WORKER",
                    "state": "ACTIVE",
                    "executor_binding": "BOUND",
                    "worker_id": "unrelated-worker",
                    "claim_id": "SHWP-UNRELATED-G99",
                    "authorized_policy_version": "other-policy",
                    "heartbeat_timing": {"fencing_token": 99},
                },
            ],
        }),
        encoding="utf-8",
    )


def successful_primary_runner(root: Path, captured_env: dict[str, str]):
    def fake_run(command, **kwargs):
        captured_env.update(kwargs.get("env") or {})
        if command[1].endswith("advance_heartbeat_transition.py"):
            (root / "control" / "heartbeat-carrier-runtime-state.json").write_text(
                json.dumps({"schema": "stegverse.heartbeat-carrier-runtime-state/v1", "epoch": 30, "generation": 30}),
                encoding="utf-8",
            )
            (root / "receipts" / "heartbeat-transition-continuity" / "latest.json").write_text(
                json.dumps({
                    "schema": "stegverse.heartbeat-state-transition-receipt/v1",
                    "state": "CARRIER_TRANSITION_COMPLETE",
                    "carrier_epoch_before": 29,
                    "carrier_epoch_after": 30,
                }),
                encoding="utf-8",
            )
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError("primary path must execute canonical transition producer first")
    return fake_run


class HB29WorkerBootstrapDeadlockTests(unittest.TestCase):
    def test_primary_path_requires_exact_g18_and_materializes_exact_hb30(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_hb29(root)
            runtime = FakeRuntime(root)
            captured_env: dict[str, str] = {}
            result = module.bootstrap_initial_carrier(
                root,
                runtime,
                env={
                    "HOME": str(root),
                    "PATH": "/usr/bin",
                    "GITHUB_TOKEN": "must-not-forward",
                    "GH_TOKEN": "must-not-forward",
                    "TVC_PRIVATE_SOURCE_READ_TOKEN": "must-not-forward",
                    "RENDER_API_KEY": "must-not-forward",
                },
                runner=successful_primary_runner(root, captured_env),
            )
            self.assertEqual(result["state"], "CARRIER_TRANSITION_COMPLETE")
            self.assertEqual(result["execution_provider"], "STEGVERSE_NATIVE")
            self.assertEqual(result["provider_role"], "PRIMARY")
            self.assertEqual(result["carrier_epoch"], 30)
            self.assertEqual(result["claim_id"], module.G18_CLAIM_ID)
            self.assertEqual(result["fencing_token"], 18)
            self.assertTrue(result["existing_g18_authority_reused"])
            self.assertFalse(result["new_claim_or_fence_created"])
            self.assertTrue(result["serialized_under_worker_runtime_lock"])
            self.assertNotIn("GITHUB_TOKEN", captured_env)
            self.assertNotIn("GH_TOKEN", captured_env)
            self.assertNotIn("TVC_PRIVATE_SOURCE_READ_TOKEN", captured_env)
            self.assertNotIn("RENDER_API_KEY", captured_env)
            self.assertFalse(runtime.locked)

    def test_existing_hb30_is_reused_under_lock_without_second_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "control").mkdir(parents=True)
            (root / "control" / "heartbeat-carrier-runtime-state.json").write_text(
                json.dumps({"schema": "stegverse.heartbeat-carrier-runtime-state/v1", "epoch": 30, "generation": 30}),
                encoding="utf-8",
            )
            runtime = FakeRuntime(root)
            result = module.bootstrap_initial_carrier(
                root,
                runtime,
                env={},
                runner=lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("must not run producer")),
            )
            self.assertEqual(result["state"], "CARRIER_ALREADY_PRESENT")
            self.assertEqual(runtime.lock_acquisitions, 1)
            self.assertFalse(runtime.locked)

    def test_concurrent_winner_is_rechecked_after_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_hb29(root)
            def materialize_on_acquire():
                (root / "control" / "heartbeat-carrier-runtime-state.json").write_text(
                    json.dumps({"schema": "stegverse.heartbeat-carrier-runtime-state/v1", "epoch": 30, "generation": 30}),
                    encoding="utf-8",
                )
            runtime = FakeRuntime(root, on_acquire=materialize_on_acquire)
            result = module.bootstrap_initial_carrier(
                root,
                runtime,
                env={},
                runner=lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("losing startup must not transition")),
            )
            self.assertEqual(result["state"], "CARRIER_ALREADY_PRESENT")
            self.assertFalse(runtime.locked)

    def test_missing_invalid_or_wrong_generation_hb29_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "control").mkdir(parents=True)
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "advance_heartbeat_transition.py").write_text("# stub\n", encoding="utf-8")
            runtime = FakeRuntime(root)
            with self.assertRaisesRegex(RuntimeError, "source is incomplete"):
                module.bootstrap_initial_carrier(root, runtime, env={})
            (root / "control" / "heartbeat-state.json").write_text(
                json.dumps({"schema": "stegverse.org-heartbeat-state/v1", "epoch": 29, "generation": 28}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "HB29/generation29"):
                module.bootstrap_initial_carrier(root, runtime, env={})
            self.assertFalse(runtime.locked)

    def test_g18_claim_or_handoff_mismatch_fails_before_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_hb29(root, claim_id="SHWP-WRONG-G18")
            runtime = FakeRuntime(root)
            with self.assertRaisesRegex(RuntimeError, "claim_id"):
                module.bootstrap_initial_carrier(root, runtime, env={}, runner=lambda *_a, **_k: None)
            self.assertFalse(runtime.locked)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_hb29(root)
            runtime = FakeRuntime(root, authorized=False)
            with self.assertRaisesRegex(RuntimeError, "execution-authorized G18"):
                module.bootstrap_initial_carrier(root, runtime, env={}, runner=lambda *_a, **_k: None)
            self.assertFalse(runtime.locked)

    def test_noninitial_successor_receipt_never_becomes_initial_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_hb29(root)
            runtime = FakeRuntime(root)
            def noninitial(*_args, **_kwargs):
                (root / "control" / "heartbeat-carrier-runtime-state.json").write_text(
                    json.dumps({"schema": "stegverse.heartbeat-carrier-runtime-state/v1", "epoch": 31, "generation": 31}),
                    encoding="utf-8",
                )
                (root / "receipts" / "heartbeat-transition-continuity" / "latest.json").write_text(
                    json.dumps({"state": "CARRIER_TRANSITION_COMPLETE", "carrier_epoch_before": 30, "carrier_epoch_after": 31}),
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            with self.assertRaisesRegex(RuntimeError, "failed closed"):
                module.bootstrap_initial_carrier(root, runtime, env={}, runner=noninitial)
            self.assertFalse(runtime.locked)

    def test_third_party_hosted_origin_is_fallback_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_hb29(root)
            runtime = FakeRuntime(root)
            calls: list[list[str]] = []
            def no_receipt_runner(command, **_kwargs):
                calls.append(command)
                return SimpleNamespace(returncode=1, stdout="", stderr="no portable receipt")
            with self.assertRaisesRegex(RuntimeError, "FALLBACK_ONLY"):
                module.bootstrap_initial_carrier(
                    root,
                    runtime,
                    env={"GITHUB_ACTIONS": "true", "HOME": str(root), "PATH": "/usr/bin"},
                    runner=no_receipt_runner,
                )
            self.assertFalse(any(command[1].endswith("advance_heartbeat_transition.py") for command in calls))
            self.assertFalse(runtime.locked)

    def test_local_portable_receipt_is_not_primary_when_native_producer_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_hb29(root)
            (root / "receipts" / "heartbeat-transition-continuity" / "iphone-portable-20260818.json").write_text(
                json.dumps({"executed_at": "2026-08-18T10:00:00Z"}), encoding="utf-8"
            )
            (root / "scripts" / "verify_iphone_heartbeat_transition_receipt.py").write_text("# verifier stub\n", encoding="utf-8")
            runtime = FakeRuntime(root)
            calls: list[list[str]] = []
            base_runner = successful_primary_runner(root, {})
            def runner(command, **kwargs):
                calls.append(command)
                return base_runner(command, **kwargs)
            result = module.bootstrap_initial_carrier(root, runtime, env={"HOME": str(root), "PATH": "/usr/bin"}, runner=runner)
            self.assertEqual(result["provider_role"], "PRIMARY")
            self.assertEqual(result["execution_provider"], "STEGVERSE_NATIVE")
            self.assertEqual(len(calls), 1)
            self.assertTrue(calls[0][1].endswith("advance_heartbeat_transition.py"))


if __name__ == "__main__":
    unittest.main()
