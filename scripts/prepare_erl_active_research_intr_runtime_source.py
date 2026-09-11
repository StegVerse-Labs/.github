#!/usr/bin/env python3
"""Prepare existing resident source for ERL active-research Universal InTr.

This helper applies only the already-merged idempotent source transforms. It
creates no listener, scheduler, worker owner, heartbeat, claim/fence, credential
path, transport event, provider operation, or runtime receipt.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER_INSTALLER = ROOT / "scripts/install_erl_active_research_universal_intr_route.py"
LINEAGE_INSTALLER = ROOT / "scripts/install_erl_device_kv_prior_lineage.py"


def run(*args: str) -> None:
    proc = subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True)
    if proc.returncode:
        raise SystemExit(proc.stdout + proc.stderr)
    if proc.stdout:
        print(proc.stdout, end="")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    mode = ["--check"] if args.check else []

    run(str(ROUTER_INSTALLER), *mode)
    run(str(LINEAGE_INSTALLER), *mode)

    print("PASS: ERL active-research resident source preparation is consistent")
    print("NONCLAIM: source preparation does not prove ingress, DEVICE_SYSTEM->KV transport, three-hop traversal, provider replay, or runtime completion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
