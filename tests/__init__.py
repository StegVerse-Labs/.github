"""OL-1b: under plain unittest (no pytest, so no tests/conftest.py), declare the
POSIX Organization ledger locus for the whole run, exactly as tests/conftest.py
declares it per test under pytest. Several workflows run these tests with
`python -m unittest`. Test-only; production selection stays org-contract.json's
declaration."""
import sys

if "pytest" not in sys.modules:
    from tests.posix_ledger_locus import sitecustomize as _posix_ledger_locus  # noqa: F401
