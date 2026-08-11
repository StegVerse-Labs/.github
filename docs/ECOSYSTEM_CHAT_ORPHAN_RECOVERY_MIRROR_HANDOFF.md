# Ecosystem Chat Orphan Recovery Mirror Handoff

## Authority and scope

This scoped handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md` and authoritative only for recovery task `RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28` and its deterministic return to parent task `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`. It does not create a second heartbeat, worker registry, model authority, route authority, credential authority, or execution authority.

```text
repository: StegVerse-Labs/.github
branch: fix/ecosystem-chat-orphan-recovery-20260810
canonical heartbeat: heartbeat_runtime.engine_v9.HeartbeatRuntime
parent task: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
ended claim: SHWP-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-G20
ended fence: 20
recovery task: RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28
recovery worker: ecosystem-chat-orphan-recovery-worker
recovery capability: orphan_lifecycle_reconstruction
credential authority: TC/TVC
local model credential requirement: NONE
github_token_required: false
```

## Originating session requirements transferred

- no GitHub-token production runtime dependency;
- TV/TVC remains credential authority and local-model credential class remains NONE;
- the already-developed local model/runtime must be used through actual discovery, launch, proof, TVC route, exact LLM-adapter execution, and Master Records reconstruction;
- no manual or descriptive `select a local model/runtime` step;
- an orphaned worker may not reuse its old claim or fence;
- recovery must be machine executable, fail closed, and automatically return the parent to executable work when reconstruction is complete.

MERGED INTO: `StegVerse-Labs/.github/docs/ECOSYSTEM_CHAT_ORPHAN_RECOVERY_MIRROR_HANDOFF.md` and `master-records/orchestration/ECOSYSTEM_CHAT_SOVEREIGN_RECONSTRUCTION_MIRROR_HANDOFF.md`.

## Historical evidence

Committed heartbeat history proves:

```text
HB17: G20 worker activated, fence 20
HB17-HB25: worker responses/checkpoints observed
HB25 checkpoint sha256: 56ac0cce7e0f575fe8500ff0dd6321c76e26f5fd1d8ea9ac32220d6fa9aa15e6
HB26-HB28: EXECUTOR_RESPONSE_ERROR:BlockerPolicyError
HB28: response-loss threshold reached; recovery task admitted; G20 worker orphaned; old claim/worker released
HB29: generated recovery quarantine reconciled to BLOCKED; old authority not reused
```

The root cause is the current blocker-policy contract: `BLOCKED` responses require a nonempty workaround candidate in addition to the concrete next solution action. The registered TC/TVC wrapper now normalizes legacy child blocker responses into that current contract without changing state or authority.

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

The generated orphan task is a **continuity root**, not an authority-bearing goal successor. Its `recovery_parent_task_id` binds evidence to the ended parent while `derivation_depth=0` and absence of `parent_task_id` prevents successor-policy inheritance from recreating the historical `SUCCESSOR_DEPTH_LIMIT_EXCEEDED` quarantine.

A bounded authorization permits only capability `orphan_lifecycle_reconstruction`, only the existing Ecosystem Chat receipt namespace, zero external cost, no services, no GitHub token, no old-authority revival, no parent execution, and no successor-parent authority. The dedicated recovery worker cannot satisfy the parent task's three execution capabilities, and the parent inference worker cannot satisfy the recovery-only capability.

The normal blocked-work engine validates the bounded authorization file and returns the recovery task to `HANDOFF_READY`. The normal heartbeat allocator then creates a fresh recovery claim/fence. The worker refuses any fence `<=20`.

## Master Records dependency

Canonical historical lifecycle custody is owned by:

```text
master-records/orchestration
  task: MR-ECOSYSTEM-CHAT-G20-ORPHAN-CUSTODY-025
  receipt: custody/worker-lifecycle/SHWP-CUSTODY-ECOSYSTEM-CHAT-INFERENCE-001-G20-001.json
  verifier: scripts/verify_ecosystem_chat_g20_orphan_custody.py
```

The recovery worker discovers only locally materialized Master Records custody and accepts only a released G20/fence20 lifecycle with `ACCEPTED_FOR_CUSTODY`, reconstruction `PASS`, and authority effect `NONE`. Missing custody remains `BLOCKED` with a machine-observable release condition.

Historical custody PASS does not mean the inference task completed and grants no execution authority.

## Automatic parent continuation

Parent `SHWP-ECOSYSTEM-CHAT-INFERENCE-001` is blocked on the recovery task ID. Once recovery reaches `COMPLETED`, the existing blocked-task engine returns the parent to `HANDOFF_READY`; the normal allocator must issue a new fencing generation greater than 20. The resumed parent then follows the already-installed chain:

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

## Claims and collision boundaries

```text
implementation role: DISTINCT INTEGRATION / RECOVERY
claim release condition: branch validates and merges; Master Records task 025 validates/merges; next resident heartbeat consumes registry fragment and executes recovery under a new fence
old fence reuse: prohibited
parent execution by recovery worker: prohibited
recovery execution by parent worker: prohibited
second heartbeat: prohibited
second worker registry: prohibited
GitHub token runtime dependency: prohibited
```

## Validation commands

```text
python -m unittest tests.test_orphan_recovery_reconciliation -v
python -m pytest -q tests/test_ecosystem_chat_orphan_recovery_activation.py
python -m pytest -q tests/test_ecosystem_chat_tc_tvc_route_worker.py
python -m pytest -q tests/test_master_records_sovereign_reconstruction_bridge.py
python scripts/run_heartbeat_runtime.py --dry-run
```

Hosted workflows are source validation only. Runtime activation requires the resident sovereign heartbeat and locally materialized workloads.

## Completion accounting

```text
required developed surfaces: 12
currently developed: 12
scaffolding/stubs: 0
missing required files: 0
static/unit validation: PENDING_BRANCH_CI
integration wiring: IMPLEMENTED
Master Records G20 custody: IMPLEMENTED_PENDING_VALIDATION
resident heartbeat post-merge observation: PENDING_MACHINE_OWNED
higher-fence parent inference execution: PENDING_MACHINE_OWNED
```

## Archive condition

This scoped implementation becomes transfer-safe when both repository branches validate/merge, implementation claims release, and the canonical handoffs contain the exact machine-owned continuation. Product activation remains pending until a resident heartbeat actually obtains a new fence greater than 20 and reaches same-execution reconstruction PASS. Session archival is determined by the organization archive gate; transfer alone does not override it.
