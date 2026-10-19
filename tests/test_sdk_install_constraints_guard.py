"""Every Labs workflow SDK install pins the SDK's transitive set at the installed commit (R-P9)."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_sdk_install_constraints as guard  # noqa: E402

SHA = "4f6aba776d7d0879d9423d0922ce1b081470bd5e"
GOOD = f"""      - name: Install the pinned StegVerse SDK
        run: |
          SDK_SHA={SHA}
          curl -fsSL "https://github.com/StegVerse-org/StegVerse-SDK/archive/${{SDK_SHA}}.tar.gz" -o /tmp/s.tgz
          tar -xzf /tmp/s.tgz -C /tmp/stegverse-sdk --strip-components=1
          export PIP_CONSTRAINT=/tmp/stegverse-sdk/constraints/sdk-install.txt
          python -m pip install --quiet /tmp/stegverse-sdk
      - name: Next
        run: echo ok
"""


def defects(text):
    with tempfile.TemporaryDirectory() as temp:
        Path(temp, "w.yml").write_text(text, encoding="utf-8")
        return guard.check(Path(temp))


class SdkInstallConstraintsTests(unittest.TestCase):
    def test_committed_workflows_pass_and_the_guard_is_not_vacuous(self):
        checked, failures = guard.check()
        self.assertEqual(failures, [])
        self.assertGreaterEqual(checked, 1)

    def test_constraint_from_the_installed_archive_or_its_raw_file_passes(self):
        self.assertEqual(defects(GOOD), (1, []))
        for raw in ("${SDK_SHA}", SHA):
            text = GOOD.replace("/tmp/stegverse-sdk/constraints/sdk-install.txt",
                                guard.RAW.format(raw))
            with self.subTest(raw=raw):
                self.assertEqual(defects(text), (1, []))

    def test_an_sdk_install_without_the_constraint_at_its_commit_fails_closed(self):
        other = "0" * 40
        cases = {
            "no constraint": GOOD.replace("          export PIP_CONSTRAINT=/tmp/stegverse-sdk/constraints/sdk-install.txt\n", ""),
            "constraint after the install": GOOD.replace(
                "          export PIP_CONSTRAINT=/tmp/stegverse-sdk/constraints/sdk-install.txt\n", "").replace(
                "/tmp/stegverse-sdk\n      - name: Next",
                "/tmp/stegverse-sdk\n          export PIP_CONSTRAINT=/tmp/stegverse-sdk/constraints/sdk-install.txt\n      - name: Next"),
            "constraint at another commit": GOOD.replace("/tmp/stegverse-sdk/constraints/sdk-install.txt",
                                                         guard.RAW.format(other)),
            "constraint from another directory": GOOD.replace("export PIP_CONSTRAINT=/tmp/stegverse-sdk/",
                                                              "export PIP_CONSTRAINT=/tmp/elsewhere/"),
            "commit not fixed": GOOD.replace(f"SDK_SHA={SHA}", "SDK_SHA=main"),
            "archive not at SDK_SHA": GOOD.replace("archive/${SDK_SHA}", f"archive/{other}"),
        }
        for name, text in cases.items():
            with self.subTest(case=name):
                checked, failures = defects(text)
                self.assertEqual(checked, 1)
                self.assertTrue(failures, name)

    def test_steps_that_do_not_install_the_sdk_are_not_judged(self):
        self.assertEqual(defects("      - run: python -m pip install pytest\n"), (0, []))


if __name__ == "__main__":
    unittest.main()
