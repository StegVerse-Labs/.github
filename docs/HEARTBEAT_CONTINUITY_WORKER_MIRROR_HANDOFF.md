# Heartbeat Continuity Worker Mirror Handoff

## Authority

This scoped handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md` and `StegVerse-Labs/.github#12`. It is the canonical continuation for the single-heartbeat worker/runtime activation goal.

Live default-branch repository state, current worker registry/status, claims, fences, checkpoints, receipts, issues, merged pull requests, and direct sovereign-node observations are authoritative over historical chat or CI claims.

## Active goal

```text
goal_id: SOVEREIGN-HEARTBEAT-PRODUCTION-ACTIVATION
repository: StegVerse-Labs/.github
canonical_owner: StegVerse-Labs/.github#12
canonical_runtime: heartbeat_runtime.engine_v9.HeartbeatRuntime
activation_carrier: single_stegverse_heartbeat
heartbeat_default_interval_ms: 10.0
worker_lease_clock: canonical_heartbeat_cycle
third_party_deployment_dependency: NONE
third_party_scheduler_dependency: NONE
third_party_process_host_dependency: NONE
heartbeat_owned_worker_execution_observed: true
durable_continuous_sovereign_runtime_observed: false
heartbeat_production_activation_percent: 96
session_continuation_workers_active: true
```

Two states remain deliberately separate:

1. heartbeat/worker implementation and worker-owned continuation are active;
2. durable continuous sovereign runtime plus end-to-end sovereign Ecosystem Chat inference remain direct-observation goals and are not made true by repository or hosted-workflow success.

## Ecosystem Chat sovereign inference worker

```text
task_id: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
worker_id: ecosystem-chat-sovereign-inference-worker
canonical_issue: StegVerse-Labs/.github#60
consumer: StegVerse-org/LLM-adapter#18
model_runtime_owner: StegVerse-002/micro-node-runtime#22
credential_policy_owner: StegVerse-Labs/TV
route_authority_owner: StegVerse-Labs/TVC
custody_reconstruction_owner: master-records/orchestration
state: ACTIVE / PRODUCT_INCOMPLETE
```

### Native local-model execution delta — 2026-08-10

The former descriptive step “execute/select a local model runtime” is superseded by executable heartbeat-worker behavior on branch `feat/ecosystem-chat-native-local-model-activation-20260810` / PR #68.

`workers/ecosystem_chat_sovereign_inference_worker.py` now:

1. searches only StegVerse-local workload locations for an already-materialized canonical `StegVerse-002/micro-node-runtime` capsule;
2. recognizes the capsule only when the canonical verifier, server, runtime module, manifest and local corpus are present;
3. on a non-hosted StegVerse carrier, directly executes `tools/verify_sovereign_model_runtime.py` instead of returning a descriptive instruction;
4. the canonical verifier launches the real loopback model server, performs real local inference, measures token/latency usage and returns the hash-bound sovereign model proof;
5. persists the accepted proof only under `receipts/ecosystem-chat-sovereign-inference/`;
6. advances to `TVC_LOCAL_MODEL_ROUTE_ADMISSION` when the proof is valid;
7. refuses to treat GitHub Actions, Render, Vercel or Cloudflare as production model-launch authority;
8. requires no GitHub token, source-repository credential or hosted-provider credential.

Canonical model implementation remains in `StegVerse-002/micro-node-runtime#22`; this heartbeat worker does not duplicate or train another model.

Credential/route boundary:

```text
TV credential policy: credential class NONE
GitHub token required: false
GitHub Actions production role: false
hosted provider credential required: false
TVC route authority required: true
model output grants authority: false
execution authority effect from route/model: NONE
```

After local proof the next required sequence is:

```text
canonical local model proof
-> TVC evaluate sovereign local model route
-> ROUTE_ADMITTED with credential_requirement=NONE
-> StegVerseLocalHTTPProviderClient consumes exactly the admitted private endpoint
-> governed E1 -> model worker -> E2
-> measured provider/model usage persisted
-> Master Records provider-usage reconstruction PASS
-> Master Records transition reconstruction PASS for same execution
-> Ecosystem Chat activation evidence
```

## Sovereign heartbeat/runtime activation worker

```text
task_id: SHWP-DURABLE-RUNTIME-ACTIVATION
worker_id: sovereign-runtime-activation-worker
canonical_issue: StegVerse-Labs/.github#59
state: ACTIVE / BLOCKED / RECHECKING
```

