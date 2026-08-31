from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

REFRESH_SPEC = importlib.util.spec_from_file_location(
    "refresh_sovereign_worker_runtime_source",
    ROOT / "scripts/refresh_sovereign_worker_runtime_source.py",
)
assert REFRESH_SPEC and REFRESH_SPEC.loader
refresh_mod = importlib.util.module_from_spec(REFRESH_SPEC)
REFRESH_SPEC.loader.exec_module(refresh_mod)

INSTALL_SPEC = importlib.util.spec_from_file_location(
    "install_sovereign_worker_source_refresh_service",
    ROOT / "scripts/install_sovereign_worker_source_refresh_service.py",
)
assert INSTALL_SPEC and INSTALL_SPEC.loader
install_mod = importlib.util.module_from_spec(INSTALL_SPEC)
INSTALL_SPEC.loader.exec_module(install_mod)


class SovereignWorkerSourceRefreshTests(unittest.TestCase):
    def test_refresh_copies_static_source_and_preserves_mutable_runtime_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            for rel in (
                "heartbeat_runtime", "workers", "handoffs", "authorizations", "schemas", "cost-basis", "management",
                "state_language", "scripts", "control/worker-registry.d", "control/process-worker-adapters.d",
                "control/task-vectors", "control/resident-execution-request.d",
            ):
                (source / rel).mkdir(parents=True, exist_ok=True)
            (source / "heartbeat_runtime/worker_runtime.py").write_text("VERSION='new'\n", encoding="utf-8")
            (source / "heartbeat_runtime/intr_derived_carrier.py").write_text("# canonical HB/InTr carrier\n", encoding="utf-8")
            (source / "workers/new_worker.py").write_text("x=1\n", encoding="utf-8")
            (source / "handoffs/new.json").write_text("{}\n", encoding="utf-8")
            (source / "control/worker-registry.json").write_text('{"schema":"x"}\n', encoding="utf-8")
            (source / "control/process-worker-adapters.json").write_text('{"schema":"x"}\n', encoding="utf-8")
            (source / "control/worker-registry.d/new.json").write_text("{}\n", encoding="utf-8")
            (source / "control/process-worker-adapters.d/new.json").write_text("{}\n", encoding="utf-8")
            (source / "control/task-vectors/new-task.json").write_text('{"profile":"task.v1","level":"task","vector":"50000000100000"}\n', encoding="utf-8")
            (source / "state_language/__init__.py").write_text("# state-language\n", encoding="utf-8")
            (source / "control/task-vector-index.json").write_text('{"schema":"stegverse.cosv-task-vector-index/v0.1"}\n', encoding="utf-8")
            (source / "control/resident-execution-request.json").write_text('{"schema":"stegverse.resident-execution-request/v1"}\n', encoding="utf-8")
            (source / "control/resident-execution-request.d/sv-dn1.json").write_text('{"schema":"stegverse.resident-execution-request/v1"}\n', encoding="utf-8")
            (source / "control/resident-execution-request.d/ecosystem-chat-parent-001.json").write_text('{"schema":"stegverse.resident-execution-request/v1"}\n', encoding="utf-8")
            (source / "control/resident-execution-request.d/hil-sovereign-receiver-001.json").write_text('{"schema":"stegverse.resident-execution-request/v1"}\n', encoding="utf-8")
            (source / "control/resident-execution-request.d/evaluator-intr-read-runtime-001.json").write_text('{"schema":"stegverse.resident-execution-request/v1"}\n', encoding="utf-8")
            (source / "control/resident-execution-request.d/sv002-public-observation-runtime-001.json").write_text('{"schema":"stegverse.resident-execution-request/v1"}\n', encoding="utf-8")
            (source / "control/resident-execution-request.d/healer-sovereign-scheduler-001.json").write_text('{"schema":"stegverse.resident-execution-request/v1"}\n', encoding="utf-8")
            for rel in refresh_mod.STATIC_FILES:
                path = source / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# source\n", encoding="utf-8")

            (runtime / "heartbeat_runtime").mkdir(parents=True)
            (runtime / "heartbeat_runtime/worker_runtime.py").write_text("VERSION='old'\n", encoding="utf-8")
            (runtime / "control").mkdir(parents=True)
            mutable = {
                "heartbeat-state.json": '{"epoch":29}\n',
                "heartbeat-carrier-runtime-state.json": '{"epoch":31}\n',
                "worker-runtime-state.json": '{"runtime_tick":2}\n',
                "worker-control-plane-coordination.json": '{"state":"retained"}\n',
                "worker-status.json": '{"state":"retained"}\n',
            }
            resident_registry = (
                '{"generation":44,"tasks":[{"task_id":"LIVE","claim_id":"claim-44",'
                '"heartbeat_timing":{"fencing_token":44},"state":"ACTIVE"}]}\n'
            )
            (runtime / "control/worker-registry.json").write_text(resident_registry, encoding="utf-8")
            for name, value in mutable.items():
                (runtime / "control" / name).write_text(value, encoding="utf-8")
            (runtime / "receipts/sovereign-host").mkdir(parents=True)
            (runtime / "receipts/sovereign-host/existing.json").write_text('{"keep":true}\n', encoding="utf-8")

            receipt = refresh_mod.refresh(source, runtime)
            self.assertTrue(receipt["mutable_runtime_state_preserved"])
            self.assertNotIn("control/worker-registry.json", receipt["copied_static_paths"])
            self.assertFalse(receipt["network_fetch_performed"])
            self.assertFalse(receipt["credential_read_or_acquired"])
            self.assertFalse(receipt["github_token_required"])
            self.assertEqual((runtime / "heartbeat_runtime/worker_runtime.py").read_text(), "VERSION='new'\n")
            self.assertTrue((runtime / "workers/new_worker.py").is_file())
            self.assertTrue((runtime / "control/worker-registry.d/new.json").is_file())
            self.assertTrue((runtime / "control/task-vectors/new-task.json").is_file())
            self.assertTrue((runtime / "control/task-vector-index.json").is_file())
            self.assertTrue((runtime / "control/resident-execution-request.json").is_file())
            self.assertTrue((runtime / "control/resident-execution-request.d/sv-dn1.json").is_file())
            self.assertTrue((runtime / "control/resident-execution-request.d/ecosystem-chat-parent-001.json").is_file())
            self.assertTrue((runtime / "control/resident-execution-request.d/hil-sovereign-receiver-001.json").is_file())
            self.assertTrue((runtime / "control/resident-execution-request.d/evaluator-intr-read-runtime-001.json").is_file())
            self.assertTrue((runtime / "control/resident-execution-request.d/sv002-public-observation-runtime-001.json").is_file())
            self.assertTrue((runtime / "control/resident-execution-request.d/healer-sovereign-scheduler-001.json").is_file())
            self.assertTrue((runtime / "state_language/__init__.py").is_file())
            for rel in (
                "scripts/run_worker_runtime.py",
                "scripts/refresh_and_execute_resident_task.py",
                "scripts/run_independent_ecosystem_chat_parent.py",
                "scripts/consume_resident_execution_request.py",
                "scripts/consume_g18_resident_execution_request.py",
                "scripts/consume_hil_resident_execution_request.py",
                "scripts/consume_evaluator_intr_resident_execution_request.py",
                "scripts/materialize_evaluator_intr_route_config.py",
                "scripts/consume_sv002_public_observation_request.py",
                "scripts/materialize_sv002_observation_route_config.py",
                "scripts/serve_sv002_observation_intr_runtime.py",
                "scripts/consume_hil_intr_materialization_request.py",
                "scripts/serve_evaluator_intr_runtime.py",
                "scripts/consume_ara_graph_resident_execution_request.py",
                "scripts/consume_cmc028_resident_execution_request.py",
                "scripts/run_sv_dn1_first_round_chain.py",
                "scripts/consume_sv_dn1_resident_execution_request.py",
                "scripts/consume_stegos_kv_intr_chain_request.py",
                "scripts/consume_bootstrap_v1_intr_bundle_delivery_request.py",
                "scripts/consume_tvc_broker_validation_request.py",
                "scripts/consume_sv002_self_characterization_request.py",
                "scripts/consume_healer_sovereign_scheduler_request.py",
                "scripts/dispatch_resident_execution_requests.py",
                "scripts/materialize_live_cosv_packet.py",
                "scripts/cosv.py",
                "scripts/cosv_state_packet.py",
            ):
                self.assertTrue((runtime / rel).is_file(), rel)
            for name, value in mutable.items():
                self.assertEqual((runtime / "control" / name).read_text(), value)
            self.assertEqual((runtime / "control/worker-registry.json").read_text(), resident_registry)
            self.assertEqual((runtime / "control/worker-registry.d/new.json").read_text(), "{}\n")
            self.assertTrue((runtime / "receipts/sovereign-host/existing.json").is_file())
            self.assertTrue((runtime / "receipts/sovereign-host/worker-source-refresh.latest.json").is_file())

    def test_mutable_runtime_state_is_explicitly_forbidden_as_refresh_source(self) -> None:
        for value in (
            Path("receipts/x.json"),
            Path("checkpoints/x.json"),
            Path("control/worker-runtime-state.json"),
            Path("control/heartbeat-carrier-runtime-state.json"),
            Path("control/worker-registry.json"),
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    refresh_mod._assert_static_path(value)

    def test_rootless_watcher_is_filesystem_event_driven_and_secret_free(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            runtime.mkdir()
            packages = base / "source-packages"
            service, path_unit = install_mod.render_units(
                source_root=source,
                runtime_root=runtime,
                python=Path("/usr/bin/python3"),
                source_package_root=packages,
            )
            self.assertIn("systemctl --user try-restart stegverse-worker-runtime.service", service)
            self.assertIn("PathChanged=", path_unit)
            self.assertIn("workers", path_unit)
            self.assertIn("heartbeat_runtime", path_unit)
            self.assertIn("scripts", path_unit)
            self.assertIn("state_language", path_unit)
            self.assertIn("worker-registry.d", path_unit)
            self.assertIn("process-worker-adapters.d", path_unit)
            self.assertIn("control/task-vectors", path_unit)
            self.assertIn("control/task-vector-index.json", path_unit)
            self.assertIn("control/resident-execution-request.json", path_unit)
            self.assertIn("control/resident-execution-request.d", path_unit)
            self.assertIn("dispatch_resident_execution_requests.py", service)
            self.assertIn("consume_hil_intr_materialization_request.py", service)
            self.assertIn(f"PathChanged={runtime / 'intr-materialization'}", path_unit)
            self.assertIn(f"PathChanged={packages.resolve()}", path_unit)
            for slug in install_mod.SOURCE_PACKAGE_COMPONENT_SLUGS:
                self.assertIn(f"PathChanged={(packages / slug).resolve()}", path_unit)
            self.assertIn(f'STEGVERSE_SOURCE_PACKAGE_ROOT={packages.resolve()}', service)
            self.assertNotIn("consume_resident_execution_request.py --source-root", service)
            self.assertNotIn("consume_g18_resident_execution_request.py --source-root", service)
            self.assertIn("consume_hil_intr_materialization_request.py", service)
            self.assertNotIn("consume_hil_resident_execution_request.py --source-root", service)
            self.assertNotIn(f"PathChanged={source / 'control/worker-registry.json'}", path_unit)
            self.assertIn("authorizations", path_unit)
            self.assertIn("cost-basis", path_unit)
            self.assertIn("management", path_unit)
            self.assertIn("WantedBy=default.target", path_unit)
            combined = service + path_unit
            for forbidden in ("GITHUB_TOKEN", "GH_TOKEN", "LoadCredential=", "git clone", "git fetch", "git pull"):
                self.assertNotIn(forbidden, combined)


    def test_default_source_package_root_honors_nonsecret_override(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "packages"
            self.assertEqual(
                install_mod.default_source_package_root({"STEGVERSE_SOURCE_PACKAGE_ROOT": str(root)}),
                root.resolve(),
            )

    def test_installer_immediately_refreshes_then_restarts_only_worker(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            runtime = base / "runtime"
            unit_root = base / "units"
            calls: list[list[str]] = []

            def runner(command, **_kwargs):
                calls.append(command)
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with mock.patch.object(install_mod, "refresh", return_value={
                "schema": "stegverse.sovereign-worker-runtime-source-refresh/v1",
                "mutable_runtime_state_preserved": True,
                "network_fetch_performed": False,
            }), mock.patch.object(install_mod.shutil, "which", return_value="/usr/bin/systemctl"):
                package_root = base / "source-packages"
                receipt = install_mod.install(
                    ROOT,
                    runtime,
                    unit_root=unit_root,
                    source_package_root=package_root,
                    runner=runner,
                    activate=True,
                    system="linux",
                )
            self.assertTrue(receipt["activated"])
            self.assertTrue(receipt["filesystem_event_driven"])
            self.assertTrue(receipt["intr_materialization_event_driven"])
            self.assertTrue(receipt["source_package_event_driven"])
            self.assertTrue((runtime / "intr-materialization").is_dir())
            self.assertTrue(package_root.is_dir())
            for slug in install_mod.SOURCE_PACKAGE_COMPONENT_SLUGS:
                self.assertTrue((package_root / slug).is_dir())
            self.assertEqual(receipt["source_package_watch"], str(package_root.resolve()))
            self.assertEqual(
                receipt["source_package_component_watches"],
                [str((package_root / slug).resolve()) for slug in install_mod.SOURCE_PACKAGE_COMPONENT_SLUGS],
            )
            self.assertFalse(receipt["second_heartbeat_created"])
            self.assertFalse(receipt["third_party_scheduler_required"])
            self.assertFalse(receipt["carrier_restarted_by_refresh"])
            self.assertEqual(len(calls), 3)
            flattened = [" ".join(command) for command in calls]
            self.assertTrue(any("enable --now stegverse-worker-source-refresh.path" in value for value in flattened))
            self.assertTrue(any("try-restart stegverse-worker-runtime.service" in value for value in flattened))
            self.assertFalse(any("stegverse-heartbeat.service" in value for value in flattened))

    def test_refresh_sources_contain_no_network_transport_or_credential_path(self) -> None:
        combined = (
            (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text(encoding="utf-8")
            + (ROOT / "scripts/install_sovereign_worker_source_refresh_service.py").read_text(encoding="utf-8")
        )
        for forbidden in ("git clone", "git fetch", "git pull", "urlopen(", "requests.get", "GITHUB_TOKEN=", "GH_TOKEN=", "LoadCredential="):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()


def test_tvc_pr92_bootstrap_helper_is_refreshed_to_resident_runtime():
    source=(ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text()
    assert 'Path("scripts/bootstrap_tvc_pr92_validation_source.py")' in source
    assert 'Path("scripts/consume_tvc_broker_validation_request.py")' in source
