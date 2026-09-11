# Site Publication InTr Consumer Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Issue: #1372
Task: `SITE-PUBLICATION-INTR-CONSUMER-001`
Parent Goal Task ID: `KV-CONNECTION-REVALIDATION-WORKER-001`
Parent Site lane: `SITE-497-THIRD-PARTY-DEPENDENCY-ERADICATION`
COSV: `50000000102000`
Canonical Site source boundary: `StegVerse-Labs/Site@bc1ee7257ebc64f77dab3f0b746bb3a86a279b6c`

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

## Source implemented on branch

- `scripts/consume_site_publication_intr_materialization_request.py`
- `tests/test_site_publication_intr_materialization_consumer.py`

The consumer validates exact request/hash/payload-manifest binding and emits a write-once `stegverse.site-publication-intr-materialization-consumption/v1` candidate receipt.

The receipt deliberately leaves all authentic runtime/publication predicates false:

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

This task is a fresh child of `KV-CONNECTION-REVALIDATION-WORKER-001`; the parent registry explicitly prohibits parent-claim reuse and requires fresh fencing for independent task control. Source registration must therefore remain non-authorizing until the existing WorkerCoordinator issues a fresh claim/fence for this task.

## Remaining work

1. Validate this consumer source and tests.
2. Register the consumer in the sovereign runtime source-refresh/bootstrap file set without changing runtime ownership.
3. Add a Site-specific profiled-ingress dispatch branch for exactly `StegOS:SitePublicationRuntime`, reusing the existing Universal InTr ingress and receipt model.
4. Obtain a fresh independent WorkerCoordinator claim/fence for `SITE-PUBLICATION-INTR-CONSUMER-001` before execution.
5. Execute one authentic bounded `EVENT_EPHEMERAL` publication lease.
6. Independently observe `/intr/profile`, exact HTTP bytes/path hashes, candidate result return, evidence export, and lease closure.
7. Keep final publication transition and DNS/TLS recovery separately admitted.

## Non-claims

Source/CI success does not prove runtime execution, public reachability, content equivalence, publication, or DNS/TLS recovery.

## README maintenance

Root README was reviewed for this child source lane. No provider/runtime wording change is required; the existing provider-neutral boundary remains correct.
