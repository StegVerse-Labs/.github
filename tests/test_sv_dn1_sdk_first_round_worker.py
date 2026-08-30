import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workers import sv_dn1_sdk_first_round_worker as worker


class SvDn1SdkFirstRoundWorkerTests(unittest.TestCase):
    def test_registry_adapter_and_handoff_preserve_production_boundary(self):
        root = Path(__file__).resolve().parents[1]
        registry = json.loads((root / "control/worker-registry.d/sv-dn1-sdk-first-round-001.json").read_text())
        adapter = json.loads((root / "control/process-worker-adapters.d/sv-dn1-sdk-first-round-001.json").read_text())
        handoff = json.loads((root / "handoffs/SV-DN1-SDK-FIRST-ROUND-001.json").read_text())

        self.assertEqual(registry["tasks"][0]["state"], "HANDOFF_READY")
        self.assertIsNone(registry["tasks"][0]["claim_id"])
        self.assertFalse(registry["github_token_required"])

        row = adapter["adapters"][0]
        self.assertEqual(row["adapter_ref"], "process:sv-dn1-sdk-first-round-v1")
        self.assertNotIn("GITHUB_TOKEN", row["env_allowlist"])
        self.assertNotIn("HF_TOKEN", row["env_allowlist"])
        self.assertNotIn("STEGVERSE_SDK_SOURCE_ROOT", row["env_allowlist"])
        self.assertIn("STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT", row["env_allowlist"])

        authority = handoff["authority"]
        self.assertTrue(authority["canonical_sdk_governed_execution_authority"])
        self.assertFalse(authority["external_consequence_authority"])
        self.assertFalse(authority["repository_writeback_authority"])
        self.assertFalse(authority["publication_authority"])
        self.assertFalse(authority["certification_authority"])
        self.assertFalse(authority["heartbeat_grants_execution_authority"])

    def test_missing_local_root_is_handoff_ready_not_fake_completion(self):
        with (
            mock.patch.object(worker, "execute", side_effect=worker.LocalArtifactPending("SDK root missing")),
            mock.patch("sys.stdin", io.StringIO(json.dumps({"schema": "x"}) + "\n")),
            mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            self.assertEqual(worker.main(), 0)
            result = json.loads(stdout.getvalue())
        self.assertEqual(result["state"], "HANDOFF_READY")
        self.assertEqual(result["transition_id"], "SV_DN1_CANONICAL_LOCAL_ARTIFACTS_PENDING")
        self.assertFalse(result["blocker"]["human_action_required"])
        self.assertFalse(result["blocker"]["third_party_runtime_required"])
        self.assertFalse(result["blocker"]["github_token_required"])

    def test_upstream_missing_is_handoff_ready(self):
        with (
            mock.patch.object(worker, "execute", side_effect=worker.UpstreamPending("InTr missing")),
            mock.patch("sys.stdin", io.StringIO(json.dumps({"schema": "x"}) + "\n")),
            mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            self.assertEqual(worker.main(), 0)
            result = json.loads(stdout.getvalue())
        self.assertEqual(result["state"], "HANDOFF_READY")
        self.assertEqual(result["transition_id"], "SV_DN1_INTR_RUNTIME_PENDING")

    def test_source_anchor_drift_fails_closed_to_source_drift(self):
        with (
            mock.patch.object(worker, "execute", side_effect=worker.SourceDrift("anchor drift")),
            mock.patch("sys.stdin", io.StringIO(json.dumps({"schema": "x"}) + "\n")),
            mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            self.assertEqual(worker.main(), 0)
            result = json.loads(stdout.getvalue())
        self.assertEqual(result["state"], "HANDOFF_READY")
        self.assertEqual(result["transition_id"], "SV_DN1_CANONICAL_SOURCE_DRIFT")
        self.assertFalse(result["blocker"]["human_action_required"])

    def test_source_prep_receipt_supplies_roots_and_content_identities(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            prep = base / "prep"
            roots = {}
            ids = {}
            original = worker.ANCHORS
            anchors = {}
            component_map = {
                "stegverse.sdk": "sdk",
                "stegverse.stegcore": "stegcore",
                "stegverse.core-lite": "core_lite",
                "stegverse.master-records": "master_records",
            }
            for component, key in component_map.items():
                root = base / key
                root.mkdir()
                roots[component] = str(root)
                ids[component] = "sha256:" + (key[0] * 64)
                anchors[key] = {}
                for rel in original[key]:
                    p = root / rel
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(f"{key}:{rel}\n")
                    anchors[key][rel] = worker.git_blob_sha1(p.read_bytes())
            prep_receipt = {
                "schema": "stegverse.sv-dn1.production-source-prep-receipt/v2",
                "state": "COMPLETE",
                "transition_id": "SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE",
                "source_identity_scheme": "sha256-content-manifest",
                "network_source_fetch_performed": False,
                "github_platform_required": False,
                "source_roots": roots,
                "source_identities": ids,
            }
            (prep / "receipts").mkdir(parents=True)
            (prep / "receipts/latest.json").write_text(json.dumps(prep_receipt))
            with (
                mock.patch.object(worker, "ANCHORS", anchors),
                mock.patch.dict("os.environ", {worker.SOURCE_PREP_STATE_ENV: str(prep)}, clear=True),
            ):
                resolved, identities, observed = worker.resolve_canonical_roots()
            self.assertEqual(set(resolved), set(component_map.values()))
            self.assertEqual(identities["sdk"], ids["stegverse.sdk"])
            self.assertEqual(observed["schema"], "stegverse.sv-dn1.production-source-prep-receipt/v2")

    def test_source_prep_receipt_rejects_external_platform_dependency(self):
        with tempfile.TemporaryDirectory() as td:
            prep = Path(td)
            (prep / "receipts").mkdir()
            (prep / "receipts/latest.json").write_text(json.dumps({
                "schema": "stegverse.sv-dn1.production-source-prep-receipt/v2",
                "state": "COMPLETE",
                "transition_id": "SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE",
                "source_identity_scheme": "sha256-content-manifest",
                "network_source_fetch_performed": True,
                "github_platform_required": False,
                "source_roots": {},
                "source_identities": {},
            }))
            with mock.patch.dict("os.environ", {worker.SOURCE_PREP_STATE_ENV: str(prep)}, clear=True):
                with self.assertRaisesRegex(worker.SourceDrift, "external platform dependency"):
                    worker.resolve_canonical_roots()

    def test_child_environment_contains_only_nonsecret_runtime_paths(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            roots = {
                "sdk": base / "sdk",
                "stegcore": base / "stegcore",
                "core_lite": base / "core-lite",
                "master_records": base / "master-records",
            }
            child = worker.child_env(roots)
            self.assertEqual(set(child), {"PATH", "HOME", "LANG", "LC_ALL", "PYTHONPATH"})
            self.assertNotIn("GITHUB_TOKEN", child)
            self.assertNotIn("HF_TOKEN", child)
            self.assertIn(str(roots["sdk"]), child["PYTHONPATH"])
            self.assertIn(str(roots["stegcore"] / "src"), child["PYTHONPATH"])

    def test_hosted_and_credential_environments_are_rejected_before_execution(self):
        with mock.patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "hosted environments"):
                worker.execute({})
        with mock.patch.dict("os.environ", {"HF_TOKEN": "present"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "credential-bearing environment"):
                worker.execute({})

    def test_completed_response_preserves_no_publication_claim(self):
        receipt = {
            "manifest_receipt_id": "MR-ABCDEF1234567890",
            "governance_state": "REVIEW",
            "publication_state": "PUBLIC_WITH_LIMITATIONS",
        }
        response = worker.completed_response(receipt)
        self.assertEqual(response["state"], "COMPLETED")
        self.assertEqual(response["transition_id"], "SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED")
        self.assertEqual(response["expected_next_transition"], "SV_DN1_PUBLIC_AUTHENTIC_DASHBOARD_PUBLISHED")
        self.assertFalse(response["github_token_used"])
        self.assertFalse(response["repository_writeback_performed"])


if __name__ == "__main__":
    unittest.main()
