# HIL Sovereign Receiver Activation Mirror Handoff

## Source of truth

```text
goal_id: SHWP-HIL-SOVEREIGN-RECEIVER-001
issue: StegVerse-Labs/.github#246
source_dependency: StegVerse-org/LLM-adapter@40eaa9af5cb7e3845ddaf4e79e02d299c76b9655
carrier_bridge_merge: 4cc85164a8fc02405140dd53f3d431d7c4f79b89
independent_admission_validation_pr: #259
independent_admission_validation_head: 9c75f65f2e275a47c60262a578e18b6b22b84476
independent_admission_validation_merge: 2f20b0c55cab8e28923955bfde8972090ae562b4
heartbeat_worker_validation_run: 32606493583 SUCCESS
organization_control_plane_validation_run: 32606493617 SUCCESS
site_discovery_pr: StegVerse-Labs/Site#435
site_discovery_merge: 1d9575fa0f2ee19b78b9232f79313c5e12426b94
site_discovery_state: COMPLETE_MERGED_MAIN_FAIL_CLOSED_UNTIL_RUNTIME_READY
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_allowed: false
participant_machine_required: false
developer_machine_required: false
current_user_iphone_required: false
hb30_browser_capsule_required: false
third_party_runtime_required: false
execution_authority_from_transport: false
source_implementation: COMPLETE_MERGED
resident_worker_registration: INSTALLED_MAIN_VALIDATED
independent_task_control_admission: VALIDATED_MERGED
resident_worker_execution: PENDING_MACHINE_OWNED_OBSERVATION
public_activation: NOT_YET_PROVEN
```

Live repository state, worker receipts, TV/TVC lifecycle evidence, Site browser receipts, and restart/reconstruction evidence supersede older chat summaries.

## Installed implementation

The HIL v1.1 receiver source is merged in `StegVerse-org/LLM-adapter`. The StegVerse carrier bridge is merged through `.github` PR #258. The organization runtime contains the resident execution surfaces:

```text
workers/hil_sovereign_receiver_bridge.py
workers/hil_sovereign_receiver_worker.py
control/worker-registry.d/hil-sovereign-receiver-001.json
control/process-worker-adapters.d/hil-sovereign-receiver-001.json
cost-basis/worker-runtime/hil-sovereign-receiver.json
handoffs/SHWP-HIL-SOVEREIGN-RECEIVER-001.json
tests/test_hil_sovereign_receiver_bridge.py
tests/test_hil_sovereign_receiver_worker_registration.py
docs/HIL_SOVEREIGN_RECEIVER_ACTIVATION_STATUS.md
```

The executable handoff is `HANDOFF_READY`; the registry binds `SHWP-HIL-SOVEREIGN-RECEIVER-001` to `hil-sovereign-receiver-worker` through `process:hil-sovereign-receiver-v1`. Its `INDEPENDENT_TASK_CONTROL` admission requires a fresh fence and does not depend on a carrier packet as execution authority. The process adapter forwards only non-secret local source/state locators and a bounded port. No GitHub credential is an allowed runtime input.

PR #259 validated the complete merged admission shape rather than only the HIL source files. Exact-head validation proved executable-handoff conformance, HIL registry/process/cost-basis binding, fresh-fence independent admission, HIL bridge/worker tests, WorkerCoordinator independent-admission behavior without carrier-event authority, no GitHub credential token in validation, and an Admissible-Existence retrospective classification that represents the HIL task without granting capability phase or activation authority.

## Site discovery/public-participant integration

`StegVerse-Labs/Site` PR #435 merged as `1d9575fa0f2ee19b78b9232f79313c5e12426b94` and removed the stale Cloudflare receiver projection. Site now preserves the unproven runtime state explicitly:

```text
receiver_base_url: null
participant_visible_provider: false
service_operator: StegVerse sovereign receiver runtime
configuration_state: AWAITING_CONFORMING_HTTPS_RECEIVER
```

The public participant surface exposes the exact Primary and prompt SHA-256 identities and retains periodic readiness observation. Source validators now distinguish source-contract validity from runtime readiness, so CI success cannot promote the null discovery state into a live receiver claim.

Exact successful final-PR validation included:

```text
Check HIL v1 Upload Surface                       32608760847 SUCCESS
Check HIL LinkedIn Launch Readiness              32608760802 SUCCESS
Check HIL v1.1 Release                           32608760774 SUCCESS
HIL Post-Submit Continuity                       32608760804 SUCCESS
HIL Site Contract                                32608760830 SUCCESS
Site Handoff Orchestrator                        32608760827 SUCCESS
Ecosystem Heartbeat Orchestration                32608760772 SUCCESS
Site Bootstrap Validate - No Non-TV/TVC Authority 32608760811 SUCCESS
Session Retirement Validate                      32608760834 SUCCESS
```

