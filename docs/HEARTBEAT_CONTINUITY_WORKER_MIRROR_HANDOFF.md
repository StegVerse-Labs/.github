# Heartbeat Continuity Worker Mirror Handoff

## Authority

This scoped handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md` and `StegVerse-Labs/.github#12`. It is the canonical continuation for the single-heartbeat worker/runtime activation goal. Live default-branch repository state, registry/status, claims, fences, checkpoints, receipts, issues, merged pull requests, and direct sovereign-node observations supersede chat or CI claims.

## Active goal

```text
goal_id: SOVEREIGN-HEARTBEAT-PRODUCTION-ACTIVATION
repository: StegVerse-Labs/.github
canonical_owner: StegVerse-Labs/.github#12
inference_task: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
inference_issue: #60
canonical_runtime: heartbeat_runtime.engine_v9.HeartbeatRuntime
activation_carrier: single_stegverse_heartbeat
heartbeat_default_interval_ms: 10.0
worker_lease_clock: canonical_heartbeat_cycle
third_party_deployment_dependency: NONE
third_party_scheduler_dependency: NONE
third_party_process_host_dependency: NONE
github_token_runtime_dependency: PROHIBITED
local_model_credential_authority: StegVerse-Labs/TV+TVC
local_model_credential_requirement: NONE
durable_continuous_sovereign_runtime_observed: false
product_activation: INCOMPLETE
```

## Canonical executable sovereign inference path

The former descriptive local-model selection step is eliminated. The canonical path is executable through the model, TVC route, and LLM-adapter transport boundaries:

```text
heartbeat discovers materialized StegVerse-002/micro-node-runtime capsule
-> starts canonical model server on loopback
-> verifies exact running endpoint without terminating it
-> persists PID/endpoint/model/proof/claim/fence lifecycle
-> discovers locally materialized canonical TVC capsule
-> invokes TVC scripts/evaluate_sovereign_local_model_route.py
-> verifies exact proof-hash + endpoint binding
-> requires ROUTE_ADMITTED / credential_requirement NONE
-> discovers locally materialized canonical StegVerse-org/LLM-adapter capsule
-> strips GitHub authentication variables from the LLM-adapter child environment
-> invokes scripts/execute_canonical_sovereign_route.py from task LLMA-SOVEREIGN-CARRIER-EXECUTION-020
-> StegVerseLocalHTTPProviderClient consumes exactly the TVC-admitted endpoint
-> measured provider/model usage is persisted in the execution receipt
-> canonical Master Records provider-usage and same-execution transition reconstruction
-> immutable zero-blocker activation receipt
-> heartbeat retires its model process after terminal success or stale/failed lease
```

No source checkout, GitHub token, hosted-model credential, hosted provider, Render, Vercel, or Cloudflare dependency belongs to the production model discovery/launch/proof/route/inference path.

## Authority split

```text
model/runtime definition + server + proof: StegVerse-002/micro-node-runtime#22
heartbeat process lifecycle + claim/fence/lease: StegVerse-Labs/.github#60
credential policy: StegVerse-Labs/TV
route authority: StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json
private provider transport + measured usage: StegVerse-org/LLM-adapter / task LLMA-SOVEREIGN-CARRIER-EXECUTION-020
custody/reconstruction: master-records/orchestration
execution/admissibility: CGE/StegGate
```

TV/TVC owns the credential decision for the local model. Current credential class is `NONE`. The heartbeat and LLM-adapter do not create or substitute a GitHub credential lane.

## Installed implementation and validation evidence

```text
formal local model/runtime: StegVerse-002/micro-node-runtime / SOVEREIGN-LOCAL-MODEL-001 / COMPLETE_RELEASED
micro-node persistent endpoint PR #28 merge: e64e1f36a85c0eb23937219118b649b9b18ae390
micro-node Validate Runtime: 31384116055 / SUCCESS
micro-node Handoff Authority: 31384116146 / SUCCESS
micro-node Continuity Provenance: 31384116566 / SUCCESS
micro-node PWC-003 Orchestrator: 31384116123 / SUCCESS

heartbeat persistent model lifecycle PR #69 merge: 4479fbb5399ccd1509ec1fdcc95dacfcc173b9b8
PR #69 control-plane validation: 31384247674 / SUCCESS
PR #69 Heartbeat Worker Project: 31384247619 / SUCCESS

heartbeat -> canonical TVC automatic route invocation PR #70 merge: f25204874189a90bc2bc07f1ac65d060be41e397
PR #70 Heartbeat Worker Project: 31384657195 / SUCCESS
PR #70 control-plane validation: 31384657111 / SUCCESS
PR #70 handoff render: 31384657161 / SUCCESS

LLM-adapter sovereign carrier executor task: LLMA-SOVEREIGN-CARRIER-EXECUTION-020
LLM-adapter PR #135 merge: 72934c7cf135ce2953591a81fe01e16c9719ec2f
PR #135 validate: 31385239611 / SUCCESS
PR #135 Architecture Guard: 31385239593 / SUCCESS
PR #135 provider-owned usage validation: 31385239563 / SUCCESS
```

