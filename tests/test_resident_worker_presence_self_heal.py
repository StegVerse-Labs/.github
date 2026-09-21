from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import install_sovereign_heartbeat_service as service
from scripts import repair_resident_worker_presence as repair
from scripts import run_heartbeat_runtime as carrier


class ResidentWorkerPresenceSelfHealTests(unittest.TestCase):
    def test_carrier_supervision_interval_is_hb_scale_and_non_authorizing(self):
        self.assertEqual(carrier.WORKER_SUPERVISION_INTERVAL_REFERENCES, 100)
        source = Path(carrier.__file__).read_text(encoding="utf-8")
        self.assertIn("ensure_worker_presence", source)
        self.assertIn("resident_worker_presence", source)
        self.assertIn("The pulse already exists before this check", source)

    def test_new_hb_au_subsignal_requests_existing_worker_presence_supervision(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            event_path = root / carrier.DERIVED_SUBSIGNAL_EVENT_LOG_REL
            event_path.parent.mkdir(parents=True, exist_ok=True)
            event_path.write_text("", encoding="utf-8")
            baseline = carrier._subsignal_activity_snapshot(root)
            event_path.write_text('{"event":"HB_DERIVED_INTR_SUBSIGNAL_PROPAGATED_LOCAL"}\n', encoding="utf-8")
            expected = {
                "state": "WORKER_ALREADY_PRESENT",
                "heartbeat_grants_execution_authority": False,
                "worker_coordinator_retains_admission_authority": True,
                "authority_effect": "NONE_SUPERVISION_ONLY",
            }
            supervisor = mock.Mock(return_value=expected)
            current, result = carrier._observe_hb_subsignal_worker_presence(
                root,
                previous_snapshot=baseline,
                carrier_pid=111,
                interval_ms=10.0,
                supervisor=supervisor,
            )
            self.assertNotEqual(current, baseline)
            self.assertEqual(result, expected)
            supervisor.assert_called_once_with(root, carrier_pid=111, interval_ms=10.0)

    def test_retained_heartbeat_subsignal_state_also_requests_existing_supervision(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state_path = root / carrier.LEGACY_SUBSIGNAL_STATE_REL
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps({
                "schema": "stegverse.heartbeat-subsignals/v1",
                "generation": 1,
                "subsignals": {"worker_coordination": {"state": "IDLE"}},
            }) + "\n", encoding="utf-8")
            baseline = carrier._subsignal_activity_snapshot(root)
            state_path.write_text(json.dumps({
                "schema": "stegverse.heartbeat-subsignals/v1",
                "generation": 2,
                "subsignals": {
                    "worker_coordination": {"state": "ACTIVE"},
                    "organization_federation": {"state": "ACTIVE"},
                    "steggate_transport_lease": {"state": "ACTIVE"},
                },
            }) + "\n", encoding="utf-8")
            supervisor = mock.Mock(return_value={"state": "WORKER_ALREADY_PRESENT", "authority_effect": "NONE_SUPERVISION_ONLY"})
            current, result = carrier._observe_hb_subsignal_worker_presence(
                root,
                previous_snapshot=baseline,
                carrier_pid=111,
                interval_ms=10.0,
                supervisor=supervisor,
            )
            self.assertNotEqual(current, baseline)
            self.assertIsNotNone(result)
            supervisor.assert_called_once_with(root, carrier_pid=111, interval_ms=10.0)

    def test_no_new_subsignal_does_not_duplicate_supervision(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            event_path = root / carrier.DERIVED_SUBSIGNAL_EVENT_LOG_REL
            event_path.parent.mkdir(parents=True, exist_ok=True)
            event_path.write_text('{"event":"HB_DERIVED_INTR_SUBSIGNAL_PROPAGATED_LOCAL"}\n', encoding="utf-8")
            baseline = carrier._subsignal_activity_snapshot(root)
            supervisor = mock.Mock()
            current, result = carrier._observe_hb_subsignal_worker_presence(
                root,
                previous_snapshot=baseline,
                carrier_pid=111,
                interval_ms=10.0,
                supervisor=supervisor,
            )
            self.assertEqual(current, baseline)
            self.assertIsNone(result)
            supervisor.assert_not_called()

    def test_subsignal_supervision_preserves_periodic_fallback_and_authority_boundary(self):
        source = Path(carrier.__file__).read_text(encoding="utf-8")
        self.assertIn('"HB_AU_SUBSIGNAL_ACTIVITY"', source)
        self.assertIn('"PERIODIC_CARRIER_FALLBACK"', source)
        self.assertIn("produced % WORKER_SUPERVISION_INTERVAL_REFERENCES == 0", source)
        self.assertIn("grants no task, claim/fence", source)
        self.assertNotIn("claim_or_fence_minted = True", source)

    def test_self_healed_worker_preserves_canonical_local_bindings(self):
        self.assertTrue(set(service.WORKER_SAFE_LOCAL_BINDINGS).issubset(repair.SAFE_ENV))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            values = {
                "STEGVERSE_TVC_ROOT": "/srv/stegverse/TVC",
                "STEGVERSE_TV_ROOT": "/srv/stegverse/TV",
                "STEGVERSE_STEGINDEX_SOURCE_ROOT": "/srv/stegverse/StegIndex",
                "STEGVERSE_MASTER_RECORDS_ROOT": "/srv/stegverse/master-records",
                "STEGVERSE_MASTER_RECORDS_ENDPOINT": "http://127.0.0.1:8765",
                "STEGVERSE_MASTER_RECORDS_TOKEN": "canonical-mr-token",
                "STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS": "10",
                "MASTER_RECORDS_DB": "/var/lib/stegverse/master-records/master-records.db",
                "MASTER_RECORDS_RECEIPT_KEY": "canonical-local-receipt-key",
                "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS": "true",
                "GITHUB_TOKEN": "must-not-propagate",
            }
            with mock.patch.dict(os.environ, values, clear=True):
                env = repair._clean_env(root)
            self.assertEqual(env["STEGVERSE_TVC_ROOT"], values["STEGVERSE_TVC_ROOT"])
            self.assertEqual(env["STEGVERSE_TV_ROOT"], values["STEGVERSE_TV_ROOT"])
            self.assertEqual(env["STEGVERSE_STEGINDEX_SOURCE_ROOT"], values["STEGVERSE_STEGINDEX_SOURCE_ROOT"])
            self.assertEqual(env["STEGVERSE_MASTER_RECORDS_ROOT"], values["STEGVERSE_MASTER_RECORDS_ROOT"])
            for key in repair.CANONICAL_CUSTODY_ENV:
                self.assertEqual(env[key], values[key])
            self.assertNotIn("GITHUB_TOKEN", env)
            self.assertEqual(env["STEGVERSE_HEARTBEAT_ROOT"], str(root.resolve()))

    def test_existing_worker_is_reused_without_second_process_and_presence_is_projected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "run_worker_runtime.py").write_text("# present\n", encoding="utf-8")
            state = root / repair.WORKER_STATE
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(json.dumps({
                "schema": "stegverse.worker-runtime-state/v1",
                "runtime_tick": 5,
                "observation_mode": "TASK_CAPABLE_WORKER_COORDINATOR",
            }) + "\n", encoding="utf-8")
            receipt = root / repair.PROCESS_RECEIPT
            receipt.parent.mkdir(parents=True)
            receipt.write_text(json.dumps({"carrier_pid": 111, "worker_pid": 222}) + "\n", encoding="utf-8")
            projected = {"resident": {"present_worker_runtime_observed": True}}
            with mock.patch.dict(os.environ, {}, clear=True), \
                 mock.patch.object(repair, "_alive", side_effect=lambda pid: pid in {111, 222}), \
                 mock.patch.object(repair, "project", return_value={"resident": {"worker_cycle_fresh": True}}), \
                 mock.patch.object(repair, "_persist_presence_projection", return_value=projected) as persist, \
                 mock.patch.object(repair, "_persist_presence_master_records_intake", return_value={"state": "MASTER_RECORDS_ROOT_NOT_DECLARED"}), \
                 mock.patch.object(repair.subprocess, "Popen") as popen:
                result = repair.ensure_worker_presence(root, carrier_pid=111)
            self.assertEqual(result["state"], "WORKER_ALREADY_PRESENT")
            self.assertFalse(result["worker_repair_attempted"])
            self.assertTrue(result["worker_cycle_fresh"])
            self.assertTrue(result["present_worker_runtime_observed"])
            self.assertEqual(result["presence_receipt_ref"], str(repair.PRESENCE_RECEIPT))
            self.assertFalse(result["heartbeat_grants_execution_authority"])
            self.assertTrue(result["worker_coordinator_retains_admission_authority"])
            retained = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(retained["canonical_carrier_runtime"], "heartbeat_runtime.engine_v13.HeartbeatRuntime")
            self.assertEqual(retained["authority_effect"], "NONE_SUPERVISION_ONLY")
            persist.assert_called_once_with(root.resolve())
            popen.assert_not_called()

    def test_alive_but_stale_worker_is_recycled_using_existing_restart_termination(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "run_worker_runtime.py").write_text("# present\n", encoding="utf-8")
            state = root / repair.WORKER_STATE
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(json.dumps({
                "schema": "stegverse.worker-runtime-state/v1",
                "runtime_tick": 9,
                "observation_mode": "TASK_CAPABLE_WORKER_COORDINATOR",
                "last_cycle_at": "2026-01-01T00:00:00Z",
            }) + "\n", encoding="utf-8")
            receipt = root / repair.PROCESS_RECEIPT
            receipt.parent.mkdir(parents=True)
            receipt.write_text(json.dumps({"carrier_pid": 111, "worker_pid": 222}) + "\n", encoding="utf-8")
            proc = mock.Mock(pid=333)
            projected = {"resident": {"present_worker_runtime_observed": True}}
            with mock.patch.dict(os.environ, {}, clear=True), \
                 mock.patch.object(repair, "_alive", side_effect=lambda pid: pid in {111, 222, 333}), \
                 mock.patch.object(repair, "project", return_value={"resident": {"worker_cycle_fresh": False}}), \
                 mock.patch.object(repair, "_terminate_process", return_value=True) as terminate, \
                 mock.patch.object(repair.subprocess, "Popen", return_value=proc) as popen, \
                 mock.patch.object(repair, "_runtime_tick", return_value=9), \
                 mock.patch.object(repair, "_wait_for_tick", return_value={"observed": True, "reason": "TASK_CAPABLE_WORKER_RUNTIME_TICK_OBSERVED", "baseline_tick": 9, "observed_tick": 10}), \
                 mock.patch.object(repair, "_persist_presence_projection", return_value=projected), \
                 mock.patch.object(repair, "_persist_presence_master_records_intake", return_value={"state": "MASTER_RECORDS_ROOT_NOT_DECLARED"}):
                result = repair.ensure_worker_presence(root, carrier_pid=111)
            self.assertEqual(result["state"], "STALE_WORKER_RECYCLED")
            self.assertTrue(result["worker_repair_attempted"])
            self.assertEqual(result["stale_worker_pid"], 222)
            self.assertEqual(result["worker_pid"], 333)
            self.assertEqual(result["stale_worker_reason"], "WORKER_CYCLE_STALE")
            self.assertTrue(result["request_drain_expected_on_worker_start"])
            terminate.assert_called_once_with(222)
            popen.assert_called_once()
            retained = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertTrue(retained["stale_worker_recycled"])
            self.assertEqual(retained["previous_worker_pid"], 222)
            self.assertEqual(retained["worker_pid"], 333)

    def test_missing_worker_is_repaired_tick_proven_and_presence_projected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "run_worker_runtime.py").write_text("# present\n", encoding="utf-8")
            proc = mock.Mock(pid=333)
            alive = {111: True, 333: True}
            projected = {"resident": {"present_worker_runtime_observed": True}}
            with mock.patch.dict(os.environ, {}, clear=True), \
                 mock.patch.object(repair, "_alive", side_effect=lambda pid: alive.get(pid, False)), \
                 mock.patch.object(repair.subprocess, "Popen", return_value=proc) as popen, \
                 mock.patch.object(repair, "_runtime_tick", return_value=7), \
                 mock.patch.object(repair, "_persist_presence_projection", return_value=projected) as persist, \
                 mock.patch.object(repair, "_persist_presence_master_records_intake", return_value={"state": "MASTER_RECORDS_ROOT_NOT_DECLARED"}), \
                 mock.patch.object(repair, "_wait_for_tick", return_value={"observed": True, "reason": "TASK_CAPABLE_WORKER_RUNTIME_TICK_OBSERVED", "baseline_tick": 7, "observed_tick": 8}):
                result = repair.ensure_worker_presence(root, carrier_pid=111)
            self.assertEqual(result["state"], "WORKER_REPAIRED")
            self.assertTrue(result["worker_repair_attempted"])
            self.assertTrue(result["present_worker_runtime_observed"])
            self.assertEqual(result["presence_receipt_ref"], str(repair.PRESENCE_RECEIPT))
            self.assertFalse(result["heartbeat_grants_execution_authority"])
            self.assertTrue(result["worker_coordinator_retains_admission_authority"])
            self.assertTrue(result["request_drain_expected_on_worker_start"])
            popen.assert_called_once()
            persist.assert_called_once_with(root.resolve())
            retained = json.loads((root / repair.PROCESS_RECEIPT).read_text(encoding="utf-8"))
            self.assertEqual(retained["worker_pid"], 333)
            self.assertTrue(retained["worker_task_capable_cycle_observed"])
            self.assertEqual(retained["canonical_carrier_runtime"], "heartbeat_runtime.engine_v13.HeartbeatRuntime")
            self.assertEqual(retained["authority_effect"], "NONE_SUPERVISION_ONLY")

    def test_projection_receipt_is_durable_observation_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.object(repair, "project", return_value={
                "schema": "stegverse.hb-runtime-presence-resident-observability/v1",
                "resident": {"present_worker_runtime_observed": False},
                "authority": {"projection_authority_effect": "NONE_OBSERVATION_ONLY"},
            }):
                result = repair._persist_presence_projection(root)
            path = root / repair.PRESENCE_RECEIPT
            self.assertTrue(path.is_file())
            retained = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(retained, result)
            self.assertEqual(retained["authority"]["projection_authority_effect"], "NONE_OBSERVATION_ONLY")

    def test_hosted_environment_cannot_become_runtime_repair_surface(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True):
            result = repair.ensure_worker_presence(Path(td), carrier_pid=111)
        self.assertEqual(result["state"], "HOSTED_ENVIRONMENT_REJECTED")
        self.assertFalse(result["worker_repair_attempted"])


if __name__ == "__main__":
    unittest.main()
