"""Master Records submission publishes only the organization ledger's own receipt (VALIDATOR row 4).

submit_org_transition_to_master_records.py checked a receipt's schema and
owner, then stamped the frame from its hb_reference. An org receipt whose
hb_reference was edited to CARRIED (head ff...ff) with its receipt_sha256 left
stale was published, carrying the forged provenance. Before anything is built
it now verifies the receipt's self-hash, requires it to be, byte-for-byte, the
receipt reachable from the organization ledger's HEAD, and runs the kernel's
CARRIED check. Every refusal is six fields and publishes 0 frames.

Source validation only. No authority effect is claimed.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.ledgered_org_receipt import ledgered_org_receipt

ROOT = Path(__file__).resolve().parents[1]
SUBMITTER = ROOT / "resident-runtime/submit_org_transition_to_master_records.py"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")
GENESIS = {"mode": "ESTABLISH_GENESIS", "node_ref": "test-node", "predecessor": None}


def sha(value):
    import hashlib
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                                 ensure_ascii=False).encode()).hexdigest()


class SubmissionProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.work = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.work, True)
        self.path, self.receipt, self.env = ledgered_org_receipt(self.work, 4096)
        self.standing = self.work / "standing.json"
        self.standing.write_text(json.dumps(GENESIS))
        self.mesh = self.work / "mesh"

    def submit(self, receipt, env=None):
        path = self.work / "submitted.json"
        path.write_text(json.dumps(receipt))
        return subprocess.run([sys.executable, "-B", str(SUBMITTER), "--org-receipt", str(path),
                               "--predecessor-ecosystem-state-sha256", "sha256:" + "1" * 64,
                               "--successor-ecosystem-state-sha256", "sha256:" + "2" * 64,
                               "--standing", str(self.standing), "--mesh-root", str(self.mesh)],
                              capture_output=True, text=True, env=env or self.env, cwd=str(self.work), timeout=120)

    def frames(self):
        return sorted((self.mesh / "frames.d").glob("*.json")) if (self.mesh / "frames.d").is_dir() else []

    def assertRefusedWithNoFrame(self, completed, code):
        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)
        record = json.loads(completed.stdout.strip().splitlines()[-1])
        self.assertEqual((record["disposition"], record["failure_code"]), ("FAIL_CLOSED", code))
        for field in SIX:
            self.assertTrue(str(record.get(field) or "").strip(), field)
        self.assertIs(record["consequence_committed"], False)
        self.assertEqual(self.frames(), [], "a refused receipt publishes no frame")

    def test_the_ledgers_own_receipt_is_published(self):
        completed = self.submit(self.receipt)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(len(self.frames()), 1)

    def test_a_reference_edited_to_carried_with_a_stale_hash_is_refused(self):
        forged = json.loads(json.dumps(self.receipt))
        forged["hb_reference"].update({"source": "ORGANIZATION_LEDGER_HEAD", "head_receipt_sha": "ff" * 32})
        self.assertRefusedWithNoFrame(self.submit(forged), "CARRIED_REFERENCE_SELF_HASH_MISMATCH")

    def test_a_reference_edited_to_carried_and_rehashed_is_not_the_ledgers_own(self):
        forged = json.loads(json.dumps(self.receipt))
        forged["hb_reference"].update({"source": "ORGANIZATION_LEDGER_HEAD", "head_receipt_sha": "ff" * 32})
        forged["receipt_sha256"] = sha({k: v for k, v in forged.items() if k != "receipt_sha256"})
        self.assertRefusedWithNoFrame(self.submit(forged), "ORGANIZATION_RECEIPT_NOT_ON_LEDGER")

    def test_an_altered_body_is_refused(self):
        altered = dict(self.receipt, boundary_evidence={"injected": True})
        self.assertRefusedWithNoFrame(self.submit(altered), "CARRIED_REFERENCE_SELF_HASH_MISMATCH")

    def test_no_organization_ledger_supplied_is_refused(self):
        env = {k: v for k, v in self.env.items() if k != "STEGVERSE_ORG_LEDGER_ROOT"}
        self.assertRefusedWithNoFrame(self.submit(self.receipt, env), "ORGANIZATION_RECEIPT_NOT_ON_LEDGER")


if __name__ == "__main__":
    unittest.main()
