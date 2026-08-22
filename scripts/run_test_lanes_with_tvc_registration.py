#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import pwd
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def invoking_home() -> Path:
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        try:
            return Path(pwd.getpwnam(sudo_user).pw_dir).expanduser().resolve()
        except KeyError:
            pass
    return Path.home().expanduser().resolve()


def workload_default(name: str) -> Path:
    return invoking_home() / ".stegverse" / "workloads" / name


def require_file(root: Path, relative: str, label: str) -> Path:
    path = root.expanduser().resolve() / relative
    if not path.is_file():
        raise SystemExit(f"{label} missing required file: {path}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Register TV/TVC provider credentials through the canonical hidden-TTY boundary and immediately run the heartbeat-independent canonical 9/9 Test Lanes experiment."
    )
    parser.add_argument("--stegfin-governance-root", type=Path, default=Path(os.environ.get("STEGVERSE_STEGFIN_GOVERNANCE_ROOT", workload_default("stegfin-governance"))))
    parser.add_argument("--tvc-root", type=Path, default=Path(os.environ.get("STEGVERSE_TVC_ROOT", workload_default("TVC"))))
    parser.add_argument("--test-lanes-root", type=Path, default=Path(os.environ.get("STEGVERSE_TEST_LANES_ROOT", workload_default("workflows"))))
    parser.add_argument("--micro-node-root", type=Path, default=Path(os.environ.get("STEGVERSE_MICRO_NODE_ROOT", workload_default("micro-node-runtime"))))
    parser.add_argument("--run-root", type=Path, default=Path(os.environ.get("STEGVERSE_TEST_LANES_RUN_ROOT", invoking_home() / ".stegverse" / "test-lanes" / "runs")))
    parser.add_argument("--skip-registration-if-provisioned", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    if os.name != "posix" or not sys.platform.startswith("linux"):
        raise SystemExit("authorized TV/TVC credential registration requires Linux")
    if os.geteuid() != 0:
        raise SystemExit("run this wrapper with sudo; credential provisioner requires root-owned tmpfs lifecycle")

    governance_root = args.stegfin_governance_root.expanduser().resolve()
    tvc_root = args.tvc_root.expanduser().resolve()
    lanes_root = args.test_lanes_root.expanduser().resolve()
    micro_node_root = args.micro_node_root.expanduser().resolve()
    run_root = args.run_root.expanduser().resolve()

    registrar = require_file(governance_root, "scripts/register_tvc_provider_keys_interactive.py", "stegfin-governance")
    direct_runner = require_file(ROOT, "scripts/run_test_lanes_direct.py", ".github")
    require_file(tvc_root, "config/test_lanes_model_selection.sv-cost-nine-lane.v1.json", "TVC")
    require_file(lanes_root, "experiments/stegverse-test-lanes/plan_test_lanes.py", "Test Lanes")
    require_file(micro_node_root, "tools/run_sovereign_model.py", "micro-node-runtime")

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
                "HOME": str(invoking_home()),
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
        "--tvc-root", str(tvc_root),
        "--test-lanes-root", str(lanes_root),
        "--micro-node-root", str(micro_node_root),
        "--run-root", str(run_root),
    ]
    environment = os.environ.copy()
    environment["HOME"] = str(invoking_home())
    return subprocess.run(command, cwd=ROOT, check=False, env=environment).returncode


if __name__ == "__main__":
    raise SystemExit(main())