The scoped Site implementation claim was released after merge. This closes the stale discovery/source-integration gap only.

## Current live-evidence boundary

The checked-in `control/worker-runtime-state.json` still records:

```text
last_cycle_at: 2026-08-18T19:47:00Z
last_observed_carrier_epoch: 31
last_observed_carrier_generation: 31
runtime_tick: 2
observation_mode: CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION
seen_assignment_packet_ids: []
```

Repository search currently exposes no `receipts/hil-sovereign-receiver/**` execution receipt. Therefore the resident HIL worker has not been proven to have executed merely because the source and Site paths are merged and validated.

## Resident execution behavior

On an admitted WorkerCoordinator invocation, the worker:

1. requires a real claim and fresh fencing token from the existing worker plane;
2. resolves the already-merged LLM-adapter receiver only from admitted local StegVerse workload/source locations;
3. rejects hosted GitHub/Render/Vercel/Cloudflare execution surfaces as the sovereign receiver runtime;
4. launches `llm_adapter.combined_gateway:app` on loopback with durable non-temporary StegVerse state and all GitHub authentication variables removed;
5. verifies `/api/hil/sovereign-receiver-profile` and `/api/hil/readiness` against the exact HIL v1.1 Primary and prompt identities;
6. persists a bounded worker receipt under `receipts/hil-sovereign-receiver/**`;
7. remains `ACTIVE`, rather than claiming completion, after local READY until public rendezvous/browser/restart/TVC evidence exists.

If local source, launch, or readiness is unavailable, the worker emits an active solution-required transition rather than treating a third-party or participant dependency as a stopping condition.

## Collision boundary

This task does not steal or mutate claims/fences belonging to `SHWP-DURABLE-RUNTIME-ACTIVATION`, `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`, WorkerCoordinator, TV/TVC, or Master Records. The HIL worker consumes the existing worker plane and has no independent heartbeat, model, route, credential, review, publication, custody, or execution authority. `heartbeat_reference_only=true` and `heartbeat_grants_execution_authority=false` remain explicit in the registry admission.

## Activation proof still required

Repository source, registry installation, process-adapter binding, deterministic tests, CI success, independent-task-control admission, or the merged Site discovery correction do **not** activate HIL. Completion of #246 still requires all of the following on the real StegVerse runtime path:

1. resident WorkerCoordinator allocates a real claim/fresh fence and the HIL worker produces a real receiver observation;
2. `/api/hil/sovereign-receiver-profile` reports the active sovereign receiver contract and `/api/hil/readiness` reports exact HIL v1.1 `READY`;
3. a public HTTPS rendezvous reachable from `stegverse.org` is bound without gaining execution/lifecycle authority;
4. Site directly observes that receiver and only then promotes discovery to `CONFORMING_HTTPS_RECEIVER_CONFIGURED`;
5. one controlled Site browser submission returns and preserves `HIL-RECEIVER-RECEIPT-v2`;
6. exact submitted bytes are independently retrieved after controlled receiver restart/replacement and the SHA-256 remains exact;
7. the package/receipt is admitted into the existing TVC HIL lifecycle continuation.

Only after those observations may downstream private review, publication, Site lifecycle projection, Master Record release, Publisher, admissibility-wiki, or stegguardian-wiki propagation be treated as eligible.

## Execution ownership

```text
manual_execution_allowed: false
source_implementation_lane: COMPLETE_MERGED_VALIDATED
site_discovery_lane: COMPLETE_MERGED_MAIN
runtime_execution_owner: resident WorkerCoordinator + hil-sovereign-receiver-worker
worker_task: SHWP-HIL-SOVEREIGN-RECEIVER-001
worker_adapter: process:hil-sovereign-receiver-v1
worker_admission: INDEPENDENT_TASK_CONTROL / fresh fence required
credential_route_authority: TV/TVC
review_publication_authority: existing TVC HIL lifecycle only
master_records_authority: master-records/orchestration
participant_or_developer_machine_role: NONE
```

## Current next transition

```text
HANDOFF_READY + VALIDATED INDEPENDENT ADMISSION + SITE DISCOVERY MERGED FAIL-CLOSED
-> resident WorkerCoordinator allocates real claim/fresh fence
-> hil-sovereign-receiver-worker executes
-> local sovereign receiver launch/observation
-> HIL_RECEIVER_LOCAL_READY_PUBLIC_RENDEZVOUS_REQUIRED
-> HIL_PUBLIC_HTTPS_RENDEZVOUS
-> Site direct readiness observation + discovery promotion
-> Site browser receipt
-> restart exact-byte proof
-> TVC lifecycle handoff
```

