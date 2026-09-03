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

If no valid lease is already present, the admitted worker may request issuance from an already-local clean TVC source containing merge `d495b67d1c322c3fdd8c9bb6db75657783e19c0c`. Under ProcessWorkerAdapter execution, the requested target is exactly `$STEGVERSE_BOUND_STATE_ROOT/autonomy/lease.active.json`; the adapter later projects only admitted bound-state paths after claim/fence validation. The worker declares `STEGVERSE_SV001_AUTONOMY_LEASE_AUTHORITY=TV/TVC` only to the TVC child process. That declaration requests TVC evaluation; it does not let `.github` construct or widen the lease.

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
-> current local TVC authority source >= d495b67d1c322c3fdd8c9bb6db75657783e19c0c
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
TVC lease authority source: MERGED `d495b67d1c322c3fdd8c9bb6db75657783e19c0c`
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

The resident worker may now request, but never self-issue, the exact TV/TVC-governed single-cycle autonomy lease when no valid canonical lease is present. The request path is constrained to an already-local clean TVC source containing merge `d495b67d1c322c3fdd8c9bb6db75657783e19c0c`, the exact TV request hash, and the TVC dispatcher transition `TVC_SV001_BOUNDED_AUTONOMY_LEASE_ISSUED`.

The request mechanism does not change the established source-completion evidence from PR #740/#743 and does not establish a live lease or runtime activation. Authentic completion still requires deployment-local issuance/observation, resident request consumption, an autonomy-cycle receipt, Master Records reconstruction, and SV002 disposition.


## Fenced bound-state lease carrier — 2026-09-02

TVC merge `d495b67d1c322c3fdd8c9bb6db75657783e19c0c` closes the sandbox boundary. The SV001 worker now treats `STEGVERSE_BOUND_STATE_ROOT` as its state root when invoked by ProcessWorkerAdapter. TVC emits the exact lease into `autonomy/lease.active.json` within that temporary root; the adapter validates the resulting state delta and projects only admitted paths. Direct resident execution outside the adapter retains the canonical same-user lease path.

This prevents the worker or TVC child from bypassing ProcessWorkerAdapter confinement through `$HOME` while preserving TVC as the lease issuer.


## 2026-09-02 final source/control closure

The autonomous TVC lease-acquisition and fenced bound-state control continuation is now merged:

- PR #749 — executable TVC lease acquisition continuation — merged as `256e91b7980741acc6de91599b59e441edc36f37`; validation runs `33634043037` and `33634043026` PASS.
- TVC PR #282 — fenced bound-state lease target — merged as `d495b67d1c322c3fdd8c9bb6db75657783e19c0c`; TVC credential-model validation `33633857236` PASS.
- PR #751 — final adapter/handoff/request/test closure — merged as `b5fb62485722eaee57465e88af97921898b95566`; organization-control `33634283779` PASS and heartbeat `33634283783` PASS.

Repository/source construction for the first SV001 bounded-autonomy cycle is therefore closed. Remaining completion is runtime evidence only and must not be inferred from these merges.

Current machine-owned evidence gates:

```text
TVC lease issuance receipt: NOT OBSERVED
resident request consumption receipt: NOT OBSERVED
SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED receipt: NOT OBSERVED
Master Records reconstruction PASS: NOT OBSERVED
SV002 adversarial observation/disposition: NOT OBSERVED
```

The queued resident request remains the canonical next machine action. No human/manual execution is authorized or required by this handoff.


## Automatic downstream evidence continuation — 2026-09-02

The post-execution chain is source-implemented under issue #761 and `docs/STEGVERSE_001_EVIDENCE_CHAIN_MIRROR_HANDOFF.md`.

Exact source floors:

- Master Records resident custody intake: `d593c920c1630aa5da20cc2622196f8676a74afd`
- SV002 deterministic adversarial evaluator: `786323f16e36346c69b2215894086515d7b1d58e`

After `SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED`, the resident consumer invokes the downstream continuation. A later `ALREADY_CONSUMED` request does not re-execute autonomy; it retries only Master Records custody/reconstruction and SV002 observation/disposition.

