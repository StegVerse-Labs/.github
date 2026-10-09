"""Test fixtures shared by the whole suite.

OL-1b: the Organization ledger locus is declared by the Organization manifest
(.stegverse/transition-ledger/org-contract.json `organization_ledger`), never
selected by the environment alone. The repository declares the Git store. Most
tests exercise the Organization ledger on a POSIX root they supply through
STEGVERSE_ORG_LEDGER_ROOT, so this fixture declares that locus for them
explicitly -- {"store": "posix"} -- on every copy of the aggregator, whether
already loaded or loaded during the test (production code loads its own copies
by file location), exactly as a manifest would. There is no silent fallback: a
test that needs the repository's own declaration marks itself
`repository_ledger_locus`.
"""
from __future__ import annotations

import importlib.machinery
import sys
import types
import weakref

import pytest

POSIX_LEDGER_LOCUS = {"store": "posix"}

# Every aggregator copy loaded by file location during the run, wherever it is
# then held: a module-level cache (org-kernel's _crossing_emitters) keeps one
# outside sys.modules and outside any module attribute. Weakly held, so copies
# nothing references any more drop out.
_AGGREGATORS: "weakref.WeakSet[types.ModuleType]" = weakref.WeakSet()
_exec_module_untracked = importlib.machinery.SourceFileLoader.exec_module


def _exec_and_track(self, module):
    _exec_module_untracked(self, module)
    if callable(getattr(module, "declared_ledger_locus", None)):
        _AGGREGATORS.add(module)


importlib.machinery.SourceFileLoader.exec_module = _exec_and_track


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "repository_ledger_locus: use org-contract.json's own organization_ledger declaration")


def _declare_posix(module, monkeypatch):
    contract = getattr(module, "C", None)
    if callable(getattr(module, "declared_ledger_locus", None)) and isinstance(contract, dict):
        monkeypatch.setitem(contract, "organization_ledger", dict(POSIX_LEDGER_LOCUS))


@pytest.fixture(autouse=True)
def declared_posix_ledger_locus(request, monkeypatch):
    """Declare the POSIX ledger locus for tests that supply a POSIX root."""
    if request.node.get_closest_marker("repository_ledger_locus"):
        yield
        return
    for module in list(sys.modules.values()):
        _declare_posix(module, monkeypatch)
        # A copy loaded by file location is held as a module attribute, not in sys.modules.
        for held in list(vars(module).values()) if module is not None else ():
            if isinstance(held, types.ModuleType):
                _declare_posix(held, monkeypatch)
    for module in list(_AGGREGATORS):
        _declare_posix(module, monkeypatch)
    loader = importlib.machinery.SourceFileLoader
    exec_module = loader.exec_module

    def exec_and_declare(self, module):
        exec_module(self, module)
        _declare_posix(module, monkeypatch)

    monkeypatch.setattr(loader, "exec_module", exec_and_declare)
    yield
