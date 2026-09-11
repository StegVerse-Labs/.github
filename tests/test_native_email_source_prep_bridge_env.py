from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import refresh_and_execute_resident_task as bridge


class NativeEmailSourcePrepBridgeEnvTests(unittest.TestCase):
    def test_all_four_source_prep_locators_survive_bridge_sanitization(self) -> None:
        expected = {
            "STEGVERSE_SDK_SOURCE_ROOT": "/local/StegVerse-SDK",
            "STEGVERSE_STEGCORE_SOURCE_ROOT": "/local/StegCore",
            "STEGVERSE_CORE_LITE_SOURCE_ROOT": "/local/core-lite",
            "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": "/local/master-records",
        }
        env = bridge.clean_exec_env({
            "PATH": "/bin",
            "HOME": "/home/stegverse",
            **expected,
            "GITHUB_TOKEN": "must-not-survive",
            "GITHUB_ACTIONS": "true",
        })
        for name, value in expected.items():
            self.assertEqual(env.get(name), value)
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("GITHUB_ACTIONS", env)
        self.assertEqual(env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"], "NONE")
        self.assertEqual(env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "TV/TVC")


if __name__ == "__main__":
    unittest.main()
