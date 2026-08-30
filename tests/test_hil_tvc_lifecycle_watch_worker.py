from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from workers import hil_sovereign_receiver_worker as mod


class Proc:
    pid = 4321


class HILTVCWatchLaunchTests(unittest.TestCase):
    def test_launches_bounded_watcher_without_github_credentials(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            watcher=root/mod.TVC_WATCHER_REL
            watcher.parent.mkdir(parents=True)
            watcher.write_text("#!/usr/bin/env python3\n")
            captured={}
            def fake_popen(command, **kwargs):
                captured["command"]=command
                captured["kwargs"]=kwargs
                return Proc()
            env={
                "GITHUB_TOKEN":"forbidden",
                "GH_TOKEN":"forbidden",
                "STEGVERSE_TVC_ROOT":"/srv/stegverse/repos/StegVerse-Labs/TVC",
            }
            with patch.dict(os.environ, env, clear=True), patch.object(mod.subprocess,"Popen",side_effect=fake_popen):
                pid=mod.launch_tvc_lifecycle_watch(root)
            self.assertEqual(pid,4321)
            self.assertIn("--runtime-root",captured["command"])
            self.assertEqual(captured["kwargs"]["cwd"],root)
            self.assertNotIn("start_new_session",captured["kwargs"])
            self.assertNotIn("GITHUB_TOKEN",captured["kwargs"]["env"])
            self.assertNotIn("GH_TOKEN",captured["kwargs"]["env"])
            self.assertEqual(captured["kwargs"]["env"]["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"],"TV/TVC")
            self.assertEqual(captured["kwargs"]["env"]["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"],"NONE")
            self.assertEqual((root/mod.TVC_WATCH_PID_REL).read_text().strip(),"4321")

    def test_missing_watcher_returns_none(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(mod.launch_tvc_lifecycle_watch(Path(td)))


if __name__=="__main__":
    unittest.main()
