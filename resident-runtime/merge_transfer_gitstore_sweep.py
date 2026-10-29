#!/usr/bin/env python3
"""Catch-up for the main-merge transfer writer: every first-parent main commit since the last ledgered one.

GitHub keeps at most one pending run per concurrency group. When main moves
again while an organization-ledger run is queued, the queued run is
cancelled even with ``cancel-in-progress: false``, and its merge is never
appended (StegVerse-Labs/.github 0ab9949d (#3362) and 47daca11 (#3363):
runs 40169514269 and 40169527347 cancelled while pending). The next push only
carries ``before..after``, so the gap would stay open.

This sweep closes it on the next push. From ``--after`` it reads the last
SWEEP_LIMIT commits of main's first-parent history and keeps (oldest first)
every one newer than the anchor that the organization ledger holds no
ORGANIZATION_MAIN_MERGE_TRANSFER receipt for. The anchor is the oldest commit
in that window that has one: the run of a later merge still appends its own
merge (7963db6a after the two above), so the gap sits behind the newest
receipt. The commits it is
given (``--commits-file``: pending.json and the pushed range, from
merge_transfer_gitstore.py commits) follow, each once.

It reads the local git object store only (``git rev-list`` and the ledger ref
through merge_transfer_gitstore's GitTreeReader): no clock, no network, no
write. It selects; it never verifies. The writer appends what it selects and
merge_transfer_gitstore.py verify, on a fresh fetch of the published ref,
stays the only evidence. Without an anchor within SWEEP_LIMIT commits it
sweeps nothing (history before the writer existed is not a gap) and says so
on stderr; the given commits are still printed.
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
SWEEP_LIMIT = 64


def _gitstore():
    name = "merge_transfer_gitstore_for_sweep"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "resident-runtime/merge_transfer_gitstore.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def ledgered_merges(organization: Any, repo: str) -> set[str]:
    """Merge commits of ``repo`` named by a sealed ORGANIZATION_MAIN_MERGE_TRANSFER receipt on the chain."""
    g = _gitstore()
    found: set[str] = set()
    for digest, receipt in g.org_chain(organization):
        if not g.sealed(receipt) or receipt["receipt_sha256"] != digest:
            break  # the verifier refuses past a broken seal; the sweep does not reach behind it either
        boundary = receipt.get("boundary_evidence", receipt.get("evidence"))
        boundary = boundary if isinstance(boundary, Mapping) else {}
        if boundary.get("operation") == g.OPERATION and boundary.get("repository") == repo \
                and isinstance(boundary.get("merge_commit"), str):
            found.add(boundary["merge_commit"])
    return found


def unledgered_since_anchor(after: str, ledgered: set[str], git_dir: Path | str = ROOT,
                            limit: int = SWEEP_LIMIT) -> tuple[list[str], str | None]:
    """(first-parent commits newer than the anchor with no receipt, oldest first; the anchor or None).

    The anchor is the oldest commit within ``limit`` first-parent commits of
    ``after`` that holds a receipt: the run of a later merge appends that merge
    even when the runs before it were cancelled, so the gap sits behind the
    newest receipt, not ahead of it.
    """
    listed = subprocess.run(["git", "-C", str(git_dir), "rev-list", "--first-parent", "--max-count",
                             str(limit), after], capture_output=True, text=True)
    if listed.returncode != 0:
        raise SystemExit("FAIL_CLOSED: MAIN_HISTORY_UNREADABLE " + listed.stderr.strip())
    window = listed.stdout.split()
    anchored = [i for i, commit in enumerate(window) if commit in ledgered]
    if not anchored:
        return [], None
    anchor = anchored[-1]
    return [c for c in reversed(window[:anchor]) if c not in ledgered], window[anchor]


def select(given: Iterable[str], swept: Iterable[str]) -> list[str]:
    out: list[str] = []
    for commit in [*swept, *given]:
        if commit not in out:
            out.append(commit)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--after", required=True)
    parser.add_argument("--commits-file", required=True)
    parser.add_argument("--git-dir", required=True, help="git dir holding main's history and the organization ledger ref")
    parser.add_argument("--ref", help="the organization ledger ref (else the declared ref)")
    parser.add_argument("--limit", type=int, default=SWEEP_LIMIT)
    args = parser.parse_args(argv)
    g = _gitstore()
    given = Path(args.commits_file).read_text(encoding="utf-8").split()
    readers = g.bind_readers(ROOT, git_dir=args.git_dir, ref=args.ref, namespace="")
    if isinstance(readers, dict):
        print("sweep: ledger unbound, nothing swept: " + readers["failure_code"], file=sys.stderr)
        swept: list[str] = []
    else:
        swept, anchor = unledgered_since_anchor(args.after, ledgered_merges(readers[0], g.repository(ROOT)),
                                                args.git_dir, limit=args.limit)
        if anchor is None:
            print("sweep: no ledgered main commit within %d first-parent commits; nothing swept" % args.limit,
                  file=sys.stderr)
        else:
            print("sweep: anchor %s; %d unledgered since: %s" % (anchor, len(swept), " ".join(swept)),
                  file=sys.stderr)
    print("\n".join(select(given, swept)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
