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
