from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from heartbeat_runtime.independent_oscillator import PROTOCOL_ANCHOR_UNIX_NS
from heartbeat_runtime.intr_derived_carrier import derive_intr_carrier_signal
from heartbeat_runtime.intr_subsignal_runtime import persist_local_intr_subsignal

ROOT = Path(__file__).resolve().parents[1]

CHAIN_SPEC = importlib.util.spec_from_file_location(
    "run_sv_dn1_first_round_chain",
    ROOT / "scripts/run_sv_dn1_first_round_chain.py",
)
assert CHAIN_SPEC and CHAIN_SPEC.loader
chain = importlib.util.module_from_spec(CHAIN_SPEC)
CHAIN_SPEC.loader.exec_module(chain)

CONSUMER_SPEC = importlib.util.spec_from_file_location(
    "consume_sv_dn1_resident_execution_request",
    ROOT / "scripts/consume_sv_dn1_resident_execution_request.py",
)
assert CONSUMER_SPEC and CONSUMER_SPEC.loader
consumer = importlib.util.module_from_spec(CONSUMER_SPEC)
CONSUMER_SPEC.loader.exec_module(consumer)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


class SvDn1SovereignExecutionChainTests(unittest.TestCase):
    def test_hosted_environment_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            with (
                mock.patch.object(chain, "refresh", return_value={"state": "PASS"}),
                self.assertRaisesRegex(RuntimeError, "hosted execution"),
            ):
                chain.execute_chain(base / "source", base / "runtime", env={"GITHUB_ACTIONS": "true"})

    def test_missing_carrier_is_handoff_ready_without_task_execution(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            runtime.mkdir()
            with mock.patch.object(chain, "refresh", return_value={"state": "PASS"}):
                result = chain.execute_chain(source, runtime, env={"HOME": str(base)})
            self.assertEqual(result["state"], "HANDOFF_READY")
            self.assertEqual(result["transition_id"], "SV_DN1_SOVEREIGN_CARRIER_REFERENCE_PENDING")
            self.assertEqual(result["completed_tasks"], [])
            self.assertEqual(result["next_task"], chain.TASKS[0])

    def test_clean_exec_env_strips_credentials_and_keeps_nonsecret_roots(self) -> None:
        env = {
            "HOME": "/tmp/home",
            "PATH": "/usr/bin",
            "GITHUB_TOKEN": "secret",
            "HF_TOKEN": "secret",
            "OPENAI_API_KEY": "secret",
            "STEGVERSE_SDK_SOURCE_ROOT": "/srv/sdk",
            "STEGVERSE_STEGCORE_SOURCE_ROOT": "/srv/stegcore",
            "STEGVERSE_SOURCE_MATERIALIZATION_ROOT": "/srv/source",
            "STEGVERSE_FORMALISM_TVC_SPOOL_ROOT": "/srv/tvc-spool",
            "STEGVERSE_SV_DN1_BROWSER_OBSERVATION_BUNDLE": "/srv/evidence/browser.json",
            "STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT": "/srv/state/source-prep",
        }
        clean = chain.clean_exec_env(env)
        self.assertNotIn("GITHUB_TOKEN", clean)
        self.assertNotIn("HF_TOKEN", clean)
        self.assertNotIn("OPENAI_API_KEY", clean)
        self.assertEqual(clean["STEGVERSE_SDK_SOURCE_ROOT"], "/srv/sdk")
        self.assertEqual(clean["STEGVERSE_STEGCORE_SOURCE_ROOT"], "/srv/stegcore")
        self.assertEqual(clean["STEGVERSE_SOURCE_MATERIALIZATION_ROOT"], "/srv/source")
        self.assertEqual(clean["STEGVERSE_FORMALISM_TVC_SPOOL_ROOT"], "/srv/tvc-spool")
        self.assertEqual(clean["STEGVERSE_SV_DN1_BROWSER_OBSERVATION_BUNDLE"], "/srv/evidence/browser.json")
        self.assertEqual(clean["STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT"], "/srv/state/source-prep")
        self.assertEqual(clean["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "TV/TVC")

    def test_receipt_validation_rejects_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            state = base / ".stegverse/state/sv-dn1-source-materialization/receipts/latest.json"
            write_json(state, {
                "state": "COMPLETE",
                "transition_id": "WRONG",
                "github_token_used": False,
                "repository_writeback_performed": False,
            })
            with mock.patch.object(chain.Path, "home", return_value=base):
                with self.assertRaisesRegex(RuntimeError, "durable receipt failed validation"):
                    chain.validate_durable_receipt("SV-DN1-SOURCE-MATERIALIZATION-001", {"HOME": str(base)})


    def test_intr_receipt_requires_shared_hb_signal_and_exact_carrier_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            intr_root = base / "intr"
            hb_root = base / "heartbeat"
            receipt_path = intr_root / "receipts/latest.json"
            main_receipt = {
                "receipt_hash": "sha256:" + "a" * 64,
                "state": "COMPLETE",
                "route_id": "SV-DN-1-HF-PUBLIC",
                "destination_validation": "PASS",
                "lineage_verified": True,
                "authority_effect": "NONE",
            }
            write_json(receipt_path, main_receipt)
            values = {
                "STEGVERSE_SV_DN1_INTR_STATE_ROOT": str(intr_root),
                "STEGVERSE_HEARTBEAT_ROOT": str(hb_root),
            }
            with self.assertRaisesRegex(RuntimeError, "carrier-binding.latest.json missing"):
                chain.validate_durable_receipt("SV-DN1-INTR-RUNTIME-001", values)

            signal = derive_intr_carrier_signal(
                packet_id="SV-DN1-INTR-TEST",
                payload_hash="sha256:" + "b" * 64,
                sampled_unix_ms=PROTOCOL_ANCHOR_UNIX_NS // 1_000_000 + 1234,
                packet_bytes=b'{"exchange":"exact"}',
                intr_transport_profile="stegverse.universal-intr.adjacent-hop/v1",
                boundary_from="EXTERNAL_SYSTEM",
                boundary_to="STEGOS_ECOSYSTEM",
                packet_receipt_hash="a" * 64,
            )
            shared = persist_local_intr_subsignal(root=hb_root, signal=signal)
            carrier = {
                "state": "COMPLETE",
                "transition_id": "SV_DN1_HB_INTR_CARRIER_BOUND",
                "intr_receipt_hash": main_receipt["receipt_hash"],
                "carrier_signal_id": signal["signal_id"],
                "carrier_binding_sha256": signal["carrier"]["carrier_binding_sha256"],
                "packet_sha256": signal["intr"]["packet_sha256"],
                "packet_recovery_verified": True,
                "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
                "heartbeat_grants_authority": False,
                "derived_carrier_grants_authority": False,
                "credential_authority": "TV/TVC",
                "authority_effect": "NONE_CARRIER_ONLY",
                "shared_hb_signal_ref": shared["signal_ref"],
                "shared_hb_signal_sha256": shared["signal_sha256"],
            }
            write_json(intr_root / "receipts/carrier-binding.latest.json", carrier)
            observed = chain.validate_durable_receipt("SV-DN1-INTR-RUNTIME-001", values)
            self.assertTrue(observed["shared_hb_signal_proof_verified"])
            self.assertEqual(observed["shared_hb_signal_ref"], shared["signal_ref"])

            carrier["shared_hb_signal_sha256"] = "0" * 64
            write_json(intr_root / "receipts/carrier-binding.latest.json", carrier)
            with self.assertRaisesRegex(RuntimeError, "shared HB signal digest mismatch"):
                chain.validate_durable_receipt("SV-DN1-INTR-RUNTIME-001", values)

    def test_source_prep_v2_receipt_is_accepted_and_legacy_shape_is_not_required(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            receipt_path = base / ".stegverse/state/sv-dn1-production-source-prep/receipts/latest.json"
            roots = {
                "stegverse.sdk": "/srv/sdk",
                "stegverse.stegcore": "/srv/stegcore",
                "stegverse.core-lite": "/srv/core-lite",
                "stegverse.master-records": "/srv/master-records",
            }
            write_json(receipt_path, {
                "schema": "stegverse.sv-dn1.production-source-prep-receipt/v2",
                "state": "COMPLETE",
                "transition_id": "SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE",
                "source_identity_scheme": "sha256-content-manifest",
                "migration_anchors_verified": True,
                "network_source_fetch_performed": False,
                "github_platform_required": False,
                "credential_used": False,
                "github_token_used": False,
                "repository_writeback_performed": False,
                "sdk_admitted": False,
                "source_roots": roots,
                "source_identities": {k: "sha256:" + (str(i + 1) * 64)[:64] for i, k in enumerate(roots)},
                "source_root_env": {
                    "STEGVERSE_SDK_SOURCE_ROOT": roots["stegverse.sdk"],
                    "STEGVERSE_STEGCORE_SOURCE_ROOT": roots["stegverse.stegcore"],
                    "STEGVERSE_CORE_LITE_SOURCE_ROOT": roots["stegverse.core-lite"],
                    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": roots["stegverse.master-records"],
                },
            })
            with mock.patch.object(chain.Path, "home", return_value=base):
                observed = chain.validate_durable_receipt("SV-DN1-PRODUCTION-SOURCE-PREP-001", {"HOME": str(base)})
            self.assertEqual(observed["receipt_path"], str(receipt_path))
            receipt = json.loads(receipt_path.read_text())
            self.assertNotIn("public_source_roots_verified", receipt)
            self.assertNotIn("private_source_roots_verified", receipt)

    def test_source_prep_v2_receipt_honors_relocated_state_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            relocated = base / "relocated-source-prep"
            receipt_path = relocated / "receipts/latest.json"
            roots = {
                "stegverse.sdk": "/srv/sdk",
                "stegverse.stegcore": "/srv/stegcore",
                "stegverse.core-lite": "/srv/core-lite",
                "stegverse.master-records": "/srv/master-records",
            }
            write_json(receipt_path, {
                "schema": "stegverse.sv-dn1.production-source-prep-receipt/v2",
                "state": "COMPLETE",
                "transition_id": "SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE",
                "source_identity_scheme": "sha256-content-manifest",
                "migration_anchors_verified": True,
                "network_source_fetch_performed": False,
                "github_platform_required": False,
                "credential_used": False,
                "github_token_used": False,
                "repository_writeback_performed": False,
                "sdk_admitted": False,
                "source_roots": roots,
                "source_identities": {k: "sha256:" + "b"*64 for k in roots},
                "source_root_env": {
                    "STEGVERSE_SDK_SOURCE_ROOT": roots["stegverse.sdk"],
                    "STEGVERSE_STEGCORE_SOURCE_ROOT": roots["stegverse.stegcore"],
                    "STEGVERSE_CORE_LITE_SOURCE_ROOT": roots["stegverse.core-lite"],
                    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": roots["stegverse.master-records"],
                },
            })
            observed = chain.validate_durable_receipt(
                "SV-DN1-PRODUCTION-SOURCE-PREP-001",
                {
                    "HOME": str(base),
                    "STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT": str(relocated),
                },
            )
            self.assertEqual(observed["receipt_path"], str(receipt_path))

    def test_source_prep_v2_receipt_rejects_root_locator_disagreement(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            receipt_path = base / ".stegverse/state/sv-dn1-production-source-prep/receipts/latest.json"
            roots = {
                "stegverse.sdk": "/srv/sdk",
                "stegverse.stegcore": "/srv/stegcore",
                "stegverse.core-lite": "/srv/core-lite",
                "stegverse.master-records": "/srv/master-records",
            }
            write_json(receipt_path, {
                "schema": "stegverse.sv-dn1.production-source-prep-receipt/v2",
                "state": "COMPLETE",
                "transition_id": "SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE",
                "source_identity_scheme": "sha256-content-manifest",
                "migration_anchors_verified": True,
                "network_source_fetch_performed": False,
                "github_platform_required": False,
                "credential_used": False,
                "github_token_used": False,
                "repository_writeback_performed": False,
                "sdk_admitted": False,
                "source_roots": roots,
                "source_identities": {k: "sha256:" + "a"*64 for k in roots},
                "source_root_env": {
                    "STEGVERSE_SDK_SOURCE_ROOT": "/wrong/sdk",
                    "STEGVERSE_STEGCORE_SOURCE_ROOT": roots["stegverse.stegcore"],
                    "STEGVERSE_CORE_LITE_SOURCE_ROOT": roots["stegverse.core-lite"],
                    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": roots["stegverse.master-records"],
                },
            })
            with mock.patch.object(chain.Path, "home", return_value=base):
                with self.assertRaisesRegex(RuntimeError, "disagrees"):
                    chain.validate_durable_receipt("SV-DN1-PRODUCTION-SOURCE-PREP-001", {"HOME": str(base)})

    def test_existing_active_task_stops_chain_without_reacquisition(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            (runtime / "control").mkdir(parents=True)
            write_json(runtime / chain.CARRIER_REL, {"schema": "stegverse.heartbeat-carrier-runtime-state/v1", "epoch": 31, "generation": 31})
            (runtime / chain.RUNNER_REL).parent.mkdir(parents=True, exist_ok=True)
            (runtime / chain.RUNNER_REL).write_text("# runner\n")
            write_json(runtime / chain.REGISTRY_REL, {
                "tasks": [{
                    "task_id": chain.TASKS[0],
                    "state": "ACTIVE",
                    "claim_id": "existing-claim",
                    "worker_id": "existing-worker",
                }]
            })
            with mock.patch.object(chain, "refresh", return_value={"state": "PASS"}):
                result = chain.execute_chain(source, runtime, env={"HOME": str(base)})
            self.assertEqual(result["state"], "HANDOFF_READY")
            self.assertEqual(result["transition_id"], "SV_DN1_EXISTING_TASK_LIFECYCLE_MUST_RESOLVE")
            self.assertEqual(result["claim_id"], "existing-claim")

    def test_simulated_sequence_advances_only_after_each_completed_registry_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            (runtime / "control").mkdir(parents=True)
            write_json(runtime / chain.CARRIER_REL, {"schema": "stegverse.heartbeat-carrier-runtime-state/v1", "epoch": 31, "generation": 31})
            (runtime / chain.RUNNER_REL).parent.mkdir(parents=True, exist_ok=True)
            (runtime / chain.RUNNER_REL).write_text("# runner\n")
            write_json(runtime / chain.REGISTRY_REL, {"tasks": []})

            seen: list[str] = []
            def runner(command, **kwargs):
                task_id = command[-1]
                seen.append(task_id)
                registry = json.loads((runtime / chain.REGISTRY_REL).read_text())
                registry["tasks"] = [
                    row for row in registry.get("tasks", []) if row.get("task_id") != task_id
                ] + [{"task_id": task_id, "state": "COMPLETED"}]
                write_json(runtime / chain.REGISTRY_REL, registry)
                return SimpleNamespace(returncode=0, stdout='{"workers_activated":1}\n', stderr="")

            def receipt(task_id, values):
                return {"task_id": task_id, "receipt_path": str(base / f"{task_id}.json")}

            with (
                mock.patch.object(chain, "refresh", return_value={"state": "PASS"}),
                mock.patch.object(chain, "validate_durable_receipt", side_effect=receipt),
                mock.patch.object(chain, "_load", wraps=chain._load),
            ):
                # The source step reads its receipt to forward source_root. Intercept
                # only that read with a real tiny receipt.
                source_receipt = base / "SV-DN1-SOURCE-MATERIALIZATION-001.json"
                write_json(source_receipt, {"source_root": str(base / "materialized-demo")})
                prep_receipt = base / "SV-DN1-PRODUCTION-SOURCE-PREP-001.json"
                write_json(prep_receipt, {
                    "source_root_env": {
                        "STEGVERSE_SDK_SOURCE_ROOT": str(base / "sdk"),
                        "STEGVERSE_STEGCORE_SOURCE_ROOT": str(base / "stegcore"),
                        "STEGVERSE_CORE_LITE_SOURCE_ROOT": str(base / "core-lite"),
                        "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": str(base / "master-records"),
                    }
                })
                def receipt_with_source(task_id, values):
                    if task_id == "SV-DN1-SOURCE-MATERIALIZATION-001":
                        return {"task_id": task_id, "receipt_path": str(source_receipt)}
                    if task_id == "SV-DN1-PRODUCTION-SOURCE-PREP-001":
                        return {"task_id": task_id, "receipt_path": str(prep_receipt)}
                    return {"task_id": task_id, "receipt_path": str(base / f"{task_id}.json")}
                with mock.patch.object(chain, "validate_durable_receipt", side_effect=receipt_with_source):
                    result = chain.execute_chain(source, runtime, runner=runner, env={"HOME": str(base)})

            self.assertEqual(result["state"], "COMPLETE")
            self.assertEqual(result["transition_id"], "SV_DN1_SOVEREIGN_FIRST_ROUND_CHAIN_COMPLETE")
            self.assertEqual(seen, list(chain.TASKS))
            self.assertEqual(result["completed_tasks"], list(chain.TASKS))

    def test_consumer_request_is_intent_only_and_retries_until_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            runtime = base / "runtime"
            source = base / "source"
            runtime.mkdir()
            source.mkdir()
            request = {
                "schema": "stegverse.resident-execution-request/v1",
                "request_id": "RESIDENT-EXEC-SV-DN1-FIRST-ROUND-001",
                "state": "REQUESTED",
                "task_id": consumer.TARGET_TASK,
                "mode": consumer.TARGET_MODE,
                "entrypoint": consumer.TARGET_ENTRYPOINT,
                "fresh_fence_minimum_exclusive": 22,
                "credential_authority": "TV/TVC",
                "github_token_required": False,
                "github_token_runtime_authority": "NONE",
                "heartbeat_grants_execution_authority": False,
                "second_machine_required": False,
                "network_source_fetch_allowed": False,
                "request_granted_authority": False,
                "authority_effect": "NONE_REQUEST_ONLY",
            }
            write_json(runtime / consumer.REQUEST_REL, request)
            entrypoint = runtime / consumer.TARGET_ENTRYPOINT
            entrypoint.parent.mkdir(parents=True, exist_ok=True)
            entrypoint.write_text("# chain\n")

            def waiting_runner(*args, **kwargs):
                return SimpleNamespace(
                    returncode=0,
                    stdout='{"state":"HANDOFF_READY","transition_id":"SV_DN1_CHAIN_STEP_NOT_TERMINAL"}\n',
                    stderr="",
                )

            first = consumer.consume(source, runtime, runner=waiting_runner, env={"HOME": str(base), "PATH": "/usr/bin"})
            self.assertEqual(first["state"], "ATTEMPT_RECORDED")
            self.assertFalse(first["request_granted_authority"])
            self.assertFalse(first["network_authority_granted_by_request"])
            self.assertFalse(consumer.previously_consumed(runtime, request, consumer.stable_hash(request)))

            def terminal_runner(*args, **kwargs):
                return SimpleNamespace(
                    returncode=0,
                    stdout='{"state":"COMPLETE","transition_id":"SV_DN1_SOVEREIGN_FIRST_ROUND_CHAIN_COMPLETE"}\n',
                    stderr="",
                )

            second = consumer.consume(source, runtime, runner=terminal_runner, env={"HOME": str(base), "PATH": "/usr/bin"})
            self.assertEqual(second["state"], "ATTEMPT_RECORDED")
            self.assertTrue(consumer.previously_consumed(runtime, request, consumer.stable_hash(request)))

    def test_consumer_rejects_hosted_environment(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "hosted environment"):
            consumer.clean_exec_env({"GITHUB_ACTIONS": "true"})


if __name__ == "__main__":
    unittest.main()
