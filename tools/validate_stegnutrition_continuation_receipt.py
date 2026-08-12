#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKERS = ROOT / "workers"
if str(WORKERS) not in sys.path:
    sys.path.insert(0, str(WORKERS))

from stegnutrition_receipt_contract import ReceiptContractError, validate_receipt


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("usage: validate_stegnutrition_continuation_receipt.py <receipt.json>", file=sys.stderr)
        return 2
    path = Path(args[0]).expanduser().resolve()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        validate_receipt(value)
    except (OSError, json.JSONDecodeError, ReceiptContractError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print(f"PASS {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