## Active integration claim

```text
task_id: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
repository: StegVerse-Labs/.github
branch: feat/llm-adapter-same-carrier-execution-20260810
role: same-carrier LLM-adapter integration
claim_state: CLAIMED_FOR_INTEGRATION
claim_created_at: 2026-08-10T15:32:00Z
release_condition: branch validates and merges, leaving direct sovereign-carrier execution/reconstruction to the machine-owned heartbeat path
collision_boundary: do not duplicate model, TV/TVC route authority, LLM-adapter transport, Master Records custody, heartbeat, or scheduler
```

Branch implementation adds `workers/llm_adapter_sovereign_execution_bridge.py`, extends `workers/ecosystem_chat_sovereign_route_worker.py`, updates process adapter generation 8, and adds `tests/test_llm_adapter_sovereign_execution_bridge.py`.

The bridge discovers only already-materialized local LLM-adapter surfaces. Before spawning task 020 it removes `GITHUB_TOKEN`, `GH_TOKEN`, `GITHUB_PAT`, `GITHUB_PERSONAL_ACCESS_TOKEN`, `ACTIONS_RUNTIME_TOKEN`, and `ACTIONS_ID_TOKEN_REQUEST_TOKEN` from the child environment. It binds `STEGVERSE_LOCAL_MODEL_CREDENTIAL_REQUIREMENT=NONE` and records TV/TVC as the credential authority. Existing provider execution receipts are reused only when they bind the exact TVC route receipt and exact runtime proof, preventing duplicate execution across heartbeat rechecks.

## Remaining direct activation predicates

Ecosystem Chat terminal activation still requires direct observation on one StegVerse-owned/federated carrier of:

1. persistent heartbeat-owned model process;
2. canonical TVC route receipt for that exact proof/endpoint;
3. canonical LLM-adapter task 020 consuming that exact route;
4. sovereign E1 -> model worker -> E2 execution;
5. measured provider/model usage persisted;
6. Master Records provider-usage reconstruction PASS;
7. Master Records transition reconstruction PASS for the same execution;
8. immutable zero-blocker Ecosystem Chat activation receipt;
9. heartbeat-owned model process retired under its release condition;
10. `third_party_inference_required=false` and `github_token_required=false` throughout the production runtime chain.

Separately, heartbeat production activation still requires durable native-service/restart continuity evidence under #59.

## Cross-repository continuation

```text
heartbeat/runtime: StegVerse-Labs/.github#59/#60
canonical model/runtime: StegVerse-002/micro-node-runtime#16/#22
credential policy: StegVerse-Labs/TV
route authority: StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json
provider transport/usage: StegVerse-org/LLM-adapter/tasks/LLMA-SOVEREIGN-CARRIER-EXECUTION-020.json
custody/reconstruction: master-records/orchestration
activation projection: StegVerse-Labs/Site
post-activation propagation: GCAT-BCAT-Engine/Publisher, StegVerse-Labs/admissibility-wiki, StegVerse-002/stegguardian-wiki
```

## Collision and fail-closed boundaries

- one heartbeat and one canonical worker registry only;
- no duplicate local-model authority;
- no source-repository checkout in production runtime discovery;
- no GitHub auth forwarded into the model/TVC/LLM-adapter child runtime path;
- GitHub Actions remains a repository validation surface only and does not define model credentials, production route authority, or runtime activation;
- no hosted provider fallback;
- TV/TVC remains credential/route authority, not execution authority;
- no duplicate LLM-adapter transport or Master Records custody;
- missing local capsule, route denial, proof mismatch, endpoint mismatch, missing custody, or reconstruction failure remains BLOCKED/FAILED rather than success.

## Completion assessment

```text
heartbeat protocol implementation: 100%
worker coordination implementation: 100%
sovereign host implementation: 100%
ephemeral E1/E2 carrier implementation: 100%
formal local-model development: COMPLETE_RELEASED
persistent local endpoint verifier: COMPLETE_MERGED_VALIDATED
heartbeat persistent model lifecycle: COMPLETE_MERGED_VALIDATED
TVC credential-free route evaluator: COMPLETE_MERGED_VALIDATED
heartbeat -> local TVC automatic route invocation: COMPLETE_MERGED_VALIDATED
LLM-adapter canonical carrier executor: COMPLETE_MERGED_VALIDATED
heartbeat -> local LLM-adapter same-route invocation: IMPLEMENTED_BRANCH_VALIDATION_PENDING
Master Records same-execution reconstruction: pending direct observation
sovereign runtime direct observation: pending
Ecosystem Chat product activation: NOT COMPLETE
```

## Archive condition

This session is not archive-ready while it owns the active heartbeat-to-LLM-adapter integration branch. After branch validation and merge, the session may transfer remaining direct-runtime predicates to the existing machine-owned #59/#60, task 020, TVC route task, and `master-records/orchestration` only if the handoffs contain the complete continuation state and no unique chat-owned task remains. Product activation must not be inferred from repository merge or CI success.
