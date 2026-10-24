"""A non-finite number never enters a receipt (VALIDATOR row 5).

NaN, Infinity and an overflowing literal such as 1e999 are not JSON (RFC
8259), and Python's json reads all three by default. A CLI input carrying one
is now the terminal six-field CLI_INPUT_INVALID, and the receipt canon and the
ledger stores serialise with allow_nan=False, so a value that reaches a writer
some other way is refused before anything is written.

Source validation only. No authority effect is claimed.
"""
import importlib.util
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "resident-runtime"))
import aggregate_repo_transition as org  # noqa: E402
import ledger_store  # noqa: E402


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kernel = _load("kernel_non_finite", "org-kernel/kernel.py")
emit = _load("emit_non_finite", ".stegverse/transition-ledger/emit.py")
NON_FINITE = (math.nan, math.inf, -math.inf)


class StrictDecodeTests(unittest.TestCase):
    def test_non_finite_literals_are_cli_input_invalid(self):
        for text in ('{"a": NaN}', '{"a": Infinity}', '{"a": -Infinity}', '{"a": 1e999}', '{"a": [1, -1E400]}'):
            with self.subTest(text=text), self.assertRaises(kernel.CliInputRefused) as caught:
                kernel.cli_json_text(text, "--x", retry_entrypoint="test")
            self.assertEqual(caught.exception.record["failure_code"], "CLI_INPUT_INVALID")
            self.assertIs(caught.exception.record["terminal"], True)

    def test_finite_numbers_still_decode(self):
        self.assertEqual(kernel.cli_json_text('{"a": 1.5, "b": -2e10, "c": 7}', "--x", retry_entrypoint="test"),
                         {"a": 1.5, "b": -2e10, "c": 7})


class CanonTests(unittest.TestCase):
    def test_every_receipt_canon_refuses_a_non_finite_value(self):
        for canon in (kernel.canon, org.canon, emit.canon):
            for value in NON_FINITE:
                with self.subTest(canon=canon.__module__, value=value), self.assertRaises(ValueError):
                    canon({"a": value})

    def test_the_posix_store_writes_nothing_for_a_non_finite_value(self):
        with tempfile.TemporaryDirectory() as work:
            store = ledger_store.PosixLedgerStore(Path(work))
            for value in NON_FINITE:
                with self.subTest(value=value), self.assertRaises(ValueError):
                    store.put("receipts/x.json", {"a": value})
            self.assertEqual([p for p in Path(work).rglob("*") if p.is_file()], [])


if __name__ == "__main__":
    unittest.main()
