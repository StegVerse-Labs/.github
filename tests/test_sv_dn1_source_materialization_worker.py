import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workers import sv_dn1_source_materialization_worker as worker


def blob(data: bytes) -> str:
    return worker.git_blob_sha1(data)


class SvDn1SourceMaterializationTests(unittest.TestCase):
    def test_registry_adapter_and_handoff_preserve_narrow_authority(self):
        root = Path(__file__).resolve().parents[1]
        registry = json.loads((root / "control/worker-registry.d/sv-dn1-source-materialization-001.json").read_text())
        adapter = json.loads((root / "control/process-worker-adapters.d/sv-dn1-source-materialization-001.json").read_text())
        handoff = json.loads((root / "handoffs/SV-DN1-SOURCE-MATERIALIZATION-001.json").read_text())

        self.assertEqual(registry["tasks"][0]["state"], "HANDOFF_READY")
        self.assertIsNone(registry["tasks"][0]["claim_id"])
        self.assertEqual(registry["credential_authority"], "TV/TVC")
        self.assertFalse(registry["github_token_required"])

        row = adapter["adapters"][0]
        self.assertEqual(row["adapter_ref"], "process:sv-dn1-source-materialization-v1")
        self.assertNotIn("GITHUB_TOKEN", row["env_allowlist"])
        self.assertNotIn("GH_TOKEN", row["env_allowlist"])
        self.assertIn("materialization/**", row["bound_state_allowed_paths"])

        authority = handoff["authority"]
        self.assertFalse(authority["repository_writeback_authority"])
        self.assertFalse(authority["observation_authority"])
        self.assertFalse(authority["sdk_admission_authority"])
        self.assertFalse(authority["governance_decision_authority"])
        self.assertFalse(authority["publication_authority"])
        self.assertTrue(authority["public_source_materialization_authority"])
        self.assertFalse(authority["heartbeat_grants_execution_authority"])

    def test_manifest_pin_drift_fails_closed(self):
        data = b'{"schema":"stegverse.sv-dn1.runtime-source-manifest/v1"}\n'
        with self.assertRaises(worker.SourcePinDrift):
            worker.validate_manifest(data)

    def test_complete_materialization_with_verified_blobs(self):
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            source_root = temp / "source"
            bound = temp / "state"
            node_path = temp / "node.json"

            manifest_source = b'print("observer")\n'
            mapping = b'{"mapping":"v1"}\n'
            support_doc = b"# handoff\n"
            support_task = b'{"task_id":"SV-DN1-RESIDENT-OBSERVER-001"}\n'
            manifest = {
                "schema": "stegverse.sv-dn1.runtime-source-manifest/v1",
                "profile_id": "SV-DN-1",
                "source_repository": worker.REPOSITORY,
                "source_basis_commit": "a" * 40,
                "hash_profile": "git-blob-sha1",
                "files": {
                    "scripts/observe_sv_dn1_hf_public.py": blob(manifest_source),
                    "config/sv_dn1_hf_mapping.v1.json": blob(mapping),
                },
            }
            manifest_bytes = (json.dumps(manifest, sort_keys=True) + "\n").encode()
            expected_manifest = blob(manifest_bytes)
            support = {
                "docs/SV_DN1_DOUBLE_INTERLOCK_MIRROR_HANDOFF.md": blob(support_doc),
                "tasks/SV-DN1-RESIDENT-OBSERVER-001.json": blob(support_task),
            }
            source_map = {
                (worker.MANIFEST_REF, worker.MANIFEST_PATH): manifest_bytes,
                ("a" * 40, "scripts/observe_sv_dn1_hf_public.py"): manifest_source,
                ("a" * 40, "config/sv_dn1_hf_mapping.v1.json"): mapping,
                ("main", "docs/SV_DN1_DOUBLE_INTERLOCK_MIRROR_HANDOFF.md"): support_doc,
                ("main", "tasks/SV-DN1-RESIDENT-OBSERVER-001.json"): support_task,
            }

            invocation = {
                "schema": "stegverse.worker-invocation/v0.1",
                "task": {
                    "task_id": worker.TASK_ID,
                    "worker_id": worker.WORKER_ID,
                    "claim_id": "claim-1",
                    "heartbeat_timing": {"fencing_token": 7},
                },
                "handoff": {
                    "authority": {
                        "credential_authority": "TV/TVC",
                        "github_token_required": False,
                        "non_tv_tvc_secret_or_token_allowed": False,
                        "repository_writeback_authority": False,
                        "observation_authority": False,
                        "heartbeat_grants_execution_authority": False,
                    },
                    "input_contract": {
                        "source_repository": worker.REPOSITORY,
                        "manifest_ref": worker.MANIFEST_REF,
                        "manifest_path": worker.MANIFEST_PATH,
                        "manifest_git_blob_sha1": expected_manifest,
                        "support_files": support,
                    },
                },
            }

            def fake_fetch(ref, path, timeout=30):
                return source_map[(ref, path)]

            with (
                mock.patch.object(worker, "EXPECTED_MANIFEST_BLOB", expected_manifest),
                mock.patch.object(worker, "SUPPORT_FILES", support),
                mock.patch.object(worker, "fetch_bytes", side_effect=fake_fetch),
                mock.patch.object(worker, "find_node", return_value=(node_path, {"declared": True})),
                mock.patch.object(worker, "require_bound_state_root", return_value=bound),
                mock.patch.object(worker, "source_root", return_value=source_root),
                mock.patch.dict("os.environ", {}, clear=True),
            ):
                receipt = worker.execute(invocation)

            self.assertEqual(receipt["state"], "COMPLETE")
            self.assertEqual(receipt["transition_id"], "SV_DN1_EXACT_SOURCE_MATERIALIZATION_COMPLETE")
            self.assertTrue(receipt["manifest_blob_verified"])
            self.assertTrue(receipt["production_source_blobs_verified"])
            self.assertTrue(receipt["support_file_blobs_verified"])
            self.assertEqual(receipt["post_write_validation"], "PASS")
            self.assertFalse(receipt["github_token_used"])
            self.assertFalse(receipt["repository_writeback_performed"])
            self.assertTrue((source_root / "scripts/observe_sv_dn1_hf_public.py").is_file())
            self.assertTrue((source_root / worker.MANIFEST_PATH).is_file())
            self.assertTrue((bound / "receipts/latest.json").is_file())

    def test_pin_drift_returns_handoff_ready_not_success(self):
        invocation = {"schema": "stegverse.worker-invocation/v0.1"}
        with (
            mock.patch.object(worker, "execute", side_effect=worker.SourcePinDrift("pin changed")),
            mock.patch("sys.stdin", io.StringIO(json.dumps(invocation) + "\n")),
            mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            self.assertEqual(worker.main(), 0)
            result = json.loads(stdout.getvalue())
        self.assertEqual(result["state"], "HANDOFF_READY")
        self.assertEqual(result["transition_id"], "SV_DN1_SOURCE_PIN_RECONCILIATION_REQUIRED")
        self.assertFalse(result["blocker"]["human_action_required"])
        self.assertFalse(result["blocker"]["github_token_required"])

    def test_hosted_environment_is_rejected(self):
        invocation = {
            "schema": "stegverse.worker-invocation/v0.1",
            "task": {
                "task_id": worker.TASK_ID,
                "worker_id": worker.WORKER_ID,
                "claim_id": "claim-1",
                "heartbeat_timing": {"fencing_token": 7},
            },
        }
        with mock.patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "hosted environments"):
                worker.execute(invocation)


if __name__ == "__main__":
    unittest.main()
