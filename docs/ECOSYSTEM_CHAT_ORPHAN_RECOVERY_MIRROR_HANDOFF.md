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
credential authority: TC/TVC
local model credential requirement: NONE
github token authority: NONE
github actions activation role: NONE
github actions persistence role: NONE
resident heartbeat epoch observed after PR #78 merge: 29
```

## Originating session requirements transferred

- no GitHub-token credential, activation, model, route, transport, reconstruction, or heartbeat-persistence dependency;
- TC/TVC is credential authority and local-model credential class is `NONE`;
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

The root cause was a blocker-policy contract mismatch: `BLOCKED` responses require a nonempty workaround candidate plus a concrete next solution action. The TC/TVC wrapper now normalizes legacy child blocker responses without changing state or authority.

## Released implementation

`.github` orphan recovery implementation:

```text
PR: StegVerse-Labs/.github#78
merge: 477b0d5e3737662a4d51fe87538bbbc2d4acc99e
validation: PASS
hosted Heartbeat Worker Project run: 31450724027 / SUCCESS
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

The Master Records billing-blocked jobs never started; this is not represented as a test PASS. Historical custody PASS does not mean the inference task completed and grants no execution authority.

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

## Recovery design

The orphan task is a **continuity root**, not an authority-bearing goal successor. `recovery_parent_task_id` binds evidence to the ended parent while `derivation_depth=0` and absence of `parent_task_id` prevents successor-policy inheritance from recreating `SUCCESSOR_DEPTH_LIMIT_EXCEEDED`.

The bounded authorization permits only `orphan_lifecycle_reconstruction`, only the existing Ecosystem Chat receipt namespace, zero external cost, no services, no GitHub token, no old-authority revival, no parent execution, and no successor-parent authority. The recovery worker cannot satisfy the parent execution capability set; the parent worker cannot satisfy the recovery-only capability. The worker rejects any recovery fence `<=20`.

PR #78 validation exercised the normal allocator in dry-run and obtained recovery fence `23`, directly proving the higher-fence rule without mutating canonical heartbeat state.

## TC/TVC and no-GitHub-token boundary

Current authority contract:

```text
credential_authority: TC/TVC
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

The former `activate-ecosystem-chat-sovereign-inference-worker.yml` used authenticated checkout plus `contents: write` and pushed heartbeat state to `main`. That behavior is superseded. The workflow is being converted to validation-only with `permissions: {}`, anonymous public git fetch, no `actions/checkout`, no `actions/setup-python`, no commit/push, and dry-run-only heartbeat execution. `heartbeat-worker-project.yml` is likewise being converted to validation-only/nonpersistent operation.

GitHub source-control API operations used to install repository changes are not execution credentials and are not passed into the StegVerse runtime. No project workflow may use GitHub credentials as TC/TVC authority.

## Automatic parent continuation

Parent `SHWP-ECOSYSTEM-CHAT-INFERENCE-001` remains blocked on the recovery task. Once recovery reaches `COMPLETED`, the blocked-task engine returns the parent to `HANDOFF_READY`; the normal resident allocator must issue a fencing generation greater than 20. The resumed parent follows the installed chain:

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

`control/heartbeat-state.json` on main remains at epoch 29 after PR #78 merge. Therefore source release is complete but **resident runtime activation has not yet been observed**. The dry-run fence 23 is validation evidence only and is not a live claim.

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
current role: MACHINE_OWNED_RUNTIME_OBSERVATION plus token-authority cleanup
old fence reuse: prohibited
parent execution by recovery worker: prohibited
recovery execution by parent worker: prohibited
second heartbeat: prohibited
second worker registry: prohibited
GitHub token runtime/activation authority: prohibited
```

## Validation commands

```text
python -m unittest tests.test_orphan_recovery_reconciliation -v
python -m pytest -q tests/test_ecosystem_chat_orphan_recovery_activation.py
python -m pytest -q tests/test_ecosystem_chat_tc_tvc_route_worker.py
python -m pytest -q tests/test_master_records_sovereign_reconstruction_bridge.py
python scripts/run_heartbeat_runtime.py --dry-run
```

Hosted workflows are validation only. Runtime activation requires the resident sovereign heartbeat and locally materialized workloads.

## Completion accounting

```text
required developed recovery surfaces: 12
currently developed: 12
scaffolding/stubs: 0
missing required files: 0
recovery implementation validation: PASS
recovery integration merge: PASS
Master Records G20 custody: COMPLETE_RELEASED
TC/TVC no-GitHub-token authority cleanup: IMPLEMENTED_PENDING_VALIDATION_AND_MERGE
resident heartbeat post-merge observation: PENDING_MACHINE_OWNED
higher-fence parent inference execution: PENDING_MACHINE_OWNED
```

## Archive condition

All unique design and implementation knowledge from this session is durable. The session is not archive-ready yet because this session still owns validation/merge of the token-authority cleanup and must then determine whether a resident heartbeat has consumed the released recovery lane. Product activation remains pending until live heartbeat state advances beyond HB29 and reaches same-execution reconstruction PASS.
