# Ecosystem Chat Orphan Recovery Mirror Handoff

Updated: 2026-08-23T16:19:00-05:00

## Authority and scope

Canonical recovery task: `RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28`.
Parent task: `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`.
Independent parent-executor issue: `.github#264`.
Independent parent-executor PR: `.github#265`.

```text
repository: StegVerse-Labs/.github
primary runtime/provider: StegVerse
third-party role: FALLBACK_ONLY
credential authority: TV/TVC
credential requirement: NONE
GitHub token runtime authority: NONE
heartbeat task authority: NONE
G18 task authority: NONE
```

Heartbeat is reference-only. Recovery and parent claims/fences belong to independent task control. G18 cleanup, WorkerCoordinator-specific execution, GitHub Actions, Render, and third-party infrastructure are not completion prerequisites.

## Authoritative terminal recovery evidence

Current `main` contains `receipts/ecosystem-chat-sovereign-inference/orphan-recovery-HB28.json` proving:

```text
state: PASS
recovery claim: SHWP-RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28-G22
recovery fence: 22
ended parent fence: 20
checkpoint_valid: true
old_authority_ended: true
old_authority_reused: false
master_records_custody_valid: true
successor_authority_granted: false
next_transition: SEPARATE_HIGHER_FENCE_PARENT_SUCCESSOR_AUTHORIZATION
github_token_required: false
third_party_execution_platform_required: false
authority_effect: NONE
```

Recovery is terminal. It must not be reacquired or replayed merely to satisfy a stale projection.

## Released recovery and reconciliation source

- Independent recovery executor: PR #245 merge `3bfc17f6d4b59f219b3354f5bdae0ecfe6b96ed5`.
- Self-contained immutable G20 custody: PR #260 merge `5e85a2d602fe7234a4bdff34aa1521b752dc2b49`.
- LIVE-009 stale validation reconciliation: PR #261 merge `ec5f95ca6125b3b46a5d0959ef1b0ad229f4c259`.
- Terminal recovery/parent reconciliation: PR #262 merge `fd10d4cfee8712663096a886f5275a3224857ebf`.

PR #262 exact validated head `c540de44f9a9b2bde680def6109f0edb9c0f117d` passed:

```text
Heartbeat Worker Project run 32619209041 / job 97144669508: SUCCESS
Organization control plane run 32619209070 / job 97144669666: SUCCESS
Ecosystem Chat Sovereign Inference Validation run 32619209045: SUCCESS
```

The recovery reconciliation claim is `COMPLETE_RELEASED`.

## Independent parent source executor: COMPLETE_RELEASED

PR #265 installed the explicit independent-task-control execution path:

```text
authorizations/SHWP-ECOSYSTEM-CHAT-INFERENCE-001-independent-parent.json
scripts/run_independent_ecosystem_chat_parent.py
control/worker-registry.d/ecosystem-chat-sovereign-inference-parent-001.json
workers/ecosystem_chat_sovereign_route_worker.py
workers/master_records_sovereign_reconstruction_bridge.py
tests/test_independent_ecosystem_chat_parent_executor.py
```

The executor:

1. refuses a duplicate current/newer parent claim;
2. projects the released parent HANDOFF_READY registration into the task-control checkout surface;
3. atomically mints a fresh fencing generation strictly greater than terminal G22;
4. treats heartbeat only as optional noncausal reference metadata;
5. invokes the existing StegVerse-local model -> TVC -> LLM-adapter worker on the actual sovereign execution surface instead of a disposable ProcessWorkerAdapter sandbox;
6. forwards only nonsecret local workload locators and explicitly strips GitHub/cloud/hosted authority inputs;
7. permits repository mutation only to `control/worker-registry.json` plus `receipts/ecosystem-chat-sovereign-inference/**`;
8. performs exact same-execution Master Records reconstruction;
9. requires the persistent conversational runtime to be ready after reconstruction before terminal completion;
10. releases each bounded parent attempt claim truthfully; nonterminal attempts return to HANDOFF_READY instead of leaving stale authority;
11. releases the parent claim before propagating an execution error or out-of-scope mutation denial, preventing fail-closed validation from stranding a live claim/fence.

