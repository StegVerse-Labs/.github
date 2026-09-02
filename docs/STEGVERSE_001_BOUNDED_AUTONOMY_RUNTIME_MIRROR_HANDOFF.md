# StegVerse-001 Bounded Autonomy Runtime Mirror Handoff

Updated: 2026-09-02
Repository: StegVerse-Labs/.github
Issue: #739
Goal: STEGVERSE001-BOUNDED-AUTONOMY-RUNTIME-001
Formal predecessor: Data-Continuation/formalism-tests Stage 35
Observer successor: SV002 adversarial observation
Custody successor: master-records/orchestration

## Source of truth

This file governs the first authentic bounded-autonomy runtime lane for StegVerse-001 / Beta_Orionis and is subordinate to `docs/ORG_MIRROR_HANDOFF.md`.

## First live autonomy objective

The first runtime goal is intentionally narrow:

```text
observe resident continuity state
-> autonomously discover continuity-audit work
-> construct a bounded two-step plan
-> validate plan against an externally issued lease
-> read current carrier/worker state
-> emit a hash-bound autonomy-cycle receipt
-> stop
```

This is real self-directed task discovery and planning, but not external side-effect autonomy.

## Lease boundary

The runtime MUST observe an external local lease at:

`STEGVERSE_SV001_AUTONOMY_LEASE`

or default:

`~/.stegverse/autonomy/stegverse001/lease.active.json`

If neither canonical lease exists, the admitted worker may request issuance from an already-local clean TVC source containing merge `92c2d6085cec2b7561d6c1f08ab157894a232340`. The worker declares `STEGVERSE_SV001_AUTONOMY_LEASE_AUTHORITY=TV/TVC` only to the TVC child process. That declaration requests TVC evaluation; it does not let `.github` construct or widen the lease.

Source merge, resident request existence, WorkerCoordinator admission, heartbeat presence, or task success does not create this lease.

The lease must identify StegVerse-001 / Beta_Orionis, be ACTIVE and unexpired, preserve TV/TVC authority, keep DENY reachable, require receipts, and explicitly allow the transition classes used by the cycle.

Missing lease => `HANDOFF_READY`.
Expired/revoked/invalid lease => fail closed.

## Authority invariant

```text
agency != autonomy
autonomy != authority
authority != sovereignty
```

The worker may not:
- self-accredit;
- create/widen its lease;
- mutate repositories;
- perform financial binding;
- create/use non-TV/TVC credentials;
- use external network access;
- claim sovereign authority;
- treat correct output as proof of authorized execution.

## Machine path

```text
resident source refresh
-> resident request dispatcher
-> stegverse001_bounded_autonomy consumer
-> existing refresh_and_execute_resident_task.py
-> WorkerCoordinator independent claim/fence
-> autonomy worker
-> current local TVC authority source >= 92c2d6085cec2b7561d6c1f08ab157894a232340
-> TVC dispatcher request for exact hash-bound single-cycle lease when absent
-> independent local lease validation
-> self-directed continuity audit
-> receipt
-> Master Records custody/reconstruction
-> SV002 adversarial observation/disposition
```

## Current source files

- `handoffs/SHWP-STEGVERSE001-BOUNDED-AUTONOMY-RUNTIME-001.json`
- `control/worker-registry.d/stegverse001-bounded-autonomy-runtime-001.json`
- `control/process-worker-adapters.d/stegverse001-bounded-autonomy-runtime-001.json`
- `control/resident-execution-request.d/stegverse001-bounded-autonomy-runtime-001.json`
- `control/task-vectors/SHWP-STEGVERSE001-BOUNDED-AUTONOMY-RUNTIME-001.json`
- `workers/stegverse001_bounded_autonomy_runtime_worker.py`
- `scripts/consume_stegverse001_bounded_autonomy_request.py`
- `cost-basis/worker-runtime/stegverse001-bounded-autonomy-runtime.json`

## Authentic completion

Runtime activation is NOT established by source or CI.

The first autonomy cycle is authentic only when a non-hosted resident emits:

`~/.stegverse/state/stegverse001-bounded-autonomy/receipts/latest.json`

with transition:

`SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED`

and Master Records later independently reconstructs the exact receipt/plan/observation chain.

## Current state

```text
Stage 35 formal proof: MERGED / PR VALIDATED
SV002 adversarial-observation source: MERGED
runtime task source: SOURCE_MERGED_VALIDATED
runtime source PR: #740
runtime source merge: 493e4558a39eb516e63fee496f06d6ca8f973ed8
validation:
  33607420338 Cross-Framework Current-Basis Resident Request Validation SUCCESS
  33607420274 Validate organization control plane SUCCESS
  33607420254 Heartbeat Worker Project SUCCESS
external live lease: NOT OBSERVED
resident request consumption: NOT OBSERVED
autonomy-cycle receipt: NOT OBSERVED
TV policy request source: MERGED `a8ed178fd5fc5b131491e41452256323c302ba3f`
TVC lease authority source: MERGED `92c2d6085cec2b7561d6c1f08ab157894a232340`
Master Records custody source: MERGED `65f97e867a09c3e5da80ef74b2b43ee810821667`
Master Records custody: NOT OBSERVED
SV002 disposition: NOT OBSERVED
```


## 2026-09-02 source merge evidence

PR #740 merged as `493e4558a39eb516e63fee496f06d6ca8f973ed8` after all three observed PR validation lanes passed:

- `33607420338` — Cross-Framework Current-Basis Resident Request Validation — SUCCESS
- `33607420274` — Validate organization control plane - No GitHub Token Authority — SUCCESS
- `33607420254` — Heartbeat Worker Project - Validation Only / No GitHub Token Authority — SUCCESS

This closes the repository-source implementation gate only. It does not establish an external live autonomy lease, resident request consumption, an autonomy-cycle receipt, Master Records custody/reconstruction, or SV002 disposition.


## 2026-09-02 TVC lease-request continuation

The resident worker may now request, but never self-issue, the exact TV/TVC-governed single-cycle autonomy lease when no valid canonical lease is present. The request path is constrained to an already-local clean TVC source containing merge `92c2d6085cec2b7561d6c1f08ab157894a232340`, the exact TV request hash, and the TVC dispatcher transition `TVC_SV001_BOUNDED_AUTONOMY_LEASE_ISSUED`.

The request mechanism does not change the established source-completion evidence from PR #740/#743 and does not establish a live lease or runtime activation. Authentic completion still requires deployment-local issuance/observation, resident request consumption, an autonomy-cycle receipt, Master Records reconstruction, and SV002 disposition.
