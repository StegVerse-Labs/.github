"""The public-ledger route of the cross-org read (E0, no credential): a carried source receipt verified on an
anonymously readable source ledger. (Twin of StegVerse-org/.github tests/test_intr_path_public_ledger_read.py.)

Deterministic and offline: the "anonymous copy" is a temporary bare repository whose objects are this
checkout's (alternates) and whose ledger ref is the pinned, already-published StegVerse-Labs ledger tip below,
which carries the authentic source receipts of StegVerse-Labs->StegVerse-org. No network, clock or credential.
The workflow's anonymous fetch is what produces such a copy for a real run.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINNED_TIP = "9a407561062757a30f90818ec6c8105b04331a39"   # StegVerse-Labs refs/stegverse/organization-ledger, read Oct 23
PID = "StegVerse-Labs->StegVerse-org:intr-destination"
CID = "intr-path-v1:StegVerse-Labs->StegVerse-org"
SOURCE_ORG_RECEIPT = "sha256:157c18d443293c70c40faccf5371bde2f1594f42f22894e3fbf80ff3779af376"
SOURCE_REPO_RECEIPT = "sha256:dd82c48f7532339f078373a8b8ec2e9e5f2ecde706621569b321f3c4d1e775bf"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pi = load("intr_path_ingress_public_route", "resident-runtime/intr_path_ingress.py")


def git_objects() -> Path:
    out = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                         capture_output=True, text=True, check=True).stdout.strip()
    return Path(out) / "objects"


class PublicLedgerRoute(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        have = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", PINNED_TIP + "^{commit}"], check=False)
        if have.returncode != 0:
            self.fail("FAIL_CLOSED LEDGER_TIP_NOT_FETCHED: fetch refs/stegverse/organization-ledger before this test")
        bare = self.root / "StegVerse-Labs.git"
        subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
        (bare / "objects" / "info" / "alternates").write_text(str(git_objects()) + "\n")
        subprocess.run(["git", "--git-dir=" + str(bare), "update-ref", pi.LEDGER_REF, PINNED_TIP], check=True)
        self.checked = {"path_id": PID, "communication_id": CID, "source_repository": "StegVerse-Labs/.github",
                        "source_organization_receipt_sha256": SOURCE_ORG_RECEIPT,
                        "source_repository_receipt_sha256": SOURCE_REPO_RECEIPT}
        self.no_tvc = self.root / "no-tvc-receipts"

    def test_public_readback_reads_the_authentic_source_pair(self):
        rb = pi.public_readback(PID, CID, "StegVerse-Labs/.github", self.root)
        self.assertEqual((rb["schema"], rb["repository"], rb["ledger_tip"], rb["read_route"]),
                         (pi.READBACK_SCHEMA, "StegVerse-Labs/.github", PINNED_TIP, "ANONYMOUS_PUBLIC_LEDGER_READ"))
        self.assertEqual(rb["organization_receipt"]["receipt_sha256"], SOURCE_ORG_RECEIPT)
        self.assertEqual(rb["repository_receipt"]["receipt_sha256"], SOURCE_REPO_RECEIPT)
        self.assertTrue(pi._included(rb, rb["organization_receipt"]))
        checked = pi.check_source_pair(rb["organization_receipt"], rb["repository_receipt"], PID, CID, "StegVerse-org")
        self.assertEqual(checked["disposition"], "ALLOW", checked)

    def test_source_inclusion_allows_without_any_credential(self):
        got = pi.source_inclusion(self.checked, self.no_tvc, self.root)
        self.assertEqual((got["disposition"], got["state"], got["source_ledger_tip"], got["tvc_read_receipt"]),
                         ("ALLOW", pi.PUBLIC_STATE, PINNED_TIP, None))

    def test_contradicted_copy_is_deny_with_six_fields(self):
        got = pi.source_inclusion({**self.checked, "source_repository_receipt_sha256": "sha256:" + "0" * 64},
                                  self.no_tvc, self.root)
        self.assertEqual((got["disposition"], got["failure_code"]), ("DENY", pi.SOURCE_LINK_UNVERIFIED))
        self.assertTrue(all(got[f] for f in SIX))

    def test_no_anonymous_copy_falls_back_to_the_tvc_route_fail_closed(self):
        for public in (self.root / "absent", None):
            with self.subTest(public=public):
                got = pi.source_inclusion(self.checked, self.no_tvc, public if public else self.root / "none")
                self.assertEqual((got["disposition"], got["failure_code"]), ("FAIL_CLOSED", pi.CREDENTIAL_NOT_ISSUED))
                self.assertTrue(all(got[f] for f in SIX))

    def test_unsafe_organization_names_are_not_resolved(self):
        for other in ("../x/.github", "/.github", ".hidden/.github", ""):
            self.assertIsNone(pi.public_ledger_dir(other, self.root))

    def test_end_to_end_is_terminal_at_e0(self):
        # From the destination's side with no destination ingress receipt in a temp ledger: terminal, never waiting.
        src = pi.public_readback(PID, CID, "StegVerse-Labs/.github", self.root)
        dst = {"schema": pi.READBACK_SCHEMA, "repository": "StegVerse-org/.github", "ledger_tip": None,
               "head_receipt_sha256": None, "chain": [], "organization_receipt": None, "repository_receipt": None}
        got = pi.verify_end_to_end(PID, CID, src, dst)
        self.assertEqual((got["disposition"], got["failure_code"], got["half"]),
                         ("FAIL_CLOSED", pi.NOT_LEDGERED, "end_to_end"))
        self.assertTrue(all(got[f] for f in SIX))


if __name__ == "__main__":
    unittest.main()