Hosted CI is validation-only. It cannot satisfy the live activation transition.

### Exact final source validation and merge

PR #265 final exact validated head:

`5d4fc1c60936098cf1128b43095a9b3f2504cd55`

```text
Ecosystem Chat Sovereign Inference Validation
run: 32666957662
job: 97261739082
result: SUCCESS
compile: PASS
independent parent executor tests: 11/11 PASS
LLM-adapter bridge tests: 4/4 PASS
Master Records reconstruction bridge tests: 5/5 PASS
total focused tests: 20/20 PASS
scope-denial claim-release regression: PASS
hosted lane non-authorizing proof: PASS
```

PR #265 merged as:

`b5119c742dc2438fed5f143c6afebcedff78b1db`

The source implementation claim was released to `COMPLETE_RELEASED` in:

`control/session-implementation-claim-2026-08-23-ecosystem-chat-independent-parent-264.json`

Release evidence commit:

`cb2f2ffd8f532d92dec7edf707cc8495896a3c77`

The generic Heartbeat Worker and organization-control workflows on the PR encountered an unrelated malformed `handoffs/HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009.json` from concurrent heartbeat work. That failure is outside #264 ownership and does not override the exact source-dependent Ecosystem Chat PASS. This lane does not mutate that concurrent heartbeat source.

## Current canonical parent state

```yaml
recovery:
  state: COMPLETED
  terminal_receipt: receipts/ecosystem-chat-sovereign-inference/orphan-recovery-HB28.json
  terminal_fence: 22
  reacquisition_allowed: false

parent_source:
  state: COMPLETE_RELEASED
  merge: b5119c742dc2438fed5f143c6afebcedff78b1db
  claim_required_from_chat: false

parent_runtime:
  task_id: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
  state: HANDOFF_READY
  recovery_dependency: SATISFIED
  executor_registration: control/worker-registry.d/ecosystem-chat-sovereign-inference-parent-001.json
  executor_source: scripts/run_independent_ecosystem_chat_parent.py
  authorization: authorizations/SHWP-ECOSYSTEM-CHAT-INFERENCE-001-independent-parent.json
  authority_domain: INDEPENDENT_TASK_CONTROL
  required_next_authority: independently admitted fresh fence >22
  recovery_grants_parent_authority: false
  live_activation_proven: false
```

## Next required live execution

```text
admitted StegVerse task-control execution surface
-> scripts/run_independent_ecosystem_chat_parent.py
-> fresh parent claim/fence >22
-> real StegVerse local/private model process
-> private/loopback endpoint proof
-> TVC ROUTE_ADMITTED / credential_requirement NONE
-> exact StegVerse LLM-adapter execution
-> measured E1 -> model -> E2 usage
-> same-execution Master Records provider-usage reconstruction PASS
-> same-execution transition reconstruction PASS
-> persistent conversational runtime READY
-> bounded parent claim released terminally
```

No heartbeat transition, G18 terminalization, WorkerCoordinator-specific cycle, recovery replay, sibling Master Records checkout, GitHub workflow, Render service, or third-party provider is required to begin that parent transition.

## Collision boundaries

1. Do not reacquire or replay completed G22 recovery.
2. Do not reuse G18, G20, or G22 authority.
3. Recovery completion does not create parent authority.
4. Parent authority must be separately admitted with fencing token >22.
5. Heartbeat remains reference-only and cannot grant task authority.
6. GitHub/hosted workflows remain validation-only.
7. StegVerse remains primary; third parties remain fallback-only.
8. TV/TVC remains sole credential/secret/token authority.
9. Do not mutate the concurrent heartbeat protocol-anchor/LIVE-009 source lane from this workstream.

## Archive rule

