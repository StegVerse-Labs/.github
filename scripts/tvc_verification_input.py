#!/usr/bin/env python3
"""The TV/TVC checkout as a declared verification input for the ratchet (E0, stdlib + git only).

StegVerse-org/.github#164 (GitHub Product, Lane C). The `tvc` input of .stegverse/test-set-spec.json
(check kind env_path, env STEGVERSE_TVC_ROOT) is needed by the [tvc] sets of
tests/test_canonical_work_in_process_admission.py and tests/test_origin_attestation_tvc_conformance.py. This tool
supplies it from one manifest, .stegverse/verification-inputs/tvc.json, which pins StegVerse-Labs/TVC to an exact
commit (never a moving branch):

  pin   --manifest M --github-output FILE
        -> repository=, commit=, path= for the job's own SHA-pinned actions/checkout step; a manifest that does not
           verify (seal, schema, repository, 40-hex commit) prints six fields and writes readable=false
  bind  --manifest M --checkout DIR --readable true|false --dest DIR2 [--env-out FILE]
        -> when the job could read the pinned commit with its own GITHUB_TOKEN and DIR's HEAD is exactly that
           commit, moves DIR to DIR2 (outside the workspace, so nothing under this repository's tree changes) and
           writes STEGVERSE_TVC_ROOT=DIR2; otherwise prints a six-field FAIL_CLOSED and writes nothing

Exit status is 0 either way: the selector, not this tool, decides. A set whose input is absent is
REQUIRED_VERIFICATION_INPUT_UNAVAILABLE (blocking every change that selects it, never bypassable) instead of the job
dying for every change. No credential is read, stored or minted here; reading a private repository takes more than
the job's GITHUB_TOKEN, and that read credential is a TV/TVC transition, never a repository secret or a PAT.
No clock is read, nothing is published, nothing is installed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "stegverse.verification-input.tvc-checkout/v1"
REPOSITORY = "StegVerse-Labs/TVC"
ENV = "STEGVERSE_TVC_ROOT"
CHECKOUT_PATH = ".verification-inputs/tvc"
RETRY = ".github/workflows/test-suite-ratchet.yml ratchet"
OWNER = "GitHub Product, Lane C (StegVerse-org/.github#164)"
READ_OWNER = ("TVC-PRIVATE-SOURCE-READ-001 (TV/TVC private-source read transition lease, StegVerse-Labs/TVC#535; "
              "custody StegVerse-Labs/TV#26)")
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def seal(manifest: Mapping[str, Any]) -> str:
    body = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    return hashlib.sha256(canonical(body).encode("utf-8")).hexdigest()


def refusal(code: str, predicate: str, repair: str, owner: str = OWNER,
            next_attempt: str = "the next ratchet run on this pull request", failure_class: str = "B") -> dict:
    return {"disposition": "FAIL_CLOSED", "failure_code": code, "failed_predicate": predicate,
            "required_evidence_or_repair": repair, "retry_entrypoint": RETRY, "owning_existing_goal": owner,
            "next_attempt": next_attempt, "failure_class": failure_class, "input": "tvc", "env": ENV,
            "lowest_supported_mode": "E0", "authority_effect": "NONE"}


def load_manifest(path: Path) -> tuple[dict | None, dict | None]:
    try:
        m = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, refusal("TVC_VERIFICATION_INPUT_MANIFEST_UNREADABLE", "TVC_INPUT_MANIFEST_VERIFIES",
                             f"{path} must be readable JSON ({type(exc).__name__})")
    problems = []
    if not isinstance(m, dict):
        problems.append("not an object")
    else:
        if m.get("schema") != SCHEMA:
            problems.append(f"schema != {SCHEMA}")
        if m.get("repository") != REPOSITORY:
            problems.append(f"repository != {REPOSITORY}")
        if not isinstance(m.get("commit"), str) or not HEX40.match(m["commit"]):
            problems.append("commit is not a 40-hex commit sha (a moving ref is never a pin)")
        if m.get("env") != ENV:
            problems.append(f"env != {ENV}")
        if m.get("manifest_sha256") != seal(m):
            problems.append("manifest_sha256 does not re-derive")
    if problems:
        return None, refusal("TVC_VERIFICATION_INPUT_MANIFEST_INVALID", "TVC_INPUT_MANIFEST_VERIFIES",
                             f"{path}: " + "; ".join(problems))
    return m, None


def pin(manifest_path: Path, github_output: Path | None) -> dict:
    m, bad = load_manifest(manifest_path)
    lines = ([f"repository={m['repository']}", f"commit={m['commit']}", f"path={CHECKOUT_PATH}", "manifest=ok"]
             if m else ["manifest=invalid"])
    if github_output:
        with github_output.open("a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    return bad or {"disposition": "ALLOW", "repository": m["repository"], "commit": m["commit"],
                   "path": CHECKOUT_PATH}


def head_of(checkout: Path) -> str:
    try:
        out = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"], capture_output=True, text=True)
    except OSError:
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def bind(manifest_path: Path, checkout: Path, readable: bool, dest: Path, env_out: Path | None) -> dict:
    m, bad = load_manifest(manifest_path)
    if bad:
        return bad
    if not readable:
        return refusal(
            "TVC_VERIFICATION_INPUT_READ_CREDENTIAL_NOT_ISSUED", "TVC_PINNED_COMMIT_READABLE_BY_THE_JOB",
            f"{REPOSITORY} is private and this job's GITHUB_TOKEN (contents: read, scoped to this repository) cannot "
            f"read commit {m['commit']}; a TV/TVC transition must issue this job a read-only, {REPOSITORY}-scoped, "
            "per-run read lease (never a repository secret, never a PAT). Until then the [tvc] sets stay "
            "REQUIRED_VERIFICATION_INPUT_UNAVAILABLE and block every change that selects them",
            owner=READ_OWNER,
            next_attempt="the next ratchet run after a TV/TVC read lease for this job is issued and bound")
    got = head_of(checkout)
    if got != m["commit"]:
        return refusal("TVC_VERIFICATION_INPUT_PIN_MISMATCH", "TVC_CHECKOUT_IS_THE_PINNED_COMMIT",
                       f"the checkout at {checkout} must be exactly {m['commit']} (got {got or 'no checkout'}); "
                       "re-run the pinned checkout")
    for rel in m.get("required_files", []):
        if not (checkout / rel).is_file():
            return refusal("TVC_VERIFICATION_INPUT_FILE_ABSENT", "TVC_CHECKOUT_HOLDS_THE_REQUIRED_FILES",
                           f"{rel} must exist at {m['commit']}; re-pin the manifest to a commit that has it")
    if dest.exists():
        return refusal("TVC_VERIFICATION_INPUT_DEST_EXISTS", "TVC_INPUT_BOUND_ONCE",
                       f"{dest} must not exist before bind (one bind per job)")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(checkout), str(dest))
    if env_out:
        with env_out.open("a", encoding="utf-8") as fh:
            fh.write(f"{ENV}={dest}\n")
    return {"disposition": "ALLOW", "input": "tvc", "env": ENV, "root": str(dest), "commit": m["commit"],
            "authority_effect": "NONE"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pin")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--github-output", type=Path)
    b = sub.add_parser("bind")
    b.add_argument("--manifest", type=Path, required=True)
    b.add_argument("--checkout", type=Path, required=True)
    b.add_argument("--readable", choices=("true", "false"), required=True)
    b.add_argument("--dest", type=Path, required=True)
    b.add_argument("--env-out", type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "pin":
        out = pin(a.manifest, a.github_output)
    else:
        out = bind(a.manifest, a.checkout, a.readable == "true", a.dest, a.env_out)
    print(("TVC_VERIFICATION_INPUT " + out["disposition"]) + " " + canonical(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
