from __future__ import annotations

import importlib.util
import json
import subprocess
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "activate_resident_stack.py"
spec = importlib.util.spec_from_file_location("activate_resident_stack", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def write_control_bundle(path: Path) -> None:
    files = {"scripts/bootstrap_sovereign_runtime.py": b"# bootstrap\n"}
    manifest = {
        "schema": "stegverse.sovereign-control-plane-bundle/v1",
        "network_fetch_required": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "bundle_grants_authority": False,
        "files": [
            {"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in files.items()
        ],
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("stegverse-control-plane-manifest.json", json.dumps(manifest))
        for name, data in files.items():
            archive.writestr(name, data)


RESIDENT_RESULT = {
    "state": "REVIEW_REQUIRED",
    "post_install_worker_prime": {"attempted": True, "task_capable_cycle_observed": True},
    "post_bootstrap_resident_request_dispatch": {"attempted": True, "state": "DISPATCH_COMPLETE"},
    "post_bootstrap_tvc_skap_successor": {"attempted": True, "state": "ACTIVE"},
}


class ResidentStackActivationTests(unittest.TestCase):
    def test_hosted_surface_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "hosted execution surface rejected"):
            module.clean_env({"RENDER": "true"})

    def test_one_shot_sequence_packages_deploys_and_records_skap_successor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "control"
            llm = root / "llm"
            (source / "scripts").mkdir(parents=True)
            (llm / "scripts").mkdir(parents=True)
            stegos = root / "StegOS"
            kv = root / "continuity-vault-kit"
            healer = root / "StegVerse-Healer"
            tv = root / "TV"
            tvc = root / "TVC"
            master_records = root / "master-records-orchestration"
            micro_node = root / "micro-node-runtime"
            tt = root / "TT"
            rtg = root / "RTG"
            gtg = root / "GTG"
            ae = root / "AE"
            stegindex = root / "StegIndex"
            (stegos / "stegos").mkdir(parents=True)
            (kv / "runtime").mkdir(parents=True)
            (stegos / "stegos" / "intr_backbone.py").write_text("# intr\n")
            (kv / "runtime" / "kv_interlock_endpoint.py").write_text("# kv\n")
            (healer / "app").mkdir(parents=True)
            (healer / "data").mkdir(parents=True)
            (healer / "docs").mkdir(parents=True)
            (healer / "app" / "dispatch_orchestrators.py").write_text("# dispatch\n")
            (healer / "data" / "orchestrator_targets.json").write_text("{}\n")
            (healer / "docs" / "HEALER_MIRROR_HANDOFF.md").write_text("# handoff\n")
            (tv / "scripts").mkdir(parents=True)
            (tv / "docs").mkdir(parents=True)
            (tv / "scripts" / "tv_run_resident_operational_proof.py").write_text("# proof\n")
            (tv / "docs" / "TV_OPERATIONAL_PROOF_SCHEMA.json").write_text("{}\n")
            (tvc / "scripts").mkdir(parents=True)
            (tvc / "tools").mkdir(parents=True)
            (tvc / "TVC_MIRROR_HANDOFF.md").write_text("# handoff\n")
            (tvc / "scripts" / "activate_coinbase_intr_resident.py").write_text("# activate\n")
            (tvc / "tools" / "hil_intr_lifecycle_intake.py").write_text("# intake\n")
            (master_records / "scripts").mkdir(parents=True)
            (master_records / "scripts" / "watch_stegverse001_autonomy_receipt.py").write_text("# watch\n")
            (master_records / "scripts" / "import_stegverse001_autonomy_receipt.py").write_text("# import\n")
            for source_root in (micro_node, tt, rtg, gtg, ae):
                source_root.mkdir(parents=True, exist_ok=True)
            (stegindex / "scripts").mkdir(parents=True)
            (stegindex / "registry").mkdir(parents=True)
            (stegindex / "STEGINDEX_MIRROR_HANDOFF.md").write_text("# handoff\n")
            (stegindex / "scripts" / "preflight.py").write_text("# preflight\n")
            (stegindex / "registry" / "capabilities.json").write_text('{"entries":[]}\n')
            (stegindex / "registry" / "predicates.json").write_text('{"predicates":[]}\n')
            (source / "scripts" / "package_sovereign_control_plane_bundle.py").write_text("# packager\n")
            (llm / "scripts" / "stegdeploy_native_gateway.py").write_text("# native gateway\n")
            receipt_path = root / "activation.json"
            calls: list[str] = []

            def runner(command, **kwargs):
                if "package_sovereign_control_plane_bundle.py" in str(command[1]):
                    self.assertIn("--master-records-root", command)
                    self.assertEqual(Path(command[command.index("--master-records-root") + 1]), master_records.resolve())
                    expected_roots = {
                        "--micro-node-root": micro_node,
                        "--tt-root": tt,
                        "--rtg-root": rtg,
                        "--gtg-root": gtg,
                        "--ae-root": ae,
                        "--stegindex-root": stegindex,
                    }
                    for flag, expected in expected_roots.items():
                        self.assertIn(flag, command)
                        self.assertEqual(Path(command[command.index(flag) + 1]), expected.resolve())
                    output = Path(command[command.index("--output") + 1])
                    write_control_bundle(output)
                    return subprocess.CompletedProcess(
                        command, 0,
                        stdout=json.dumps({"bundle_sha256": "abc123"}) + "\n",
                        stderr="",
                    )
                if "stegdeploy_native_gateway.py" in str(command[1]):
                    self.assertEqual(command[2:7], ["start", "--host", "127.0.0.1", "--port", "8000"])
                    self.assertNotIn("docker", " ".join(command))
                    calls.append("native_start")
                    native_receipt = {
                        "schema": "stegdeploy.native-sovereign-gateway-receipt/v1",
                        "state": "LOCAL_NATIVE_GATEWAY_STARTED",
                        "docker_required": False,
                        "health": {"gates_transition": False},
                    }
                    return subprocess.CompletedProcess(
                        command, 0, stdout=json.dumps(native_receipt, indent=2) + "\n", stderr="",
                    )
                if "bootstrap_sovereign_runtime.py" in str(command[1]):
                    self.assertEqual(calls, ["native_start"])
                    control_root = llm.resolve() / ".stegdeploy" / "resident-control-plane"
                    self.assertEqual(Path(command[1]), control_root / "scripts" / "bootstrap_sovereign_runtime.py")
                    self.assertEqual(command[2:], ["--source-root", str(control_root), "--skip-post-bootstrap-stegfin"])
                    child_env = kwargs["env"]
                    self.assertEqual(child_env["STEGVERSE_HEARTBEAT_SOURCE_ROOT"], str(control_root))
                    self.assertEqual(child_env["STEGVERSE_LLM_ADAPTER_ROOT"], str(llm.resolve()))
                    self.assertEqual(
                        child_env["STEGVERSE_RESIDENT_SOURCE_MANIFEST"],
                        str(control_root / ".stegverse-source-manifest.json"),
                    )
                    roots = json.loads(child_env["STEGVERSE_REPO_ROOTS_JSON"])
                    self.assertEqual(roots["StegVerse-Labs/.github"], str(control_root))
                    calls.append("resident_bootstrap")
                    return subprocess.CompletedProcess(command, 0, stdout=json.dumps(RESIDENT_RESULT) + "\n", stderr="")
                raise AssertionError(command)

            receipt = module.activate(
                source,
                llm,
                stegos_root=stegos,
                kv_source_root=kv,
                healer_root=healer,
                tv_root=tv,
                tvc_root=tvc,
                master_records_root=master_records,
                micro_node_root=micro_node,
                tt_root=tt,
                rtg_root=rtg,
                gtg_root=gtg,
                ae_root=ae,
                stegindex_root=stegindex,
                receipt_path=receipt_path,
                runner=runner,
                env={"PATH": "/usr/bin"},
            )
            self.assertEqual(receipt["state"], "COMPLETE")
            self.assertTrue(receipt["resident_task_capable_cycle_observed"])
            self.assertTrue(receipt["resident_request_dispatch_attempted"])
            self.assertEqual(receipt["g18_housekeeping_state"], "REVIEW_REQUIRED")
            self.assertFalse(receipt["g18_required_for_stack_completion"])
            self.assertTrue(receipt["stegos_source_bundled"])
            self.assertTrue(receipt["kv_source_bundled"])
            self.assertTrue(receipt["healer_source_bundled"])
            self.assertTrue(receipt["tv_source_bundled"])
            self.assertTrue(receipt["tvc_source_bundled"])
            self.assertTrue(receipt["master_records_source_bundled"])
            self.assertTrue(receipt["micro_node_source_bundled"])
            self.assertTrue(receipt["stegindex_source_bundled"])
            self.assertEqual(receipt["formal_sources_bundled"], {"TT": True, "RTG": True, "GTG": True, "AE": True})
            self.assertFalse(receipt["sv002_principal_execution_claimed"])
            self.assertFalse(receipt["formal_evaluation_claimed"])
            self.assertTrue(receipt["tvc_skap_successor_attempted"])
            self.assertEqual(receipt["tvc_skap_successor_state"], "ACTIVE")
            self.assertEqual(receipt["github_token_runtime_authority"], "NONE")
            self.assertFalse(receipt["orchestrator_grants_authority"])
            self.assertTrue(receipt_path.is_file())
            self.assertEqual(calls, ["native_start", "resident_bootstrap"])
            self.assertTrue(receipt["native_gateway_started"])
            self.assertFalse(receipt["container_framework_required"])
            self.assertFalse(receipt["destination_liveness_is_transition_predicate"])
            self.assertEqual(receipt["resident_bootstrap"]["state"], "REVIEW_REQUIRED")


    def _activate_with_native_start(self, root: Path, native_result, calls: list[str]) -> dict:
        source = root / "control"
        llm = root / "llm"
        (source / "scripts").mkdir(parents=True)
        (llm / "scripts").mkdir(parents=True)
        (source / "scripts" / "package_sovereign_control_plane_bundle.py").write_text("# packager\n")
        (llm / "scripts" / "stegdeploy_native_gateway.py").write_text("# native gateway\n")

        def runner(command, **kwargs):
            if "package_sovereign_control_plane_bundle.py" in str(command[1]):
                write_control_bundle(Path(command[command.index("--output") + 1]))
                return subprocess.CompletedProcess(command, 0, stdout="{}\n", stderr="")
            if "stegdeploy_native_gateway.py" in str(command[1]):
                calls.append("native_start")
                return native_result(command)
            if "bootstrap_sovereign_runtime.py" in str(command[1]):
                calls.append("resident_bootstrap")
                return subprocess.CompletedProcess(command, 0, stdout=json.dumps(RESIDENT_RESULT) + "\n", stderr="")
            raise AssertionError(command)

        named = {
            name: root / name
            for name in (
                "stegos_root", "kv_source_root", "healer_root", "tv_root", "tvc_root",
                "master_records_root", "micro_node_root", "tt_root", "rtg_root", "gtg_root",
                "ae_root", "stegindex_root",
            )
        }
        return module.activate(
            source,
            llm,
            **named,
            receipt_path=root / "activation.json",
            runner=runner,
            env={"PATH": "/usr/bin", "STEGVERSE_SERVICE_GATEWAY_NATIVE_STATE_ROOT": str(root / "gateway-state")},
        )

    def test_failed_native_start_records_six_field_non_allow_without_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            calls: list[str] = []
            receipt = self._activate_with_native_start(
                Path(tmp),
                lambda command: subprocess.CompletedProcess(command, 1, stdout="", stderr="RuntimeError: port_invalid\n"),
                calls,
            )
            self.assertEqual(calls, ["native_start"])
            self.assertEqual(receipt["state"], "INCOMPLETE")
            self.assertFalse(receipt["native_gateway_started"])
            resident = receipt["resident_bootstrap"]
            self.assertFalse(resident["attempted"])
            for field in (
                "failure_code", "failed_predicate", "required_evidence_or_repair",
                "retry_entrypoint", "owning_existing_goal", "next_attempt",
            ):
                self.assertTrue(resident[field], field)
            self.assertIn("port_invalid", resident["required_evidence_or_repair"])

    def test_already_running_native_gateway_is_a_closed_start_transition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "gateway-state"
            state.mkdir()
            (state / "native-deployment-receipt.json").write_text(json.dumps({
                "schema": "stegdeploy.native-sovereign-gateway-receipt/v1",
                "state": "LOCAL_NATIVE_GATEWAY_STARTED",
            }))
            calls: list[str] = []
            receipt = self._activate_with_native_start(
                root,
                lambda command: subprocess.CompletedProcess(
                    command, 1, stdout="", stderr="RuntimeError: native_gateway_already_running\n",
                ),
                calls,
            )
            self.assertEqual(calls, ["native_start", "resident_bootstrap"])
            self.assertTrue(receipt["native_gateway_already_running"])
            self.assertTrue(receipt["native_gateway_started"])
            self.assertEqual(receipt["state"], "COMPLETE")
            self.assertEqual(receipt["native_gateway_receipt_ref"], str((state / "native-deployment-receipt.json").resolve()))


if __name__ == "__main__":
    unittest.main()