No third-party host or participant hardware may be substituted as production authority merely because the live carrier evidence is not yet present.

## 2026-08-28 bounded resident execution request bridge

A missing machine-remediation surface has been implemented on branch `exec/hil-resident-request-20260828` without granting new execution authority:

```text
request: control/resident-execution-request.d/hil-sovereign-receiver-001.json
consumer: scripts/consume_hil_resident_execution_request.py
request id: RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-001
mode: TARGETED_INDEPENDENT_TASK_CONTROL
existing executor: scripts/refresh_and_execute_resident_task.py --task-id SHWP-HIL-SOVEREIGN-RECEIVER-001
exactly-once key: request id + canonical request hash
credential authority: TV/TVC
participant credential requirement: NONE_FOR_PARTICIPANT_INTAKE
GitHub token runtime authority: NONE
second user machine required: false
network source fetch allowed: false
request grants authority: false
runtime execution observed: false
```

The rootless local source-refresh watcher is wired to invoke this consumer after refreshing already-local static worker source. The request may only trigger the existing admitted targeted executor; claim/fence authority remains with the worker-control plane. A branch merge or CI PASS remains source validation only and must not be represented as receiver execution or HIL activation.

## 2026-08-28 resident request merge and exact-head validation

PR #370 merged the bounded HIL resident-request bridge as `44798bb946fe64ed48ba04ac49eec00181649d12` after exact-head validation at `825456d876f349027e96e4bd334cde20439383ec`:

```text
Heartbeat Worker Project run 33228209273 / job 99035966356: SUCCESS
Organization control plane run 33228209246 / job 99035966209: SUCCESS
complete deterministic repository suite: PASS
JSON/handoff validation: PASS
no GitHub credential token in validation: PASS
request authority: NONE_REQUEST_ONLY
runtime execution observed: false
```

Current HIL resident-request state is therefore `MERGED_VALIDATED_RUNTIME_NOT_OBSERVED`. Repository search still exposes no `hil-resident-execution-request-consumption.latest.json` and no real `receipts/hil-sovereign-receiver/**` execution receipt. The next legitimate transition is resident consumption and real targeted execution; no source or CI event may be promoted to receiver READY or HIL activation.


## Resident dispatch ordering invariant — 2026-08-29

A live G18/HIL trace identified a circular execution-order risk in the shared sovereign bootstrap: bounded resident requests were dispatched only after the full activation proof passed, while G18/HIL execution can produce evidence needed by that proof.

The corrected invariant is:

```text
native resident installation/materialization succeeds
-> dispatch all bounded resident execution requests independently
-> G18/HIL consumers apply their existing fail-closed authority checks
-> final sovereign activation verifier runs
-> activation is claimed only if every canonical predicate passes
```

This does not make HIL depend on the G18 claim, does not let a request grant authority, and does not turn dispatch into activation proof. HIL remains an independently admitted task-control lane. The change only removes the shared ordering deadlock so an eligible resident runtime can actually attempt the HIL worker before the verifier makes its final determination.

Runtime evidence remains required: a real HIL resident-consumption receipt, worker claim/fresh fence, receiver ACTIVE/READY observation, public HTTPS rendezvous, Site browser `HIL-RECEIVER-RECEIPT-v2`, restart exact-byte proof, and TVC lifecycle handoff.


## 2026-08-29 canonical Universal InTr activation-order reconciliation

Merged source now changes the HIL causal ordering:

```text
Site PR #606 / merge 1cb2b9b950674400c5e5aa341b8b6efba5cbeb47
  -> Submit creates stegverse.universal-intr-transport/v1 immediately

LLM-adapter PR #213 / merge ad1a7c3f8bb727d1007f254930d9a77df0bfa94f
  -> receiving Interlock validates exact packet
  -> DEVICE_SYSTEM -> STEGOS_ECOSYSTEM receipt
  -> HIL:Ingress -> HIL:Custody receipt
  -> durable next HIL:Custody -> TVC:HIL-Lifecycle intent

TVC PR #240 / merge 31a4ea2fcc42b807ec24ae2612df4e60d38a73eb
  -> independently validates the upstream chain + exact PDF/provenance
  -> emits the TVC receiving InTr receipt
  -> creates the separately governed private-review Interlock intent
```

Canonical availability semantics are inherited from StegOS Universal InTr:

```text
event_triggered=true
always_on_receiver_required=false
second_user_device_required=false
receiver_unavailable_disposition=DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION
exact_packet_transport_retry_allowed=true
blind_consequence_retry_allowed=false
```

Therefore this older activation ordering is **not** a valid prerequisite chain:

```text
G18 complete
-> resident HIL receiver already running
-> receiver READY
-> participant may Submit
```

The correct causal chain is:

```text
participant Submit
-> Universal InTr transport intent exists
-> exact packet is transported immediately, durably queued, or causes bounded event-ephemeral materialization
-> receiving Interlock verifies the boundary
-> receiver-side receipt/custody lineage is emitted
-> TVC-bound next Interlock intent is emitted
-> TVC independently admits and receipts its boundary
```

The existing `hil-sovereign-receiver-worker` remains a valid bounded materialization/observation executor, but its READY state is a **downstream runtime observation**, not the condition that permits creation of the transport intent. The worker may be reused when already resident or materialized event-ephemerally when an admitted InTr event requires it.

G18 remains a separate sovereign-runtime evidence lane. Shared resident substrate may service both tasks, but:

```text
G18 completion required for HIL Submit: false
G18 claim/fence consumed by HIL: false
G18 runtime receipt satisfies HIL receipt: false
HIL transport grants G18 authority: false
```

The remaining authentic HIL evidence denominator is now:

1. a real participant Universal InTr intent;
2. a real receiver-side InTr boundary receipt;
3. a real HIL custody Interlock receipt;
4. a real TVC lifecycle InTr receipt produced from exact packet/provenance validation;
5. controlled receiver replacement/reconstruction proof where applicable;
6. separately governed TVC #8 private-review decision and later publication/Master Records transitions.

Source merges and CI runs establish the contract only. They do not establish that an authentic participant packet has traversed this chain.


## 2026-08-29 Universal InTr event-materialization consumer

The canonical Universal InTr availability policy now has a merged materialization-request source seam and a bounded HIL consumer path.

```text
StegOS PR #91 / merge 5ac248c223c9233cb741cda7a2856c30b0afb017
-> stegverse.universal-intr-materialization-request/v1
-> deterministic, write-once, non-authorizing request
-> exact transport-intent hash + payload hash + destination binding

local sovereign runtime / intr-materialization/*.json
-> existing rootless worker source-refresh path watcher
-> scripts/consume_hil_intr_materialization_request.py
-> validates destination = STEGOS_ECOSYSTEM / HIL:Ingress
-> invokes only scripts/refresh_and_execute_resident_task.py
-> --task-id SHWP-HIL-SOVEREIGN-RECEIVER-001
-> existing WorkerCoordinator remains sole claim/fence authority
```

No new resident daemon is introduced. The already-existing rootless watcher observes both local canonical-source changes and durable local `intr-materialization/` events. The HIL materialization consumer is copied through the existing source-refresh and native-runtime materialization paths.

Authority remains unchanged:

```text
materialization request grants execution authority: false
consumer mints claim/fence: false
transport grants execution authority: false
heartbeat grants execution authority: false
G18 completion required: false
G18 claim/fence consumed: false
GitHub token runtime authority: NONE
credential authority: TV/TVC
blocked HIL materialization blocks unrelated work: false
```

Successful exact materialization attempts are not blindly re-executed. A blocked attempt is recorded as nonterminal HIL evidence and does not fail the shared watcher or block unrelated worker reconciliation.

The resulting causal chain is now:

```text
participant Submit
-> Universal InTr transport intent
-> durable queue or event-ephemeral materialization request
-> existing HIL targeted executor under existing WorkerCoordinator authority
-> receiver materialization/readiness observation
-> receiver InTr receipt + HIL custody receipt
-> TVC-bound next Interlock intent
-> TVC receiving receipt
-> separately governed private-review Interlock
```

This source integration still does not prove that a real participant event reached a StegOS runtime or that the materialization request was consumed. Authentic runtime receipts remain required.


## 2026-08-29 authentic resident activation acceptance harness

A bounded resident-runtime acceptance harness has been added on branch `test/hil-resident-activation-20260829` to collapse the first five missing runtime observations into one real execution path without fabricating receipts.

```text
runner: scripts/run_hil_resident_activation_test.py
test: tests/test_hil_resident_activation_acceptance.py
hosted GitHub/Render/Vercel/Cloudflare execution: REJECTED
credential authority: TV/TVC
GitHub token runtime authority: NONE
G18 completion required: false
G18 claim/fence consumed: false
request grants authority: false
```

On an eligible StegVerse-owned/federated resident runtime the runner:

