# StegVerse Test Lanes Autolaunch Mirror Handoff

Updated: 2026-08-18T15:00:00-05:00

## Active goal and claim

```text
goal_id: STEGVERSE-TEST-LANES-AUTOLAUNCH-001
originating_goal: Automatically execute the canonical full nine-lane StegVerse test only when all required runtime, authority, credential, model, immutable-input, validation, duplicate-claim and evidence boundaries are actually satisfied.
repository: StegVerse-Labs/.github
branch: main
canonical_executable_handoff: handoffs/STEGVERSE-TEST-LANES-AUTOLAUNCH-001.json
canonical_registry_fragment: control/worker-registry.d/test-lanes-autolaunch.json
canonical_adapter_fragment: control/process-worker-adapters.d/test-lanes-autolaunch.json
canonical_matrix: control/test-lanes-autolaunch-matrix.v1.json
claim_state: SOURCE_IMPLEMENTED_REGISTERED_REQUIRED_LIVE_EXECUTION_PENDING
primary_provider: stegverse_local
third_party_role: CONTROL_OR_FALLBACK_ONLY
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_allowed: false
heartbeat_grants_execution_authority: false
archive_state: PROHIBITED_UNTIL_CANONICAL_9_LANE_RUNTIME_OUTCOME_IS_TERMINAL
```

## Canonical dependencies

- `handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json` — G18 machine-owned HB30+/WorkerCoordinator activation.
- `.github#60` / `handoffs/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json` — same-execution StegVerse sovereign inference proof.
- `StegVerse-Labs/TVC/docs/PROVIDER_CAPSULE_MIRROR_HANDOFF.md` — live vault readiness, Provider Capsule, lease and external execution authority.
- `GCAT-BCAT-Engine/workflows/experiments/stegverse-test-lanes/TEST_LANES_MIRROR_HANDOFF.md` — exact nine-lane manifest/planner/primary adapter/evidence/comparator.

## Authority model

The v12 heartbeat carrier is a wake/reference signal only. It may carry a non-authorizing assignment trigger for this `HANDOFF_READY` task. WorkerCoordinator independently:

1. applies the registry fragment;
2. validates the executable handoff/authority;
3. resolves the exact worker capability/adapter;
4. creates a fresh scheduler claim/fence with a finite assignment timer;
5. invokes the worker.

The worker's matrix may return only `BLOCKED`, `FAIL_CLOSED`, or `ALLOW_EXECUTION_CLAIM`. `ALLOW_EXECUTION_CLAIM` still grants no execution authority; the worker creates a subordinate fresh **test-run** claim bound to the scheduler claim/fence, exact matrix evaluation, plan/manifest hashes and non-secret model-selection hash before the first candidate call.

## Installed source/control surfaces

```text
f62213a829d02a86de38228a4e727cdaa21c292f  initial mirror handoff
394dae06...  initial condition matrix
c8001f5e58ddb5c329fc4848e1b308c8c77ceeaa  matrix with explicit external-model-selection gate
f13a5f4a42738b8691bb8b92c833e6fc6dd42559  deterministic matrix evaluator
b495c85544d98d2002ce7739871859b30f358b85  initial matrix tests
c391a89db9eca1018806c620f87b77bd26d27f65  model-selection matrix-test reconciliation
507005bbf3439419c475acd08e8fdc58b516e9b7  heartbeat-managed autolaunch worker
f1ee26904a3eb2927dd6d22a2b2514a8cb32debc  worker boundary/fence tests
87cea4e615c6f53956ad7f0f6c08154de3440f89  bounded authorization
19046cd6833a2d8c78d32098024a3fc07bdedae4  initial worker-registry fragment
1d1fcbdf94f8ea097ac75d457bf783a99710da54  initial process-adapter fragment
3873b08edcc40a73b0ced0bc4249e73722a696e0  runtime-safe autolaunch entrypoint
4c3a88aa4f052ccdb4654f259efe82d63dc637ba  adapter switched to runtime-safe entrypoint
3ba7d204cddc00e5fe516220e1711018f6ec838d  initial validation-only workflow
b17ea05655768b94d5cdbc57fe9d55a556a2f4f6  validation workflow reconciled with executable scheduler binding
e22be83c1a27040dc2baa84a4ee122583622409e  finite worker cost basis
ff3392e2acfa2f6518456ad5140bde387c62b606  executable handoff
5b93a37289a91162079790ea8fc4cc0637fa451e  registry fragment bound to executable handoff/cost basis
```

## Required matrix

The canonical full 9/9 run requires all of the following simultaneously:

- separated carrier epoch >= HB30;
- WorkerCoordinator has observed the current carrier;
- transition/state reconstruction passes;
- same-execution sovereign activation receipt passes;
- live loopback StegVerse primary endpoint is READY, private-only and model-verified;
- StegVerse credential requirement is `NONE` and third-party inference is not required;
- TVC route is admitted with credential authority `TV/TVC`;
- no NON-TV/TVC provider/GitHub secret/token authority is present;
- OpenAI, Anthropic, DeepSeek and Kimi each resolve `READY_FOR_TVC_EXECUTION` through live TVC vault state;
- exact external API model IDs are present in a non-secret local `stegverse.test-lanes-model-selection/v1` file;
- exact manifest/task/plan identities pass;
- 9 logical lanes and 5 execution groups are READY;
- runtime-safe source validation passes;
- evidence sink is writable;
- no conflicting test-run claim exists.

