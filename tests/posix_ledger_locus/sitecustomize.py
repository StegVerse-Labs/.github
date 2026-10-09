"""OL-1b test fixture for subprocesses: declare the POSIX Organization ledger locus.

A test that runs repository code in a child interpreter and supplies a POSIX
ledger root puts this directory on that child's PYTHONPATH. Every aggregator
loaded there then carries organization_ledger {"store": "posix"}, exactly as
tests/conftest.py declares it in process. Test-only: nothing outside tests/
reads it, and production selection stays org-contract.json's declaration.
"""
import importlib.machinery

_exec_module = importlib.machinery.SourceFileLoader.exec_module


def _exec_and_declare(self, module):
    _exec_module(self, module)
    contract = getattr(module, "C", None)
    if callable(getattr(module, "declared_ledger_locus", None)) and isinstance(contract, dict):
        contract["organization_ledger"] = {"store": "posix"}


importlib.machinery.SourceFileLoader.exec_module = _exec_and_declare