1. invokes the existing sovereign bootstrap;
2. requires the real resident request dispatcher to run;
3. creates a deterministic controlled PDF fixture and exact hash-bound Universal InTr materialization request;
4. wraps it in the exact registered-Node trigger/outbox shape;
5. sends it through the actual loopback HTTP HIL InTr ingress listener;
6. requires an authentic `INGRESS_ADMITTED` receipt;
7. invokes the existing HIL materialization consumer;
8. requires the existing targeted executor/WorkerCoordinator lane to produce resident execution evidence;
9. requires the HIL worker receipt to contain a real claim ID, fencing token, and `receiver_ready=true`;
10. writes only a local test-observation summary after inspecting the component-produced receipts.

The runner does not synthesize any of the acceptance receipts it checks. It returns nonzero unless all of these are genuinely present on that runtime:

```text
receipts/sovereign-host/resident-request-dispatch.latest.json
receipts/sovereign-host/hil-resident-execution-request-consumption.latest.json
receipts/sovereign-host/resident-targeted-execution.latest.json
receipts/sovereign-network/hil-intr-ingress.latest.json
receipts/sovereign-host/hil-intr-materialization-consumption.latest.json
receipts/hil-sovereign-receiver/SHWP-HIL-SOVEREIGN-RECEIVER-001.json
```

A successful run therefore proves the resident dispatch -> independent HIL claim/fence -> Node/InTr ingress -> materialization -> receiver READY segment on a real sovereign runtime. It still does not satisfy exact PDF custody, controlled restart/reconstruction, or TVC HIL lifecycle receipt until those downstream receivers emit their own evidence.

Source/CI validation of this harness remains non-runtime evidence. The authentic transition is only a PASS emitted by the harness on an eligible resident runtime with the component receipts above.


## 2026-08-30 ESRL blocker reconciliation

Live StegOS state supersedes any interpretation that HIL requires a permanent
physical process host or completion of the G18 durable-runtime lane.

Verified existing StegOS source:

```text
ESRL v0.3 provider-neutral lease primitive: MERGED / MODEL_CONFORMANCE
provider-neutral runtime dispatch controller: MERGED
concrete SovereignEphemeralNodeAdapter: MERGED
Universal InTr materialization request: MERGED
HIL-specific Universal InTr -> ESRL INTAKE binding/controller: MERGED via StegOS PR #98 / aa20980ecda3e1849aaa97953e026b11352e9a67 / CI 33294309548 SUCCESS
```

The HIL-specific source path is now:

```text
verified stegverse.universal-intr-materialization-request/v1
-> ESRL INTAKE / EVENT_EPHEMERAL lease request
-> replaceable non-authorizing compute/runtime adapters
-> local implementation/readiness verification
-> freshly discovered lease-bound public HTTPS rendezvous
-> independent public HTTPS identity/readiness observation
-> LEASE_OPEN
-> existing .github HIL materialization/WorkerCoordinator path
-> HIL independent claim/fresh fence
-> receiver READY
-> exact PDF custody/reconstruction
-> TVC lifecycle receipts
```

Important blocker correction:

```text
permanent/always-on host required for HIL: false
G18 completion required for HIL: false
G18 claim/fence may satisfy HIL: false
second user machine required: false
GitHub-hosted production runtime allowed: false
transport/compute authority_effect: false
credential_authority: TV/TVC
```

The currently merged sovereign Node adapter proves reusable deployment-local
compute/materialization source exists, but its relay rendezvous probe is local
and MUST NOT be promoted to HIL public HTTPS evidence. HIL remains runtime
blocked until a concrete replaceable rendezvous path produces a freshly observed
public HTTPS endpoint and independent public identity/readiness proof.

StegOS PR #98 is source/model work only until its exact-head validation passes
and it is merged. Even after merge, no HIL activation may be claimed until the
authentic ESRL lease/rendezvous and downstream HIL receipts are observed.

`handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json` remains authoritative for the
separate G18 lane only. Its PHYSICAL_RESOURCE language MUST NOT be used as a HIL
prerequisite or HIL blocker.


## 2026-08-30 shared Service Gateway ESRL runtime closure

StegOS now contains the concrete HIL ESRL runtime adapter required to consume the
already-merged shared Service Gateway architecture:

```text
StegVerse-Labs/StegOS PR #102
merge: 878f06bf258c2ee47c49bad8d24d1581a61d3546
exact-head StegOS CI: 33295276292 SUCCESS

stegos/hil_shared_gateway_runtime.py
tests/test_hil_shared_gateway_runtime.py
```

Canonical event path is now:

