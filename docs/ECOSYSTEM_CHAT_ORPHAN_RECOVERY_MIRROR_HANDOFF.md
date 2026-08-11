# Ecosystem Chat Orphan Recovery Mirror Handoff

## Authority and scope

This scoped handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md` and authoritative for recovery task `RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28` and its deterministic return to parent task `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`. It does not create a second heartbeat, worker registry, model authority, route authority, credential authority, or execution authority.

```text
repository: StegVerse-Labs/.github
canonical branch: main
canonical heartbeat: heartbeat_runtime.engine_v9.HeartbeatRuntime
parent task: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
ended claim: SHWP-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-G20
ended fence: 20
recovery task: RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28
recovery worker: ecosystem-chat-orphan-recovery-worker
recovery capability: orphan_lifecycle_reconstruction
credential authority: TV/TVC
local model credential requirement: NONE
github token authority: NONE
github actions activation role: NONE
github actions persistence role: NONE
resident heartbeat epoch last directly observed: 29
```

## Originating session requirements transferred

- no GitHub-token credential, activation, model, route, transport, reconstruction, or heartbeat-persistence dependency;
- TV/TVC is credential authority and local-model credential class is `NONE`;
- the already-developed local model/runtime is used through actual discovery, launch, proof, TVC route, exact LLM-adapter execution, and Master Records reconstruction;
- no manual or descriptive `select a local model/runtime` step remains;
- an orphaned worker may not reuse its old claim or fence;
- recovery is machine executable, fail closed, and returns the parent to executable work when reconstruction is complete;
- hosted validation cannot commit or push heartbeat state and cannot activate the production worker.

MERGED INTO: `StegVerse-Labs/.github/docs/ECOSYSTEM_CHAT_ORPHAN_RECOVERY_MIRROR_HANDOFF.md` and `master-records/orchestration/ECOSYSTEM_CHAT_SOVEREIGN_RECONSTRUCTION_MIRROR_HANDOFF.md`.

## Historical evidence and root cause

```text
HB17: G20 worker activated, fence 20
HB17-HB25: worker responses/checkpoints observed
HB25 checkpoint sha256: 56ac0cce7e0f575fe8500ff0dd6321c76e26f5fd1d8ea9ac32220d6fa9aa15e6
HB26-HB28: EXECUTOR_RESPONSE_ERROR:BlockerPolicyError
HB28: response-loss threshold reached; recovery task admitted; G20 worker orphaned; old claim/worker released
HB29: generated recovery quarantine reconciled to BLOCKED; old authority not reused
```

The root cause was a blocker-policy contract mismatch: `BLOCKED` responses require a nonempty workaround candidate plus a concrete next solution action. The TV/TVC wrapper now normalizes legacy child blocker responses without changing state or authority.

## Released implementation

Orphan recovery implementation:

```text
PR: StegVerse-Labs/.github#78
merge: 477b0d5e3737662a4d51fe87538bbbc2d4acc99e
validation: PASS
Heartbeat Worker Project run: 31450724027 / SUCCESS
critical dry-run evidence: recovery claim fence 23 > ended fence 20
```

Master Records historical G20 custody:

```text
PR: master-records/orchestration#27
merge: 4c6f4679c20c7fc70a65753cf4f87e6b929f09ef
task: MR-ECOSYSTEM-CHAT-G20-ORPHAN-CUSTODY-025 / COMPLETE_RELEASED
release-state commit: be24e4b8790fd092318a1237cd4fd22a6e297948
custody: custody/worker-lifecycle/SHWP-CUSTODY-ECOSYSTEM-CHAT-INFERENCE-001-G20-001.json
hosted Actions: BLOCKED_BY_ACCOUNT_BILLING / ZERO STEPS / not counted as PASS
deterministic pinned checkpoint/event reconstruction: PASS
```

TV/TVC no-GitHub-token authority cleanup:

```text
PR: StegVerse-Labs/.github#79
merge: f6265ff0f74a51adf79985da09691b871b7576dc
state: COMPLETE_RELEASED
Ecosystem Chat no-token validation run: 31453552033 / SUCCESS
Heartbeat Worker Project no-token validation run: 31453552032 / SUCCESS
Organization control-plane no-token validation run: 31453552110 / SUCCESS
complete deterministic heartbeat suite: 97 tests PASS
authority result: GitHub Actions cannot activate, persist, claim, fence, or provide TV/TVC credentials
```

GitHub Actions itself reports its platform-internal metadata-read token even under `permissions: {}`. StegVerse workflow commands do not receive or use `GITHUB_TOKEN`, `GH_TOKEN`, or a PAT; checkout is anonymous public git fetch. That platform metadata facility is not a StegVerse credential surface and is not forwarded to TVC, the model runtime, LLM-adapter, Master Records, or the resident heartbeat.

## Installed recovery surfaces

```text
heartbeat_runtime/orphan_recovery.py
heartbeat_runtime/engine_v4.py
workers/ecosystem_chat_orphan_recovery_worker.py
workers/ecosystem_chat_tc_tvc_route_worker.py
control/worker-capability-profiles.json
control/process-worker-adapters.json
control/worker-registry.d/ecosystem-chat-orphan-recovery-hb28.json
authorizations/RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28.json
handoffs/generated/RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28.json
handoffs/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json
tests/test_orphan_recovery_reconciliation.py
tests/test_ecosystem_chat_orphan_recovery_activation.py
```

## TV/TVC and no-GitHub-token boundary

Current authority contract:

```text
credential_authority: TV/TVC
credential_requirement: NONE
route_authority: StegVerse-Labs/TVC
model/runtime: StegVerse-local
transport: StegVerse-org/LLM-adapter
reconstruction: master-records/orchestration
github_token_authority: false
github_actions_activation_role: false
github_actions_persistence_role: false
source_checkout_runtime_requirement: false
```

The former hosted activation workflow that used authenticated checkout, `contents: write`, heartbeat mutation, commit, and push is retired. Its filename remains for compatibility but it is now validation-only with `permissions: {}`, anonymous public git fetch, no action-based checkout/setup, no commit/push, and dry-run-only heartbeat evaluation. `heartbeat-worker-project.yml` and `org-control-plane-validate.yml` follow the same non-authorizing/no-project-token validation model.

## Recovery design and automatic continuation

The orphan task is a continuity root, not an authority-bearing goal successor. `recovery_parent_task_id` binds evidence to the ended parent while `derivation_depth=0` and absence of `parent_task_id` prevents successor-policy inheritance from recreating `SUCCESSOR_DEPTH_LIMIT_EXCEEDED`.

The bounded authorization permits only `orphan_lifecycle_reconstruction`, only the existing Ecosystem Chat receipt namespace, zero external cost, no services, no GitHub token, no old-authority revival, no parent execution, and no successor-parent authority. The recovery worker rejects any recovery fence `<=20`.

Parent `SHWP-ECOSYSTEM-CHAT-INFERENCE-001` remains blocked on the recovery task. Once recovery reaches `COMPLETED`, the blocked-task engine returns the parent to `HANDOFF_READY`; the normal resident allocator must issue a fencing generation greater than 20. The resumed parent follows:

```text
locally developed model/runtime
-> live private proof
-> TVC ROUTE_ADMITTED / credential_requirement NONE
-> exact LLM-adapter task 020 execution
-> measured E1 -> model -> E2
-> same-carrier Master Records task 024 reconstruction
-> provider_usage_reconstruction_pass
-> transition_reconstruction_pass
-> same_execution
-> zero-blocker activation verification
```

## Current machine state

The last directly observed canonical `control/heartbeat-state.json` remained at epoch 29. PR #79 deliberately cannot advance it. Source implementation and authority cleanup are complete, but resident runtime activation is not inferred from merge or hosted validation.

Dry-run validation proves what the next resident heartbeat will do if the released source and Master Records workload are locally materialized: it releases the recovery authorization, selects the unique recovery worker, allocates fence 23 (>20), and fails closed at `MASTER_RECORDS_CUSTODY_NOT_PROVEN` when the custody workload is absent. That dry-run claim is not a live claim.

Machine-observable next state:

```text
resident heartbeat advances beyond epoch 29
-> registry fragment is consumed
-> recovery task receives a live claim/fence > 20
-> local Master Records task-025 custody resolves
-> orphan recovery receipt reaches PASS / task COMPLETED
-> parent becomes HANDOFF_READY
-> parent receives a new live fence > 20
-> local model/TVC/LLM/Master Records chain executes
```

## Claims and collision boundaries

```text
recovery implementation claim: RELEASED / PR #78
Master Records task-025 claim: RELEASED
TV/TVC no-token authority cleanup claim: RELEASED / PR #79
current owner: MACHINE_OWNED_RUNTIME_OBSERVATION / resident heartbeat
old fence reuse: prohibited
parent execution by recovery worker: prohibited
recovery execution by parent worker: prohibited
second heartbeat: prohibited
second worker registry: prohibited
GitHub token runtime/activation authority: prohibited
```

## Completion accounting

```text
required developed recovery/authority surfaces: 16
currently developed: 16
scaffolding/stubs: 0
missing required files: 0
source implementation validation: PASS
source integration merge: PASS
Master Records G20 custody: COMPLETE_RELEASED
TV/TVC no-GitHub-token authority cleanup: COMPLETE_RELEASED
resident heartbeat post-release observation: PENDING_MACHINE_OWNED
higher-fence parent inference execution: PENDING_MACHINE_OWNED
same-execution activation proof: PENDING_MACHINE_OWNED
```

## Archive condition

All unique design, implementation, recovery, and credential-authority knowledge from this session is durable. Product activation remains incomplete because the resident sovereign heartbeat has not been directly observed advancing past HB29 and completing the recovery -> higher-fence parent -> local model -> TVC -> LLM-adapter -> Master Records chain. The organization archive gate remains authoritative; source release alone does not permit an activation-complete archive claim.