The continuation script is included in sovereign bootstrap, source-refresh, and native-service materialization manifests. No manual receipt transfer is required by source design. Authentic completion remains NOT OBSERVED until deployment-local receipts exist.


## Active machine progression path — 2026-09-02

The SV001 goal must not be represented as “wait for runtime evidence.”

After issue #794, an already-authorized sovereign resident may actively execute the two required bounded progression stages through the existing portable one-shot bridge:

```text
1. refresh + dispatch one_shot_resident_stack_activation
   -> complete source materialization / StegDeploy / resident bootstrap

2. refresh + dispatch stegverse001_bounded_autonomy
   -> TVC lease request if needed
   -> WorkerCoordinator claim/fence
   -> Beta_Orionis bounded continuity-audit cycle
```

The resulting receipts are completion evidence for performed work; they are not the work itself.

If stage 1 or stage 2 returns a nonterminal machine state, the next task is to repair/execute that specific failed transition and re-run the bounded selector. Do not replace that with observation-only polling.

## Single-command bounded activation progression — 2026-09-02

Issue #801 adds the executable progression:

```text
python scripts/run_stegverse001_activation_progression.py \
  --source-root <already-local-current-.github> \
  --runtime-root <sovereign-runtime>
```

One invocation performs at most two active targeted dispatches:

```text
Stage 1: one_shot_resident_stack_activation
  require: state COMPLETED|ALREADY_CONSUMED + activation_complete=true
  otherwise: stop and name the actual next machine transition

Stage 2: stegverse001_bounded_autonomy
  execute only after Stage 1 is complete
  terminal when the consumer reports terminal_execution_observed=true
```

The procedure does not loop, watch, poll, or sleep waiting for evidence. If a stage is nonterminal, its `next_required_machine_transition` names the work to execute/repair before a later bounded invocation.

After terminal SV001 execution, the already-merged consumer continues Master Records custody/reconstruction and SV002 adversarial disposition independently without re-running terminal autonomy.

## Stack-activation execution-order gate — 2026-09-02

Issue #803 makes the staged execution order enforceable rather than advisory.

When the current one-shot resident-stack request is present, the SV001 consumer now requires its matching consumption receipt to prove `activation_complete=true` before invoking WorkerCoordinator/autonomy execution.

```text
one-shot request present + activation incomplete
-> SV001 state STACK_ACTIVATION_PENDING
-> runtime_execution_attempted=false
-> next_required_machine_transition=EXECUTE_ONE_SHOT_RESIDENT_STACK_ACTIVATION

one-shot activation COMPLETE
-> completion receipt persisted
-> immediate bounded progression helper invoked once
-> Stage 1 re-enters as ALREADY_CONSUMED
-> Stage 2 executes stegverse001_bounded_autonomy
```

An already-terminal SV001 receipt still wins and is never re-executed; downstream Master Records/SV002 continuation remains independently retryable.

## Current external execution boundary — 2026-09-02

The source/runtime path is now explicit through merge `3e9aec9680d159a1419aeebb52022316a3b392ed`.

The next work is **not** to watch for the five receipts. The next work is to execute:

```text
python scripts/run_stegverse001_activation_progression.py \
  --source-root <current-local-.github> \
  --runtime-root <sovereign-runtime>
```

on the actual non-hosted sovereign resident execution surface.

The current ChatGPT/GitHub connector surface can mutate and validate repository state but cannot launch a local StegVerse process on that sovereign node. GitHub Actions may not be substituted because they have no production/runtime authority.

If the native resident is already active with the current local source, its recurring machine dispatch can perform the same work without operator intervention. If it is not active/current, the external prerequisite is to make that resident execution surface available from the current source. Once the resident is active, Stage 1 -> Stage 2 -> Master Records -> SV002 is machine-owned.

Receipt absence is only diagnostic:

```text
no progression receipt -> progression process did not execute
STACK_ACTIVATION_INCOMPLETE -> execute/repair the named Stage-1 transition
SV001_AUTONOMY_EXECUTION_INCOMPLETE -> execute/repair the named Stage-2 transition
terminal SV001 -> downstream MR/SV002 continuation executes independently
```