It completes only after a StegVerse-owned/federated node directly proves durable materialization, native service registration, continuous runtime-v9 execution, advancing heartbeat epochs, worker subsignal carriage, worker execution, controlled restart, no epoch/registry regression, no split-brain state and durable reconstruction across restart.

## Production host boundary

Canonical production surfaces include:

```text
heartbeat_runtime/engine_v9.py
scripts/run_heartbeat_runtime.py
scripts/install_sovereign_heartbeat_service.py
workers/sovereign_runtime_activation_worker.py
workers/ecosystem_chat_sovereign_inference_worker.py
handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json
handoffs/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json
control/worker-registry.json
control/worker-status.json
```

The node OS service manager provides process liveness only. `HeartbeatRuntime` owns cadence, worker-control evaluation, claims, fences, cycle leases and worker coordination.

After local materialization:

```text
network_fetch_required: false
github_runtime_dependency: false
third_party_process_host_required: false
third_party_deployment_required: false
third_party_scheduler_required: false
execution_authority_effect: NONE
```

GitHub repositories/Actions may be mirrors, review and validation surfaces. They may not own production deployment, liveness, scheduling, worker leasing, runtime model retrieval, model execution or execution authority.

## Validation boundary

PR #68 validation may prove source compatibility and deterministic behavior only. It cannot satisfy the sovereign-carrier predicates.

Required deterministic validation for the native local-model delta:

```text
reference proof acceptance/rejection
materialized local runtime discovery
real local verifier process invocation contract
proof persistence in admitted worker receipt namespace
hosted validation environment rejected as production launch authority
no GitHub-token requirement
```

## Remaining direct activation predicates

Ecosystem Chat product activation reaches 100% only after the inference worker directly observes:

1. real model process on a StegVerse-owned/federated node;
2. loopback/private/StegVerse-local inference endpoint;
3. TVC `ROUTE_ADMITTED` for that canonical runtime proof with credential class `NONE`;
4. the admitted endpoint consumed by `StegVerseLocalHTTPProviderClient`;
5. sovereign E1 -> worker -> E2 execution;
6. measured model/provider usage persisted;
7. provider-usage reconstruction PASS in Master Records;
8. transition reconstruction PASS for the same execution;
9. `third_party_inference_required=false` and `github_token_required=false`.

No synthetic fixture, hosted CI success or manually constructed receipt satisfies these predicates.

## Cross-repository continuation

```text
heartbeat/runtime worker: StegVerse-Labs/.github#59
inference worker: StegVerse-Labs/.github#60
archive worker gate: StegVerse-Labs/.github#61
sovereign migration: StegVerse-002/micro-node-runtime#16
canonical local model/runtime: StegVerse-002/micro-node-runtime#22
credential policy: StegVerse-Labs/TV/policies/sovereign_local_model_credential_policy.v1.json
route activation: StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json
inference transport: StegVerse-org/LLM-adapter#18
custody/reconstruction: master-records/orchestration
```

## Collision boundaries

- no second heartbeat or scheduler;
- no duplicate local-model authority outside micro-node-runtime;
- no GitHub token or source-repository checkout in runtime discovery/launch/execution;
- no hosted provider as a production fallback;
- no duplicate TV/TVC route or credential authority;
- no duplicate LLM-adapter transport;
- no duplicate Master Records custody;
- no CI evidence represented as sovereign runtime activation.

## Completion assessment

```text
heartbeat protocol implementation: 100%
worker coordination implementation: 100%
sovereign host implementation: 100%
ephemeral E1/E2 carrier implementation: 100%
canonical local-model development: COMPLETE_RELEASED in micro-node-runtime#22
heartbeat-worker automatic local runtime discovery/launch/proof: IMPLEMENTED_IN_PR_68 / VALIDATION_PENDING
third-party production blocker: REMOVED
GitHub-token runtime dependency: PROHIBITED
sovereign runtime direct observation: pending
TVC-admitted local-model route direct observation: pending
LLM-adapter same-carrier private execution: pending
Master Records same-execution reconstruction: pending
Ecosystem Chat product activation: NOT COMPLETE
```

## Session consolidation / archive condition

The local-model selection and formal-model-development requirements are durable in `StegVerse-002/micro-node-runtime#22`. The no-GitHub-token correction is durable in TV/TVC and LLM-adapter task reconciliation. This session additionally owns PR #68 until deterministic validation, merge and main-branch reconciliation are complete.

After PR #68 is merged and validated, unfinished production predicates remain machine-owned by #59/#60, TVC route task, LLM-adapter #18 and Master Records. Product activation must still not be reported as complete until direct runtime evidence exists.
