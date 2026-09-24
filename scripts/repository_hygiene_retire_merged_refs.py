#!/usr/bin/env python3
"""Repository-native bulk retirement. Never invoke from a classifier or CI.

Uses the existing repository administrator's git/gh authentication supplied by
the canonical TV/TVC path. A routed candidate is not itself deletion authority.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from urllib.parse import quote
from pathlib import Path

SHA = re.compile(r"^[0-9a-f]{40}$")
PROTECTED = re.compile(r"^(main|master|gh-pages|release/.*|support/.*)$")
OWNER = "HYGIENE-BRANCH-REF-RETIREMENT"
SCHEMA = "stegverse.repository-hygiene-native-ref-retirement/v1"

def command(*args):
    p = subprocess.run(args, text=True, capture_output=True, check=False)
    if p.returncode:
        raise RuntimeError(f"command failed ({p.returncode}): {args[0]} {args[1] if len(args)>1 else ''}: {p.stderr.strip()}")
    return p.stdout.strip()

def validate_entry(item, repository):
    if item.get("repository") != repository:
        return "REPOSITORY_MISMATCH"
    branch = item.get("branch")
    if not isinstance(branch, str) or not branch or branch.startswith("-") or branch.endswith("/") or ".." in branch or "@{" in branch or any(c.isspace() for c in branch) or not re.fullmatch(r"[A-Za-z0-9._/-]+", branch):
        return "INVALID_REF"
    if PROTECTED.fullmatch(branch):
        return "PROTECTED_REF"
    if not SHA.fullmatch(str(item.get("expected_sha", ""))):
        return "MISSING_EXACT_EXPECTED_SHA"
    if item.get("release_authority") != OWNER or item.get("owner_disposition") != "TERMINAL_UNOWNED_EVIDENCE_SAFE":
        return "MISSING_OWNER_RELEASE"
    if item.get("intr_decision") != "ALLOW":
        return "MISSING_INTR_ALLOW_REFERENCE"
    for k in ("intr_receipt_sha256", "org_receipt_sha256", "master_records_receipt_sha256"):
        value = str(item.get(k, ""))
        if not re.fullmatch(r"sha256:[a-f0-9]{64}", value):
            return "MISSING_EXACT_CUSTODY_DIGEST"
    if item.get("master_records_reconstruction") != "PASS" or item.get("evidence_retention_clearance") is not True:
        return "MISSING_RECONSTRUCTION_OR_RETENTION_CLEARANCE"
    if item.get("merge_pr") is None and item.get("explicit_unmerged_release") is not True:
        return "CLOSED_UNMERGED_PR_NOT_RELEASED"
    return None

def preflight_live(repository, item):
    owner, name = repository.split("/", 1)
    branch = item["branch"]
    # Read authenticated GitHub state; never trust a stale census as a live ref.
    found = json.loads(command("gh", "api", f"repos/{repository}/branches/{quote(branch, safe=chr(0)[:0])}"))
    if found.get("protected") or found.get("name") != branch:
        return "PROTECTED_OR_CHANGED"
    live_sha = (found.get("commit") or {}).get("sha")
    if live_sha != item["expected_sha"]:
        return "REF_TIP_MOVED"
    # A branch head still owned by any open PR cannot be retired.
    prs = json.loads(command("gh", "api", f"repos/{repository}/pulls?state=open&per_page=100&head={quote(owner + chr(58) + branch, safe=chr(0)[:0])}"))
    if prs:
        return "ACTIVE_PR_HEAD"
    if item.get("merge_pr") is not None:
        pr = json.loads(command("gh", "api", f"repos/{repository}/pulls/{int(item['merge_pr'])}"))
        if not pr.get("merged") or (pr.get("head") or {}).get("ref") != branch:
            return "MERGE_PROOF_MISMATCH"
    # Current default-branch ancestry is required even for a merged PR.
    default = json.loads(command("gh", "api", f"repos/{repository}")).get("default_branch")
    if branch == default:
        return "DEFAULT_BRANCH"
    relation = json.loads(command("gh", "api", f"repos/{repository}/compare/{default}...{item['expected_sha']}"))
    if relation.get("ahead_by") != 0 or relation.get("files"):
        return "UNMERGED_OR_UNIQUE_SOURCE"
    return None

def run(plan, apply):
    if plan.get("schema") != SCHEMA:
        raise ValueError("invalid authority packet schema")
    repository = plan["repository"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("invalid repository")
    results = []
    for item in plan.get("releases", []):
        branch = item.get("branch", "")
        reason = validate_entry(item, repository)
        if not reason:
            try:
                reason = preflight_live(repository, item)
            except (RuntimeError, ValueError, KeyError, TypeError) as exc:
                reason = "LIVE_PREFLIGHT_FAILED:" + str(exc)[:200]
        if reason:
            results.append({"branch": branch, "result": "RETAIN", "reason": reason})
            continue
        if not apply:
            results.append({"branch": branch, "result": "PREFLIGHT_ONLY_NO_DELETE"})
            continue
        # Atomic compare-and-delete: if the remote branch moved since preflight,
        # --force-with-lease fails. Never force-delete an unexpected successor.
        ref = f"refs/heads/{branch}"
        expected = item["expected_sha"]
        try:
            remote = command("git", "remote", "get-url", "origin")
            if not remote.endswith((f"github.com/{repository}.git", f"github.com/{repository}")):
                raise RuntimeError("origin does not match approved repository")
            command("git", "push", f"--force-with-lease={ref}:{expected}", "origin", f":{ref}")
            if command("git", "ls-remote", "--heads", "origin", ref):
                raise RuntimeError("branch still exists after deletion attempt")
            results.append({"branch": branch, "result": "REF_DELETED_ORG_MR_CLOSURE_REQUIRED", "deleted_sha": expected})
        except RuntimeError as exc:
            results.append({"branch": branch, "result": "RETAIN", "reason": "DELETE_FAILED:" + str(exc)[:200]})
    return {
        "schema": "stegverse.repository-hygiene-native-ref-retirement-result/v1",
        "repository": repository, "authority_owner": OWNER, "apply": apply,
        "results": results,
        "note": "Typed packet fields are prerequisites, not authentic receipt verification. The existing authorized custody owner must independently authenticate exact InTr/org/MR evidence before repository-admin execution. No canonical terminal closure is claimed until authentic post-deletion organization transition receipt and Master Records reconstruction are recorded."
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority-packet", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="Existing authenticated repository-admin execution only; never GitHub Actions")
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    result = run(json.loads(a.authority_packet.read_text()), a.apply)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"checked": len(result["results"]), "deleted": sum(x["result"]=="REF_DELETED_ORG_MR_CLOSURE_REQUIRED" for x in result["results"]), "retained": sum(x["result"]=="RETAIN" for x in result["results"]), "dry_run": not a.apply}))
    if any(x["result"]=="RETAIN" for x in result["results"]):
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