Recovery and the #264 parent-executor source implementation are terminal and released. This chat session no longer owns a source implementation claim for them. Product activation remains nonterminal until actual fresh-fence parent execution produces same-execution Master Records PASS and persistent conversational runtime readiness. Site #388 publication and current-phone governed wallet proof remain separate nonterminal goals and should continue through their canonical owners.


## Canonical parent registry reconciliation — 2026-08-27

Live inspection found a material machine-state contradiction after terminal G22 recovery:

```text
authoritative parent handoff: HANDOFF_READY
parent registry fragment: HANDOFF_READY / INDEPENDENT_TASK_CONTROL / fresh fence >22
canonical control/worker-registry.json row: stale G20 BLOCKED / no admission object
```

Because registry fragments are intentionally append-only and do not overwrite an existing task ID, the stale canonical row prevented `WorkerCoordinator._activate_independently_admitted_tasks` from seeing the authorized parent candidate even though the newer fragment and handoff were correct.

The canonical registry row is now reconciled to the terminal-recovery successor state while preserving historical G20 transition history as evidence. Required current machine state:

```text
task_id: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
state: HANDOFF_READY
executor_binding: AUTHORIZED
claim_id: null
worker_id: null
heartbeat_timing: null
admission.authority_domain: INDEPENDENT_TASK_CONTROL
admission.claim_state: AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM
admission.minimum_fencing_token_exclusive: 22
old G20 authority reused: false
G22 recovery authority reused: false
heartbeat grants execution authority: false
```

The emitted task vector remains canonical and visible. After canonical-registry reconciliation, `control/worker-registry.json` is the single vector-bearing registry source for this task; the append-only registry fragment references the vector file but no longer duplicates the vector payload:

```text
notation: L R U I V G O C M T B E A P
vector:   50000000100000
profile:  task.v1
state:    EMITTED
```

This reconciliation does not execute the parent task and does not mint live activation evidence. It removes a stale canonical-registry blocker so the already-authorized independent task-control executor can truthfully acquire a new fence strictly greater than 22 when an admitted StegVerse execution surface is available.


## Resident execution request bridge — source validation pending

To reduce dependence on manual resident-console invocation without weakening task authority, this branch adds a bounded local source-refresh consumption path:

```text
control/resident-execution-request.json
-> local source refresh copies the non-authorizing request
-> scripts/consume_resident_execution_request.py
-> exactly one attempt per request id + content hash
-> scripts/refresh_and_execute_resident_task.py --ecosystem-chat-parent
-> scripts/run_independent_ecosystem_chat_parent.py
```

Required semantics:

```text
request grants authority: false
parent executor retains claim/fence authority: true
fresh fence floor: >22
heartbeat execution authority: false
GitHub-token runtime authority: NONE
credential authority: TV/TVC
network source fetch: false
second user-operated machine required: false
same request automatic retry: false
runtime execution observed: false
```

This is source integration only until exact validation succeeds and the source is merged. Even after merge, it does not prove the resident source-refresh service is installed or active and does not prove the request was consumed. The direct portable one-shot remains valid independently of the watcher. A resident attempt must be evidenced by sovereign-host receipts and a fresh parent fence; hosted validation cannot satisfy that boundary.


## Resident execution request merge/validation — 2026-08-27

PR #321 merged exact validated head `a4537c9b373d949481da21d0d76616ca22bf8ced` as `a81ee4e60916bb32aa7aa2c5f6a1cb25530b80e5`.

Source validation:

```text
Heartbeat Worker Project run 33119900198: SUCCESS
Organization control plane run 33119900137: SUCCESS
complete deterministic repository suite: PASS
```

Current live boundary after merge:

```text
resident request source: MERGED / VALIDATED
worker-source-refresh.latest.json: NOT OBSERVED
resident-execution-request-consumption.latest.json: NOT OBSERVED
resident-targeted-execution.latest.json: NOT OBSERVED
fresh parent fence >22: NOT OBSERVED
independent_parent_activation.latest.json: NOT OBSERVED
runtime execution: NOT OBSERVED
activation: NOT PROVEN
```

