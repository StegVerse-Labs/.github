# StegVerse Test Lanes Autolaunch Mirror Handoff

Updated: 2026-08-18T17:19:00-05:00

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

- `handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json` — G18 carrier + task-capable WorkerCoordinator release gate.
- `docs/SOVEREIGN_HEARTBEAT_DEPLOYMENT_MIRROR_HANDOFF.md` — canonical separated-runtime deployment state.
- `.github#60` / `docs/ECOSYSTEM_CHAT_ORPHAN_RECOVERY_MIRROR_HANDOFF.md` — recovery and same-execution StegVerse sovereign inference proof.
- `StegVerse-Labs/TVC/docs/PROVIDER_CAPSULE_MIRROR_HANDOFF.md` — live vault readiness, Provider Capsule, lease and external execution authority.
- `GCAT-BCAT-Engine/workflows/experiments/stegverse-test-lanes/TEST_LANES_MIRROR_HANDOFF.md` — exact nine-lane manifest/planner/primary adapter/evidence/comparator.

## Corrected sovereign runtime dependency

HB31 carrier continuity is observed, but the current worker state is still:

```text
carrier: ACTIVE HB31 / generation31
worker observed carrier: 31/31
worker observation_mode: CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION
worker runtime tick: 2
G18 active lease: still projected
task-capable WorkerCoordinator cycle at HB31+: NOT OBSERVED
```

The prior transition receipt's `RELEASE_COMPLETE` interpretation is superseded for runtime-goal release by the task-capable-worker hardening:

```text
130c18fb9e87682400d8b9e43c836ad322b803eb  corrected transition release validator
5d728a928de9ed5b5f4d24d474bb1e4252725591  observation-only regression tests
73578a3a8b3d600077e86e43cfd2e3ad7e74bbea  supervisor requires post-spawn worker tick
90450ff986a1f2051193b466602150a8be3ee23c  supervisor regression tests
1200bfa4d3d38770dedd4d8eb99ff95539bb553b  sovereign activation proof requires worker progress
aba4c7fc658f1d23cd8e64cc664aa76dc50de323  activation verifier tests
ac25265839eba094bcf1250fd04ec4b640947784  corrected release reconciliation receipt
```

A carrier reference observation can wake this matrix, but it cannot satisfy the sovereign runtime dependency. The required upstream sequence is now:

```text
#122/#12 starts/restarts task-capable scripts/run_worker_runtime.py
-> WorkerCoordinator real cycle at HB31+
-> G18 terminal response consumed
-> G18 claim/fence released
-> orphan recovery fresh fence >20
-> parent fresh fence >20
-> StegVerse local model/TVC/LLM-adapter/Master Records same-execution proof
-> only then can sovereign_same_execution_activation=true
```

Therefore the existing matrix predicate `sovereign_same_execution_activation=true` already prevents the canonical 9/9 test from launching on observation-only HB31 state; no duplicate matrix authority is added.

## Authority model

The v12 heartbeat carrier is a wake/reference signal only. It may carry a non-authorizing assignment trigger for this `HANDOFF_READY` task. WorkerCoordinator independently:

1. applies the registry fragment;
2. validates executable handoff/authority;
3. resolves exact worker capability/adapter;
4. creates a fresh scheduler claim/fence with finite assignment timer;
5. invokes the worker.

The worker's matrix may return only `BLOCKED`, `FAIL_CLOSED`, or `ALLOW_EXECUTION_CLAIM`. `ALLOW_EXECUTION_CLAIM` still grants no execution authority; the worker creates a subordinate fresh test-run claim bound to the scheduler claim/fence, exact matrix evaluation, plan/manifest hashes and non-secret model-selection hash before the first candidate call.

## Installed source/control surfaces

```text
f62213a829d02a86de38228a4e727cdaa21c292f  initial mirror handoff
c8001f5e58ddb5c329fc4848e1b308c8c77ceeaa  matrix with external-model-selection gate
f13a5f4a42738b8691bb8b92c833e6fc6dd42559  deterministic matrix evaluator
c391a89db9eca1018806c620f87b77bd26d27f65  matrix tests
507005bbf3439419c475acd08e8fdc58b516e9b7  heartbeat-managed autolaunch worker
f1ee26904a3eb2927dd6d22a2b2514a8cb32debc  worker boundary/fence tests
87cea4e615c6f53956ad7f0f6c08154de3440f89  bounded authorization
3873b08edcc40a73b0ced0bc4249e73722a696e0  runtime-safe autolaunch entrypoint
4c3a88aa4f052ccdb4654f259efe82d63dc637ba  production adapter uses runtime-safe entrypoint
b17ea05655768b94d5cdbc57fe9d55a556a2f4f6  validation workflow reconciled
 e22be83c1a27040dc2baa84a4ee122583622409e  finite worker cost basis
ff3392e2acfa2f6518456ad5140bde387c62b606  executable handoff
5b93a37289a91162079790ea8fc4cc0637fa451e  registry fragment bound to handoff/cost basis
```

