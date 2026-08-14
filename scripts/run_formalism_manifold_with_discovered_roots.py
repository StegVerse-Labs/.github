#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd().resolve()
MANIFEST = ROOT / "receipts" / "formalism-source-discovery" / "formalism-roots.json"
WORKER = ROOT / "workers" / "formalism_manifold_orchestration_worker.py"


def resolved_roots_json() -> str | None:
    explicit = os.environ.get("STEGVERSE_FORMALISM_ROOTS_JSON")
    if explicit:
        try:
            value = json.loads(explicit)
        except json.JSONDecodeError:
            return None
        return json.dumps(value, sort_keys=True, separators=(",", ":")) if isinstance(value, dict) else None
    if not MANIFEST.is_file():
        return None
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        return None
    roots = manifest.get("roots") if isinstance(manifest, dict) else None
    if manifest.get("schema") != "stegverse.formalism-roots-manifest/v0.1" or manifest.get("state") != "COMPLETED" or not isinstance(roots, dict):
        return None
    if manifest.get("credential_authority") != "TV/TVC" or manifest.get("github_token_required") is not False or manifest.get("network_checkout_performed") is not False:
        return None
    if not all(isinstance(repo, str) and isinstance(path, str) and path for repo, path in roots.items()):
        return None
    return json.dumps(roots, sort_keys=True, separators=(",", ":"))


def main() -> int:
    payload = sys.stdin.buffer.read()
    roots_json = resolved_roots_json()
    if roots_json is None:
        # Preserve the canonical worker's fail-closed behavior: invoke with an
        # explicitly empty root map rather than guessing or performing checkout.
        roots_json = "{}"
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "STEGVERSE_FORMALISM_ROOTS_JSON": roots_json,
    }
    result = subprocess.run(
        [sys.executable, str(WORKER)],
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=ROOT,
        env=env,
        check=False,
    )
    sys.stdout.buffer.write(result.stdout)
    sys.stderr.buffer.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
