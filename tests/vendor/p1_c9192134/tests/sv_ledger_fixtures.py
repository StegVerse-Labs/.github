"""Org-ledger fixtures in the real field layout (StegVerse-Labs/.github#3255 head 75fc4ddd; runtime files unchanged from main).

Built with the real side-effect-free functions where they exist:
  aggregate_repo_transition.verify_source (resident-runtime/aggregate_repo_transition.py:627-651) for the org receipt's
  source fields, kernel.hb_reference(epoch=...) (org-kernel/kernel.py:68-74) for hb_reference, ledger_store.receipt_key /
  source_key / HEAD_KEY (resident-runtime/ledger_store.py:44-61) for addressing.
The append functions themselves (aggregate_repo_transition._append_locked :1038-1095, .stegverse/transition-ledger/emit.py
::append :84-126) need a ledger store and stamp observed_at from the host clock (:1083), so their body layout is mirrored
exactly here: repo receipt = emit.py:116-117, org receipt = aggregate_repo_transition.py:1073-1089 (observed_at is a
fixture constant, never a clock read). HEAD.json mirrors :1092.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, rel):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


agg = _load("aggregate_repo_transition_fx", "resident-runtime/aggregate_repo_transition.py")
kernel, ledger_store, sha = agg.kernel, agg.ledger_store, agg.sha
FIXTURE_OBSERVED_AT = "FIXTURE-observed_at-not-a-clock-read"  # :1083 stamps datetime.now(); fixtures read no clock


def repo_receipt(evidence, hb_epoch, *, transition_id="sv-check-receipt:fixture", previous=None,
                 repository="StegVerse-Labs/.github"):
    """emit.py:116-117 (repository from the repo contract C["repository"])."""
    b = {"schema": "stegverse.repo-transition-receipt/v1", "repository": repository, "transition_id": transition_id,
         "transition_class": "SV_CHECK_RECEIPT_APPEND", "predecessor_state_sha256": "sha256:" + "0" * 64,
         "successor_state_sha256": sha(evidence), "evidence": evidence if evidence is not None else {},
         "authority_effect": "NONE", "hb_reference": kernel.hb_reference(epoch=hb_epoch), "previous_receipt_sha256": previous}
    return {**b, "receipt_sha256": sha(b)}


def org_receipt(source_receipt, hb_epoch, *, boundary_evidence=None, previous=None, custody_generation=1,
                hb_reference=None):
    """aggregate_repo_transition.py:1073-1089 over the real verify_source fields (:627-651)."""
    source = agg.verify_source(source_receipt)
    body = {"schema": "stegverse.organization-transition-receipt/v1", "organization": agg.C["organization"], **source,
            "org_transition_class": "ORGANIZATION_STATE_TRANSITION",
            "predecessor_org_state_sha256": previous, "successor_org_state_sha256": source["source_transition_sha256"],
            "boundary_evidence": dict(boundary_evidence or {}), "authority_effect": "NONE",
            "hb_reference": hb_reference if hb_reference is not None else kernel.hb_reference(epoch=hb_epoch),
            "observed_at": FIXTURE_OBSERVED_AT, "previous_receipt_sha256": previous, "custody_generation": custody_generation}
    return {**body, "receipt_sha256": sha(body)}


def boundary(operation="sv_check_receipt"):
    return {"operation": operation, "profile_id": "fixture-profile", "disposition": "ALLOW", "communication_id": "fixture-communication"}


def ledger_objects(commit, org, repo=None, *, head=True):
    """The bytes a read of refs/stegverse/organization-ledger at `commit` returns, keyed "<commit>:<path>"."""
    out = {}
    key = ledger_store.receipt_key(org["receipt_sha256"])
    out[commit + ":" + key] = (json.dumps(org, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    if repo is not None:
        out[commit + ":" + ledger_store.source_key(repo["receipt_sha256"])] = \
            (json.dumps(repo, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    if head:
        out[commit + ":" + ledger_store.HEAD_KEY] = json.dumps(
            {"organization": agg.C["organization"], "receipt_sha256": org["receipt_sha256"], "receipt_path": key}).encode()
    return out


def org_ref(commit, org):
    return "refs/stegverse/organization-ledger@%s:%s" % (commit, ledger_store.receipt_key(org["receipt_sha256"]))
