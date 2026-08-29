import io
import json
import tarfile
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from workers import sv_dn1_production_source_prep_worker as worker


def archive(files):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w:gz") as tf:
        for rel, data in files.items():
            info = tarfile.TarInfo("repo-root/" + rel)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return out.getvalue()


class SvDn1ProductionSourcePrepTests(unittest.TestCase):
    def test_registry_and_handoff_keep_private_transport_in_tvc(self):
        root = Path(__file__).resolve().parents[1]
        registry = json.loads((root / "control/worker-registry.d/sv-dn1-production-source-prep-001.json").read_text())
        handoff = json.loads((root / "handoffs/SV-DN1-PRODUCTION-SOURCE-PREP-001.json").read_text())
        task = registry["tasks"][0]
        self.assertEqual(task["state"], "HANDOFF_READY")
        self.assertEqual(task["admission"]["authority_domain"], "INDEPENDENT_TASK_CONTROL")
        self.assertEqual(task["admission"]["parent_task_id"], "SV-DN1-INTR-RUNTIME-001")
        self.assertEqual(handoff["task"]["dependencies"], ["SV-DN1-INTR-RUNTIME-001"])
        self.assertTrue(handoff["authority"]["tvc_spool_request_emission_authority"])
        self.assertFalse(handoff["authority"]["private_repository_transport_authority"])
        self.assertFalse(handoff["authority"]["repository_writeback_authority"])
        self.assertFalse(handoff["authority"]["github_token_required"])

    def test_private_request_is_nonsecret_and_exact(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "source"
            now = datetime(2026, 8, 29, 1, 0, tzinfo=timezone.utc)
            value = worker.build_private_warrant(base, "StegVerse-Labs/StegCore", now)
            self.assertEqual(value["schema"], worker.WARRANT_SCHEMA)
            self.assertEqual(value["operation_class"], "MATERIALIZE_SOURCE_ARCHIVE")
            self.assertEqual(value["expected_base_sha"], worker.COMMITS["StegVerse-Labs/StegCore"])
            self.assertEqual(value["credential_authority"], "TV/TVC")
            self.assertFalse(value["consumer_credential_present"])
            self.assertFalse(value["secret_values_present"])
            self.assertNotIn("token", json.dumps(value).lower())
            self.assertTrue(value["destination_identity"].endswith("StegVerse-Labs/StegCore"))

    def test_missing_private_roots_emit_requests_and_wait(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "source"
            spool = Path(td) / "spool"
            now = datetime(2026, 8, 29, 1, 0, tzinfo=timezone.utc)
            row = worker.request_or_verify_private(base, spool, "master-records/orchestration", now)
            self.assertEqual(row["state"], "TVC_MATERIALIZATION_REQUESTED")
            request = json.loads(Path(row["request_path"]).read_text())
            self.assertEqual(request["repository"], "master-records/orchestration")
            self.assertFalse(request["consumer_credential_present"])
            self.assertFalse(request["secret_values_present"])

    def test_public_archive_materializes_and_anchor_verifies(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "source"
            repo = "Data-Continuation/core-lite"
            payload = b"route\n"
            anchors = {repo: {"core_lite/transaction_route.py": worker.git_blob_sha1(payload)}}
            commits = {**worker.COMMITS, repo: "1" * 40}
            data = archive({"core_lite/transaction_route.py": payload})
            with (
                mock.patch.object(worker, "ANCHORS", anchors | {k:v for k,v in worker.ANCHORS.items() if k != repo}),
                mock.patch.object(worker, "COMMITS", commits),
                mock.patch.object(worker, "fetch_public_archive", return_value=data),
            ):
                row = worker.ensure_public_repo(base, repo)
            self.assertEqual(row["state"], "MATERIALIZED_VERIFIED")
            self.assertTrue((base / "Data-Continuation/core-lite/core_lite/transaction_route.py").is_file())

    def test_private_receipt_must_be_sanitized_and_commit_bound(self):
        repo = "StegVerse-Labs/StegCore"
        good = {
            "schema": worker.RECEIPT_SCHEMA,
            "operation_class": "MATERIALIZE_SOURCE_ARCHIVE",
            "repository": repo,
            "result": {"status": "MATERIALIZED", "commit_sha": worker.COMMITS[repo]},
            "credential_authority": "TV/TVC",
            "credential_value_exposed": False,
            "non_tv_tvc_secret_or_token_used": False,
            "scope_expanded": False,
            "merge_performed": False,
        }
        worker.validate_private_receipt(good, repo)
        bad = dict(good)
        bad["credential_value_exposed"] = True
        with self.assertRaisesRegex(RuntimeError, "credential exposure"):
            worker.validate_private_receipt(bad, repo)

    def test_hosted_or_credential_environment_rejected_before_work(self):
        with mock.patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "hosted environments"):
                worker.execute({})
        with mock.patch.dict("os.environ", {"TVC_EPHEMERAL_GITHUB_TOKEN": "x"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "credential-bearing"):
                worker.execute({})

    def test_safe_extract_rejects_path_escape(self):
        out = io.BytesIO()
        with tarfile.open(fileobj=out, mode="w:gz") as tf:
            info = tarfile.TarInfo("repo-root/../../escape")
            data = b"x"
            info.size = 1
            tf.addfile(info, io.BytesIO(data))
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(RuntimeError):
                worker.safe_extract_archive(out.getvalue(), Path(td) / "repo")


if __name__ == "__main__":
    unittest.main()
