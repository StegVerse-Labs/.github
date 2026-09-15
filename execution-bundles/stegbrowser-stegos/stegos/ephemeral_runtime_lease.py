"""Bounded StegOS lease subset for the StegBrowser invocation carrier.

Source semantics are pinned to StegVerse-Labs/StegOS main. This file contains
only the lease types consumed by SovereignLocalEventRuntimeAdapter and the
StegBrowser reusable runner. Authority effect remains NONE.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class RuntimeClass(str, Enum):
    CONTINUOUS = "CONTINUOUS"
    LEASED = "LEASED"
    EVENT_EPHEMERAL = "EVENT_EPHEMERAL"
    PURE_STATE_NO_RUNTIME = "PURE_STATE_NO_RUNTIME"

class LeaseProfile(str, Enum):
    INTAKE = "INTAKE"
    EGRESS = "EGRESS"

class RendezvousRequirement(str, Enum):
    REQUIRED = "REQUIRED"
    NOT_REQUIRED = "NOT_REQUIRED"

class BatchingMode(str, Enum):
    SINGLE = "SINGLE"
    BOUNDED_BATCH = "BOUNDED_BATCH"
    RENEWED_LEASE = "RENEWED_LEASE"

@dataclass(frozen=True)
class AuthorityBoundary:
    credential_authority: str = "TV/TVC"
    compute_authority_effect: bool = False
    transport_authority_effect: bool = False
    model_output_authority_effect: bool = False
    review_authority: bool = False
    publication_authority: bool = False
    master_record_authority: bool = False

    def validate(self) -> None:
        if self.credential_authority != "TV/TVC":
            raise ValueError("credential_authority_must_be_tv_tvc")
        if self.compute_authority_effect:
            raise ValueError("compute_must_be_non_authorizing")
        if self.transport_authority_effect:
            raise ValueError("transport_must_be_non_authorizing")
        if self.model_output_authority_effect:
            raise ValueError("model_output_must_be_non_authorizing")

@dataclass(frozen=True)
class LeaseRequest:
    lease_id: str
    trigger_id: str
    operation: str
    implementation_ref: str
    source_receipt_id: str
    consequence_id: str
    consequence_registry_hash: str
    generation: int = 1
    state_root_binding: str = ""
    profile: LeaseProfile = LeaseProfile.INTAKE
    runtime_class: RuntimeClass = RuntimeClass.EVENT_EPHEMERAL
    rendezvous: RendezvousRequirement = RendezvousRequirement.NOT_REQUIRED
    batching_mode: BatchingMode = BatchingMode.SINGLE
    persistent_host_required: bool = False
    participant_machine_required: bool = False
    developer_machine_required: bool = False
    stateful: bool = True
    max_operations: int = 1
    credential_mandate_required: bool = False
    protocol_response_schema_ref: str | None = None
    authority: AuthorityBoundary = field(default_factory=AuthorityBoundary)

    @property
    def idempotency_key(self) -> tuple[str, str, int]:
        return (self.source_receipt_id, self.consequence_id, self.generation)

    @property
    def public_reachability_required(self) -> bool:
        return self.profile == LeaseProfile.INTAKE and self.rendezvous == RendezvousRequirement.REQUIRED

    def validate(self) -> None:
        self.authority.validate()
        required = (self.lease_id, self.trigger_id, self.operation, self.implementation_ref, self.source_receipt_id, self.consequence_id, self.consequence_registry_hash)
        if not all(required) or self.generation <= 0:
            raise ValueError("lease_identity_incomplete")
        if self.runtime_class == RuntimeClass.EVENT_EPHEMERAL and self.persistent_host_required:
            raise ValueError("event_ephemeral_cannot_require_persistent_host")
        if self.max_operations <= 0:
            raise ValueError("max_operations_must_be_positive")
        if self.stateful and not self.state_root_binding:
            raise ValueError("stateful_lease_requires_state_root_binding")
        if self.profile == LeaseProfile.EGRESS and self.rendezvous != RendezvousRequirement.NOT_REQUIRED:
            raise ValueError("egress_rendezvous_must_be_not_required")

SOURCE_PROVENANCE = {
    "repository": "StegVerse-Labs/StegOS",
    "source_path": "stegos/ephemeral_runtime_lease.py",
    "source_blob_sha": "75ef57d9b885cfac74a48a11679683408abc3ae2",
    "subset_reason": "only types imported by manifest-bound StegBrowser EVENT_EPHEMERAL runner",
    "authority_effect": "NONE",
}
