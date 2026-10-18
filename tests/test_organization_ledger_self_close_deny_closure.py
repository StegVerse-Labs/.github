"""The self-close step of organization-ledger-transition.yml on a DENY closure.

H36 D1 (StegVerse-org/.github#162): ``intr_destination_ingress.py --self-close``
returns 1 for a DENY closure. The step runs under ``set -euo pipefail``, so that
return ends the step before the closure-summary heredoc runs, and the
``SELF_CLOSURE_NOT_ALLOW`` six-field message is never printed.

This test runs the step's own shell, as written in the workflow, with bash. The
ingress script is a stub that writes a DENY closure and exits 1, the way the
real script does. ``python`` resolves to this interpreter. Temporary
directories only; no ledger ref is read or written.

KNOWN FAILING. It is recorded in data/test-suite-baseline.json ``known_failing``
so the ratchet reports it rather than hiding it. It needs both:
- StegVerse-Labs/.github#3207, which adds the SELF_CLOSURE_NOT_ALLOW message; and
- the D1 fix: ``|| true`` on the ingress call plus a SELF_CLOSURE_RESULT_ABSENT
  guard for a missing result (the StegVerse-org/.github#184 pattern).
Once both are on main the ratchet reports it NEWLY_PASSING; remove the baseline
row then.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "organization-ledger-transition.yml"
STEP = "- name: Append the diagnostic self-closure to the repository and organization ledgers"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
DENY_PREDICATE = "SUBMISSION_IS_AN_ECOSYSTEM_COMMUNICATION"

STUB_INGRESS = """\
import argparse, json, sys
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument("--self-close", action="store_true")
parser.add_argument("--hb-epoch")
parser.add_argument("--communication-id")
parser.add_argument("--packet-id")
parser.add_argument("--registry")
parser.add_argument("--out", type=Path)
args = parser.parse_args()
closure = {
    "disposition": "DENY",
    "communication_id": args.communication_id,
    "failed_predicate": %r,
    "detail": "payload is not an object",
    "federation_directory_consulted": False,
    "peer_enumerated": False,
}
args.out.parent.mkdir(parents=True, exist_ok=True)
args.out.write_text(json.dumps(closure), encoding="utf-8")
print(json.dumps(closure, sort_keys=True))
sys.exit(1)
""" % DENY_PREDICATE


def self_close_step_script() -> str:
    """Return the ``run: |`` body of the self-close step, dedented."""
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    start = next(index for index, line in enumerate(lines) if line.strip() == STEP)
    run = next(index for index in range(start + 1, len(lines)) if lines[index].strip() == "run: |")
    body = []
    for line in lines[run + 1:]:
        if line.strip().startswith("- name:") or line.strip().startswith("- uses:"):
            break
        body.append(line)
    return textwrap.dedent("\n".join(body)).strip() + "\n"


class SelfCloseDenyClosure(unittest.TestCase):
    def test_deny_closure_prints_the_six_field_self_closure_not_allow_block(self):
        bash = shutil.which("bash")
        self.assertIsNotNone(bash, "bash is required to execute the workflow step")
        script = self_close_step_script()
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp, "work")
            (work / "resident-runtime").mkdir(parents=True)
            (work / "resident-runtime" / "intr_destination_ingress.py").write_text(
                STUB_INGRESS, encoding="utf-8")
            (work / "org-boundary" / "registry").mkdir(parents=True)
            (work / "org-boundary" / "registry" / "services.json").write_text("{}", encoding="utf-8")
            shim = Path(tmp, "bin")
            shim.mkdir()
            (shim / "python").write_text('#!/bin/sh\nexec "%s" "$@"\n' % sys.executable, encoding="utf-8")
            (shim / "python").chmod(0o755)
            runner_temp = Path(tmp, "runner")
            runner_temp.mkdir()
            env = dict(
                os.environ,
                PATH=str(shim) + os.pathsep + os.environ.get("PATH", ""),
                GITHUB_WORKSPACE=str(work),
                RUNNER_TEMP=str(runner_temp),
                LEDGER_REF="refs/stegverse/organization-ledger",
                REPO_LEDGER_NAMESPACE="repository-ledger/StegVerse-Labs/.github",
                HB_EPOCH="7",
                CLOSURE_COMMUNICATION_ID="self-closure-deny-001",
                CLOSURE_PACKET_ID="intr-destination-self-closure",
            )
            run = subprocess.run([bash, "-c", script], cwd=work, env=env,
                                 capture_output=True, text=True, timeout=60)

        # A DENY closure still fails the step: nothing is published after it.
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        messages = []
        for line in run.stdout.splitlines():
            try:
                message = json.loads(line)
            except ValueError:
                continue
            if isinstance(message, dict) and message.get("failure_code") == "SELF_CLOSURE_NOT_ALLOW":
                messages.append(message)
        self.assertEqual(len(messages), 1,
                         "SELF_CLOSURE_NOT_ALLOW was not printed on a DENY closure; stdout:\n"
                         + run.stdout + "\nstderr:\n" + run.stderr)
        message = messages[0]
        self.assertEqual(message.get("disposition"), "DENY")
        for field in SIX_FIELDS:
            self.assertIsInstance(message.get(field), str, (field, message))
            self.assertTrue(message[field].strip(), (field, message))
        self.assertEqual(message["failed_predicate"], DENY_PREDICATE)
        self.assertEqual(message["retry_entrypoint"], ".github/workflows/organization-ledger-transition.yml")


if __name__ == "__main__":
    unittest.main()