The merge therefore improves the resident execution path but does not satisfy runtime execution. The next machine boundary is observation or activation of an existing sovereign resident source-consumption/startup path. GitHub Actions remains validation-only.


## Post-parent projection + TVC persistence closure — 2026-08-27

The resident execution source chain now includes both post-terminal projection and the downstream TVC-owned durable evidence-persistence seam.

```text
.github resident request bridge:
  merge: a81ee4e60916bb32aa7aa2c5f6a1cb25530b80e5
  runtime request consumption: NOT OBSERVED

.github automatic post-parent projection:
  validated head: d539b7ef074be46ff835962d28c1a80a3fdd68ba
  Heartbeat Worker validation: 33135790458 SUCCESS
  Organization Control Plane: 33135790453 SUCCESS
  merge: b746671d1db4d16ab486f94b9b0bd4683c2a3010
  runtime projection observed: false

TVC activation-evidence persistence:
  task: TVC-ECOSYSTEM-CHAT-ACTIVATION-EVIDENCE-001
  validated head: 7af83362d3314105831b50240a23cf8e9079cb47
  validation: 33135951150 SUCCESS
  merge: 4c8d3440fde168414c700f7e54909e81b2f27e1e
  runtime packet: receipts/ecosystem-chat-activation-evidence/transport.latest.json
  runtime persistence observed: false
  expected state after genuine execution: READY_FOR_SITE_IMPORT

Site downstream owner:
  active lane: PR #474
  claim: SITE-ECOSYSTEM-CHAT-ACTIVATION-RETENTION-CREDENTIAL-CLEAN-471-20260823
  duplicate Site importer authorized: false
```

Current live receipts remain absent for source refresh, request consumption, resident targeted execution, terminal parent activation, and TVC transport persistence. Therefore the actual product state remains `HANDOFF_READY / LIVE_EXECUTION_PENDING`, not activated.

The machine sequence is now source-complete through the TVC persistence boundary:

`resident consumption -> fresh fence >22 -> local model -> TVC route -> exact LLM-adapter -> same-execution Master Records PASS -> persistent runtime READY -> parent PASS -> LLM sovereign projection -> TVC READY_FOR_SITE_IMPORT packet -> existing Site activation-retention owner`.

No iPhone/WebAuthn/credential/provider action is required by this inference lane at the current boundary. No second user-operated machine may be introduced as a workaround.

## Fresh resident parent execution request — 2026-08-28

Live canonical reinspection before mutation confirmed:

```text
control/worker-registry.json generation: 22
parent task: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
parent state: HANDOFF_READY
executor_binding: AUTHORIZED
claim_id: null
worker_id: null
authority_domain: INDEPENDENT_TASK_CONTROL
minimum fresh fence exclusive: 22
old G20 authority reused: false
G22 recovery authority reused: false
```

No resident runtime receipts were present in repository custody for:
- `receipts/sovereign-host/worker-source-refresh.latest.json`;
- `receipts/sovereign-host/resident-execution-request-consumption.latest.json`;
- `receipts/sovereign-host/resident-targeted-execution.latest.json`;
- `receipts/ecosystem-chat-sovereign-inference/independent_parent_activation.latest.json`.

A fresh non-authorizing source-refresh request was therefore emitted on canonical `main`:

```text
request_id: RESIDENT-EXEC-ECOSYSTEM-CHAT-PARENT-002
request commit: d8f563f6a35eda0dbeea2db259b2993b0ab5d949
request grants authority: false
parent executor retains claim/fence authority: true
fresh fence floor: >22
credential authority: TV/TVC
GitHub token runtime authority: NONE
second user-operated machine required: false
network source fetch allowed: false
```

This request is not activation evidence. It is intended to be consumed exactly once by an already-installed sovereign resident source-refresh path. The next machine-observable state change is either a resident consumption/targeted-execution receipt or a separately evidenced absence/failure of the resident source-refresh service. Do not manufacture a parent PASS from repository mutation alone.

