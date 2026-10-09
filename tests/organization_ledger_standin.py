"""A temporary bare Git repository standing in for the declared Organization ledger locus.

CI evidence only. The declared locus (org-contract.json `organization_ledger_locus`)
is reached at the declared repository's own address; Git's `url.<base>.insteadOf`
rewrites that address to a temporary bare repository for the duration of a test,
so an append exercises the real expected-head compare-and-swap against a real
Git remote and never reaches the durable Organization ledger. Nothing appended
here is Organization runtime reality.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / ".stegverse/transition-ledger/org-contract.json").read_text())
LOCUS = CONTRACT["organization_ledger_locus"]
DECLARED_URL = "https://github.com/" + LOCUS["repository"] + ".git"


def standin_environment(remote: Path) -> dict[str, str]:
    """Git configuration that routes the declared repository's address to `remote`."""
    return {
        "GIT_CONFIG_COUNT": "2",
        "GIT_CONFIG_KEY_0": "url." + Path(remote).resolve().as_uri() + ".insteadOf",
        "GIT_CONFIG_VALUE_0": DECLARED_URL,
        "GIT_CONFIG_KEY_1": "commit.gpgsign",
        "GIT_CONFIG_VALUE_1": "false",
        "GIT_TERMINAL_PROMPT": "0",
    }


def make_remote(base: Path) -> Path:
    remote = Path(base) / "standin-remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    return remote


def remote_head(remote: Path) -> str | None:
    result = subprocess.run(["git", "--git-dir", str(remote), "rev-parse", "--verify", "-q", LOCUS["ref"]],
                            capture_output=True, text=True)
    return result.stdout.strip() or None


@contextmanager
def standin_locus(base: Path | None = None, *, cache: Path | None = None):
    """Route the declared locus to a fresh bare repository; optionally set the cache variable.

    Yields the bare repository's path. The routing is verified before the body
    runs, so a test can never reach the declared repository itself.
    """
    with tempfile.TemporaryDirectory() as scratch:
        remote = make_remote(Path(base) if base is not None else Path(scratch))
        env = standin_environment(remote)
        if cache is not None:
            env["STEGVERSE_ORG_LEDGER_ROOT"] = str(cache)
        with mock.patch.dict(os.environ, env):
            routed = subprocess.run(["git", "ls-remote", "--get-url", DECLARED_URL],
                                    capture_output=True, text=True, check=True).stdout.strip()
            if routed != remote.resolve().as_uri():
                raise AssertionError("declared locus is not routed to the stand-in: " + routed)
            yield remote


def _routed_standin() -> Path:
    """The stand-in the declared address is routed to now; refuses anything that is not a local bare repo."""
    routed = subprocess.run(["git", "ls-remote", "--get-url", DECLARED_URL],
                            capture_output=True, text=True, check=True).stdout.strip()
    if not routed.startswith("file://"):
        raise AssertionError("declared locus is not routed to a stand-in: " + routed)
    return Path(routed[len("file://"):])


_LEDGER = None


def _ledger_module():
    global _LEDGER
    if _LEDGER is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("aggregate_repo_transition_standin",
                                                      ROOT / "resident-runtime/aggregate_repo_transition.py")
        _LEDGER = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_LEDGER)
    return _LEDGER


def publish_tampering(cache: Path) -> str:
    """Commit a cache's ledger files, exactly as they now stand, onto the stand-in ref.

    A forgery written only into a non-authoritative cache is discarded the next
    time the cache is read from the locus. To exercise verification, a tamper
    has to be made at the locus itself, as a writer holding the ref could make
    it. Stand-in only: refuses unless the declared address routes to a local
    bare repository.
    """
    _routed_standin()
    module = _ledger_module()
    git = module.GitLocus(Path(cache), module.bound_locus(cache))
    head = git.fetch()
    commit = git.commit(git.tree(head), head, "stand-in tampering")
    swapped, result = git.compare_and_swap(commit, head)
    if not swapped:
        raise AssertionError("stand-in tampering was not published: " + result.stderr.decode())
    return commit


def bind(cache: Path) -> Path:
    """Bind an empty directory as a cache of the declared locus, as ledger_root() would."""
    module = _ledger_module()
    return module.bind_cache(cache, module.declared_locus())
