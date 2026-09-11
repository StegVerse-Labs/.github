# Site Publication InTr Consumer Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Issue: #1372
Task: `SITE-PUBLICATION-INTR-CONSUMER-001`
Parent Goal Task ID: `KV-CONNECTION-REVALIDATION-WORKER-001`
Parent Site lane: `SITE-497-THIRD-PARTY-DEPENDENCY-ERADICATION`
COSV: `50000000102000`
Canonical Site source boundary: `StegVerse-Labs/Site@bc1ee7257ebc64f77dab3f0b746bb3a86a279b6c`
Consumer source merge: `.github@e89a65307248a69e057bc07dac07a5ca98bc4677` (PR #1373)

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

## Merged consumer source

PR #1373 merged after all three exact-head organization suites passed.

- `scripts/consume_site_publication_intr_materialization_request.py`
- `tests/test_site_publication_intr_materialization_consumer.py`

The merged consumer validates exact request/hash/payload-manifest binding and emits a write-once `stegverse.site-publication-intr-materialization-consumption/v1` candidate receipt.

## Current runtime-ingress integration slice

This continuation adds:

- `workers/site_publication_intr_ingress.py`
- `scripts/install_site_publication_universal_intr_route.py`
- `tests/test_install_site_publication_universal_intr_route.py`

`workers/` is already copied wholesale by `scripts/refresh_sovereign_worker_runtime_source.py`, so the Site publication ingress adapter propagates through the existing sovereign source-refresh path without widening that whitelist.

The route installer follows the existing CanonicalWork pattern: it idempotently and fail-closed transforms the existing `workers/universal_intr_profiled_ingress.py`, advertises `StegOS:SitePublicationRuntime`, and inserts one Site publication destination branch. It does not create a second listener, heartbeat, scheduler, WorkerCoordinator, claim/fence path, credential path, or runtime owner.

The ingress adapter persists the exact validated materialization request write-once and emits only `INGRESS_ADMITTED_CANDIDATE_ONLY`. It deliberately leaves authentic runtime/publication predicates false:

```text
runtime_materialization_attempted = false
runtime_execution_observed = false
public_https_profile_observed = false
exact_http_readback_observed = false
content_equivalence_observed = false
lease_closure_observed = false
final_publication_transition_admitted = false
```

It also preserves:

```text
persistent Node identity = required
persistent host = false
always-on receiver = false
second user-operated device = false
hosted provider = false
Render = prohibited
credential authority = TV/TVC
GitHub token runtime authority = NONE
```

## Independent-task boundary

This task is a fresh child of `KV-CONNECTION-REVALIDATION-WORKER-001`; parent-claim reuse remains prohibited. Neither ingress admission nor source routing mints a claim/fence. Authentic lease execution remains blocked until the existing WorkerCoordinator issues a fresh independent claim/fence for `SITE-PUBLICATION-INTR-CONSUMER-001`.

## Remaining work

1. Validate and merge the current runtime-ingress integration slice.
2. Register/derive the child task in canonical worker/task control so WorkerCoordinator can issue its fresh independent claim/fence without parent reuse.
3. Install the Site route into the bounded runtime copy of the existing Universal InTr ingress.
4. Execute one authentic bounded `EVENT_EPHEMERAL` publication lease.
5. Independently observe `/intr/profile`, exact HTTP bytes/path hashes, candidate result return, evidence export, and lease closure.
6. Keep final publication transition and DNS/TLS recovery separately admitted.

## Non-claims

Source/CI success does not prove authentic ingress, runtime execution, public reachability, content equivalence, publication, or DNS/TLS recovery.

## README maintenance

Root README was reviewed for this child lane. No provider/runtime wording change is required; the existing provider-neutral boundary remains correct.
