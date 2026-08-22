# Ecosystem Chat Orphan Recovery Mirror Handoff

Updated: 2026-08-22T07:13:00-05:00

## Authority and scope

This handoff is canonical for recovery task `RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28` and its deterministic return to parent task `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`.

```text
repository: StegVerse-Labs/.github
branch: main
canonical carrier: independent oscillator-derived heartbeat reference only
ended parent claim: SHWP-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-G20
ended parent fence: 20
recovery task: RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28
recovery worker: ecosystem-chat-orphan-recovery-worker
credential authority: TV/TVC
local model credential requirement: NONE
primary runtime/provider: StegVerse
third_party_role: FALLBACK_ONLY
github token runtime authority: NONE
archive_dependency: true
```

Heartbeat, G18, WorkerCoordinator-specific execution, hosted CI, and third-party infrastructure are not recovery execution prerequisites. The recovery worker cannot revive G20, reuse fence20, create a second heartbeat, introduce a provider/runtime credential path, or inherit stale G18 authority.

## Current architecture

`.github#122` is authoritative: heartbeat is an independent carrier/reference frame and grants no task/control authority. Recovery is a separate task-control transition under its own admitted bounded authorization.

```text
heartbeat grants task authority: false
heartbeat snapshot required locally for recovery: false
G18 cleanup required: false
WorkerCoordinator-specific execution required: false
GitHub Actions production authority: false
TV/TVC credential authority: true
StegVerse primary: true
```

## Historical recovery source and custody

```text
StegVerse-Labs/.github PR #78 merge: 477b0d5e3737662a4d51fe87538bbbc2d4acc99e
historical recovery dry-run fence: 23 > ended fence20
master-records/orchestration PR #27 merge: 4c6f4679c20c7fc70a65753cf4f87e6b929f09ef
MR-ECOSYSTEM-CHAT-G20-ORPHAN-CUSTODY-025: COMPLETE_RELEASED
pinned checkpoint/event reconstruction: PASS
```

## Independent recovery execution path

The recovery bounded authorization is already ADMITTED and the registry task is `HANDOFF_READY`. Required sequence:

```text
ADMITTED recovery authorization
-> HANDOFF_READY recovery task
-> compliant StegVerse task-control executor acquires fresh claim/fence >20
-> ecosystem-chat-orphan-recovery-worker executes
-> Master Records G20 custody reconstruction PASS
-> bounded recovery claim/fence released
-> recovery COMPLETED
-> parent reconciled to HANDOFF_READY without authority creation
-> parent independently receives fresh fence >20
-> StegVerse local/private model launch + proof
-> TVC ROUTE_ADMITTED / credential_requirement NONE
-> exact LLM-adapter execution
-> measured E1 -> model -> E2 usage
-> same-execution Master Records provider-usage + transition reconstruction PASS
```

## Standalone independent task-control executor

The remaining descriptive execution gap has been replaced by a bounded repository-native entrypoint:

```text
scripts/run_independent_orphan_recovery.py
  install: d30032c737fa356f7481050333c4e152ee3c8433
  remove heartbeat-snapshot prerequisite: 93febaab3edda6cacee92364741a5091feac1f7a

tests/test_independent_orphan_recovery_executor.py
  install: 6195372e64d13a0e8ca55135b3df99eb69209f61
  no-heartbeat-snapshot regression: 466524be3bd79ba3c8fcfa06ae121909780b9c37

claim:
  control/session-implementation-claim-2026-08-22-independent-orphan-recovery-executor.json
  current state: CLAIMED_FOR_VALIDATION
  validation PR: #245
```

The executor validates the existing bounded authorization and `HANDOFF_READY` registry contract, allocates a fresh fence greater than fence20 and every projected generation/fence, invokes only `ecosystem-chat-orphan-recovery-worker` through `ProcessWorkerAdapter`, carries only the optional `STEGVERSE_MASTER_RECORDS_ROOT` path reference in its environment allowlist, releases recovery authority after every bounded attempt, and never creates parent authority. Missing local heartbeat state returns a non-authorizing reference sentinel and does not prevent recovery acquisition or execution.

GitHub Actions may validate this source but may not execute it as production/task-control authority.

## Validation state

First PR #245 validation head `3663370252913ac33bc1c8662b404465c3a9bebf` produced:

```text
Heartbeat Worker Project run 32572214172: FAILURE before unit tests
  anonymous/no-GitHub-token checkout: PASS
  compile runtime/workers/scripts: PASS
  canonical JSON parsing: PASS (312)
  failure: unrelated HEARTBEAT-OSCILLATOR-RESIDENT-START-012 executable-handoff/source_refs defect

Validate organization control plane run 32572214106: FAILURE
  workflow surface hygiene: PASS
  org control invariants: PASS
  active-worker ownership: PASS
  handoff execution ownership partition: PASS
  failure: unrelated HEARTBEAT-OSCILLATOR-RESIDENT-START-012 AE binding/retrospective conformance defect

Render Organization Handoff State run 32572214120: SUCCESS
```

Those failures are not accepted as recovery validation PASS because the focused tests were skipped. A concurrent resident-start owner is repairing that separate lane. PR #245 must be rebased onto the released repair and revalidated before this source claim releases.

## Current claim state

```yaml
independent_executor_source:
  task_id: SHWP-INDEPENDENT-ORPHAN-RECOVERY-EXECUTOR-001
  claim_ref: control/session-implementation-claim-2026-08-22-independent-orphan-recovery-executor.json
  state: CLAIMED_FOR_VALIDATION
  release_condition: direct validation evidence for the independent executor and handoff reconciliation; live execution then returns to admitted StegVerse task control

recovery:
  task_id: RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28
  owner: admitted StegVerse task-control executor + ecosystem-chat-orphan-recovery-worker
  state: HANDOFF_READY_AWAITING_FRESH_FENCE_EXECUTION
  release_condition: recovery COMPLETED under a fresh independently admitted fence >20

parent:
  task_id: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
  owner: admitted StegVerse task-control executor -> TVC -> LLM-adapter -> Master Records
  state: MACHINE_OWNED_AFTER_RECOVERY
  release_condition: immutable same-execution sovereign activation evidence
```

## Collision boundaries

1. Do not reset, advance, or require heartbeat merely to execute recovery.
2. Do not reuse G18 or G20 authority.
3. Do not mint recovery or parent fences from a chat/GitHub mutation lane; the released executor creates recovery authority only when actually invoked on an admitted StegVerse task-control surface.
4. Do not create a second heartbeat, scheduler, credential authority, model runtime, provider route, or Master Records custody path.
5. Do not use GitHub Actions, Render, Vercel, Cloudflare, or another hosted provider as production activation authority.
6. StegVerse remains PRIMARY; third parties remain fallback-only.
7. TV/TVC remains sole credential/secret/token authority.
8. Recovery completion does not itself grant parent authority.

## Machine-observable completion predicates

Recovery terminal evidence requires:
- independent executor source validated/released;
- fresh recovery claim/fence strictly greater than 20;
- admitted StegVerse execution of the recovery worker;
- Master Records G20 custody reconstruction PASS;
- old G20/G18 authority not reused;
- recovery claim released after attempt;
- recovery task terminal `COMPLETED`.

Parent terminal evidence then requires:
- separate fresh parent fence >20;
- real private StegVerse model process observed;
- TVC `ROUTE_ADMITTED`, credential requirement `NONE`;
- exact LLM-adapter route executed;
- measured usage persisted;
- Master Records provider-usage and transition reconstruction PASS;
- `same_execution=true`;
- no NON-TV/TVC secret/token authority.

## Exact next execution

1. Rebase PR #245 onto the completed resident-start repair and inspect the new validation runs.
2. Release `SHWP-INDEPENDENT-ORPHAN-RECOVERY-EXECUTOR-001` only after the independent executor tests actually execute and PASS.
3. Invoke `scripts/run_independent_orphan_recovery.py` from an admitted StegVerse task-control surface; no heartbeat snapshot is required.
4. If canonical Master Records G20 custody is not locally materialized, consume the bounded `BLOCKED` receipt, materialize the existing custody through the StegVerse workload path, and retry under another fresh fence.
5. On PASS, reconcile the parent to `HANDOFF_READY` without minting authority, independently acquire the parent, and continue the StegVerse-local model -> TVC -> LLM-adapter -> Master Records chain.

## Archive rule

Archive is prohibited because independent executor validation, recovery execution, parent inference, and same-execution activation evidence have not all occurred. Stale G18 state or the absence of a heartbeat snapshot is not an archive blocker.
