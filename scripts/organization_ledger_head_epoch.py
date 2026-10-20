#!/usr/bin/env python3
"""Print the heartbeat epoch the Organization ledger HEAD records, or refuse it.

The organization claim allocator has no carrier frame of its own. The frame it
continues is the Organization receipt chain, so the epoch it supplies
(`--hb-epoch`) is the one the verified chain's HEAD receipt records in
`hb_reference.epoch` -- read from the ledger, never from a clock or a date.

The chain is verified with the consumer's EXISTING `ledger_custody` and
`verify_organization_chain`; the epoch is checked with the kernel's shared
`supplied_epoch_failure`, so a HEAD whose `derived_from_clock` is not exactly
false is refused like any other unsupplied epoch. Every refusal is a six-field
FAIL_CLOSED printed as JSON with exit status 1; nothing is appended. Stdlib only.

The ledger roots are the ones the consumer takes (`--repo-ledger-root`,
`--org-ledger-root`). Wiring this into the claim-allocator workflow is a
separate step (B-P8 transition 1, after StegVerse-Labs/.github#3241).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Mapping

CONSUMER_REL = Path("scripts/consume_org_claim_allocator_request.py")
FAILED_PREDICATE = "ORGANIZATION_LEDGER_HEAD_RECORDS_A_SUPPLIED_HB_EPOCH"
RETRY_ENTRYPOINT = "scripts/organization_ledger_head_epoch.py (--source-root, --repo-ledger-root, --org-ledger-root)"
OWNING_EXISTING_GOAL = "SHWP-ORG-CLAIM-ALLOCATOR-001"
NEXT_ATTEMPT = "after the Organization ledger HEAD records a supplied epoch; nothing was appended"


def refusal(failure_code: str, detail: str, repair: str) -> dict[str, Any]:
    return {
        "disposition": "FAIL_CLOSED",
        "failure_code": failure_code,
        "failed_predicate": FAILED_PREDICATE,
        "detail": detail,
        "required_evidence_or_repair": repair,
        "retry_entrypoint": RETRY_ENTRYPOINT,
        "owning_existing_goal": OWNING_EXISTING_GOAL,
        "next_attempt": NEXT_ATTEMPT,
        "derived_from_clock": False,
        "consequence_committed": False,
        "authority_effect": "NONE_REFUSAL_ONLY",
    }


def head_epoch(chain: Mapping[str, Any], kernel: Any) -> tuple[str | None, dict[str, Any] | None]:
    """(epoch digits, None) for the verified chain's HEAD receipt, or (None, six-field refusal)."""
    receipts = chain.get("receipts") or []
    head = receipts[-1] if receipts else None
    if not isinstance(head, dict) or head.get("receipt_sha256") != chain.get("head_sha256"):
        return None, refusal("LEDGER_HEAD_UNVERIFIED", "the verified chain carries no HEAD receipt",
                             "supply an Organization ledger whose HEAD and chain verify")
    reference = head.get("hb_reference")
    epoch = reference.get("epoch") if isinstance(reference, dict) else None
    failure = kernel.supplied_epoch_failure(epoch, reference)
    if failure is not None:
        code, detail = failure
        return None, refusal(code, "HEAD " + str(head.get("receipt_sha256")) + ": " + detail,
                             "the Organization ledger HEAD records hb_reference.epoch as a supplied epoch "
                             "(ASCII digits, value >= 32, derived_from_clock exactly false); it is never "
                             "filled from a clock")
    return str(epoch), None


def ledger_head_epoch(source_root: Path, repo_ledger_root: Path,
                      org_ledger_root: Path | None = None) -> tuple[str | None, dict[str, Any] | None]:
    source = source_root.expanduser().resolve()
    if not (source / CONSUMER_REL).is_file():
        return None, refusal("LEDGER_HEAD_UNVERIFIED", "consumer not materialized: " + str(CONSUMER_REL),
                             "materialize " + str(CONSUMER_REL) + " in the source root")
    spec = importlib.util.spec_from_file_location("organization_ledger_head_epoch_consumer", source / CONSUMER_REL)
    consumer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(consumer)
    try:
        custody = consumer.ledger_custody(source, repo_ledger_root, org_ledger_root)
        chain = consumer.verify_organization_chain(custody)
    except consumer.ClaimFailClosed as exc:
        return None, refusal("LEDGER_HEAD_UNVERIFIED", exc.predicate + ": " + exc.detail, exc.repair)
    return head_epoch(chain, custody["organization_ledger"].kernel)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--repo-ledger-root", type=Path, required=True)
    parser.add_argument("--org-ledger-root", type=Path, default=None)
    args = parser.parse_args(argv)
    epoch, refused = ledger_head_epoch(args.source_root, args.repo_ledger_root, args.org_ledger_root)
    if refused is not None:
        print(json.dumps(refused, sort_keys=True))
        return 1
    print(epoch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
