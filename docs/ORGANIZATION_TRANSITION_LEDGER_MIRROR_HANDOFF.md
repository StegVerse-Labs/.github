# Organization Transition Ledger Mirror Handoff

Organization: `StegVerse-Labs`

Every state transition that occurs within the organization emits an organization-level receipt. Repository transitions remain owned and replayable in their originating repositories and retain their exact repository receipt linkage; canonical governed transitions that are not repository transitions are hash-bound directly as their own source transition and are not relabeled as repository transitions.

Contract: `.stegverse/transition-ledger/org-contract.json`  
Recorder/rollup: `resident-runtime/aggregate_repo_transition.py`

The organization ledger accepts:
- `stegverse.repo-transition-receipt/v1`
- `stegverse.canonical-state-transition-receipt/v1`

Both produce the existing `stegverse.organization-transition-receipt/v1` append-only/hash-linked chain. The receipt preserves the exact source receipt schema, source transition digest, transition identity, and previous organization receipt hash. Repository-specific fields remain populated only when the source really is a repository transition.

Under `ORGANIZATION-ROLE-RUNTIME-REALITY-DEPLOYMENT-001` the organization is the `runtime_reality_authority`, and this ledger root — under the organization ledger lock, written by manifest-directed append — is its locus. A transition within the organization is real when it is appended here.

`master-records` is the recorder of released organization batch receipts: it takes batches this organization has independently verified and released, for durable cross-organization custody and complex reconstruction. It is not a gate on this organization's runtime reality and is never awaited. An unavailable recorder yields `DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION` with `always_on_receiver_required: false`; it does not downgrade an appended organization transition. Canonical state-transition custody still records and verifies this organization receipt before attempting the Master Records lane, and a Master Records closure remains its own evidence class that organization recording never implies. Organization replay remains independent of ecosystem replay. Recording creates no transition, execution, credential, routing, publication, or governance authority.

See `docs/ORGANIZATION_ROLE_RUNTIME_REALITY_DEPLOYMENT.md`.

Only the organization receipt and evidence required for ecosystem reconstruction propagate upward. Absence of retained runtime receipts remains UNKNOWN until authentic runtime evidence establishes the state.
