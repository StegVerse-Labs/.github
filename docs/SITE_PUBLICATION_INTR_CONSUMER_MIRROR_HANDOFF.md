# Site Publication InTr Consumer Mirror Handoff

Updated: 2026-09-11
Repository: `StegVerse-Labs/.github`
Issue: #1372
Task: `SITE-PUBLICATION-INTR-CONSUMER-001`
Parent Goal Task ID: `KV-CONNECTION-REVALIDATION-WORKER-001`
Parent Site lane: `SITE-497-THIRD-PARTY-DEPENDENCY-ERADICATION`
COSV: `50000000102000`
Canonical Site source boundary: `StegVerse-Labs/Site@bc1ee7257ebc64f77dab3f0b746bb3a86a279b6c`
Consumer source merge: `.github@e89a65307248a69e057bc07dac07a5ca98bc4677` (PR #1373)
Runtime-ingress integration merge: `.github@3cead1c10329f5df2577b36259f68180e43d52c2` (PR #1381)
WorkerCoordinator registration merge: `.github@7444aefbdd2c644c46ae105192af4a524ef02172` (PR #1398)

## Purpose

Consume the exact Site publication materialization request already produced by the merged Site adapter without creating a new runtime owner or conflating queue admission with publication success.

Canonical input:

```text
operation_id = SITE_PUBLICATION_EVENT
destination = STEGOS_ECOSYSTEM / StegOS:SitePublicationRuntime
downstream_owner_ref = StegVerse-Labs/StegOS:canonical-runtime-lane
request schema = stegverse.universal-intr-materialization-request/v1
request state = QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION
runtime class = EVENT_EPHEMERAL
```

## Merged source

PR #1373 merged the strict candidate consumer. PR #1381 merged the Site publication adapter and fail-closed shared Universal InTr route installer. PR #1398 merged the independently claimable WorkerCoordinator task after all required exact-head suites passed.

Merged registration surfaces include:

- `workers/site_publication_intr_consumer_worker.py`
- `control/worker-registry.d/site-publication-intr-consumer-001.json`
- `control/process-worker-adapters.d/site-publication-intr-consumer-001.json`
- `cost-basis/worker-runtime/site-publication-intr-consumer.json`
- `control/task-vectors/SITE-PUBLICATION-INTR-CONSUMER-001.json`
- `handoffs/SITE-PUBLICATION-INTR-CONSUMER-001.json`
- `tests/test_site_publication_intr_worker_registration.py`

`workers/` is already copied wholesale by `scripts/refresh_sovereign_worker_runtime_source.py`; no second listener or source-refresh owner was introduced.

## WorkerCoordinator state

The child remains deliberately unclaimed in repository source:

```text
state = HANDOFF_READY
claim_id = null
heartbeat_timing = null
lease = null
fresh_fence_required = true
minimum_fencing_token_exclusive = 0
```

The zero floor requires checkout to mint a nonzero fresh generation; it does not hard-code or reuse any historical task fence. The worker refuses invocation without a real `claim_id` and integer fencing token. It accepts only `STEGVERSE_SITE_PUBLICATION_MATERIALIZATION_ID`, and the process adapter allowlists only that opaque identifier.

The parent goal registry independently remains `HANDOFF_READY`, unclaimed, and unleased with COSV `50000000102000`; its own minimum fencing-token floor remains greater than 22 and is not reusable by this child.

## Heartbeat validation repair and PR #1398 merge

The earlier exact head `aef2740e9f0bb57241d78ec5d7898e8c6a436a92` passed Organization Control and the Deterministic Repository Suite but failed Heartbeat Worker Project run `34566974758` at the later carrier-only/non-mutating dry-run proof.

Commit `041a929253ca058138d3ab2d0c8f3e6bdae1854a` changed only CI transport of the dry-run JSON: the projection is written to a temporary file and parsed from that file instead of being transported as one command-line argument. Repository before/after hashes and every carrier non-authority/projection assertion were preserved.

Final PR head `ff07cd41a6042245f88f2ac9a48712d15c82d6cf` passed all three required suites:

- Heartbeat Worker Project run `34615815337`, including the formerly failing carrier-only/non-mutating proof.
- Deterministic Repository Suite run `34615815364`.
- Organization Control run `34615815476`.

PR #1398 then merged at `7444aefbdd2c644c46ae105192af4a524ef02172`.

## Exact admitted Site materialization

Canonical Site source `bc1ee7257ebc64f77dab3f0b746bb3a86a279b6c` passed Site 497 Publication Observation Contract run `34553032100`. Its deterministic request evidence identifies:

```text
artifact_manifest_sha256 = sha256:e6bc47580f25296df61d16dfe5a74f3f49fec0dda018c813696195c960e77f09
packet_id = INTR-58dec5416bd4358190c11372
materialization_id = INTR-MAT-0e1ba4786b0ea8a00e1f166e
materialization_state = QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION
runtime_class = EVENT_EPHEMERAL
```

That same validation evidence explicitly records that the request grants no execution authority and that authentic event-ephemeral publication exchange, independent publication observation, DNS mutation, TLS recovery, and public-content equivalence were not observed/claimed.

The exact materialization id above is therefore the only currently evidenced value eligible to bind to `STEGVERSE_SITE_PUBLICATION_MATERIALIZATION_ID` for the next fresh fenced invocation. Binding the id alone is not runtime or publication proof.

## Runtime access condition

The authorized native remote-runtime surface was queried after PR #1398 merged and reported no connected device. Therefore no sovereign source refresh, WorkerCoordinator checkout, claim, fence, worker invocation, publication lease, or native receipt is claimed from this continuation.

The existing runtime path remains authoritative and requires no hosted substitute. On the next authentic native runtime visit, the sequence is:

1. Refresh already-local merged `.github` source through the existing local-only sovereign source-refresh path; no network-source fallback.
2. Run the existing WorkerCoordinator targeted execution path for `SITE-PUBLICATION-INTR-CONSUMER-001` so checkout/admission mints a fresh independent claim/fence.
3. Bind `STEGVERSE_SITE_PUBLICATION_MATERIALIZATION_ID=INTR-MAT-0e1ba4786b0ea8a00e1f166e` only for that fenced process invocation.
4. Retain the candidate-validation receipt and fencing generation.
5. Execute one authentic bounded `EVENT_EPHEMERAL` publication lease through the canonical StegOS/InTr runtime owner.
6. Independently observe `/intr/profile`, exact HTTP byte/path hashes, candidate evidence export, and lease closure.
7. Separately admit final publication transition before any DNS/TLS recovery claim.

## Runtime/publication predicates still false

```text
sovereign source refresh observed after #1398 = false
fresh WorkerCoordinator claim/fence observed = false
runtime worker execution observed = false
bounded EVENT_EPHEMERAL lease execution observed = false
public HTTPS /intr/profile observed = false
exact HTTP byte/path equivalence observed = false
lease closure observed = false
final publication transition admitted = false
DNS/TLS recovery proven = false
```

Persistent Node continuity remains required. Persistent host, always-on receiver, second user-operated device, hosted-provider runtime, and Render remain prohibited/not required.

## README maintenance

Root README was re-reviewed for this child lane after PR #1398. No provider/runtime wording change is required; the existing provider-neutral and no-required-third-party-runtime boundary remains correct.

## Current continuation

The repository registration and CI repair phase is complete. The next evidence-producing phase is authentic native source refresh + fresh WorkerCoordinator claim/fence + exact-materialization candidate validation. Until a native runtime surface is connected and those receipts exist, the task remains active and all runtime/publication predicates above remain false.
