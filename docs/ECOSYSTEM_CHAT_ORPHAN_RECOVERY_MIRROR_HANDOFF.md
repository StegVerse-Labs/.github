# Ecosystem Chat Orphan Recovery Mirror Handoff

Updated: 2026-08-18T18:04:00-05:00

## Authority and scope

This handoff is canonical for recovery task `RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28` and its deterministic return to parent task `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`.

```text
repository: StegVerse-Labs/.github
branch: main
canonical carrier: separated heartbeat v12
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

Heartbeat continuity is already released:

```text
control/heartbeat-carrier-runtime-state.json: ACTIVE HB31 / generation31
control/worker-runtime-state.json: observed carrier 31/31
legacy control/heartbeat-state.json: immutable HB29
receipts/heartbeat-transition-continuity/latest.json: CARRIER_TRANSITION_COMPLETE / RELEASE_COMPLETE
state reconstruction: PASS
no duplicate claim/fence predicate for released transition: PASS
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

Recovery is its own worker/domain transition under independently admitted authority. It consumes HB31 as a reference/evidence input, not as an application-control gate.

Required sequence:

```text
HB31 RELEASE_COMPLETE evidence available
-> recovery task independently admitted under a fresh claim/fence >20
-> admitted StegVerse task executor runs ecosystem-chat-orphan-recovery-worker
-> Master Records G20 custody reconstruction PASS
-> recovery COMPLETED
-> parent becomes HANDOFF_READY
-> parent independently receives a fresh fence >20
-> StegVerse local/private model launch + proof
-> TVC ROUTE_ADMITTED / credential_requirement NONE
-> exact LLM-adapter execution
-> measured E1 -> model -> E2 usage
-> same-execution Master Records provider-usage + transition reconstruction PASS
```

The executor may be the canonical WorkerCoordinator when available, but **no specific G18 transition, G18 terminal response, G18 claim cleanup, or task-capable WorkerCoordinator cycle performed for heartbeat completion is a prerequisite**. A compliant StegVerse task-control execution opportunity under the recovery task's own authority is sufficient.

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
obsolete_release_hardening:
  task_id: SHWP-WORKER-TASK-CAPABLE-RELEASE-HARDENING-001
  claim_ref: control/session-implementation-claim-2026-08-18-worker-task-capable-release-hardening.json
  state: SUPERSEDED
  archive_dependency: false

recovery:
  task_id: RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28
  owner: admitted StegVerse task-control executor + ecosystem-chat-orphan-recovery-worker
  state: MACHINE_OWNED_REQUIRED_EXECUTION
  manual_execution_allowed: false
  release_condition: recovery COMPLETED under fresh independently admitted fence >20

parent:
  task_id: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
  owner: admitted StegVerse task-control executor -> TVC -> LLM-adapter -> Master Records
  state: MACHINE_OWNED_AFTER_RECOVERY
  manual_execution_allowed: false
  release_condition: immutable same-execution sovereign activation evidence
```

## Collision boundaries

1. Do not reset HB31.
2. Do not reuse G18 or G20 authority.
3. Do not manually mint recovery or parent fences.
4. Do not create a second heartbeat/scheduler/credential authority.
5. Do not use GitHub Actions or any hosted provider as production activation authority.
6. StegVerse remains PRIMARY; third parties remain fallback/control only.
7. TV/TVC remains sole credential authority.
8. Do not wait for G18 cleanup before admitting recovery under its own authority.

## Machine-observable release conditions

Before recovery completion:

- recovery owns a fresh independently admitted claim/fence strictly greater than 20;
- the recovery worker executes using an admitted StegVerse task-control executor;
- Master Records G20 custody reconstruction passes;
- recovery emits terminal evidence without reviving G20 or G18.

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
heartbeat continuity: RELEASE_COMPLETE HB31
recovery source validation: historical PASS
G18 cleanup prerequisite: SUPERSEDED / NOT REQUIRED
recovery live execution: NO
fresh parent inference execution: NO
same-execution activation proof: NO
```

## Archive rule

Archive is prohibited because recovery, parent inference, and same-execution evidence have not occurred. It is **not** prohibited by stale G18 projection or absence of a G18 terminalization event.