```text
participant Submit
-> Universal InTr materialization request
-> ESRL INTAKE / EVENT_EPHEMERAL lease
-> sovereign runtime materialization
-> existing separated carrier + WorkerCoordinator runtime
-> scripts/materialize_hil_gateway_route_config.py
-> loopback workers/hil_intr_profiled_ingress.py
-> local /intr/profile verification
-> shared Service Gateway https://stegverse.org
-> independent /intr/materialization/readiness verification
-> ESRL LEASE_OPEN
-> public POST /intr/materialization
-> HIL materialization consumer
-> independent WorkerCoordinator HIL claim/fresh fence
-> receiver READY
-> exact PDF custody/reconstruction
-> TVC lifecycle receipt
```

This supersedes both older assumptions:

```text
permanent host first -> receiver READY -> Submit
bespoke HIL public tunnel provider required
```

The shared Service Gateway is transport-only and must continue to report no
receipt, execution, or custody authority. The generic StegOS command-backed HTTPS
rendezvous adapter is optional compatibility/fallback capacity only.

Current authentic evidence remains:

```text
event -> ESRL lease execution: NOT OBSERVED
public Gateway HIL readiness READY: NOT OBSERVED
ESRL LEASE_OPEN: NOT OBSERVED
public HIL materialization POST: NOT OBSERVED
HIL WorkerCoordinator claim/fence: NOT OBSERVED
receiver custody/reconstruction: NOT OBSERVED
TVC lifecycle receipt: NOT OBSERVED
```

No additional generic HIL ESRL/runtime/rendezvous source adapter is presently
identified as missing. The next authorized transition is authentic event-driven
execution through the merged shared-Gateway ESRL path.


## 2026-08-30 ESRL shared-Gateway execution-gate merge

The event consumer itself is now bound to the shared-Gateway ESRL lifecycle:

```text
StegVerse-Labs/.github PR #519
merge: 9591ddc3f59f851f176c9126e1031774207af8c0
Validate organization control plane run: 33295465321 SUCCESS
Heartbeat Worker Project run: 33295465332 SUCCESS

workers/hil_esrl_runtime_bridge.py
scripts/consume_hil_intr_materialization_request.py
tests/test_hil_intr_materialization_consumer.py
```

The previous local-only behavior is removed:

```text
OLD:
admitted materialization -> relay-specific adapter -> LOCAL_READY
-> targeted HIL WorkerCoordinator execution

CURRENT:
admitted materialization
-> SharedGatewayHILRuntimeAdapter
-> sovereign runtime materialized
-> local HIL profile verified
-> PUBLIC_VERIFYING
-> shared Gateway readiness independently verified
-> LEASE_OPEN
-> only then targeted HIL WorkerCoordinator execution
```

The consumer now fails closed when the ESRL bridge returns only LOCAL_READY or
when public shared-Gateway readiness is absent. WorkerCoordinator remains the sole
claim/fence authority after LEASE_OPEN.

Current source/control completion:

```text
Universal InTr -> ESRL HIL binding/controller: COMPLETE_VALIDATED_MERGED
concrete shared-Gateway HIL ESRL runtime adapter: COMPLETE_VALIDATED_MERGED
HIL materialization consumer LEASE_OPEN gate: COMPLETE_VALIDATED_MERGED
known source scaffolding/stubs in this HIL activation path: 0
authentic runtime execution: NOT OBSERVED
```


## 2026-08-30 resident acceptance harness LEASE_OPEN reconciliation

The original bounded resident activation acceptance runner predated the shared-
Gateway ESRL execution gate. It could inspect the old outer-runtime receipt paths
without explicitly proving the now-required ESRL `LEASE_OPEN` result.

This branch corrects that acceptance denominator:

```text
scripts/run_hil_resident_activation_test.py
tests/test_hil_resident_activation_acceptance.py
```

A PASS now requires the component-produced materialization result for the exact
controlled materialization ID to prove:

```text
state = MATERIALIZATION_EXECUTION_ATTEMPTED
esrl_lease_state = LEASE_OPEN
esrl_runtime_instantiated = true
esrl_local_identity_verified = true
hil_public_https_rendezvous_observed = true
public_gateway_readiness_verified = true
public_gateway_origin = https://stegverse.org
```

The runner then resolves `esrl_runtime_root` from that exact receipt and requires
the targeted-execution and HIL receiver receipts from the materialized ESRL runtime
itself, rather than assuming they exist under the outer bootstrap runtime root.

This runner remains an observer only. It does not synthesize LEASE_OPEN, public
Gateway readiness, WorkerCoordinator claim/fence, or receiver READY evidence.
Source/CI validation cannot satisfy the authentic runtime gate.