## Durable multi-request registry correction — 2026-08-28

Machine-readable inspection found that Ecosystem Chat still used the singleton `control/resident-execution-request.json`, while newer resident lanes already use `control/resident-execution-request.d/*.json`. Because the singleton is a shared overwrite surface, an unrelated resident request could replace the Ecosystem Chat request before a sovereign source refresh.

Bounded source correction:

```text
claim: ECOSYSTEM-CHAT-RESIDENT-REQUEST-DURABILITY-20260828
branch: fix/ecosystem-chat-resident-request-durable-20260828
canonical request: control/resident-execution-request.d/ecosystem-chat-parent-001.json
compatibility request: control/resident-execution-request.json
request id: RESIDENT-EXEC-ECOSYSTEM-CHAT-PARENT-002
consumer: scripts/consume_resident_execution_request.py
request authority: NONE_REQUEST_ONLY
credential authority: TV/TVC
GitHub-token runtime authority: NONE
activation effect: false
```

The canonical consumer now reads the dedicated multi-request registry entry. The singleton remains temporarily as a byte-equivalent compatibility surface for older resident source copies; because the stable request hash is computed from the JSON object, either old or new consumer observes the same request identity and cannot create a second automatic attempt after a matching consumption receipt exists.

The sovereign source-refresh path already copies the entire `control/resident-execution-request.d` directory, and the deterministic refresh tests now assert that the Ecosystem Chat request survives source refresh independently of the singleton.

The durability correction was exact-head validated and merged:

```text
PR: #360
exact validated head: fb441403fd28f5f1638494c5cca88f25b97a05c0
Heartbeat Worker Project: 33171649292 SUCCESS
Organization control plane: 33171649218 SUCCESS
merge: 6531070319f562bbcd18a3136f21e21b3ded244c
claim state: COMPLETE_RELEASED
```

The canonical executable handoff `handoffs/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json` is now reconciled to:
- canonical request ref `control/resident-execution-request.d/ecosystem-chat-parent-001.json`;
- compatibility singleton `control/resident-execution-request.json`;
- current request id `RESIDENT-EXEC-ECOSYSTEM-CHAT-PARENT-002`;
- durability merge and validation evidence;
- `runtime_execution_observed:false`.

This is source durability and machine-readable reconciliation only. It does not prove resident source refresh, request consumption, fresh fence issuance, model execution, Master Records reconstruction, or product activation.


## Shared HB runtime-observability registry binding — 2026-09-03

Canonical consumer descriptor:

```text
control/runtime-observability-consumers/ecosystem-chat-sovereign-inference-001.json
registration issue: #853
registration PR: #854
registration merge: c25a76729c02111d914c486f845979790088e245
shared owner: #814
```

This is source-of-truth registration only. Distinct deployment-local predicates remain independently NOT OBSERVED: resident presence/currentness, request consumption, fresh parent fence >22, private model execution, TVC ROUTE_ADMITTED, exact LLM-adapter execution, measured usage persistence, same-execution Master Records reconstruction, and persistent conversational runtime readiness.

HB remains reference/observability only; fresh claim/fence authority remains independent task control; TV/TVC remains sole credential authority; GitHub-token runtime authority remains NONE.


## Same-device execution correction — 2026-09-03

Architecture invariant `#201` now prohibits any other machine as a required routine inference dependency, including another StegVerse node.

The canonical Ecosystem Chat parent must therefore execute its model/runtime, TVC route consumption, exact LLM-adapter path, measured usage capture, and reconstruction from the same established device execution boundary. A remote private endpoint or remote StegVerse model host may be an optional peer only; it cannot be required for product activation.

If the current device lacks the required same-device runtime path, the state is `INCOMPLETE_REQUIRES_CONTINUED_BUILD` / `OTHER_MACHINE_REQUIRED`, not "execution pending on another sovereign machine."

The existing authentic StegOS iOS device-local inference proof remains relevant evidence that same-device inference is technically present on this device class, but it does not by itself satisfy this parent execution chain.
