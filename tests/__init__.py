"""Test package.

OL-1b: an Organization ledger append through a cache of the declared locus is
published to the declared ref in StegVerse-Labs/.github. Every unittest
TestCase therefore runs with that address routed to its own temporary bare
repository (tests/organization_ledger_standin.py; CI evidence only), exactly
as tests/conftest.py does for pytest functions, so no test reaches the durable
Organization ledger and no test's chain leaks into another's.
"""
import tempfile
import unittest

from tests.organization_ledger_standin import standin_locus

_run = unittest.TestCase.run


def _run_with_organization_ledger_standin(self, result=None):
    with tempfile.TemporaryDirectory(prefix="organization-ledger-locus-") as scratch, standin_locus(scratch):
        return _run(self, result)


unittest.TestCase.run = _run_with_organization_ledger_standin