## 2026-08-30 controlled receiver restart/reconstruction verifier

Implemented on branch `feat/hil-post-restart-reconstruction-20260830`:

```text
scripts/verify_hil_post_restart_reconstruction.py
tests/test_hil_post_restart_reconstruction.py
```

This verifier consumes the SAME canonical Site browser observation evidence
(`stegverse.hil.canonical-observation-evidence/v1 state=OBSERVED`) rather than
creating a second submission.

Required source observation bindings include:

```text
receiver_schema = HIL-RECEIVER-RECEIPT-v2
custody_state = EXACT_BYTES_PERSISTED
registry_state = RECORDED
exact_byte_reconstruction = PASS
tvc_lifecycle_intent_observed = true
tvc_receiving_receipt_observed = false
receiver_restart_reconstruction_observed = false
controlled_pdf_sha256 = sha256:<exact bytes>
```

Runtime sequence:

```text
same browser-observed submission_id
-> load HIL WorkerCoordinator receiver receipt from ESRL runtime root
-> require receiver_ready=true and an exact positive receiver_pid
-> GET same submission status before restart
-> terminate ONLY that receiver_pid
-> preserve durable_state_root unchanged
-> restart same sovereign receiver using existing receiver bridge
-> require exact receiver READY again
-> GET same submission status after restart
-> TV/TVC-authenticated GET /api/hil/submissions/{id}/exact-bytes
-> require X-SteGVerse-HIL-Reconstruction-State=EXACT_BYTES_HASH_VERIFIED
-> independently SHA-256 returned bytes
-> require equality with browser-observed controlled_pdf_sha256
-> emit stegverse.hil.post-restart-reconstruction/v1 PASS
```

The TV/TVC reconstruction token is checked for runtime presence only and is never
written into the result, logs, repository, or receipt. If it is absent, the
verifier returns `PREDICATE_PENDING:TVC_RECONSTRUCTION_AUTH_NOT_OBSERVED`.
If the WorkerCoordinator receipt does not identify a receiver PID, the verifier
returns `PREDICATE_PENDING:CONTROLLED_RECEIVER_PID_NOT_AVAILABLE` rather than
terminating an unknown process.

A PASS does not claim TVC receiving admission, private review, publication, or
Master Records authority. TVC #8 remains independently owned.

Source/CI does not establish a real restart or reconstruction observation.


## 2026-08-30 automatic HIL custody -> TVC lifecycle event consumption

Current source branch:
`feat/hil-tvc-lifecycle-outbox-current-20260830`.

New bounded runtime surfaces:

```text
scripts/consume_hil_tvc_lifecycle_outbox.py
scripts/watch_hil_tvc_lifecycle_outbox.py
tests/test_hil_tvc_lifecycle_outbox_consumer.py
tests/test_hil_tvc_lifecycle_outbox_watch.py
tests/test_hil_tvc_lifecycle_watch_worker.py
```

The HIL receiver itself still does not invoke TVC and the browser remains
non-authorizing. After the WorkerCoordinator-owned receiver reaches exact READY,
the HIL worker starts one bounded watcher process in the same runtime process
group. The watcher observes only the durable receiver-owned TVC outbox and exits
when:

```text
TVC lifecycle admission is observed
OR a fail-closed result occurs
OR the finite lease/watch window expires
OR the containing runtime/lease is torn down
```

The durable input pair is produced by merged LLM-adapter
`0f9ddde691f73a6477b25e609d1f2538073839f1`:

```text
<durable HIL root>/intr-outbox/tvc-hil-lifecycle/<submission_id>.json
<durable HIL root>/receiver-receipts/<submission_id>.json
```

The event consumer requires the receiver receipt path to remain inside the
receiver-owned durable receipt directory and invokes only the already-merged TVC
one-shot lifecycle adapter.

TVC source floor:

```text
StegVerse-Labs/TVC
2787eece099604a4d2aad93c575167dc73e54037
```

Later TVC main movement is admitted only when that floor remains an ancestor and
the HIL lifecycle adapter/backend protected files are byte-unchanged relative to
the floor. Dirty protected paths fail closed.

The TVC controlled-cycle state was separately hardened in TVC PR #259 so all
runtime lifecycle state resides beneath the caller-owned HIL/TVC runtime output
root rather than mutating the TVC source checkout.

Authority remains:

```text
credential_authority = TV/TVC
github_token_runtime_authority = NONE
authority_effect = NONE_TRANSPORT_TRIGGER_ONLY / NONE_EVENT_WATCH_ONLY
private_review_owner = StegVerse-Labs/TVC#8
private_review_completed = false
publication_authorized = false
master_record_authorized = false
second_user_device_required = false
g18_completion_required = false
```

