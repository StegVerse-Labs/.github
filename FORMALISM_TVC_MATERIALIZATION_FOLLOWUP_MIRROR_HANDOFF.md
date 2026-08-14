# Formalism TVC Materialization Follow-up Mirror Handoff

## Source of truth

```text
organization: StegVerse-Labs
repository: .github
branch: feat/formalism-tvc-materialization-followup-001
goal_id: FORMALISM-TVC-MATERIALIZATION-FOLLOWUP-001
parent_goal: FORMALISM-TVC-LOCAL-SPOOL-001
credential_authority: TV/TVC
consumer_secret_or_token_authority: NONE
github_token_required: false
archive_ready: false
```

## Originating requirement

The bounded local spool can carry non-secret inspection requests from the formalism heartbeat worker into TV/TVC and sanitized receipts back. Missing-source continuity is still incomplete unless an exact successful inspection receipt can deterministically produce the next TVC `MATERIALIZE_SOURCE_ARCHIVE` warrant without a chat session.

This goal adds that transition only. It does not create owner-source implementation content and does not widen the transport broker beyond the first-cohort source-materialization policy.

## Transition

```text
source-discovery receipt says repository missing
-> .github emits INSPECT_REPOSITORY_STATE request
-> TVC spool intake returns sanitized exact base_ref/base_sha receipt
-> .github validates request/receipt identity and TV/TVC safety predicates
-> .github emits deterministic MATERIALIZE_SOURCE_ARCHIVE warrant
-> TVC independently authorizes it under its local materialization policy
-> TVC materializes exact commit into /var/lib/stegverse/source/<owner>/<repo>
-> source-discovery re-runs and accepts the root only when a real *_MIRROR_HANDOFF.md exists
```

## Required invariants

The follow-up warrant must preserve the original repository, base_ref, destination identity, maximum byte budget, and source receipt lineage. `expected_base_sha` must come only from the matching sanitized TVC inspection receipt. The request remains non-secret and includes `consumer_credential_present=false`, `secret_values_present=false`, and `credential_authority=TV/TVC`.

A mismatched request id, repository, ref, unsafe receipt, malformed SHA, expired receipt/request, or duplicate completed materialization fails closed. The heartbeat never receives `TVC_EPHEMERAL_GITHUB_TOKEN`.

## Scope

```text
workers/formalism_tvc_repository_transport_worker.py
tests/test_formalism_tvc_repository_transport_worker.py
FORMALISM_TVC_REPOSITORY_TRANSPORT_CONSUMERS_MIRROR_HANDOFF.md
control/session-implementation-claim-2026-08-14-formalism-tvc-materialization-followup.json
```

## Non-goals

```text
owner-source code generation
owner branch mutation
PR merge
mathematical authority
StegCore execution authority
provider operations
wallet contact/sign/broadcast
```

## Completion

Hosted no-token repository validation must pass, the change must be canonically admitted, and TVC PR #20 must expose the complementary local spool inspection/materialization intake. Runtime activation is proven only after one actual missing-source request produces a TVC materialization receipt and source discovery subsequently re-observes that repository.

## Archive condition

Do not archive the originating session while the follow-up is unvalidated/unmerged, while TVC PR #20 is not validated/canonical, or while owner-source implementation generation/mutation remains an unowned chat dependency.