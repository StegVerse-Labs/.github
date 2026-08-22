# Ecosystem Chat Orphan Recovery Mirror Handoff

Updated: 2026-08-22T07:08:00-05:00

## Authority and scope

This handoff is canonical for recovery task `RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28` and its deterministic return to parent task `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`.

```text
repository: StegVerse-Labs/.github
branch: main
canonical carrier: separated heartbeat v12 / oscillator-derived reference
ended parent claim: SHWP-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-G20
ended parent fence: 20
recovery task: RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28
recovery worker: ecosystem-chat-orphan-recovery-worker
credential authority: TV/TVC
local model credential requirement: NONE
primary runtime/provider: StegVerse
third-party role: CONTROL_OR_FALLBACK_ONLY
github token runtime authority: NONE
archive_dependency: true
```

The recovery worker cannot revive G20, reuse fence 20, create a second heartbeat, introduce a provider/runtime credential path, or inherit stale G18 authority.

## Current heartbeat state

Heartbeat continuity is already released and is reference-only for this task. It grants no recovery execution authority.

```text
control/heartbeat-carrier-runtime-state.json: released HB31 evidence retained
legacy control/heartbeat-state.json: immutable HB29 provenance
heartbeat grants task authority: false
G18 cleanup required: false
WorkerCoordinator-specific execution required: false
```

Under the corrected architecture in `.github#122`, heartbeat is the regulatory carrier/reference frame. Worker/control-plane lifecycle is separate. Therefore neither G18 registry terminalization nor a task-capable WorkerCoordinator cycle performed merely for G18 may gate this recovery.

## Historical recovery source

Orphan recovery source remains released and valid:

```text
StegVerse-Labs/.github PR #78
merge: 477b0d5e3737662a4d51fe87538bbbc2d4acc99e
recovery dry-run fence: 23 > ended fence 20
```

Historical G20 custody remains available in Master Records:

```text
master-records/orchestration PR #27
merge: 4c6f4679c20c7fc70a65753cf4f87e6b929f09ef
MR-ECOSYSTEM-CHAT-G20-ORPHAN-CUSTODY-025: COMPLETE_RELEASED
pinned checkpoint/event reconstruction: PASS
```

TV/TVC no-GitHub-token authority cleanup remains released; hosted validation does not grant runtime authority.

## Corrected recovery design

Recovery is its own worker/domain transition under independently admitted authority. It may consume a heartbeat reference as evidence metadata, but heartbeat is not an application-control gate.

Required sequence:

```text
recovery bounded authorization already ADMITTED
-> recovery task HANDOFF_READY
-> compliant StegVerse task-control executor atomically acquires fresh claim/fence >20
-> admitted executor runs ecosystem-chat-orphan-recovery-worker
-> Master Records G20 custody reconstruction PASS
-> bounded recovery attempt releases its claim/fence
-> recovery COMPLETED
-> parent becomes HANDOFF_READY through a separate non-authorizing reconciliation
-> parent independently receives a fresh fence >20
-> StegVerse local/private model launch + proof
-> TVC ROUTE_ADMITTED / credential_requirement NONE
-> exact LLM-adapter execution
-> measured E1 -> model -> E2 usage
-> same-execution Master Records provider-usage + transition reconstruction PASS
```

The canonical WorkerCoordinator may be one compliant task-control executor, but it is not required. No specific G18 transition, G18 terminal response, G18 claim cleanup, carrier-trigger packet, GitHub workflow, or hosted runtime is a prerequisite.

## Independent task-control executor — SOURCE INSTALLED / VALIDATION ACTIVE

A bounded repository-native execution entrypoint is now installed so `HANDOFF_READY` is no longer merely descriptive:

```text
scripts/run_independent_orphan_recovery.py
  source commit: d30032c737fa356f7481050333c4e152ee3c8433

tests/test_independent_orphan_recovery_executor.py
  source commit: 6195372e64d13a0e8ca55135b3df99eb69209f61

implementation claim:
  control/session-implementation-claim-2026-08-22-independent-orphan-recovery-executor.json
  claim commit: 4c6a36e92eecff8f36aaebc0af2fd9d1beeb29ca
```

The executor:

- validates the already-admitted independent recovery contract before acquisition;
- requires the canonical recovery registry fragment to be `HANDOFF_READY` and `AUTHORIZED`;
- computes a fresh fencing generation strictly greater than fence20 and every currently projected generation/fence;
- binds only `ecosystem-chat-orphan-recovery-worker` / `process:ecosystem-chat-orphan-recovery-v1`;
- invokes the existing `ProcessWorkerAdapter`, preserving handoff path scope and a minimal environment allowlist containing only the optional `STEGVERSE_MASTER_RECORDS_ROOT` location reference;
- never forwards GitHub/provider/wallet secrets;
- treats heartbeat epoch only as a reference label, not authority;
- does not use or terminalize G18;
- does not reuse G20;
- does not mint parent inference authority;
- releases the bounded recovery claim after `COMPLETED`, `BLOCKED`, or executor failure so a stale recovery claim cannot become a new prerequisite;
- requires any retry to acquire another fresh generation.

