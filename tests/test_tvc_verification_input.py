"""The TV/TVC checkout input of the ratchet: pinned, read with the job's own token only, fail closed in six fields.

StegVerse-org/.github#164 (Lane C). scripts/tvc_verification_input.py binds STEGVERSE_TVC_ROOT for the [tvc] sets
only when the checkout is exactly the commit .stegverse/verification-inputs/tvc.json pins; otherwise it prints a
six-field FAIL_CLOSED and binds nothing, so the selector reports those sets as REQUIRED_VERIFICATION_INPUT_UNAVAILABLE.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".stegverse/verification-inputs/tvc.json"
WORKFLOW = ROOT / ".github/workflows/test-suite-ratchet.yml"
SPEC = ROOT / ".stegverse/test-set-spec.json"


def _load():
    spec = importlib.util.spec_from_file_location("tvc_verification_input", ROOT / "scripts/tvc_verification_input.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


t = _load()


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(subprocess.run, ["rm", "-rf", str(self.tmp)])
        self.repo = self.tmp / "checkout"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        for rel in ("scripts/tv_credential_sign_export_resident.py", "scripts/tv_credential_verify_export_resident.py"):
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / rel).write_text("# stand-in\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "c")
        self.commit = git(self.repo, "rev-parse", "HEAD")
        self.manifest = self.write(dict(json.loads(MANIFEST.read_text(encoding="utf-8")), commit=self.commit))

    def write(self, m, reseal=True):
        m = copy.deepcopy(m)
        if reseal:
            m["manifest_sha256"] = t.seal(m)
        path = self.tmp / f"tvc-{len(list(self.tmp.glob('tvc-*.json')))}.json"
        path.write_text(json.dumps(m), encoding="utf-8")
        return path

    def assertSix(self, out, code):
        self.assertEqual(out["disposition"], "FAIL_CLOSED")
        self.assertEqual(out["failure_code"], code)
        for field in t.SIX:
            self.assertTrue(out[field], field)
        self.assertEqual(out["lowest_supported_mode"], "E0")


class ManifestTests(Base):
    def test_the_committed_manifest_pins_tvc_to_an_exact_commit_and_its_seal_re_derives(self):
        m, bad = t.load_manifest(MANIFEST)
        self.assertIsNone(bad)
        self.assertEqual(m["repository"], "StegVerse-Labs/TVC")
        self.assertRegex(m["commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(m["env"], "STEGVERSE_TVC_ROOT")
        self.assertIn("scripts/tv_credential_sign_export_resident.py", m["required_files"])

    def test_a_moving_ref_is_never_a_pin(self):
        raw = json.loads(self.manifest.read_text())
        out = t.pin(self.write(dict(raw, commit="main")), None)
        self.assertSix(out, "TVC_VERIFICATION_INPUT_MANIFEST_INVALID")
        self.assertIn("moving ref", out["required_evidence_or_repair"])

    def test_a_manifest_edited_without_its_seal_is_refused(self):
        raw = json.loads(self.manifest.read_text())
        raw["commit"] = "0" * 40
        self.assertSix(t.pin(self.write(raw, reseal=False), None), "TVC_VERIFICATION_INPUT_MANIFEST_INVALID")

    def test_pin_writes_the_checkout_inputs_or_manifest_invalid(self):
        out_file = self.tmp / "out"
        self.assertEqual(t.pin(self.manifest, out_file)["disposition"], "ALLOW")
        lines = out_file.read_text().splitlines()
        self.assertIn(f"commit={self.commit}", lines)
        self.assertIn("manifest=ok", lines)
        bad = self.tmp / "missing.json"
        out_file.write_text("")
        self.assertSix(t.pin(bad, out_file), "TVC_VERIFICATION_INPUT_MANIFEST_UNREADABLE")
        self.assertEqual(out_file.read_text().splitlines(), ["manifest=invalid"])


class BindTests(Base):
    def test_unreadable_by_the_job_token_routes_the_read_credential_to_a_tv_tvc_lease_and_binds_nothing(self):
        env = self.tmp / "env"
        out = t.bind(self.manifest, self.repo, False, self.tmp / "dest", env)
        self.assertSix(out, "TVC_VERIFICATION_INPUT_READ_CREDENTIAL_NOT_ISSUED")
        self.assertIn("TVC-PRIVATE-SOURCE-READ-001", out["owning_existing_goal"])
        self.assertIn("never a PAT", out["required_evidence_or_repair"])
        self.assertFalse(env.exists())
        self.assertTrue(self.repo.exists())

    def test_the_exact_pinned_checkout_is_moved_out_and_bound(self):
        env, dest = self.tmp / "env", self.tmp / "inputs" / "tvc"
        out = t.bind(self.manifest, self.repo, True, dest, env)
        self.assertEqual(out["disposition"], "ALLOW")
        self.assertEqual(env.read_text(), f"STEGVERSE_TVC_ROOT={dest}\n")
        self.assertTrue((dest / "scripts/tv_credential_verify_export_resident.py").is_file())
        self.assertFalse(self.repo.exists())

    def test_a_checkout_at_another_commit_is_refused(self):
        (self.repo / "x").write_text("x")
        git(self.repo, "add", "x")
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "moved")
        env = self.tmp / "env"
        self.assertSix(t.bind(self.manifest, self.repo, True, self.tmp / "d", env), "TVC_VERIFICATION_INPUT_PIN_MISMATCH")
        self.assertFalse(env.exists())

    def test_no_checkout_is_a_pin_mismatch_not_a_pass(self):
        self.assertSix(t.bind(self.manifest, self.tmp / "absent", True, self.tmp / "d", None),
                       "TVC_VERIFICATION_INPUT_PIN_MISMATCH")

    def test_a_required_file_absent_at_the_pin_is_refused(self):
        raw = json.loads(self.manifest.read_text())
        raw["required_files"] = raw["required_files"] + ["scripts/not_here.py"]
        self.assertSix(t.bind(self.write(raw), self.repo, True, self.tmp / "d", None),
                       "TVC_VERIFICATION_INPUT_FILE_ABSENT")

    def test_the_cli_exits_zero_and_prints_the_disposition(self):
        r = subprocess.run(["python3", str(ROOT / "scripts/tvc_verification_input.py"), "bind", "--manifest",
                            str(self.manifest), "--checkout", str(self.repo), "--readable", "false",
                            "--dest", str(self.tmp / "d")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertTrue(r.stdout.startswith("TVC_VERIFICATION_INPUT FAIL_CLOSED "))


class WorkflowTests(unittest.TestCase):
    def test_the_ratchet_reads_tvc_with_its_own_token_through_the_pinned_checkout_before_selection(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("scripts/tvc_verification_input.py pin --manifest .stegverse/verification-inputs/tvc.json", text)
        self.assertIn("scripts/tvc_verification_input.py bind --manifest .stegverse/verification-inputs/tvc.json", text)
        self.assertIn("uses: actions/checkout@08eba0b27e820071cde6df949e0beb9ba4906955", text)
        self.assertIn("GH_TOKEN: ${{ github.token }}", text)
        self.assertLess(text.index("tvc_verification_input.py bind"), text.index("scripts/test_set_selection.py select"))
        step = text.split("TV/TVC checkout at the pinned commit", 1)[1].split("- name:", 1)[0]
        self.assertIn("persist-credentials: false", step)
        self.assertIn("ref: ${{ steps.tvc-pin.outputs.commit }}", step)
        self.assertNotIn("token:", step)   # the checkout uses the job's own GITHUB_TOKEN, never a supplied one
        for word in ("secrets.", "continue-on-error"):
            self.assertNotIn(word, text)

    def test_the_tvc_sets_need_the_input_and_are_never_bypassable(self):
        spec = json.loads(SPEC.read_text(encoding="utf-8"))
        self.assertEqual(spec["inputs"]["tvc"]["check"], {"env": "STEGVERSE_TVC_ROOT", "kind": "env_path"})
        self.assertNotIn("bypass", json.dumps(spec["inputs"]["tvc"]).lower())


if __name__ == "__main__":
    unittest.main()
