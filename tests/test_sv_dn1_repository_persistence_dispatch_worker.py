from __future__ import annotations

import base64
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import unittest
from unittest import mock

from workers import sv_dn1_repository_persistence_dispatch_worker as worker


def package_fixture() -> dict:
    rows = []
    for name in worker.FILES:
        raw = ("authentic-" + name + "\n").encode("utf-8")
        rows.append({
            "path": f"{worker.TARGET_ROOT}/{name}",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "size": len(raw),
            "content_base64": base64.b64encode(raw).decode("ascii"),
        })
    body = {
        "schema": "stegverse.sv-dn1.repository-persistence-package/v1",
        "state": "READY_FOR_ADMITTED_REPOSITORY_MUTATION",
        "target_repository": worker.TARGET_REPO,
        "target_ref": worker.TARGET_REF,
        "target_root": worker.TARGET_ROOT,
        "exchange_id": "sha256:" + "a" * 64,
        "manifest_receipt_id": "MR-EXAMPLE",
        "publication_state": "PUBLIC_OBSERVED",
        "observation_class": "LIVE",
        "files": rows,
        "exact_bytes_preserved": True,
        "semantic_rewrite_performed": False,
        "network_fetch_performed": False,
        "credential_used": False,
        "repository_writeback_performed": False,
        "deployment_performed": False,
        "authority_effect": "NONE_PERSISTENCE_PACKAGE_ONLY",
    }
    value = dict(body)
    value["package_sha256"] = worker.sha_bytes(worker.stable_package_bytes(body))
    return value


class PersistenceDispatchTests(unittest.TestCase):
    def test_package_validation_preserves_exact_five_utf8_files(self):
        package = package_fixture()
        package_sha, files = worker.validate_package(package)
        self.assertEqual(package_sha, package["package_sha256"])
        self.assertEqual(set(files), set(worker.FILES))
        for name in worker.FILES:
            self.assertEqual(hashlib.sha256(files[name]["content_utf8"].encode()).hexdigest(), files[name]["sha256"])

    def test_apply_warrant_is_exact_and_credential_free(self):
        package = package_fixture()
        package_sha, files = worker.validate_package(package)
        inspected = {
            files[name]["path"]: {
                "path": files[name]["path"],
                "state": "ABSENT" if name == "result-receipt.json" else "PRESENT",
                "sha256": None if name == "result-receipt.json" else "b" * 64,
            }
            for name in worker.FILES
        }
        warrant = worker.apply_warrant(
            package_sha, files, "c" * 40, inspected,
            datetime(2026, 8, 31, 13, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(warrant["operation_class"], "APPLY_BOUNDED_FILE_SET")
        self.assertEqual(warrant["repository"], worker.TARGET_REPO)
        self.assertEqual(warrant["expected_base_sha"], "c" * 40)
        self.assertEqual(warrant["maximum_file_count"], 5)
        self.assertEqual(len(warrant["files"]), 5)
        self.assertEqual(warrant["credential_authority"], "TV/TVC")
        self.assertFalse(warrant["secret_values_present"])
        self.assertNotIn("consumer_credential_present", warrant)
        self.assertNotIn("source_package_sha256", warrant)
        self.assertNotIn("authority_effect", warrant)
        by_path = {row["path"]: row for row in warrant["files"]}
        self.assertIsNone(by_path[f"{worker.TARGET_ROOT}/result-receipt.json"]["expected_source_sha256"])
        self.assertEqual(by_path[f"{worker.TARGET_ROOT}/index.html"]["expected_source_sha256"], "b" * 64)

    def test_mutation_admission_is_exact_tvc_issue_264_gate(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "admission.json"
            path.write_text(json.dumps({
                "schema": worker.ADMISSION_SCHEMA,
                "state": "ADMITTED",
                "issue": 264,
                "repository": worker.TARGET_REPO,
                "credential_authority": "TV/TVC",
                "consumer_credential_allowed": False,
                "allowed_operation_classes": ["APPLY_BOUNDED_FILE_SET", "OPEN_PULL_REQUEST"],
            }))
            self.assertTrue(worker.mutation_admitted(path))
            bad = json.loads(path.read_text())
            bad["issue"] = 263
            path.write_text(json.dumps(bad))
            self.assertFalse(worker.mutation_admitted(path))

    def test_execute_stages_apply_but_does_not_submit_before_tvc_admission(self):
        package = package_fixture()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            persist = root / "persist"
            bound = root / "bound"
            persist.joinpath("packages").mkdir(parents=True)
            persist.joinpath("packages/latest.json").write_text(json.dumps(package))
            fixed = datetime(2026, 8, 31, 13, 0, tzinfo=timezone.utc)
            request = worker.inspect_request(package["package_sha256"], fixed)
            worker.write_once(bound / "staged/inspection-request.json", request)
            receipt = {
                "schema": worker.INSPECT_RECEIPT_SCHEMA,
                "request_id": request["request_id"],
                "request_sha256": worker.canonical_hash(request),
                "repository": worker.TARGET_REPO,
                "base_ref": worker.TARGET_REF,
                "base_sha": "d" * 40,
                "paths": [
                    {"path": p, "state": "PRESENT", "sha256": "e" * 64, "size": 1}
                    for p in request["paths"]
                ],
                "credential_authority": "TV/TVC",
                "credential_value_exposed": False,
                "consumer_credential_present": False,
                "non_tv_tvc_secret_or_token_used": False,
            }
            worker.write_once(bound / f"inbox/{request['request_id']}.json", receipt)
            invocation = {
                "schema": "stegverse.worker-invocation/v0.1",
                "task": {
                    "task_id": worker.TASK_ID,
                    "worker_id": worker.WORKER_ID,
                    "claim_id": "claim-1",
                    "heartbeat_timing": {"fencing_token": 31},
                },
            }
            with (
                mock.patch.dict("os.environ", {
                    worker.PERSIST_ENV: str(persist),
                    worker.BOUND_ENV: str(bound),
                    worker.ADMISSION_ENV: str(root / "missing-admission.json"),
                    "PATH": "/usr/bin",
                }, clear=True),
                mock.patch.object(worker, "datetime") as dt,
            ):
                dt.now.return_value = fixed
                dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
                with self.assertRaisesRegex(worker.Pending, "TVC#264"):
                    worker.execute(invocation)

            staged_apply = json.loads((bound / "staged/apply-warrant.json").read_text())
            self.assertEqual(staged_apply["operation_class"], "APPLY_BOUNDED_FILE_SET")
            self.assertFalse((bound / f"outbox/{staged_apply['operation_id']}.json").exists())

    def test_hosted_or_credential_environment_fails_closed(self):
        with mock.patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "hosted environment"):
                worker.execute({})
        with mock.patch.dict("os.environ", {"TVC_EPHEMERAL_GITHUB_TOKEN": "secret"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "credential-bearing environment"):
                worker.execute({})


if __name__ == "__main__":
    unittest.main()
