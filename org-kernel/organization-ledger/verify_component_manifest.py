#!/usr/bin/env python3
"""Verify that every component module matches its pinned git blob digest. DRAFT (candidate 10). Stdlib only.

component-manifest.json: {"schema":"stegverse.organization-ledger-component-manifest/v1",
  "source_commit":"<40-hex>", "modules": {"<relative path>": "<git blob sha1>"}}
A module that is missing or locally edited is refused with the six fields. Nothing runs past a refusal.
"""
import argparse, hashlib, json, sys
from pathlib import Path

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", type=Path, required=True); ap.add_argument("--manifest", type=Path, required=True)
    a = ap.parse_args(); m = json.loads(a.manifest.read_text()); bad = []
    for rel, want in sorted(m["modules"].items()):
        p = a.root / rel
        got = git_blob_sha(p.read_bytes()) if p.is_file() else None
        if got != want: bad.append({"path": rel, "expected": want, "observed": got})
    if bad:
        print(json.dumps({"disposition": "FAIL_CLOSED", "failure_code": "COMPONENT_DIGEST_MISMATCH",
              "failed_predicate": "EVERY_COMPONENT_MODULE_EQUALS_ITS_PINNED_BLOB", "mismatches": bad,
              "required_evidence_or_repair": "consume the component unmodified at its published commit; a local edit is a fork",
              "retry_entrypoint": "org-kernel/organization-ledger/verify_component_manifest.py", "owning_existing_goal": "StegVerse-org/.github#163",
              "next_attempt": "re-run with the published component_ref; nothing was appended", "consequence_committed": False}, sort_keys=True))
        return 1
    print(json.dumps({"disposition": "ALLOW", "modules_verified": len(m["modules"]), "source_commit": m.get("source_commit")}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
