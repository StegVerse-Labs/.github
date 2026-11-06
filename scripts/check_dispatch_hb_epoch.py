#!/usr/bin/env python3
"""Workflow-dispatch heartbeat epoch gate: the kernel's six-field refusal, or exit 0.

A workflow writer step that takes the epoch as a workflow_dispatch input runs
this before any append, with the name of the environment variable holding the
input. The value is checked by the kernel's shared rule (writer_epoch_refusal),
uncoerced. A workflow_dispatch string input cannot tell empty from absent, so
an empty or unset value is HB_EPOCH_NOT_SUPPLIED; '+33', ' 33', fullwidth
digits, '33.0', '31' and 'abc' are HB_EPOCH_INVALID. No clock is read.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def refusal(value: str | None, retry_entrypoint: str) -> dict | None:
    spec = importlib.util.spec_from_file_location("org_kernel_dispatch_epoch", ROOT / "org-kernel" / "kernel.py")
    kernel = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kernel)
    return kernel.writer_epoch_refusal(value or None, retry_entrypoint=retry_entrypoint)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: check_dispatch_hb_epoch.py <ENV_VAR> <retry_entrypoint>")
    refused = refusal(os.environ.get(argv[1]), argv[2])
    if refused is not None:
        print(json.dumps(refused, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
