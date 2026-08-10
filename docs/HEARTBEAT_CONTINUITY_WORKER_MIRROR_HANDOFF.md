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

The descriptive local-model selection step is eliminated. PR #68 already merged deterministic local capsule discovery and verifier invocation. `StegVerse-002/micro-node-runtime#28` subsequently merged persistent endpoint verification so the same model process can remain alive after proof.

Active integration branch `feat/persistent-sovereign-model-lifecycle-20260810` upgrades `workers/ecosystem_chat_sovereign_inference_worker.py` from temporary proof generation to heartbeat-owned model process lifecycle:

```text
find canonical materialized micro-node capsule
-> start tools/run_sovereign_model.py on free 127.0.0.1 port
-> verify exact running endpoint through canonical verifier --endpoint
-> persist live_model_process.json with pid/endpoint/model/proof/claim/fence
-> keep process alive across heartbeat cycles
-> require TVC ROUTE_ADMITTED / credential_requirement NONE
-> LLM-adapter consumes exactly admitted endpoint
-> governed E1 -> model -> E2
-> measured usage + same-execution Master Records reconstruction
-> heartbeat retires its model process after terminal success or stale/failed lease
```

The worker distinguishes a historical temporary-probe proof from a persistent endpoint proof. Route admission may advance only when the proof has `process_owned_by_verifier=false`, `live_endpoint_remains_available=true`, private endpoint evidence, matching canonical model identity, no third-party inference, no model authority, and no GitHub-token requirement.

Persistent lifecycle receipt:

```text
receipts/ecosystem-chat-sovereign-inference/live_model_process.json
schema: stegverse.sovereign-live-model-process/v0.1
heartbeat_owned: true
credential_requirement: NONE
github_token_required: false
third_party_execution_platform_required: false
```

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

No layer above grants authority merely because the model is co-resident or responsive.

## Validation evidence

Released predecessor:

```text
PR #68 merge: d4e22a3aa39b7f567e3a66d73d00abec1dcee494
Heartbeat Worker Project: 31381743245 / SUCCESS
organization control-plane validation: 31381743221 / SUCCESS
```

Canonical persistent-endpoint dependency:

```text
StegVerse-002/micro-node-runtime PR #28
merge: e64e1f36a85c0eb23937219118b649b9b18ae390
Validate Micro-Node Runtime: 31384116055 / job 93440650414 / SUCCESS
Handoff Authority: 31384116146 / SUCCESS
Continuity Provenance: 31384116566 / SUCCESS
PWC-003 Runtime Orchestrator: 31384116123 / SUCCESS
```

Current heartbeat lifecycle branch adds tests proving that a temporary verifier-owned proof cannot be mistaken for a live endpoint and that the heartbeat writes a bounded `LIVE_VERIFIED` lifecycle with credential `NONE` and no GitHub token. Hosted CI can validate these semantics but cannot satisfy production activation.

## Remaining direct activation predicates

Ecosystem Chat activation reaches terminal success only after one StegVerse-owned/federated carrier directly proves:

1. canonical model process remains live under the heartbeat-owned lifecycle;
2. TVC admits that exact private endpoint with credential class `NONE`;
3. `StegVerseLocalHTTPProviderClient` consumes that exact endpoint;
4. sovereign E1 -> model worker -> E2 completes;
5. measured provider/model usage persists;
6. Master Records provider-usage reconstruction PASS;
7. Master Records transition reconstruction PASS for the same execution;
8. model process is retired by the heartbeat after terminal/release condition;
9. `third_party_inference_required=false` and `github_token_required=false` throughout.

Separately, heartbeat production activation still requires direct durable service/restart continuity evidence under #59. Repository/CI success is not that evidence.

## Collision boundaries

- one heartbeat and one canonical worker registry only;
- no duplicate local-model authority;
- no GitHub token/source checkout in runtime discovery, launch, proof, route or inference;
- GitHub Actions is validation only;
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
heartbeat persistent model lifecycle: IMPLEMENTED_BRANCH_VALIDATION_PENDING
TVC credential-free route evaluator: COMPLETE_MERGED / carrier observation pending
GitHub-token runtime dependency: PROHIBITED
same-carrier LLM-adapter execution: pending
Master Records same-execution reconstruction: pending
sovereign runtime direct observation: pending
Ecosystem Chat product activation: NOT COMPLETE
```

## Session consolidation / archive condition

The model development, no-GitHub-token requirement, persistent endpoint proof contract, authority split, and remaining exact activation sequence are durable in canonical repositories. This session still owns the heartbeat persistent lifecycle branch until validation/merge. After merge, continuation moves to the TVC/LLM-adapter/Master Records same-carrier integration unless another active claim already owns it. Do not declare archive-ready while inherited activation goals remain non-terminal without a measurably progressing canonical successor.