Watching, waiting, or polling is not an authorized completion action.


## Canonical HB runtime observability consumer binding — 2026-09-02

SV001 is a consumer of the shared organization contract, not an independent runtime-signal project.

Canonical owner surfaces:

```text
management/HB_RUNTIME_PRESENCE_RESIDENT_OBSERVABILITY_CONTRACT.json
heartbeat_runtime/runtime_presence_projection.py
scripts/project_hb_runtime_presence.py
canonical validation: tests/test_runtime_presence_projection.py
resident-local extension: merged via StegVerse-Labs/.github#814 / PR #822 @ 6358375c81fedb579cb6fcac59946268ea485ebb
```

SV001 predicate mapping remains distinct:

```text
resident_process_alive_supervised
  <- shared resident-presence / direct runtime activation evidence only

node_runtime_fresh
  <- HB reference + resident/worker observation correlation only

governed_request_consumed
  <- receipts/sovereign-host/stegverse001-bounded-autonomy-request-consumption.latest.json

runtime_execution_completed
  <- SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED task-specific receipt

receipt_retained
  <- task-specific retained evidence path

replay_reconstruction_proven
  <- Master Records reconstruction PASS

SV002 adversarial disposition
  <- independent SV002 evidence
```

Neither HB progression, source installation, request-file presence, merge, CI, nor projection-file presence satisfies any of those machine predicates.

This session's exact currently unresolved first predicate is `resident_process_alive_supervised`. It must be supplied by the shared canonical runtime-presence contract when authentic deployment-local activation/liveness evidence exists.


## Canonical observability reference reconciliation — 2026-09-02

The earlier SV001 prose still named the superseded experimental projection surfaces
`org-kernel/runtime_observability.py` and `scripts/project_runtime_observability.py`.
The organization contract now explicitly marks those surfaces superseded.

SV001 therefore binds only to the current canonical resident-local projection:

```text
management/HB_RUNTIME_PRESENCE_RESIDENT_OBSERVABILITY_CONTRACT.json
-> heartbeat_runtime/runtime_presence_projection.py
-> scripts/project_hb_runtime_presence.py
-> tests/test_runtime_presence_projection.py
```

This is a source-reference correction only. It does not change any runtime predicate,
claim/fence authority, TV/TVC credential authority, or activation state.

## Shared observability registry installation — 2026-09-03

The SV001 bounded-autonomy lane is now installed in the canonical shared runtime-observability consumer registry:

```text
consumer descriptor:
  control/runtime-observability-consumers/stegverse001-bounded-autonomy-runtime-001.json
registration issue: #849
registration PR: #856
registration merge: 3c798be98e931306867d24a870bffb218e96ff96
shared owner: #814
```

This registration changes no runtime truth. The first unresolved shared predicate remains `resident_process_alive_supervised`, followed by independently observed node freshness, request consumption, `SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED`, retained receipt, Master Records reconstruction, and SV002 disposition.

Source, merge, CI, HB progression, request presence, or registry membership cannot satisfy those predicates.


## Same-device execution correction — 2026-09-03

Architecture invariant: `StegVerse-Labs/.github#201`.

The earlier wording that treated a separate "sovereign resident execution surface" as a possible external prerequisite is superseded.

```text
required execution scope: SAME_DEVICE
requires_other_machine: false
other StegVerse machine allowed as required executor: false
remote machine role: OPTIONAL only
blocker when another machine is required:
  OTHER_MACHINE_REQUIRED
  INCOMPLETE_REQUIRES_CONTINUED_BUILD
```

The existing Python resident progression remains valid as a reference implementation and for same-device hosts that can execute it locally. It MUST NOT become a requirement that the active device delegate routine activation/execution to another machine.

For the current device class, completion therefore requires an equivalent same-device StegOS execution path that preserves the same TV/TVC lease, WorkerCoordinator admission/claim/fence, receipt, Master Records, and SV002 evidence semantics. Until that same-device path is independently installed and observed, this lane is implementation-incomplete rather than "waiting for another sovereign machine."

No runtime evidence is claimed by this correction.
