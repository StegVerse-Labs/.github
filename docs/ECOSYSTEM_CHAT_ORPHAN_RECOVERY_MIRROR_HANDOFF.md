# Ecosystem Chat Orphan Recovery Mirror Handoff

Updated: 2026-08-22T23:47:00-05:00

## Authority and scope

This handoff is canonical for recovery task `RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28` and its deterministic return to parent task `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`.

```text
repository: StegVerse-Labs/.github
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
```

Heartbeat, G18, WorkerCoordinator-specific execution, hosted CI, and third-party infrastructure are not recovery execution prerequisites. Heartbeat grants no recovery authority. The recovery worker cannot revive G20, reuse fence20, create a second heartbeat, introduce a provider/runtime credential path, or inherit stale G18 authority.

## Released independent recovery executor

The descriptive execution gap is closed at source level. The repository contains:

```text
scripts/run_independent_orphan_recovery.py
  install: d30032c737fa356f7481050333c4e152ee3c8433
  heartbeat-snapshot decoupling: 93febaab3edda6cacee92364741a5091feac1f7a

tests/test_independent_orphan_recovery_executor.py
  install: 6195372e64d13a0e8ca55135b3df99eb69209f61
  no-heartbeat-snapshot regression: 466524be3bd79ba3c8fcfa06ae121909780b9c37

source claim:
  control/session-implementation-claim-2026-08-22-independent-orphan-recovery-executor.json
  state: COMPLETE_RELEASED_SOURCE_VALIDATED
  validation PR: #245
```

The executor validates the already-ADMITTED bounded recovery authorization and `HANDOFF_READY` registry contract, allocates a fresh fence greater than fence20 and every projected generation/fence, invokes only `ecosystem-chat-orphan-recovery-worker` through `ProcessWorkerAdapter`, carries only the optional `STEGVERSE_MASTER_RECORDS_ROOT` location reference, releases recovery authority after every bounded attempt, and never creates parent authority. A missing heartbeat snapshot is not an execution prerequisite and does not stop acquisition or execution.

## Self-contained immutable G20 custody

The remaining sibling-checkout portability dependency has been removed. PR #260 merged as `5e85a2d602fe7234a4bdff34aa1521b752dc2b49` and installs the exact immutable, non-authorizing Master Records G20 lifecycle custody record under the recovery worker's existing repository-local workload search path:

```text
workloads/master-records/orchestration/custody/worker-lifecycle/SHWP-CUSTODY-ECOSYSTEM-CHAT-INFERENCE-001-G20-001.json
```

The packaged record is bound to released G20 fence20 custody, `ACCEPTED_FOR_CUSTODY`, reconstruction `PASS`, `authority_effect: NONE`, and the canonical Master Records identity. It grants no execution, parent, release, heartbeat, credential, or provider authority.

PR #260 validation evidence:

```text
head: a181df62e094195c04bf59cfcf4f66b8c468dda2
Heartbeat Worker Project: run 32609238302 / job 97119379258
  no-GitHub-token checkout: PASS
  compile: PASS
  canonical JSON: PASS
  executable handoffs: PASS
  independent recovery tests: PASS, including self-contained G20 custody
  repository-wide result: RED only on two unrelated LIVE-009 state-expectation tests
Organization control plane: run 32609238303 / job 97119379172
  all steps: PASS
merge: 5e85a2d602fe7234a4bdff34aa1521b752dc2b49
```

Recovery therefore no longer requires a sibling `master-records/orchestration` checkout merely to locate the already-released custody evidence. An explicit `STEGVERSE_MASTER_RECORDS_ROOT` may still be used when available, but absence of that sibling checkout is no longer a recovery-start blocker.

## Validation evidence

PR #245 was rebased onto current `main` at head `dd2eb7ca632d3f376c008ad10b3db1d4b6794f13` and directly inspected.

Heartbeat Worker Project validation:

```text
run: 32608524799
job: 97117508606
anonymous/no-GitHub-token checkout: PASS
compile runtime/workers/scripts: PASS
canonical JSON parse: PASS (324)
executable handoff validation: PASS (39, live lanes 35)
independent orphan recovery focused tests: PASS 5/5
```

Focused PASS set:

- `test_acquire_claim_uses_new_generation_without_parent_or_g18_dependency`
- `test_blocked_attempt_releases_claim_for_fresh_retry`
- `test_completed_attempt_releases_recovery_authority_without_minting_parent_authority`
- `test_missing_carrier_snapshot_is_not_an_execution_prerequisite`
- `test_registered_executor_is_independent_and_available`

The repository-wide suite continued and failed only on two unrelated heartbeat-live-proof tests whose fixtures expected `HANDOFF_READY` while current state was `BLOCKED_DEPENDENCY`. Those unrelated failures do not invalidate the recovery tests and are not represented as repository-wide PASS.

Organization control-plane validation:

```text
run: 32608524804
job: 97117508786
result: PASS
all validation steps: PASS
GitHub credential authority: NONE
```

CI remains validation-only and grants no runtime/task-control authority.

## Current execution state

```yaml
independent_executor_source:
  task_id: SHWP-INDEPENDENT-ORPHAN-RECOVERY-EXECUTOR-001
  state: COMPLETE_RELEASED_SOURCE_VALIDATED
  archive_dependency: false

recovery_custody_portability:
  state: COMPLETE_RELEASED_INTEGRATED
  pr: 260
  merge: 5e85a2d602fe7234a4bdff34aa1521b752dc2b49
  authority_effect: NONE

recovery:
  task_id: RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28
  state: HANDOFF_READY_AWAITING_FRESH_FENCE_EXECUTION
  owner: admitted StegVerse task-control executor + ecosystem-chat-orphan-recovery-worker
  release_condition: recovery COMPLETED under fresh independently admitted fence >20

parent:
  task_id: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
  state: MACHINE_OWNED_AFTER_RECOVERY
  owner: admitted StegVerse task-control executor -> TVC -> LLM-adapter -> Master Records
  release_condition: immutable same-execution sovereign activation evidence
```

The recovery registry fragment is already `HANDOFF_READY`, `AUTHORIZED`, `INDEPENDENT_TASK_CONTROL`, `fresh_fence_required=true`, and `minimum_fencing_token_exclusive=20`. No new scheduler, heartbeat, sibling checkout, or duplicate task is required.

## Required downstream sequence

```text
HANDOFF_READY recovery
-> admitted StegVerse task-control execution opportunity
-> fresh recovery claim/fence >20
-> ecosystem-chat-orphan-recovery-worker
-> packaged/canonical G20 custody reconstruction PASS
-> recovery claim released
-> recovery COMPLETED
-> parent reconciled to HANDOFF_READY without authority creation
-> separate fresh parent claim/fence >20
-> real StegVerse local/private model process
-> TVC ROUTE_ADMITTED / credential_requirement NONE
-> exact LLM-adapter execution
-> measured usage persisted
-> same-execution Master Records provider-usage + transition reconstruction PASS
```

## Collision boundaries

1. Do not reset, advance, or require heartbeat merely to execute recovery.
2. Do not require or terminalize G18.
3. Do not reuse G18 or G20 authority.
4. Do not manually mint recovery or parent fences from chat/GitHub mutation authority.
5. Do not create a second heartbeat, scheduler, credential authority, model runtime, provider route, or Master Records custody path.
6. GitHub Actions and hosted providers are validation/control surfaces only, never production activation authority.
7. StegVerse remains PRIMARY; third parties remain fallback-only.
8. TV/TVC remains sole credential/secret/token authority.
9. Recovery completion does not itself grant parent authority.

## Archive rule

Archive is prohibited because live recovery execution, fresh parent inference, and same-execution activation evidence have not occurred. The source executor and its self-contained historical custody input are validated and released; stale G18 state, WorkerCoordinator-specific execution, heartbeat snapshot availability, or a sibling Master Records checkout are not completion prerequisites.
