"""Every pytest test reaches the declared Organization ledger locus only through a stand-in.

OL-1b: an append through a cache of the declared locus is published to the
declared ref in StegVerse-Labs/.github. Under test, each test gets its own
temporary bare repository standing in for that ref (CI evidence only), so no
test can reach the durable Organization ledger and no test's chain leaks into
another's.
"""
import pytest

from tests.organization_ledger_standin import standin_locus


@pytest.fixture(autouse=True)
def _organization_ledger_locus_standin(tmp_path_factory):
    with standin_locus(tmp_path_factory.mktemp("organization-ledger-locus")):
        yield
