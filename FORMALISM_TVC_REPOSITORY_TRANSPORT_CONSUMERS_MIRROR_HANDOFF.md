# Formalism TVC Repository Transport Consumers Mirror Handoff

## Source of truth

```text
organization: StegVerse-Labs
repository: .github
branch: feat/formalism-tvc-repository-transport-consumers-001
goal_id: FORMALISM-TVC-REPOSITORY-TRANSPORT-CONSUMERS-001
parent_goals:
  - FORMALISM-SOURCE-DISCOVERY-001
  - FORMALISM-MANIFOLD-IMPLEMENTATION-ADMISSION-001
credential_authority: TV/TVC
consumer_secret_or_token_authority: NONE
github_token_required: false
archive_ready: false
```

## Originating requirement

Close the two remaining chat/manual repository-transport gaps without giving the organization heartbeat, formalism workers, or owner repositories any GitHub/provider/wallet credential:

1. when formalism source discovery proves a required first-cohort repository is absent, derive a bounded non-secret TVC source-materialization request;
2. when implementation admission emits a canonical owner work manifest, derive bounded non-secret TVC branch/PR transport requests for the admitted owner repository.

The TVC transport authority is `StegVerse-Labs/TVC` goal `TVC-GITHUB-REPOSITORY-OPERATION-BROKER-001` / issue #19 / PR #20. Until that broker is validated and canonically admitted, these consumers must emit `BLOCKED_TVC_BROKER_NOT_CANONICAL` rather than attempting repository transport.

## Authority boundary

These consumers may construct and persist non-secret exact-warrant requests. They may not possess, request, read, forward, infer, log, or expose `TVC_EPHEMERAL_GITHUB_TOKEN` or any other credential value. Credential execution remains entirely inside TV/TVC.

They may not select a different formalism owner, widen an admitted path set, redefine AE mathematics, alter StegCore evaluator semantics, merge a PR, sign/broadcast a transaction, or treat transport success as mathematical/runtime/release authority.

## Installed surfaces

```text
control/formalism-tvc-repository-transport.json
handoffs/SHWP-FORMALISM-TVC-REPOSITORY-TRANSPORT-CONSUMERS-001.json
control/worker-registry.d/formalism-tvc-repository-transport-consumers-001.json
control/process-worker-adapters.d/formalism-tvc-repository-transport-consumers-001.json
workers/formalism_tvc_repository_transport_worker.py
tests/test_formalism_tvc_repository_transport_worker.py
requests/tvc-repository-operations/**
receipts/formalism-tvc-repository-transport/**
```

## Consumer contract

The worker consumes only durable non-secret inputs:

```text
formalism source-discovery receipt / roots manifest
formalism implementation-admission receipt / owner work manifests
TVC broker standing manifest
```

It emits request envelopes with:

```text
schema
request_id
operation_class
repository
base_ref
expected_base_sha
bounded destination identity OR bounded file set and source hashes OR exact PR head
credential_authority=TV/TVC
consumer_credential_present=false
secret_values_present=false
issuer=.github formalism transport worker
created_at
expires_at
source_receipt_refs
```

The envelope is not an authorization. TVC must independently validate owner standing and mint/consume its own exact non-secret authorization before any credential-bearing operation executes.

## Activation and completion

The worker is heartbeat-owned and may run on each admitted heartbeat while either source materialization or owner mutation transport remains unresolved. It terminates a request only after a TVC operation receipt with the same exact request/warrant identity is observed and the corresponding source-discovery or implementation-admission successor can re-evaluate the changed repository state.

Completion requires one observed end-to-end cycle for each applicable class:

```text
missing source -> bounded TVC materialization request -> TVC receipt -> source rediscovered
owner work manifest -> bounded TVC branch/PR requests -> owner validation/PR path -> reconciliation re-observes the change
```

## Claims

This slice owns only new `.github` consumer contract/worker/test/request/receipt surfaces. It does not modify TVC broker source, TVC runtime observer scope, AE/StegCore source, or existing heartbeat fence/lease semantics.

## Archive condition

Do not archive the originating session while these consumers are unvalidated, while TVC PR #20 is not canonically executable, or while the full recursive proof has not shown that a discovered gap can enter an owner repository PR path and be re-observed without a chat session or non-TV/TVC credential.