A source merge does not prove a browser submission, TVC receiving receipt, private
review, publication, Master Record admission, or HIL runtime activation.


## 2026-08-30 targeted local refresh and HIL request dispatch

The fresh resident request `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002` is merged,
but repository merge is not source transport. The sovereign runtime intentionally
performs no network fetch, so the exact remaining pre-execution predicate is:

```text
already-local StegVerse-Labs/.github source contains merge
0aa81bc8b18732a74d64989ff83aaeef94f36f40 or a validated descendant
-> local static source refresh preserves mutable resident state
-> dispatch exactly consumer hil
-> consume request RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002
```

The portable bridge supports that exact bounded transition:

```text
python scripts/refresh_and_dispatch_resident_requests.py \
  --source-root <already-local-current-.github-checkout> \
  --runtime-root <existing-sovereign-runtime-root> \
  --only-consumer hil
```

The historical frozen-v0.4 consumer remains the default. `hil` must be selected
explicitly; unrelated resident requests are not visited. Unsupported selectors
fail before refresh or dispatch. The bridge still rejects hosted or credential-
bearing environments, performs no network source fetch, mints no claim/fence,
and grants no runtime authority.

This closes the missing targeted invocation surface only. Authentic HIL execution
remains blocked until the already-local checkout is current and this local command
or the installed source watcher executes on an eligible sovereign runtime. A CI
PASS cannot satisfy that predicate.

## 2026-08-31 portable TVC source-proof closure

The portable resident bundle now carries an optional machine-verifiable TVC source proof generated from an already-local Git checkout. For the HIL lifecycle protected surface, the canonical packager records the TVC HEAD, proves the validated source-floor commit is present, proves the protected HIL lifecycle paths are unchanged since that floor, and records the exact materialized subpath.

StegDeploy persists the verified bundle manifest locally and passes it to the native WorkerCoordinator as `STEGVERSE_RESIDENT_SOURCE_MANIFEST`.

`consume_hil_tvc_lifecycle_outbox.py` now accepts either:

```text
ordinary local TVC Git proof
or
verified portable bundle proof + exact current protected-file digest match
```

The portable proof path does not copy `.git`, Git remotes, credentials, or network authority into the resident. Missing/unverified proof remains predicate-pending; digest or identity mismatch fails closed.

This removes a portability defect where the bundled TVC source could execute ordinary resident activation but the HIL lifecycle consumer could reject the exact same verified materialization solely because `.git` metadata was intentionally excluded.


## Same-device rendezvous correction — 2026-09-03

Architecture owner: `StegVerse-Labs/.github#201`  
Remediation owner: `StegVerse-Labs/.github#889`.

The earlier HIL path treated the shared Service Gateway at `https://stegverse.org` as replaceable transport capacity while still requiring its public readiness before ESRL `LEASE_OPEN`. Under the corrected same-device invariant, that requirement is not admissible unless the gateway itself executes on the same established device.

Current source therefore contains a real other-machine dependency:

```text
public_origin=https://stegverse.org
public_tls_terminated_by=STEGVERSE_SHARED_SERVICE_GATEWAY
public_gateway_readiness_required_before_LEASE_OPEN=true
same_device_gateway_execution_observed=false
```

The HIL lane is reclassified:

```text
state=INCOMPLETE_REQUIRES_CONTINUED_BUILD
blocker_code=OTHER_MACHINE_REQUIRED
same_device_execution_required=true
other_machine_may_be_required=false
runtime_activation_claimed=false
```

This correction does not revoke valid local HIL source, WorkerCoordinator admission, Interlock/InTr semantics, TV/TVC authority, custody logic, or historical validation. It removes only the invalid assumption that a required remote StegVerse gateway is acceptable because it is StegVerse-controlled.

The next legitimate implementation is to remove the required remote-gateway dependency from routine HIL activation/execution or implement an equivalent same-device rendezvous path. Remote peers may remain optional only.

Until that implementation exists, authentic HIL runtime execution is not the next blocker. The source/control path itself is incomplete.

No second machine may be assigned to the user.


### Same-device fail-closed source merge

StegOS PR #178 / merge `2efe6678e859e19d96d2a6afd6edf924bab186d2`, CI `33713897558 SUCCESS`, now enforces the route predicates in executable HIL ESRL source:

```text
requires_other_machine=false
activation_execution_scope=SAME_DEVICE
same_device_gateway_execution=true
```

A required remote shared Gateway now fails closed in source. This merge removes acceptance of the invalid topology; it does not yet provide or prove an on-device public rendezvous.
