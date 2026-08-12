#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers/stegnutrition_continuation_worker.py"
WORKERS = ROOT / "workers"
if str(WORKERS) not in sys.path:
    sys.path.insert(0, str(WORKERS))

from stegnutrition_receipt_contract import ReceiptContractError, validate_receipt


def main() -> int:
    raw = sys.stdin.read()
    proc = subprocess.run(
        [sys.executable, str(WORKER)],
        cwd=ROOT,
        input=raw,
        text=True,
        capture_output=True,
        check=False,
        timeout=205,
    )
    if proc.returncode != 0:
        if proc.stdout:
            sys.stdout.write(proc.stdout)
        if proc.stderr:
            sys.stderr.write(proc.stderr)
        return proc.returncode
    try:
        response = json.loads(proc.stdout)
        checkpoint_ref = response.get("checkpoint_ref")
        if not isinstance(checkpoint_ref, str) or not checkpoint_ref:
            raise ReceiptContractError("worker response missing checkpoint_ref")
        receipt_path = (ROOT / checkpoint_ref).resolve()
        admitted_root = (ROOT / "receipts/stegnutrition-continuation").resolve()
        if admitted_root not in receipt_path.parents:
            raise ReceiptContractError("checkpoint_ref escaped admitted receipt namespace")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        validate_receipt(receipt)
        if receipt.get("claim_id") != (response.get("claim_id") or receipt.get("claim_id")):
            raise ReceiptContractError("response/receipt claim mismatch")
    except (OSError, json.JSONDecodeError, ReceiptContractError) as exc:
        print(f"StegNutrition continuation receipt validation failed: {exc}", file=sys.stderr)
        return 12
    sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