## Required matrix

The canonical full 9/9 run requires simultaneously:

- separated carrier epoch >= HB30;
- WorkerCoordinator observed current carrier;
- transition/state reconstruction passes;
- **same-execution sovereign activation receipt passes**;
- live loopback StegVerse primary endpoint READY/private/model-verified;
- StegVerse credential requirement `NONE`; third-party inference not required;
- TVC route admitted with credential authority `TV/TVC`;
- no NON-TV/TVC provider/GitHub secret/token authority;
- OpenAI, Anthropic, DeepSeek and Kimi each `READY_FOR_TVC_EXECUTION` through live TVC vault state;
- exact external API model IDs in non-secret local model-selection file;
- exact manifest/task/plan identities pass;
- 9 logical lanes and 5 execution groups READY;
- runtime-safe source validation passes;
- evidence sink writable;
- no conflicting test-run claim.

A partial portable experiment may skip unavailable external controls. Only this named `CANONICAL_FULL_9_OF_9` autolaunch requires all four external providers. That does not change StegVerse precedence.

## Worker execution pipeline

```text
v12 carrier transition
-> task-capable WorkerCoordinator fresh scheduler claim/fence
-> runtime-safe source validation
-> live TVC vault materialization/resolution
-> exact portable re-plan
-> conditional matrix evaluation
-> BLOCKED: persist exact predicates and retry on later worker ticks
-> FAIL_CLOSED: persist authority/integrity failure
-> ALLOW_EXECUTION_CLAIM: acquire fresh subordinate test-run claim
-> one StegVerse PRIMARY candidate via already-live loopback endpoint
-> four TVC external candidates through existing broker/vault boundary
-> build exactly nine sanitized lane-evidence records
-> deterministic comparator
-> terminal receipt only when PASS and lane_evidence_count=9
```

## Test Lanes source consumed

```text
462b829abb1f09516dadef4e41a41c494aa62a4f  sovereign PRIMARY candidate adapter
d57d43c29f7657b77d3a5a8c061c3e90d6e6d1d5  stdlib primary-adapter tests
83fad5f1fa0e560ea42090bbfcb2ca4fdab4f2b2  five-candidate -> nine-lane evidence builder
aa94e8d443a4768f4bf0ce1b28a43c5617454a29  evidence + comparator tests
a1739fe5940a1597e2114a6c63da46f040b74fef  Test Lanes validation hook
```

RAW/GOVERNED pairs reuse the exact same external candidate; governance occurs at the StegVerse output boundary and does not make a second provider call.

## External model identity boundary

Historical Generation-2 UI labels are not silently converted into API model IDs. Exact model selection is a non-secret local boundary and TVC independently validates each selected model before lease issuance.

## Validation state

```text
Test Lanes/autolaunch source: INSTALLED
release-hardening source: INSTALLED
latest release-hardening hosted workflow directly observed: NO
combined status exposed: NO
live task-capable WorkerCoordinator cycle: NO
G18 terminalization: NO
orphan recovery live execution: NO
same-execution sovereign activation: NO
live matrix evaluation receipt: NO
canonical 9/9 runtime result: NO
```

## Collision boundaries

1. Do not mutate/duplicate G18 heartbeat implementation or fence.
2. Heartbeat never grants execution authority.
3. Do not create another TV/TVC vault/provider broker/credential ingress/lease ledger.
4. External providers never become PRIMARY or sovereign prerequisites.
5. Source, plan, READY, handoff, assignment, machine ownership, workflow success, PID presence, or observation-only worker state are never runtime completion.
6. Do not label fewer than nine executed logical lanes as canonical 9/9.
7. Do not guess external API model IDs.

## Exact next execution

1. Existing #122/#12 sovereign owner starts/restarts task-capable WorkerCoordinator.
2. G18 terminalizes and releases fence18.
3. Orphan recovery obtains fresh fence >20 and completes custody reconstruction.
4. Parent obtains fresh fence >20 and produces same-execution StegVerse model/TVC/LLM/Master Records proof.
5. Autolaunch task receives a task-capable WorkerCoordinator claim and persists matrix result.
6. Once every matrix predicate passes, execute five candidates, build nine evidence records, compare, and persist terminal PASS.
7. Propagate verified terminal evidence to TVC, Test Lanes, Master Records, and required release/publication surfaces.

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
