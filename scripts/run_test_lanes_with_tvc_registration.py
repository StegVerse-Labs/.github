#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require_file(root: Path, relative: str, label: str) -> Path:
    path = root.expanduser().resolve() / relative
    if not path.is_file():
        raise SystemExit(f"{label} missing required file: {path}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Register TV/TVC provider credentials through the canonical hidden-TTY boundary and immediately run the heartbeat-independent canonical 9/9 Test Lanes experiment."
    )
    parser.add_argument("--stegfin-governance-root", type=Path, required=True)
    parser.add_argument("--tvc-root", type=Path, required=True)
    parser.add_argument("--test-lanes-root", type=Path, required=True)
    parser.add_argument("--micro-node-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--skip-registration-if-provisioned", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    if os.name != "posix" or not sys.platform.startswith("linux"):
        raise SystemExit("authorized TV/TVC credential registration requires Linux")
    if os.geteuid() != 0:
        raise SystemExit("run this wrapper with sudo; credential provisioner requires root-owned tmpfs lifecycle")

    governance_root = args.stegfin_governance_root.expanduser().resolve()
    registrar = require_file(governance_root, "scripts/register_tvc_provider_keys_interactive.py", "stegfin-governance")
    direct_runner = require_file(ROOT, "scripts/run_test_lanes_direct.py", ".github")

    secret_dir = governance_root / "runtime-secrets"
    provider_files = [
        secret_dir / "provider_openai",
        secret_dir / "provider_anthropic",
        secret_dir / "provider_deepseek",
        secret_dir / "provider_kimi",
    ]
    all_provisioned = all(path.is_file() and path.stat().st_size > 0 for path in provider_files)

    if not (args.skip_registration_if_provisioned and all_provisioned):
        registration = subprocess.run(
            [sys.executable, str(registrar)],
            cwd=governance_root,
            check=False,
            env={
                "PATH": os.environ.get("PATH", ""),
                "PYTHONPATH": str(governance_root),
                "HOME": os.environ.get("HOME", ""),
                "LANG": os.environ.get("LANG", "C.UTF-8"),
                "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
            },
        )
        if registration.returncode != 0:
            raise SystemExit(registration.returncode)

    command = [
        sys.executable,
        str(direct_runner),
        "--stegfin-governance-root", str(governance_root),
        "--tvc-root", str(args.tvc_root.expanduser().resolve()),
        "--test-lanes-root", str(args.test_lanes_root.expanduser().resolve()),
        "--micro-node-root", str(args.micro_node_root.expanduser().resolve()),
    ]
    if args.run_root is not None:
        command.extend(["--run-root", str(args.run_root.expanduser().resolve())])
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
