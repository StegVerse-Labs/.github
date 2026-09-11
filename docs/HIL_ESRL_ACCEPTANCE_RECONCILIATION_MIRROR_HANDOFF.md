# HIL ESRL Acceptance Reconciliation Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Issue: `#1354`
Parent task: `SHWP-HIL-SOVEREIGN-RECEIVER-001`
Parent handoff: `docs/HIL_RESIDENT_SESSION_MANIFOLD_ACTIVATION_MIRROR_HANDOFF.md`
Current COSV: `50000000103000`

## Purpose

Prewire the exact canonical state transition that becomes lawful only after the physical current-iPhone ESRL artifact is accepted by `scripts/intake_hil_browser_esrl_evidence.py`.

This is a non-mutating preparation surface. It does not claim the physical ESRL predicate is satisfied.

## Implementation

`scripts/reconcile_hil_esrl_acceptance.py` consumes:

- an accepted `stegverse.hil-browser-esrl-evidence-intake/v1` receipt;
- the canonical task vector `control/task-vectors/SHWP-HIL-SOVEREIGN-RECEIVER-001.json`;
- the canonical worker registry fragment `control/worker-registry.d/hil-sovereign-receiver-001.json`.

It fails closed unless the parent is still exactly at `50000000103000`, has exactly three blockers, remains `HANDOFF_READY`, is not archive eligible, and has no evidence/activation/propagation terminal state.

When those inputs and an authentic accepted ESRL intake receipt agree, the evaluator proposes exactly one state change:

```text
previous vector: 50000000103000
remove: AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED
proposed vector: 50000000102000
remaining blockers:
  POST_RESTART_EXACT_BYTE_PROOF_NOT_YET_PRESERVED
  TVC_HIL_LIFECYCLE_HANDOFF_NOT_YET_PROVEN
next runtime stage: HIL_RECEIVER_READY_AND_CUSTODY
```

It explicitly preserves:

- `HANDOFF_READY`;
- `archive_eligible=false`;
- `activated=false`;
- `propagated=false`;
- post-restart exact-byte proof not observed;
- TVC lifecycle receipt not observed;
- broader HIL lifecycle incomplete.

The output is `stegverse.hil-esrl-acceptance-reconciliation-proposal/v1` with `mutation_performed=false`. Repository state must be mutated only in a separately reviewed reconciliation change after the authentic intake receipt exists.

## Relationship to post-ESRL readiness

PR `#1353`, merged at `8ce03ba2d7597f844cdf791d0201f2aaf1273a24`, installed `scripts/evaluate_hil_post_esrl_readiness.py`. That classifier determines the first unsupported downstream runtime stage after accepted ESRL evidence.

This reconciliation proposal is the preceding canonical bookkeeping bridge: accepted ESRL evidence first reduces the parent blocker count from three to two, then the readiness evaluator directs execution to receiver READY/custody without rerunning G25.

## Tests

`tests/test_reconcile_hil_esrl_acceptance.py` verifies:

- exact accepted ESRL evidence proposes only the ESRL blocker removal;
- `50000000103000 -> 50000000102000` is the only admitted vector transition;
- unaccepted ESRL fails closed;
- premature post-restart evidence promotion fails closed;
- unexpected current vector fails closed;
- blocker-set drift fails closed.

## README review

README was re-reviewed. No prose change is required: this is an internal non-mutating state-reconciliation helper and does not introduce a new public runtime interface or change the existing execution/governance architecture.

## Remaining parent boundary

Until an exact physical ESRL artifact is accepted, the canonical parent remains unchanged at `50000000103000` with three blockers. Source, tests, CI, merge, or this proposal generator cannot discharge the ESRL blocker.
