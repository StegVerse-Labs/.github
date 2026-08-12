#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def sha256_file(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--org", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--participant-class", required=True, choices=["CONTROL", "RUNTIME", "SERVICE", "EVIDENCE", "REPO_LIVENESS"])
    parser.add_argument("--runtime-id")
    parser.add_argument("--handoff")
    parser.add_argument("--capability", action="append", default=[])
    parser.add_argument("--dependency", action="append", default=[], help="repo_id or repo_id:optional")
    parser.add_argument("--status", default="READY", choices=["READY", "DEGRADED", "BLOCKED", "FAILED", "RETIRED"])
    parser.add_argument("--sequence", type=int, required=True)
    parser.add_argument("--fresh-seconds", type=int, default=300)
    parser.add_argument("--output")
    args = parser.parse_args()

    root = Path(args.repo_root).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit("repo root not found")
    if args.sequence < 0 or args.fresh_seconds <= 0:
        raise SystemExit("sequence/freshness out of range")

    commit = git(root, "rev-parse", "HEAD")
    ref = git(root, "symbolic-ref", "--quiet", "--short", "HEAD") or None
    tag = git(root, "describe", "--tags", "--exact-match", "HEAD") or None
    if args.participant_class in {"CONTROL", "RUNTIME", "SERVICE"}:
        if len(commit) != 40 or not args.runtime_id:
            raise SystemExit("control/runtime/service participant requires git commit and runtime-id")
    elif len(commit) != 40:
        commit = None

    handoff = (root / args.handoff).resolve() if args.handoff else None
    if handoff is not None and root not in handoff.parents and handoff != root:
        raise SystemExit("handoff escaped repo root")
    if handoff is not None and not handoff.is_file():
        raise SystemExit("handoff not found")

    dependencies = []
    for item in args.dependency:
        optional = item.endswith(":optional")
        repo_id = item[:-9] if optional else item
        if not repo_id:
            raise SystemExit("invalid dependency")
        dependencies.append({"repo_id": repo_id, "required": not optional})

    now = datetime.now(timezone.utc)
    manifest = {
        "schema": "stegverse.repo-heartbeat-manifest/v0.1",
        "repo_id": args.repo_id,
        "org": args.org,
        "repository": args.repository,
        "participant_class": args.participant_class,
        "commit_sha": commit,
        "ref": ref,
        "release_tag": tag,
        "runtime_id": args.runtime_id,
        "handoff_hash": sha256_file(handoff),
        "sequence": args.sequence,
        "emitted_at": now.isoformat().replace("+00:00", "Z"),
        "fresh_until": (now + timedelta(seconds=args.fresh_seconds)).isoformat().replace("+00:00", "Z"),
        "status": args.status,
        "capabilities": sorted(set(args.capability)),
        "dependencies": dependencies,
        "last_success": now.isoformat().replace("+00:00", "Z") if args.status in {"READY", "DEGRADED"} else None,
        "evidence_refs": [args.handoff] if args.handoff else [],
        "authority": {
            "credential_authority": "TV/TVC",
            "heartbeat_grants_execution_authority": False,
            "github_token_required": False,
        },
    }
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
