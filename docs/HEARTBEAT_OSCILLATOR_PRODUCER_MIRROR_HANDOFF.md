# Heartbeat Oscillator Producer Mirror Handoff

Updated: 2026-08-20T19:18:00-05:00

## Identity

```text
goal_id: HEARTBEAT-OSCILLATOR-PRODUCER-011
parent_goal: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122
repository: StegVerse-Labs/.github
branch: main
canonical_parent_handoff: docs/HEARTBEAT_RUNTIME_SEPARATION_MIRROR_HANDOFF.md
credential_authority: TV/TVC
github_token_runtime_authority: NONE
third_party_role: FALLBACK_ONLY
authority_effect: NONE_CARRIER_ONLY
```

## Goal

Replace invocation/event-paced heartbeat production with an independent 10 ms oscillator-produced reference stream while preserving the carrier as non-authorizing and keeping WorkerCoordinator/task-control authority separate.

The heartbeat reference must exist because oscillator phase traveled, not because a repository event, workflow, task, worker, claim, fence, route, credential, scheduler event, or downstream consumer caused a cycle.

## Installed source

```text
heartbeat_runtime/independent_oscillator.py
heartbeat_runtime/oscillator_producer.py
scripts/run_heartbeat_runtime.py
control/runtime-separation-contract.json
scripts/validate_heartbeat_runtime_separation.py
tests/test_oscillator_producer.py
tests/test_heartbeat_carrier_non_authority.py
heartbeat_runtime/assignment_timer.py
heartbeat_runtime/worker_runtime.py
tests/test_worker_assignment_timer.py
tests/test_worker_runtime_independent_admission.py
receipts/heartbeat/HEARTBEAT-OSCILLATOR-PRODUCER-011-source-validation.json
```

## Current implementation state

```text
phase source: INDEPENDENT_PHASE_OSCILLATOR
period: 10 ms
frequency: 100 Hz
progression dependency: OSCILLATOR_ONLY
public runner production mode: oscillator phase deadline driven
event trigger required: false
repository/workflow/task/worker trigger required: false
post-cycle interval sleep as heartbeat clock: removed from production runner
missed reference behavior: compress contiguous due range into one bounded pulse batch
sink controls progression: false
sink grants authority: false
```

`heartbeat_runtime/oscillator_producer.py` derives the next deadline from the immutable oscillator anchor and the last emitted epoch. `scripts/run_heartbeat_runtime.py` now waits for that phase deadline and observes/materializes the already-due reference. `--interval-ms` remains a deprecated compatibility argument and no longer controls heartbeat cadence.

The initial legacy HB29 cutover is bounded to one oscillator quantum so an old historical timestamp cannot manufacture millions of references at first migration. After cutover, oscillator-backed state retains its stable anchor and elapsed phase travel derives later references.

## Worker-control divergence repair

The parent architecture states that independently admitted task control must not depend on a new heartbeat event. The canonical WorkerCoordinator previously activated HANDOFF_READY work only after reading a `worker_assignment_trigger_carried` event.

Current repair:

```text
independent task state: HANDOFF_READY
required admission authority_domain: INDEPENDENT_TASK_CONTROL
required claim_state: AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM
fresh fence required: true
heartbeat grants execution authority: false
carrier event prerequisite: false
assignment custody: existing Master Records worker-assignment path
minimum fence: enforced from minimum_fencing_token_exclusive
```

`heartbeat_runtime/assignment_timer.py` now provides `independent_task_control_packet()`, a non-authorizing observation packet that enters the same worker selection, fence, timer, and Master Records binding path without pretending a carrier event occurred. WorkerCoordinator records `source_admission_ref`, sets `source_carrier_event_ref=null`, and preserves `carrier_granted_authority=false`.

Carrier-emitted assignment packets remain a compatibility observation path; they are no longer the sole way an already-authorized independent task can execute.

## Validation evidence

Hosted run `32431877047`, job `96624983857`, exact head `c9be04b422c2a6ba248e6ccecca77732c839bf88` established:

```text
anonymous checkout: PASS
GitHub credential token present: false
compile runtime/workers/scripts: PASS
canonical JSON parse: PASS
executable handoff validation: PASS
oscillator producer focused tests: 6/6 PASS
full repository suite: FAIL, 450 tests / 10 failures / 16 errors
```

The focused producer tests were green. The full-suite failures exposed architecture/test divergence, including stale v12 expectations while canonical carrier is v13, stale event/task-capable heartbeat assumptions, obsolete handoff key expectations, and a real initial-cutover epoch extrapolation defect. The v13 expectation and HB29 cutover defect have since been repaired. No full-suite PASS is claimed yet for the newer head.

## Collision / authority boundaries

1. Do not create another heartbeat or scheduler.
2. Do not make WorkerCoordinator, GitHub Actions, repository events, task admission, or a sink the heartbeat clock.
3. Do not make oscillator phase progression execution authority.
4. Do not manually mint a claim or fence outside canonical WorkerCoordinator assignment logic.
5. TV/TVC remains sole credential authority.
6. No GitHub token or non-TV/TVC secret/token may become production authority.
7. Existing canonical carrier remains `heartbeat_runtime.engine_v13.HeartbeatRuntime`; v13 fragment observation does not grant task authority.
8. Live oscillator activation requires resident oscillator-produced carrier evidence and independent worker observation; source completion and hosted CI are insufficient.

## 2026-09-06 carrier CLI and activation-truth repair

Direct execution of the canonical resident-start command exposed two source
failures that import-based tests did not exercise:

```text
python scripts/install_sovereign_heartbeat_carrier.py
-> ModuleNotFoundError: No module named 'scripts'
```

After restoring repository-root package resolution, an execution host whose
`systemctl` compatibility wrapper returned zero without running systemd exposed
that supervisor command success alone could falsely produce
`carrier_active=true`.

The repaired installer now requires two valid persisted carrier observations
with increasing oscillator epochs before it emits `carrier_active=true`. Both
observations must retain the canonical 10 ms / 100 Hz, observation-only,
`OSCILLATOR_ONLY` invariants. Registration without progression fails closed.

Focused source validation after the repair: 35/35 PASS. The diagnostic host
correctly returned `carrier_start_reported=true`, `carrier_active=false` when
no oscillator state appeared. This is source/failure-semantics validation only;
it is not canonical resident activation evidence.

The runtime task remains `HEARTBEAT-OSCILLATOR-RESIDENT-START-012` and no new
heartbeat, oscillator, scheduler, WorkerCoordinator, claim/fence, credential
path, or runtime owner is introduced.

## Remaining work

```text
1. Run exact-head hosted validation after the batched oscillator/worker-control repairs.
2. Reconcile only genuine stale heartbeat architecture tests revealed by that run; do not restore superseded event-trigger semantics to make tests green.
3. Observe a resident oscillator-produced carrier state with frequency_rule=INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL and oscillator proof.
4. Independently observe WorkerCoordinator against that carrier without making it timing authority.
5. Execute eligible independently admitted HANDOFF_READY work through the new no-carrier-event task-control path and retain Master Records assignment evidence.
6. Continue Ecosystem Chat parent inference -> TVC -> LLM-adapter -> Master Records same-execution activation chain after lawful task-control admission.
```

## Completion accounting

```text
oscillator production source: COMPLETE_SOURCE
phase-deadline resident runner integration: COMPLETE_SOURCE
no-event contract guard: COMPLETE_SOURCE
HB29 one-quantum cutover repair: COMPLETE_SOURCE
independent task-control packet/custody path: COMPLETE_SOURCE
WorkerCoordinator no-carrier-event admission path: COMPLETE_SOURCE
focused hosted producer validation: PASS at earlier head
current exact-head full repository validation: PENDING
live resident oscillator proof: PENDING
live independent worker observation: PENDING
product activation: PENDING
archive eligible: false
```
