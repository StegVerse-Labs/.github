import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


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
            self.assertEqual(result["state"], "BLOCKED_LOCAL_SOURCE_ROOTS_NOT_OBSERVED")
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

    def test_no_request_is_noop(self):
        with tempfile.TemporaryDirectory() as td:
            result = MOD.consume(ROOT, Path(td), env={"PATH": "/bin", "HOME": td})
            self.assertEqual(result["state"], "NO_REQUEST")
            self.assertFalse(result["runtime_execution_attempted"])


if __name__ == "__main__":
    unittest.main()