A partial portable experiment may still skip unavailable external controls. **Only this named `CANONICAL_FULL_9_OF_9` autolaunch requires all four external providers.** That requirement does not change StegVerse provider precedence.

## Worker execution pipeline

```text
v12 carrier transition
-> non-authorizing assignment-trigger packet
-> WorkerCoordinator fresh scheduler claim/fence
-> runtime-safe source validation
-> live TVC vault materialization/resolution
-> exact portable re-plan
-> conditional matrix evaluation
-> if BLOCKED: persist exact predicates and retry on later worker ticks
-> if FAIL_CLOSED: persist authority/integrity failure
-> if ALLOW_EXECUTION_CLAIM: acquire fresh subordinate test-run claim
-> one StegVerse PRIMARY candidate via already-live loopback endpoint
-> four TVC external candidates through existing broker/vault boundary
-> build exactly nine sanitized lane-evidence records
-> deterministic comparator
-> terminal receipt only when PASS and lane_evidence_count=9
```

The worker never accepts a provider API key. Provider keys remain inside the existing TV/TVC vault/broker path. Hosted environments are rejected as production execution surfaces. GitHub Actions is validation-only.

## Test Lanes source completed for autolaunch

The autolaunch worker consumes newly installed source in `GCAT-BCAT-Engine/workflows`:

```text
462b829abb1f09516dadef4e41a41c494aa62a4f  sovereign PRIMARY candidate adapter with measured latency
d57d43c29f7657b77d3a5a8c061c3e90d6e6d1d5  stdlib primary-adapter tests
83fad5f1fa0e560ea42090bbfcb2ca4fdab4f2b2  five-candidate -> nine-lane evidence builder
aa94e8d443a4768f4bf0ce1b28a43c5617454a29  nine-evidence + comparator tests
a1739fe5940a1597e2114a6c63da46f040b74fef  Test Lanes validation workflow hook
```

The evidence builder enforces identical candidate output/hash for each external RAW/GOVERNED pair and adds deterministic output-boundary governance evidence without making another provider call.

## External model identity boundary

Historical Generation-2 artifacts are insufficient as universal API model selectors: some contain UI labels or unspecified UI identity. The worker therefore does not guess API identifiers. The exact model-selection file is non-secret and may be supplied at `STEGVERSE_TEST_LANES_MODEL_SELECTION`, `~/.stegverse/test-lanes/model-selection.json`, or the admitted runtime-local path. TVC independently validates each selected model before lease issuance.

## Validation state

```text
matrix/evaluator source: INSTALLED
matrix tests: INSTALLED
worker/entrypoint source: INSTALLED
worker boundary/fence tests: INSTALLED
executable handoff: INSTALLED
worker-registry fragment: INSTALLED
process-adapter fragment: INSTALLED
finite cost basis: INSTALLED
validation-only workflow: INSTALLED
hosted validation directly observed for current source: NO
live registry-fragment projection into monolithic worker registry: NOT_YET_OBSERVED
live v12 assignment trigger for this task: NOT_YET_OBSERVED
live WorkerCoordinator claim/fence for this task: NOT_YET_OBSERVED
live matrix evaluation receipt: NOT_YET_OBSERVED
canonical 9/9 runtime result: NOT_YET_OBSERVED
```

Direct commit workflow/status queries expose no current run/status records, so CI PASS is not inferred.

## Collision boundaries

1. Do not mutate/duplicate G18 heartbeat implementation or fencing token.
2. Heartbeat never grants execution authority.
3. Do not create another TV/TVC vault, provider broker, credential ingress or lease ledger.
4. Do not make external providers PRIMARY or sovereign prerequisites.
5. Do not accept source, plan, `READY`, handoff, assignment, machine-owned state or workflow success as runtime completion.
6. Do not label fewer than nine executed logical lanes as this canonical 9/9 result.
7. Do not guess external API model IDs from historical UI labels.

## Exact next execution

1. Observe G18 produce/validate separated HB30+ carrier and WorkerCoordinator state.
2. WorkerCoordinator applies this task fragment; a subsequent carrier cycle emits its non-authorizing assignment trigger; WorkerCoordinator binds the fresh scheduler claim/fence.
3. The worker executes and persists its matrix result. While provider credentials/model IDs or sovereign predicates remain absent it must stay `BLOCKED`, not `COMPLETED`.
4. Once all matrix predicates pass, run the five candidate executions, nine-evidence build and deterministic comparison automatically.
5. Consume and verify the terminal receipt; propagate terminal evidence to TVC, Test Lanes, Master Records and any required release/publication surfaces.

## Completion accounting

```text
required developed surfaces: 10/10
scaffolding/stubs: 0
missing source files: 0
validation mechanisms installed: 5/5
hosted validation directly observed: 0/1
worker-control-plane integration installed: 4/4
live activation/execution predicates: 0/5
source implementation: 100%
goal activation: 58%
archive readiness: 0% until canonical 9/9 runtime outcome is terminal
```
