# HB Machine Continuation Mirror Handoff

Updated: 2026-08-31

## Authority

```text
goal_id: HB-MACHINE-CONTINUATION-001
repository: StegVerse-Labs/.github
canonical_branch: main
implementation_branch: fix/hb-machine-continuation-current-main-20260902
parent_handoffs:
  - docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
  - docs/ORG_MIRROR_HANDOFF.md
  - LOCAL_SOURCE_GENERATION_EXECUTOR_MIRROR_HANDOFF.md
credential_authority: TV/TVC
github_token_runtime_authority: NONE
heartbeat_grants_execution_authority: false
authority_effect: NONE_TRIGGER_ONLY
```

## Goal

Restore automatic machine-owned continuation using the canonical 100 Hz HeartBeat reference instead of an external wall-clock monitor.

The derived continuation signal is synchronization/trigger metadata only. It may cause the already-running resident worker loop to revisit already-admitted work, but it cannot grant admission, claim, fence, credential, repository, merge, publication, or consequence authority.

## Canonical sequence

```text
HB32 protocol anchor / 100 Hz
-> deterministic continuation window
-> non-authorizing continuation trigger
-> canonical WorkerCoordinator cycle
-> existing independently admitted task control
-> existing resident request dispatcher
-> task-specific workers / source-generation chain / TV-TVC authority as applicable
-> receipts / checkpoints / reconstruction
```

Default continuation cadence:

```text
100 Hz * 3600 seconds = 360000 HB quanta
```

The cadence is derived from the HB protocol reference. Wall-clock scheduling is not authority and no ChatGPT automation is part of this implementation.

## Required implementation

```text
heartbeat_runtime/machine_continuation.py
scripts/run_worker_runtime.py
tests/test_hb_machine_continuation.py
HB_MACHINE_CONTINUATION_MIRROR_HANDOFF.md
```

## Invariants

```text
HB progression remains OSCILLATOR_ONLY
continuation trigger grants authority: false
worker/task authority remains WorkerCoordinator + existing handoffs
credential authority remains TV/TVC
GitHub Actions runtime authority: NONE
third-party scheduler required: false
targeted WorkerCoordinator invocations do not recursively dispatch continuation
dry-run does not persist continuation state or dispatch requests
one continuation dispatch per derived HB window
missed windows collapse to the current derived window rather than replaying every missed window
```

## Completion gates

```text
source implementation: IMPLEMENTED_CURRENT_MAIN
focused tests: ADDED / VALIDATION PENDING
hosted validation: PENDING_CURRENT_HEAD
merge: PENDING
authentic resident continuation receipt: PENDING / runtime evidence only
```


## 2026-09-02 current-main continuation

The original implementation branch/PR #688 was not merged and predates substantial resident-runtime changes. This current-main continuation preserves its non-authorizing HB-derived window semantics while integrating with the current local request dispatcher rather than replacing current immediate request sweeps.

The HB-derived continuation is therefore an additional deterministic re-evaluation opportunity for already-registered resident work, not a second scheduler and not an admission surface. Authentic resident continuation remains separately observable only from deployment-local receipts.
