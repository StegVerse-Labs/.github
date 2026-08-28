#!/usr/bin/env python3
"""Fail-closed production entrypoint for the canonical G18 activation worker.

G18 is a sovereign worker/runtime-substrate activation lane. HeartBeat is already
terminal and oscillator-only, so this entrypoint delegates directly to the
canonical G18 worker, which uses the existing v13 self-bootstrap and activation
verifier. It creates no heartbeat, claim, fence, credential, route, scheduler,
or runtime authority.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path.cwd().resolve()


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _load(
    "sovereign_runtime_activation_worker_base",
    ROOT / "workers" / "sovereign_runtime_activation_worker.py",
)


def main() -> int:
    return int(base.main())


if __name__ == "__main__":
    raise SystemExit(main())
