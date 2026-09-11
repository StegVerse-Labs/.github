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

PR #1373 merged the strict candidate consumer. PR #1381 merged the Site publication adapter and fail-closed shared Universal InTr route installer after organization control, Heartbeat validation, and the deterministic repository suite all passed on the repaired exact head.

Merged surfaces include:

- `scripts/consume_site_publication_intr_materialization_request.py`
- `workers/site_publication_intr_ingress.py`
- `scripts/install_site_publication_universal_intr_route.py`
- associated regression tests

`workers/` is already copied wholesale by `scripts/refresh_sovereign_worker_runtime_source.py`; no second listener or source-refresh owner was introduced.

## Current WorkerCoordinator registration slice

This continuation registers the child task without pre-claiming it:

- `workers/site_publication_intr_consumer_worker.py`
- `control/worker-registry.d/site-publication-intr-consumer-001.json`
- `control/process-worker-adapters.d/site-publication-intr-consumer-001.json`
- `cost-basis/worker-runtime/site-publication-intr-consumer.json`
- `control/task-vectors/SITE-PUBLICATION-INTR-CONSUMER-001.json`
- `handoffs/SITE-PUBLICATION-INTR-CONSUMER-001.json`
- `tests/test_site_publication_intr_worker_registration.py`

The registry state is deliberately:

```text
state = HANDOFF_READY
claim_id = null
heartbeat_timing = null
lease = null
fresh_fence_required = true
minimum_fencing_token_exclusive = 0
```

The zero floor encodes only that checkout must mint a nonzero fresh generation; it does not hard-code or reuse any historical task fence. The actual claim/fencing generation remains a WorkerCoordinator runtime operation.

The worker refuses an invocation without both a real `claim_id` and integer fencing token. It accepts only `STEGVERSE_SITE_PUBLICATION_MATERIALIZATION_ID`, which must identify an already-admitted exact Site request. Candidate validation then remains ACTIVE with authentic lease/public-observation work still unresolved.

## Exact-head validation repair

The previous exact head `aef2740e9f0bb57241d78ec5d7898e8c6a436a92` passed Organization Control and the Deterministic Repository Suite but failed Heartbeat Worker Project run `34566974758` at the later carrier-only/non-mutating dry-run proof. The heartbeat workflow on the branch matched the current main workflow; the failure was isolated to transport of the full branch-specific dry-run projection as one command-line argument.

Commit `041a929253ca058138d3ab2d0c8f3e6bdae1854a` changes only that validation transport: `scripts/run_heartbeat_runtime.py --dry-run --cycles 1` is tee'd to a temporary file and the same JSON is parsed from that file. The existing before/after repository hashes and every carrier non-authority/projection assertion remain unchanged. No heartbeat authority, admission, claim, fence, task activation, worker invocation, lease mutation, or repository persistence is added by this repair.

Exact-head validation for the repaired branch is pending and must be green across Organization Control, Deterministic Repository Suite, and Heartbeat Worker Project before PR #1398 can merge.

## Runtime/publication predicates still false

```text
runtime execution observed = false
public HTTPS /intr/profile observed = false
exact HTTP byte/path equivalence observed = false
lease closure observed = false
final publication transition admitted = false
DNS/TLS recovery proven = false
```

Persistent Node continuity remains required. Persistent host, always-on receiver, second user-operated device, hosted-provider runtime, and Render remain prohibited/not required.

## Remaining work

1. Obtain all three green exact-head validation suites and merge PR #1398 only then.
2. Refresh the merged source into the already-local sovereign runtime.
3. Target `SITE-PUBLICATION-INTR-CONSUMER-001` through the existing WorkerCoordinator so it receives a fresh independent claim/fence; do not reuse the parent claim.
4. Bind only the exact admitted Site publication materialization id to that fenced invocation.
5. Execute one authentic bounded `EVENT_EPHEMERAL` publication lease.
6. Independently observe `/intr/profile`, exact HTTP bytes/path hashes, candidate-result evidence export, and lease closure.
7. Separately admit the final publication transition; only then proceed to canonical-domain DNS/TLS recovery proof.

## Non-claims

Source/CI success, task registration, ingress admission, HeartBeat observation, or candidate receipts do not prove authentic runtime execution, public reachability, content equivalence, publication, or DNS/TLS recovery.

## README maintenance

Root README was reviewed for this child lane. No provider/runtime wording change is required; the existing provider-neutral boundary remains correct.