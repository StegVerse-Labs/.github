# Site Publication InTr Consumer Mirror Handoff

Updated: 2026-09-13
Repository: `StegVerse-Labs/.github`
Issue: #1372
Task: `SITE-PUBLICATION-INTR-CONSUMER-001`
Parent runtime Goal Task: `SITE-PUBLICATION-NATIVE-RUNTIME-EXECUTION-001`
Parent ECE consumer: `SITE-ECE-CURRENT-PROJECTION-MATERIALIZER-001`
COSV: `50000000102000`
State: `HANDOFF_READY / MACHINE OWNER INSTALLED / AUTHENTIC CLAIM+LEASE EVIDENCE PENDING`

## Purpose

Consume the exact Site publication materialization request already admitted by the shared Universal InTr ingress, under a fresh WorkerCoordinator claim/fence, without creating a new listener, runtime owner, publication authority, or user-verification path.

Canonical operation:

```text
operation_id = SITE_PUBLICATION_EVENT
destination = STEGOS_ECOSYSTEM / StegOS:SitePublicationRuntime
downstream_owner_ref = StegVerse-Labs/StegOS:canonical-runtime-lane
request state = QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION
runtime class = EVENT_EPHEMERAL
```

## Canonical source history

- PR #1373 merged the strict candidate consumer.
- PR #1381 merged the Site publication adapter and shared Universal InTr route integration.
- PR #1398 merged the independently claimable WorkerCoordinator child at `7444aefbdd2c644c46ae105192af4a524ef02172` after Heartbeat `34615815337`, Deterministic Repository Suite `34615815364`, and Organization Control `34615815476` passed.
- Reusable Task Component reconciliation later bound the parent runtime Goal to existing reusable source-refresh, governed processing, publication, InTr transport, runtime observation, and Master Records custody components rather than adding bespoke orchestration.

Machine-owned registration surfaces:

```text
workers/site_publication_intr_consumer_worker.py
workers/site_publication_intr_ingress.py
control/worker-registry.d/site-publication-intr-consumer-001.json
control/process-worker-adapters.d/site-publication-intr-consumer-001.json
control/task-vectors/SITE-PUBLICATION-INTR-CONSUMER-001.json
handoffs/SITE-PUBLICATION-INTR-CONSUMER-001.json
```

`workers/`, task-vector fragments, worker-registry fragments, adapter fragments, and related control surfaces are propagated through the existing local-only sovereign source-refresh component. No second source-refresh owner is created.

## WorkerCoordinator state and authority

Repository source remains intentionally unclaimed:

```text
state = HANDOFF_READY
claim_id = null
heartbeat_timing = null
lease = null
fresh_fence_required = true
minimum_fencing_token_exclusive = 0
```

Only WorkerCoordinator may create the fresh claim/fence. The InTr materialization request and ingress receipt do not mint claim/fence or execution authority. Interlock/InTr remains transition/admission authority. TV/TVC remains credential/provider/release authority. KV/SKAP Vault remains the sole user-verification authority. GitHub runtime authority is `NONE`.

There is no device-verification policy, device identity gate, connected-device prerequisite, or second-user-device requirement in this lane.

## Exact admitted materialization evidence

Existing source-validation lineage identifies:

```text
artifact_manifest_sha256 = sha256:e6bc47580f25296df61d16dfe5a74f3f49fec0dda018c813696195c960e77f09
packet_id = INTR-58dec5416bd4358190c11372
materialization_id = INTR-MAT-0e1ba4786b0ea8a00e1f166e
materialization_state = QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION
runtime_class = EVENT_EPHEMERAL
```

Those source artifacts do not prove resident ingress or publication. Authentic execution requires the resident Universal InTr ingress to persist a write-once `stegverse.site-publication-intr-ingress/v1` receipt plus the exact queued request under the same runtime root.

## Materialization binding rule

The worker no longer treats an out-of-band environment value as sufficient evidence of the admitted materialization.

For a fenced invocation, the worker resolves the opaque materialization id from:

```text
receipts/sovereign-network/site-publication-intr-ingress.latest.json
-> exact write-once queue_ref
-> intr-materialization/<materialization_id>.json
```

The ingress receipt must be `INGRESS_ADMITTED_CANDIDATE_ONLY`, must record `exact_request_validated=true`, `write_once_persisted=true`, `request_grants_execution_authority=false`, `claim_or_fence_minted=false`, and `authority_effect=NONE_INGRESS_CANDIDATE_ONLY`. The queue reference must resolve exactly to the same runtime root and the queued request must carry the same materialization id.

`STEGVERSE_SITE_PUBLICATION_MATERIALIZATION_ID` remains an optional opaque correlation binding because the process adapter already allowlists it. If supplied, it must equal the locally admitted materialization id. A mismatch fails closed. The environment value never substitutes for the admitted ingress receipt.

This removes the previous manual env-binding step as a source of truth while preserving the existing authority separation: authentic InTr ingress identifies the candidate; WorkerCoordinator separately supplies claim/fence authority.

## Runtime sequence

```text
already-local source refresh through RT-SOVEREIGN-SOURCE-REFRESH-001 / existing refresh implementation
-> resident Universal InTr ingress retains exact Site publication candidate
-> WorkerCoordinator discovers SITE-PUBLICATION-INTR-CONSUMER-001 from worker-registry.d
-> fresh independent claim/fence
-> worker resolves exact materialization from local admitted-ingress evidence
-> candidate validation receipt retained
-> bounded EVENT_EPHEMERAL Site publication lease
-> independent /intr/profile + exact HTTP byte/path observation
-> lease closure
-> final Interlock/InTr publication transition admission
-> Master Records publication evidence custody/reconstruction
-> conditional DNS/TLS recovery proof when applicable
```

The neutral reusable scheduler may advance reusable source refresh when scheduling is required, but scheduling itself is not a Goal completion predicate and grants no authority.

## Runtime/publication predicates still false until authentic evidence

```text
SOVEREIGN_SOURCE_REFRESH_OBSERVED
FRESH_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED
RUNTIME_WORKER_EXECUTION_OBSERVED
BOUNDED_EVENT_EPHEMERAL_LEASE_EXECUTION_OBSERVED
PUBLIC_HTTPS_INTR_PROFILE_OBSERVED
EXACT_HTTP_BYTE_PATH_EQUIVALENCE_OBSERVED
LEASE_CLOSURE_OBSERVED
FINAL_PUBLICATION_TRANSITION_ADMITTED
DNS_TLS_RECOVERY_PROVEN
```

Source merge, CI, registration, scheduler definition, user-observed homepage reachability, or a materialization identifier alone does not satisfy these predicates.

## Current continuation

Validate and merge the admitted-ingress binding repair. Then advance the already-existing reusable source-refresh / WorkerCoordinator / Site publication component chain and retain authentic receipts. The ECE materializer consumes this publication owner; it must not create a second served-root runtime or source-repository publication path.
