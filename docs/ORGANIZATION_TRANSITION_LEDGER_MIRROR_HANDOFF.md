# Organization Transition Ledger Mirror Handoff

Organization: `StegVerse-Labs`

Every state transition that occurs within the organization emits an organization-level receipt. Repository transitions remain owned and replayable in their originating repositories and retain their exact repository receipt linkage; canonical governed transitions that are not repository transitions are hash-bound directly as their own source transition and are not relabeled as repository transitions.

Contract: `.stegverse/transition-ledger/org-contract.json`  
Recorder/rollup: `resident-runtime/aggregate_repo_transition.py`

The organization ledger accepts:
- `stegverse.repo-transition-receipt/v1`
- `stegverse.canonical-state-transition-receipt/v1`

Both produce the existing `stegverse.organization-transition-receipt/v1` append-only/hash-linked chain. The receipt preserves the exact source receipt schema, source transition digest, transition identity, and previous organization receipt hash. Repository-specific fields remain populated only when the source really is a repository transition.

Canonical state-transition custody records and verifies this organization receipt before progressing to Master Records. Organization replay remains independent of ecosystem replay. Recording creates no transition, execution, credential, routing, publication, or governance authority.

Only the organization receipt and evidence required for ecosystem reconstruction propagate upward. Absence of retained runtime receipts remains UNKNOWN until authentic runtime evidence establishes the state.
