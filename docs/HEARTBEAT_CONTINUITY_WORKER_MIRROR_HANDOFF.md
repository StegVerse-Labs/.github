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
durable_continuous_sovereign_runtime_observed: false
product_activation: INCOMPLETE
```

## Sovereign local-model lifecycle

The descriptive local-model selection step is eliminated. PR #68 merged local capsule discovery/verifier invocation. `StegVerse-002/micro-node-runtime#28` merged persistent endpoint verification. `.github#69` merged heartbeat-owned persistent model process lifecycle at `4479fbb5399ccd1509ec1fdcc95dacfcc173b9b8` and passed PR plus main validation.

Canonical live sequence is now executable through the TVC boundary:

```text
heartbeat discovers materialized micro-node capsule
-> starts tools/run_sovereign_model.py on a loopback port
-> verifies that exact running endpoint through canonical verifier --endpoint
-> persists live_model_process.json with pid/endpoint/model/proof/claim/fence
-> keeps process alive across heartbeat cycles
-> discovers a locally materialized canonical TVC capsule
-> invokes TVC scripts/evaluate_sovereign_local_model_route.py
-> verifies the TVC receipt binds exact proof hash + endpoint
-> requires ROUTE_ADMITTED / credential_requirement NONE / github_token_required false
-> advances to LLM_ADAPTER_SAME_ENDPOINT_EXECUTION
-> governed E1 -> model -> E2
-> measured usage + same-execution Master Records reconstruction
-> heartbeat retires its model process after terminal success or stale/failed lease
```

`workers/tvc_sovereign_route_bridge.py` does not reimplement TVC policy. It locates the canonical TVC task/module/CLI on StegVerse-local workload paths and invokes that code. `workers/ecosystem_chat_sovereign_route_worker.py` chains the canonical inference worker into TVC route authority and fails closed if TVC is absent or denies the exact proof/endpoint.

`control/process-worker-adapters.json` generation 7 points `process:ecosystem-chat-sovereign-inference-v1` to this chained worker. Production environment allowlist remains empty: no GitHub token or hosted-provider credential is admitted to the worker process.

## Authority split

```text
model/runtime definition + server + proof: StegVerse-002/micro-node-runtime#22
heartbeat process lifecycle + claim/fence/lease: StegVerse-Labs/.github#60
credential policy: StegVerse-Labs/TV / class NONE
route authority: StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json
private provider transport: StegVerse-org/LLM-adapter#18
custody/reconstruction: master-records/orchestration
execution/admissibility: CGE/StegGate
```

No model, route, transport, or heartbeat liveness observation grants execution authority.

## Validation evidence

```text
PR #68 merge: d4e22a3aa39b7f567e3a66d73d00abec1dcee494
PR #68 Heartbeat Worker Project: 31381743245 / SUCCESS
micro-node-runtime PR #28 merge: e64e1f36a85c0eb23937219118b649b9b18ae390
micro-node Validate Runtime: 31384116055 / job 93440650414 / SUCCESS
micro-node Handoff Authority: 31384116146 / SUCCESS
micro-node Continuity Provenance: 31384116566 / SUCCESS
micro-node PWC-003 Orchestrator: 31384116123 / SUCCESS
.github PR #69 merge: 4479fbb5399ccd1509ec1fdcc95dacfcc173b9b8
.github PR #69 control-plane validation: 31384247674 / SUCCESS
.github PR #69 Heartbeat Worker Project: 31384247619 / job 93441007434 / SUCCESS
.github main control-plane validation after #69: 31384310412 / SUCCESS
```

Current branch `feat/tvc-local-route-auto-admission-20260810` adds deterministic tests for local TVC discovery, exact proof-hash/endpoint binding, credential class `NONE`, and route authority ceiling. Hosted CI remains validation only and cannot satisfy sovereign-carrier activation.

## Remaining direct activation predicates

Ecosystem Chat terminal activation still requires direct observation on one StegVerse-owned/federated carrier of:

1. persistent heartbeat-owned model process;
2. canonical TVC route receipt for that exact proof/endpoint;
3. `StegVerseLocalHTTPProviderClient` consuming that exact route;
4. sovereign E1 -> model worker -> E2;
5. measured provider/model usage persisted;
6. Master Records provider-usage reconstruction PASS;
7. Master Records transition reconstruction PASS for the same execution;
8. heartbeat-owned model process retired under its release condition;
9. `third_party_inference_required=false` and `github_token_required=false` throughout.

Separately, heartbeat production activation still requires durable native-service/restart continuity evidence under #59.

## Collision boundaries

- one heartbeat and one canonical worker registry only;
- no duplicate local-model authority;
- no GitHub token/source checkout in runtime discovery, launch, proof, route or inference;
- GitHub Actions is validation only, never production route/runtime authority;
- no hosted provider fallback;
- TV/TVC remains credential/route authority, not execution authority;
- no duplicate LLM-adapter transport or Master Records custody.

## Completion assessment

```text
heartbeat protocol implementation: 100%
worker coordination implementation: 100%
sovereign host implementation: 100%
ephemeral E1/E2 carrier implementation: 100%
formal local-model development: COMPLETE_RELEASED
persistent local endpoint verifier: COMPLETE_MERGED_VALIDATED
heartbeat persistent model lifecycle: COMPLETE_MERGED_VALIDATED
TVC credential-free route evaluator: COMPLETE_MERGED / carrier observation pending
heartbeat -> local TVC automatic route invocation: IMPLEMENTED_BRANCH_VALIDATION_PENDING
GitHub-token runtime dependency: PROHIBITED
same-carrier LLM-adapter execution: pending
Master Records same-execution reconstruction: pending
sovereign runtime direct observation: pending
Ecosystem Chat product activation: NOT COMPLETE
```

## Session consolidation / archive condition

The model development, no-GitHub-token rule, persistent endpoint proof/lifecycle, TVC route contract, authority split, and remaining exact activation sequence are durable. This session owns the automatic heartbeat-to-TVC integration branch until validation/merge. After that, the next unique integration is LLM-adapter same-endpoint execution unless a live claim already owns it. Do not declare archive-ready while inherited activation goals remain non-terminal without a measurably progressing canonical successor.
