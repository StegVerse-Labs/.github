# HIL Sovereign Receiver Activation Mirror Handoff

## Source of truth

```text
goal_id: SHWP-HIL-SOVEREIGN-RECEIVER-001
issue: StegVerse-Labs/.github#246
source_dependency: StegVerse-org/LLM-adapter@40eaa9af5cb7e3845ddaf4e79e02d299c76b9655
carrier_bridge_merge: 4cc85164a8fc02405140dd53f3d431d7c4f79b89
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
resident_worker_registration: INSTALLED_MAIN
resident_worker_execution: PENDING_MACHINE_OWNED_OBSERVATION
public_activation: NOT_YET_PROVEN
```

Live repository state, worker receipts, TV/TVC lifecycle evidence, Site browser receipts, and restart/reconstruction evidence supersede older chat summaries.

## Installed implementation

The HIL v1.1 receiver source is merged in `StegVerse-org/LLM-adapter`. The StegVerse carrier bridge is merged through `.github` PR #258. The organization runtime now also contains the resident execution surfaces:

```text
workers/hil_sovereign_receiver_bridge.py
workers/hil_sovereign_receiver_worker.py
control/worker-registry.d/hil-sovereign-receiver-001.json
control/process-worker-adapters.d/hil-sovereign-receiver-001.json
handoffs/SHWP-HIL-SOVEREIGN-RECEIVER-001.json
tests/test_hil_sovereign_receiver_bridge.py
tests/test_hil_sovereign_receiver_worker_registration.py
docs/HIL_SOVEREIGN_RECEIVER_ACTIVATION_STATUS.md
```

The executable handoff is `HANDOFF_READY`; the registry binds `SHWP-HIL-SOVEREIGN-RECEIVER-001` to `hil-sovereign-receiver-worker` through `process:hil-sovereign-receiver-v1`. The process adapter forwards only non-secret local source/state locators and a bounded port. No GitHub credential is an allowed runtime input.

## Resident execution behavior

On an admitted heartbeat invocation, the worker:

1. requires a real claim and fencing token from the existing worker plane;
2. resolves the already-merged LLM-adapter receiver only from admitted local StegVerse workload/source locations;
3. rejects hosted GitHub/Render/Vercel/Cloudflare execution surfaces as the sovereign receiver runtime;
4. launches `llm_adapter.combined_gateway:app` on loopback with durable non-temporary StegVerse state and all GitHub authentication variables removed;
5. verifies `/api/hil/sovereign-receiver-profile` and `/api/hil/readiness` against the exact HIL v1.1 Primary and prompt identities;
6. persists a bounded worker receipt under `receipts/hil-sovereign-receiver/**`;
7. remains `ACTIVE`, rather than claiming completion, after local READY until public rendezvous/browser/restart/TVC evidence exists.

If local source, launch, or readiness is unavailable, the worker emits an active solution-required transition rather than treating a third-party or participant dependency as a stopping condition.

## Collision boundary

This task does not steal or mutate claims/fences belonging to `SHWP-DURABLE-RUNTIME-ACTIVATION`, `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`, WorkerCoordinator, TV/TVC, or Master Records. The HIL worker consumes the existing worker plane and has no independent heartbeat, model, route, credential, review, publication, custody, or execution authority.

## Activation proof still required

Repository source, registry installation, process-adapter binding, deterministic tests, or CI success do **not** activate HIL. Completion of #246 still requires all of the following on the real StegVerse runtime path:

1. resident worker execution produces a real carrier observation with the HIL receiver `READY`;
2. a public HTTPS rendezvous reachable from `stegverse.org` is bound to that ready receiver without gaining execution/lifecycle authority;
3. the public Site upload control becomes `READY` from direct observation of that receiver;
4. one controlled Site browser submission returns and preserves `HIL-RECEIVER-RECEIPT-v2`;
5. the exact submitted bytes are independently retrieved after controlled receiver restart/replacement and the SHA-256 remains exact;
6. the package/receipt is admitted into the existing TVC HIL lifecycle continuation.

Only after those observations may downstream private review, publication, Site lifecycle projection, Master Record release, Publisher, admissibility-wiki, or stegguardian-wiki propagation be treated as eligible.

## Execution ownership

```text
manual_execution_allowed: false
source_implementation_lane: COMPLETE_MERGED
runtime_execution_owner: resident WorkerCoordinator + hil-sovereign-receiver-worker
worker_task: SHWP-HIL-SOVEREIGN-RECEIVER-001
worker_adapter: process:hil-sovereign-receiver-v1
credential_route_authority: TV/TVC
review_publication_authority: existing TVC HIL lifecycle only
master_records_authority: master-records/orchestration
participant_or_developer_machine_role: NONE
```

## Current next transition

```text
HANDOFF_READY
-> admitted resident worker claim/fence
-> local sovereign receiver launch/observation
-> HIL_RECEIVER_LOCAL_READY_PUBLIC_RENDEZVOUS_REQUIRED
-> HIL_PUBLIC_HTTPS_RENDEZVOUS
-> Site browser receipt
-> restart exact-byte proof
-> TVC lifecycle handoff
```

No third-party host or participant hardware may be substituted as production authority merely because the live carrier evidence is not yet present.
