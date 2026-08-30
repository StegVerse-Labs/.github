import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "consume_cross_framework_current_basis_v04_request.py"
SPEC = importlib.util.spec_from_file_location("current_basis_consumer", MODULE_PATH)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class CurrentBasisResidentConsumerTests(unittest.TestCase):
    def request(self):
        return json.loads(
            (ROOT / "control" / "resident-execution-request.d" / "cross-framework-current-basis-v04-001.json").read_text(encoding="utf-8")
        )

    def test_request_contract_validates(self):
        MOD.validate_request(self.request())

    def test_hosted_environment_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "hosted environment"):
            MOD.clean_env({"PATH": "/bin", "HOME": "/tmp", "GITHUB_ACTIONS": "true"})

    def test_github_credential_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "forbidden credential"):
            MOD.clean_env({"PATH": "/bin", "HOME": "/tmp", "GITHUB_TOKEN": "not-a-runtime-authority"})

    def test_missing_local_source_roots_blocks_without_execution(self):
        calls = []

        def runner(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("runner must not be called when roots are missing")

        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            req_path = runtime / MOD.REQUEST_REL
            req_path.parent.mkdir(parents=True, exist_ok=True)
            req_path.write_text(json.dumps(self.request()), encoding="utf-8")
            result = MOD.consume(
                ROOT,
                runtime,
                runner=runner,
                env={"PATH": "/bin", "HOME": td},
            )
            self.assertEqual(result["state"], "BLOCKED_LOCAL_SOURCE_PACKAGE_NOT_OBSERVED")
            self.assertFalse(result["runtime_execution_attempted"])
            self.assertFalse(result["user_action_required"])
            self.assertFalse(result["second_machine_required"])
            self.assertEqual(calls, [])


    def test_canonical_materialization_root_is_discovered_without_four_explicit_env_vars(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "source"
            expected = {
                "STEGVERSE_SDK_SOURCE_ROOT": base / "components/sdk",
                "STEGVERSE_STEGCORE_SOURCE_ROOT": base / "components/stegcore",
                "STEGVERSE_CORE_LITE_SOURCE_ROOT": base / "components/core-lite",
                "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": base / "components/master-records",
            }
            for path in expected.values():
                path.mkdir(parents=True, exist_ok=True)
            roots, missing = MOD.source_roots({
                MOD.SOURCE_MATERIALIZATION_ROOT_ENV: str(base),
            })
            self.assertEqual(missing, [])
            self.assertEqual(roots, {key: path.resolve() for key, path in expected.items()})

    def test_explicit_component_root_overrides_canonical_default(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "source"
            explicit = Path(td) / "sdk-explicit"
            explicit.mkdir(parents=True)
            for rel in ("components/stegcore", "components/core-lite", "components/master-records"):
                (base / rel).mkdir(parents=True, exist_ok=True)
            roots, missing = MOD.source_roots({
                MOD.SOURCE_MATERIALIZATION_ROOT_ENV: str(base),
                "STEGVERSE_SDK_SOURCE_ROOT": str(explicit),
            })
            self.assertEqual(missing, [])
            self.assertEqual(roots["STEGVERSE_SDK_SOURCE_ROOT"], explicit.resolve())


    def test_exact_source_identity_verifier_accepts_bound_local_blobs(self):
        original = MOD.EXPECTED_SOURCE_BLOBS
        try:
            with tempfile.TemporaryDirectory() as td:
                base = Path(td)
                roots = {}
                expected = {}
                for idx, key in enumerate(MOD.REQUIRED_ROOT_ENV):
                    root = base / key.lower()
                    root.mkdir(parents=True)
                    rel = f"fixture-{idx}.txt"
                    raw = f"fixture-{idx}".encode("utf-8")
                    (root / rel).write_bytes(raw)
                    roots[key] = root
                    expected[key] = {rel: MOD.git_blob_sha1(raw)}
                MOD.EXPECTED_SOURCE_BLOBS = expected
                observed, mismatches = MOD.verify_exact_source_identity(roots)
                self.assertEqual(mismatches, [])
                self.assertEqual(observed, expected)
        finally:
            MOD.EXPECTED_SOURCE_BLOBS = original

    def test_exact_source_identity_verifier_reports_drift_without_execution(self):
        original = MOD.EXPECTED_SOURCE_BLOBS
        try:
            with tempfile.TemporaryDirectory() as td:
                base = Path(td)
                roots = {}
                expected = {}
                for idx, key in enumerate(MOD.REQUIRED_ROOT_ENV):
                    root = base / key.lower()
                    root.mkdir(parents=True)
                    rel = f"fixture-{idx}.txt"
                    raw = f"fixture-{idx}".encode("utf-8")
                    (root / rel).write_bytes(raw)
                    roots[key] = root
                    expected[key] = {rel: MOD.git_blob_sha1(raw)}
                first = MOD.REQUIRED_ROOT_ENV[0]
                rel = next(iter(expected[first]))
                expected[first][rel] = "0" * 40
                MOD.EXPECTED_SOURCE_BLOBS = expected
                observed, mismatches = MOD.verify_exact_source_identity(roots)
                self.assertEqual(len(mismatches), 1)
                self.assertEqual(mismatches[0]["root"], first)
                self.assertNotEqual(observed[first][rel], expected[first][rel])
        finally:
            MOD.EXPECTED_SOURCE_BLOBS = original


    def _build_package(self, key, files):
        rows = []
        payloads = []
        for rel, raw in sorted(files.items()):
            digest = MOD._sha256_bytes(raw)
            row = {"path": rel, "sha256": digest, "size": len(raw)}
            rows.append(row)
            payloads.append({**row, "content_base64": __import__("base64").b64encode(raw).decode("ascii")})
        bundle = MOD._sha256_bytes(MOD._canonical_bytes(rows))
        return {
            "schema": MOD.PACKAGE_SCHEMA,
            "package_version": MOD.PACKAGE_VERSION,
            "component_id": MOD.COMPONENT_IDS[key],
            "source_identity": "sha256:" + bundle,
            "credential_material_included": False,
            "manifest": {"file_count": len(rows), "source_bundle_sha256": bundle, "files": rows},
            "files": payloads,
            "authority_effect": "NONE_SOURCE_TRANSPORT_ONLY",
        }

    def test_local_source_package_repairs_missing_component_without_network_or_credentials(self):
        original = MOD.EXPECTED_SOURCE_BLOBS
        try:
            with tempfile.TemporaryDirectory() as td:
                base = Path(td)
                materialization = base / "source"
                package_store = base / "packages"
                key = "STEGVERSE_SDK_SOURCE_ROOT"
                files = {
                    "scripts/run_cross_framework_current_basis_v04.py": b"harness",
                    "inspection/examples/cross-framework-current-basis-request.draft.json": b"manifest",
                }
                MOD.EXPECTED_SOURCE_BLOBS = {
                    **original,
                    key: {rel: MOD.git_blob_sha1(raw) for rel, raw in files.items()},
                }
                package = self._build_package(key, files)
                package_path = package_store / MOD.PACKAGE_SLUGS[key] / "package.json"
                package_path.parent.mkdir(parents=True)
                package_path.write_text(json.dumps(package), encoding="utf-8")
                env = {
                    MOD.SOURCE_MATERIALIZATION_ROOT_ENV: str(materialization),
                    MOD.SOURCE_PACKAGE_ROOT_ENV: str(package_store),
                }
                repaired, needs = MOD.repair_from_local_packages(env, [key])
                self.assertEqual(needs, [])
                self.assertEqual(repaired[0]["state"], "LOCAL_SOURCE_PACKAGE_MATERIALIZED")
                self.assertFalse(repaired[0]["network_source_fetch_performed"])
                self.assertFalse(repaired[0]["credential_read_or_acquired"])
                target = materialization / MOD.DEFAULT_COMPONENT_ROOTS[key]
                self.assertEqual((target / "scripts/run_cross_framework_current_basis_v04.py").read_bytes(), b"harness")
                self.assertEqual(MOD._component_mismatches(key, target), [])
        finally:
            MOD.EXPECTED_SOURCE_BLOBS = original

    def test_local_source_package_can_replace_stale_component_atomically(self):
        original = MOD.EXPECTED_SOURCE_BLOBS
        try:
            with tempfile.TemporaryDirectory() as td:
                base = Path(td)
                materialization = base / "source"
                package_store = base / "packages"
                key = "STEGVERSE_STEGCORE_SOURCE_ROOT"
                target = materialization / MOD.DEFAULT_COMPONENT_ROOTS[key]
                stale = target / "src/stegcore/current_basis.py"
                stale.parent.mkdir(parents=True, exist_ok=True)
                stale.write_bytes(b"stale")
                files = {"src/stegcore/current_basis.py": b"current"}
                MOD.EXPECTED_SOURCE_BLOBS = {
                    **original,
                    key: {rel: MOD.git_blob_sha1(raw) for rel, raw in files.items()},
                }
                package = self._build_package(key, files)
                package_path = package_store / MOD.PACKAGE_SLUGS[key] / "package.json"
                package_path.parent.mkdir(parents=True)
                package_path.write_text(json.dumps(package), encoding="utf-8")
                env = {
                    MOD.SOURCE_MATERIALIZATION_ROOT_ENV: str(materialization),
                    MOD.SOURCE_PACKAGE_ROOT_ENV: str(package_store),
                }
                repaired, needs = MOD.repair_from_local_packages(env, [key])
                self.assertEqual(needs, [])
                self.assertEqual(repaired[0]["state"], "LOCAL_SOURCE_PACKAGE_MATERIALIZED")
                self.assertEqual(stale.read_bytes(), b"current")
                self.assertEqual(MOD._component_mismatches(key, target), [])
                self.assertFalse((target.parent / ".stegcore.pre-current-basis-v04").exists())
        finally:
            MOD.EXPECTED_SOURCE_BLOBS = original


    def test_package_remediation_never_mutates_explicit_source_root(self):
        original = MOD.EXPECTED_SOURCE_BLOBS
        try:
            with tempfile.TemporaryDirectory() as td:
                base = Path(td)
                materialization = base / "source"
                package_store = base / "packages"
                explicit = base / "explicit-sdk"
                key = "STEGVERSE_SDK_SOURCE_ROOT"
                rel = "scripts/run_cross_framework_current_basis_v04.py"
                stale = explicit / rel
                stale.parent.mkdir(parents=True, exist_ok=True)
                stale.write_bytes(b"stale-explicit")
                expected_raw = b"current-canonical"
                MOD.EXPECTED_SOURCE_BLOBS = {
                    **original,
                    key: {rel: MOD.git_blob_sha1(expected_raw)},
                }
                package = self._build_package(key, {rel: expected_raw})
                package_path = package_store / MOD.PACKAGE_SLUGS[key] / "package.json"
                package_path.parent.mkdir(parents=True)
                package_path.write_text(json.dumps(package), encoding="utf-8")
                env = {
                    MOD.SOURCE_MATERIALIZATION_ROOT_ENV: str(materialization),
                    MOD.SOURCE_PACKAGE_ROOT_ENV: str(package_store),
                    key: str(explicit),
                }
                repaired, needs = MOD.repair_from_local_packages(env, [key])
                self.assertEqual(needs, [])
                self.assertEqual(repaired[0]["state"], "LOCAL_SOURCE_PACKAGE_MATERIALIZED")
                self.assertFalse(repaired[0]["explicit_source_root_mutated"])
                self.assertTrue(repaired[0]["canonical_materialization_root_only"])
                self.assertEqual(stale.read_bytes(), b"stale-explicit")
                canonical = materialization / MOD.DEFAULT_COMPONENT_ROOTS[key] / rel
                self.assertEqual(canonical.read_bytes(), expected_raw)
                roots, missing = MOD.source_roots(env)
                self.assertEqual(missing, [])
                self.assertEqual(roots[key], explicit.resolve())
                observed, mismatches = MOD.verify_exact_source_identity({**{
                    k: materialization / MOD.DEFAULT_COMPONENT_ROOTS[k] for k in MOD.REQUIRED_ROOT_ENV
                }, key: explicit.resolve()})
                self.assertTrue(any(row["root"] == key for row in mismatches))
        finally:
            MOD.EXPECTED_SOURCE_BLOBS = original

    def test_source_package_with_wrong_critical_blob_fails_closed(self):
        original = MOD.EXPECTED_SOURCE_BLOBS
        try:
            with tempfile.TemporaryDirectory() as td:
                base = Path(td)
                package_store = base / "packages"
                key = "STEGVERSE_CORE_LITE_SOURCE_ROOT"
                MOD.EXPECTED_SOURCE_BLOBS = {
                    **original,
                    key: {"core_lite/transaction_route.py": MOD.git_blob_sha1(b"expected")},
                }
                package = self._build_package(key, {"core_lite/transaction_route.py": b"wrong"})
                package_path = package_store / MOD.PACKAGE_SLUGS[key] / "package.json"
                package_path.parent.mkdir(parents=True)
                package_path.write_text(json.dumps(package), encoding="utf-8")
                env = {
                    MOD.SOURCE_MATERIALIZATION_ROOT_ENV: str(base / "source"),
                    MOD.SOURCE_PACKAGE_ROOT_ENV: str(package_store),
                }
                with self.assertRaisesRegex(RuntimeError, "exact frozen-v0.4 execution source"):
                    MOD._materialize_local_package(env, key)
                self.assertFalse((base / "source" / MOD.DEFAULT_COMPONENT_ROOTS[key]).exists())
        finally:
            MOD.EXPECTED_SOURCE_BLOBS = original


    def test_sdk_source_guard_binds_hardened_result_packager(self):
        self.assertEqual(
            MOD.EXPECTED_SOURCE_BLOBS["STEGVERSE_SDK_SOURCE_ROOT"][
                "scripts/package_cross_framework_current_basis_results.py"
            ],
            "5cd6d104d5d08042aa60330ade92370d53fad28a",
        )

    def test_local_publication_packet_is_prepared_without_transport_or_writeback(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            sdk = base / "sdk"
            result_dir = base / "result"
            state_root = base / "state"
            manifest = sdk / "inspection/examples/cross-framework-current-basis-request.draft.json"
            packager = sdk / "scripts/package_cross_framework_current_basis_results.py"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            packager.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text("{}\n", encoding="utf-8")
            packager.write_text("# canonical packager fixture\n", encoding="utf-8")
            result_dir.mkdir(parents=True)

            calls = []
            def runner(command, **kwargs):
                calls.append((command, kwargs))
                output_dir = Path(command[command.index("--output-dir") + 1])
                output_dir.mkdir(parents=True, exist_ok=True)
                (output_dir / "RESULT_PACKET_INDEX.json").write_text(
                    json.dumps({
                        "schema": "stegverse.sdk.cross-framework-result-publication.v1",
                        "frozen_manifest_sha256": MOD.EXPECTED_SHA256,
                        "frozen_manifest_git_blob_sha1": MOD.EXPECTED_BLOB,
                        "github_actions_runtime_authority": False,
                    }) + "\n",
                    encoding="utf-8",
                )
                (output_dir / "artifact.txt").write_text("evidence\n", encoding="utf-8")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            ready = MOD.prepare_local_publication_packet(
                sdk_root=sdk,
                result_dir=result_dir,
                manifest=manifest,
                state_root=state_root,
                runner=runner,
                env={"PATH": "/bin", "HOME": td},
            )
            self.assertEqual(ready["state"], "LOCAL_PACKET_READY_FOR_EVIDENCE_TRANSPORT")
            self.assertFalse(ready["network_transport_performed"])
            self.assertFalse(ready["repository_writeback_performed"])
            self.assertFalse(ready["github_actions_runtime_authority"])
            self.assertFalse(ready["publication_authority"])
            self.assertFalse(ready["credential_read_or_acquired"])
            self.assertTrue(Path(ready["archive"]).is_file())
            self.assertEqual(ready["archive_sha256"], MOD._sha256_file(Path(ready["archive"])))
            self.assertTrue((state_root / MOD.PUBLICATION_READY_FILE).is_file())
            self.assertEqual(len(calls), 1)

    def test_no_request_is_noop(self):
        with tempfile.TemporaryDirectory() as td:
            result = MOD.consume(ROOT, Path(td), env={"PATH": "/bin", "HOME": td})
            self.assertEqual(result["state"], "NO_REQUEST")
            self.assertFalse(result["runtime_execution_attempted"])


if __name__ == "__main__":
    unittest.main()
