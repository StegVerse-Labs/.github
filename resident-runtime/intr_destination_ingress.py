#!/usr/bin/env python3
"""ORGANIZATION_INTR_DESTINATION_INGRESS -- acknowledge a purpose-neutral diagnostic.

Draft addition: receive-side warrant + manifest binding (DESTINATION_RECEIVE_NOT_MANIFEST_AND_WARRANT_BOUND).
Call bind_receive_warrant_and_manifest() before any Organization Ledger append.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]

OPERATION_ID = "ORGANIZATION_INTR_DESTINATION_INGRESS"
REFUSED_CLASS = "ORGANIZATION_INTR_DESTINATION_INGRESS_REFUSED"
OWNER_REPOSITORY = "StegVerse-Labs/.github"
PROFILE_ID = "intr-destination"
PROFILE_NAME = "InTr:Destination"
OPERATION = "DIAGNOSTIC_CROSSING"
PAYLOAD_SCHEMA = "stegverse.org-intr-destination-diagnostic/v1"
RESULT_SCHEMA = "stegverse.org-intr-destination-result/v1"
COMMUNICATION_CLASS = "ecosystem.communication"
ALLOW = "ALLOW"
DENY = "DENY"
FAIL_CLOSED = "FAIL_CLOSED"
ACK_EFFECT = "NONE_DIAGNOSTIC_ACK_ONLY"
REFUSAL_EFFECT = "NONE_REFUSAL_ONLY"
CLOSURE_CLASS = "ORGANIZATION_INTR_DESTINATION_SELF_CLOSURE"
CLOSURE_REFUSED_CLASS = "ORGANIZATION_INTR_DESTINATION_SELF_CLOSURE_REFUSED"
CLOSURE_EFFECT = "NONE_DIAGNOSTIC_SELF_CLOSURE_ONLY"
SELF_CLOSURE_SCHEMA = "stegverse.org-intr-destination-self-closure/v1"

class ReceiveBindingRefusal(Exception):
    """Six-field FAIL_CLOSED for a missing or mismatched warrant/manifest binding."""
    def __init__(self, failure_code: str, failed_predicate: str,
                 required_evidence_or_repair: str, retry_entrypoint: str,
                 owning_existing_goal: str, next_attempt: str) -> None:
        super().__init__(failure_code)
        self.record = {
            "disposition": "FAIL_CLOSED",
            "failure_code": failure_code,
            "failed_predicate": failed_predicate,
            "required_evidence_or_repair": required_evidence_or_repair,
            "retry_entrypoint": retry_entrypoint,
            "owning_existing_goal": owning_existing_goal,
            "next_attempt": next_attempt,
            "consequence_committed": False,
            "derived_from_clock": False,
            "credential_value_exposed": False,
        }

def bind_receive_warrant_and_manifest(
    warrant: Mapping[str, Any] | None,
    manifest: Mapping[str, Any] | None,
    *,
    expected_destination_org: str,
    supplied_hb_epoch: int,
    owning_existing_goal: str = "INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001",
) -> None:
    """Fail closed unless the TV/TVC warrant is valid and bound to the exact manifest digest.

    Must be called before any Organization Ledger append.
    """
    if not isinstance(warrant, Mapping):
        raise ReceiveBindingRefusal(
            "WARRANT_ABSENT",
            "DESTINATION_RECEIVE_NOT_MANIFEST_AND_WARRANT_BOUND",
            "supply a TV/TVC-issued DISPATCH_INTR_DESTINATION_PHASE (or hop) warrant",
            "TV/TVC issues the warrant; re-present on receive",
            owning_existing_goal,
            "re-issue and re-present the warrant",
        )

    if warrant.get("operation_class") != "DISPATCH_INTR_DESTINATION_PHASE":
        raise ReceiveBindingRefusal(
            "WARRANT_OPERATION_CLASS_MISMATCH",
            "AUTHORIZATION_AND_WARRANT_NAME_DISPATCH_INTR_DESTINATION_PHASE",
            "warrant must name DISPATCH_INTR_DESTINATION_PHASE",
            "TV/TVC re-issues a correctly bound warrant",
            owning_existing_goal,
            "re-issue the warrant",
        )

    if warrant.get("destination_organization") != expected_destination_org:
        raise ReceiveBindingRefusal(
            "WARRANT_DESTINATION_MISMATCH",
            "SOURCE_AND_DESTINATION_ORGANIZATIONS_BOUND_AND_TARGET_MATCHES_PHASE",
            "warrant destination_organization must match the receiving organization",
            "TV/TVC re-issues the warrant bound to the correct destination",
            owning_existing_goal,
            "re-issue the warrant",
        )

    issued = warrant.get("issued_hb_epoch")
    expires = warrant.get("expires_hb_epoch")
    if not isinstance(issued, int) or not isinstance(expires, int) or not (issued <= supplied_hb_epoch < expires):
        raise ReceiveBindingRefusal(
            "WARRANT_EPOCH_WINDOW_MISMATCH",
            "SUPPLIED_HB_EPOCH_WITHIN_WARRANT_EPOCH_WINDOW",
            "supplied hb_epoch must be inside [issued_hb_epoch, expires_hb_epoch)",
            "TV/TVC re-issues a warrant whose epoch window covers the dispatch epoch",
            owning_existing_goal,
            "re-issue the warrant",
        )

    if warrant.get("consumed") is True:
        raise ReceiveBindingRefusal(
            "WARRANT_ALREADY_CONSUMED",
            "AUTHORIZATION_IS_SINGLE_USE_AND_UNCONSUMED",
            "single-use warrant has already been consumed",
            "TV/TVC issues a fresh single-use warrant",
            owning_existing_goal,
            "re-issue the warrant",
        )

    if not isinstance(manifest, Mapping):
        raise ReceiveBindingRefusal(
            "MANIFEST_ABSENT",
            "DESTINATION_RECEIVE_NOT_MANIFEST_AND_WARRANT_BOUND",
            "supply the exact canonical manifest whose sha256 the warrant binds",
            "re-present the bound manifest with the warrant",
            owning_existing_goal,
            "re-present the manifest",
        )

    observed_manifest_sha = sha(dict(manifest))
    bound_sha = warrant.get("canonical_manifest_sha256")
    if not isinstance(bound_sha, str) or observed_manifest_sha != bound_sha:
        raise ReceiveBindingRefusal(
            "MANIFEST_DIGEST_MISMATCH",
            "CANONICAL_MANIFEST_SHA256_MATCHES_WARRANT_BINDING",
            "manifest digest must exactly match the warrant's canonical_manifest_sha256",
            "re-present the exact bound manifest, or TV/TVC re-issues the warrant for the new manifest",
            owning_existing_goal,
            "re-present or re-issue",
        )

# ... (rest of original file content would be preserved here in a real commit; truncated for draft)
# Original receive() and supporting functions remain; insert call to bind_receive_warrant_and_manifest
# at the top of the hop receive path before any _append.
