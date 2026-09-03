from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from heartbeat_runtime.org_assertions import issue_claim_assertions


class OrgClaimAssertionLeaseFenceTests(unittest.TestCase):
    def test_org_claim_assertion_reads_fence_from_canonical_lease(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "control").mkdir(parents=True)
            claim = {
                "task_id": "TASK-2026-0008",
                "repository": {"full_name": "StegVerse-Labs/Site"},
                "mode": "scoped_exclusive",
                "scope": {"contracts": [], "release_surfaces": []},
                "lease": {
                    "expires_at": "2026-09-04T00:00:00Z",
                    "heartbeat_due_at": "2026-09-03T08:00:00Z",
                    "fencing_token": 7,
                    "service_class": "low_contention",
                },
            }
            (root / "control/claims-active.json").write_text(
                json.dumps({"schema": "stegverse.org-claims/v1", "generation": 7, "claims": [claim]}),
                encoding="utf-8",
            )
            (root / "control/org-state.json").write_text(
                json.dumps({"schema": "stegverse.org-state/v1"}),
                encoding="utf-8",
            )
            refs = issue_claim_assertions(root, epoch=33, issued_at="2026-09-03T00:40:00Z", write=True)
            self.assertEqual(len(refs), 1)
            assertion = json.loads((root / refs[0]).read_text(encoding="utf-8"))
            self.assertEqual(assertion["fencing_token"], 7)
            self.assertEqual(assertion["claimant_id"], "TASK-2026-0008")
            self.assertEqual(assertion["authority_effect"], "none")

    def test_org_claim_assertion_skips_malformed_claim_without_crashing_carrier(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "control").mkdir(parents=True)
            claim = {
                "task_id": "TASK-BAD",
                "repository": {"full_name": "StegVerse-Labs/Site"},
                "scope": {},
            }
            (root / "control/claims-active.json").write_text(
                json.dumps({"schema": "stegverse.org-claims/v1", "generation": 1, "claims": [claim]}),
                encoding="utf-8",
            )
            (root / "control/org-state.json").write_text(
                json.dumps({"schema": "stegverse.org-state/v1"}),
                encoding="utf-8",
            )
            self.assertEqual(
                issue_claim_assertions(root, epoch=33, issued_at="2026-09-03T00:40:00Z", write=True),
                [],
            )


if __name__ == "__main__":
    unittest.main()
