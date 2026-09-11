import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "refresh_and_dispatch_resident_requests.py"


def load_module():
    spec = importlib.util.spec_from_file_location("sdk_workspace_portable_dispatch", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class SDKWorkspacePortableDispatchTests(unittest.TestCase):
    def test_exact_sdk_workspace_selectors_are_admitted_without_changing_default(self):
        mod = load_module()
        self.assertEqual(mod.TARGET_CONSUMER, "cross_framework_current_basis_v04")
        self.assertIn("sdk_workspace_external_collab_client_secret_reseal", mod.ALLOWED_TARGET_CONSUMERS)
        self.assertIn("sdk_workspace_external_collab_consent_listener", mod.ALLOWED_TARGET_CONSUMERS)

    def test_listener_nonsecret_inputs_cross_portable_bridge_and_secret_names_do_not(self):
        mod = load_module()
        source = {
            "PATH": "/usr/bin",
            "HOME": "/tmp/home",
            "STEGVERSE_GOOGLE_DRIVE_CLIENT_ID": "public-client-id.apps.googleusercontent.com",
            "STEGVERSE_OWNER_BINDING_DIGEST": "a" * 64,
            "STEGVERSE_STEGFIN_SOURCE_ROOT": "/srv/stegverse/stegfin-governance",
            "UNDECLARED_SECRET": "must-not-cross",
        }
        env = mod.clean_exec_env(source)
        self.assertEqual(env["STEGVERSE_GOOGLE_DRIVE_CLIENT_ID"], source["STEGVERSE_GOOGLE_DRIVE_CLIENT_ID"])
        self.assertEqual(env["STEGVERSE_OWNER_BINDING_DIGEST"], source["STEGVERSE_OWNER_BINDING_DIGEST"])
        self.assertEqual(env["STEGVERSE_STEGFIN_SOURCE_ROOT"], source["STEGVERSE_STEGFIN_SOURCE_ROOT"])
        self.assertNotIn("UNDECLARED_SECRET", env)
        self.assertEqual(env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "TV/TVC")
        self.assertEqual(env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"], "NONE")
        with self.assertRaises(RuntimeError):
            mod.clean_exec_env({**source, "GITHUB_TOKEN": "forbidden"})

    def test_each_sdk_workspace_selector_remains_exact_one_consumer_dispatch(self):
        for selector in (
            "sdk_workspace_external_collab_client_secret_reseal",
            "sdk_workspace_external_collab_consent_listener",
        ):
            with self.subTest(selector=selector), tempfile.TemporaryDirectory() as td:
                mod = load_module()
                root = Path(td)
                source = root / "source"
                runtime = root / "runtime"
                source.mkdir()
                runtime.mkdir()

                def fake_refresh(source_root, runtime_root):
                    dispatcher = runtime_root / mod.DISPATCHER_REL
                    dispatcher.parent.mkdir(parents=True, exist_ok=True)
                    dispatcher.write_text("# dispatcher placeholder\n", encoding="utf-8")
                    return {
                        "network_fetch_performed": False,
                        "credential_read_or_acquired": False,
                        "mutable_runtime_state_preserved": True,
                    }

                def fake_runner(command, cwd, **kwargs):
                    self.assertEqual(command[-2:], ["--only-consumer", selector])
                    dispatch_path = Path(cwd) / mod.DISPATCH_RECEIPT_REL
                    dispatch_path.parent.mkdir(parents=True, exist_ok=True)
                    dispatch_path.write_text(json.dumps({
                        "state": "DISPATCH_COMPLETE",
                        "selection_scope": "EXACT_SELECTOR",
                        "selected_consumers": [selector],
                        "consumer_count": 1,
                    }) + "\n", encoding="utf-8")
                    return SimpleNamespace(returncode=0, stdout="", stderr="")

                mod.refresh = fake_refresh
                receipt = mod.refresh_and_dispatch(
                    source,
                    runtime,
                    target_consumer=selector,
                    runner=fake_runner,
                    env={
                        "PATH": "/usr/bin",
                        "HOME": "/tmp/home",
                        "STEGVERSE_TVC_ROOT": "/srv/stegverse/TVC",
                        "STEGVERSE_GOOGLE_DRIVE_CLIENT_ID": "public-client-id.apps.googleusercontent.com",
                        "STEGVERSE_OWNER_BINDING_DIGEST": "b" * 64,
                        "STEGVERSE_STEGFIN_SOURCE_ROOT": "/srv/stegverse/stegfin-governance",
                    },
                )
                self.assertEqual(receipt["state"], "REFRESH_AND_DISPATCH_COMPLETE")
                self.assertEqual(receipt["target_consumer"], selector)
                self.assertTrue(receipt["exact_consumer_selection_observed"])
                self.assertFalse(receipt["unrelated_consumers_dispatched"])
                self.assertFalse(receipt["bridge_grants_execution_authority"])
                self.assertFalse(receipt["bridge_mints_claim_or_fence"])
                self.assertFalse(receipt["source_refresh_is_runtime_execution"])
                self.assertEqual(receipt["github_token_runtime_authority"], "NONE")
                self.assertEqual(receipt["credential_authority"], "TV/TVC")


if __name__ == "__main__":
    unittest.main()