GitHub Actions may validate this source but may not execute it as production/task-control authority.

## G18 treatment

G18/fence18 may remain projected in historical/live registry state until independent lifecycle maintenance reconciles it. Recovery and parent activation must ignore that stale projection except as historical evidence and collision context.

```text
g18 cleanup required for heartbeat release: false
g18 cleanup required for recovery admission: false
g18 cleanup required for parent inference admission: false
g18 authority reusable by recovery/parent: false
```

## Current claim state

```yaml
independent_executor_source:
  task_id: SHWP-INDEPENDENT-ORPHAN-RECOVERY-EXECUTOR-001
  claim_ref: control/session-implementation-claim-2026-08-22-independent-orphan-recovery-executor.json
  state: CLAIMED_FOR_IMPLEMENTATION
  release_condition: focused source validation + canonical handoff reconciliation; live execution then returns to admitted StegVerse task control

obsolete_release_hardening:
  task_id: SHWP-WORKER-TASK-CAPABLE-RELEASE-HARDENING-001
  claim_ref: control/session-implementation-claim-2026-08-18-worker-task-capable-release-hardening.json
  state: SUPERSEDED
  archive_dependency: false

recovery:
  task_id: RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28
  owner: admitted StegVerse task-control executor + ecosystem-chat-orphan-recovery-worker
  state: HANDOFF_READY_AWAITING_FRESH_FENCE_EXECUTION
  manual_chat_claim_allowed: false
  release_condition: recovery COMPLETED under fresh independently admitted fence >20

parent:
  task_id: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
  owner: admitted StegVerse task-control executor -> TVC -> LLM-adapter -> Master Records
  state: MACHINE_OWNED_AFTER_RECOVERY
  manual_chat_claim_allowed: false
  release_condition: immutable same-execution sovereign activation evidence
```

## Collision boundaries

1. Do not reset or advance heartbeat merely to execute recovery.
2. Do not reuse G18 or G20 authority.
3. Do not mint recovery or parent fences from a chat/GitHub mutation lane; the released executor mints the recovery fence only when actually invoked on an admitted StegVerse task-control surface.
4. Do not create a second heartbeat/scheduler/credential authority.
5. Do not use GitHub Actions or any hosted provider as production activation authority.
6. StegVerse remains PRIMARY; third parties remain fallback/control only.
7. TV/TVC remains sole credential authority.
8. Do not wait for G18 cleanup before admitting recovery under its own authority.
9. Recovery completion does not itself grant the parent a claim; parent authority is a separate transition.

## Machine-observable release conditions

Before recovery completion:

- the independent executor source is validated and released;
- recovery owns a fresh independently admitted claim/fence strictly greater than 20;
- the recovery worker executes using an admitted StegVerse task-control executor;
- Master Records G20 custody reconstruction passes;
- recovery emits terminal evidence without reviving G20 or G18;
- the recovery claim is released after the bounded attempt.

Before parent completion:

- parent owns a separate fresh fence >20;
- real private StegVerse model process observed;
- TVC route admitted with credential requirement NONE;
- exact LLM-adapter path executed;
- measured usage persisted;
- provider-usage and transition reconstruction PASS;
- `same_execution=true`;
- no non-TV/TVC secret/token authority.

## Validation state

```text
heartbeat continuity/reference: RELEASED / NON-AUTHORIZING
recovery historical source validation: PASS
independent registry promotion validation: PASS (bb7c85385782eb499fedecd9689a3f59735311d5 / 83a3450dec202914007305ea0637dbdfa0f33fb4)
independent executor source installed: YES
independent executor focused tests installed: YES
independent executor hosted validation: PENDING
independent executor live StegVerse execution: NO
recovery live execution: NO
fresh parent inference execution: NO
same-execution activation proof: NO
```

## Exact next execution

1. Validate the independent executor on the repository's non-authorizing test lane.
2. Release `SHWP-INDEPENDENT-ORPHAN-RECOVERY-EXECUTOR-001` only after that validation evidence is directly inspected.
3. Invoke `scripts/run_independent_orphan_recovery.py` from an admitted StegVerse task-control execution opportunity. Do not invoke it from GitHub Actions as production authority.
4. If Master Records custody is not materialized locally, consume the worker's bounded `BLOCKED` receipt, materialize the already-existing canonical custody through the StegVerse workload path, and retry under another fresh fence.
5. On recovery PASS, reconcile the parent to `HANDOFF_READY` without minting parent authority, then independently acquire the parent under a fresh fence >20 and continue the StegVerse-local model -> TVC -> LLM-adapter -> Master Records chain.

## Archive rule

Archive is prohibited because independent executor validation, recovery execution, parent inference, and same-execution evidence have not all occurred. It is **not** prohibited by stale G18 projection or absence of a G18 terminalization event.
