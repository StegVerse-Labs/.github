# SV-DN-1 Repository Merge Dispatch Mirror Handoff

Updated: 2026-08-31
Repository: `StegVerse-Labs/.github`
Goal: `SV-DN1-REPOSITORY-MERGE-DISPATCH-001`
Task: `SV-DN1-REPOSITORY-MERGE-DISPATCH-001`
Upstream: `SV-DN1-REPOSITORY-PERSISTENCE-DISPATCH-001`
TVC merge authority: `StegVerse-Labs/TVC:TVC-SV-DN1-REPOSITORY-MERGE-GATE-001`
Credential authority: `TV/TVC`
GitHub token runtime authority: `NONE`
Authority effect: `NONE_MERGE_REQUEST_STAGING_ONLY`

## Goal

Close the machine-owned gap between the exact TVC-created SV-DN-1 product PR and the
separate bounded TV/TVC merge gate.

```text
SV_DN1_REPOSITORY_PERSISTENCE_PR_CREATED
-> exact non-secret merge request
-> TVC SV-DN-1 merge spool
-> exact sanitized merge receipt
-> SV_DN1_REPOSITORY_PERSISTENCE_PR_MERGED
```

This worker never receives the TVC credential and never calls GitHub.

## Inputs

Persistence-dispatch receipt:

`~/.stegverse/transport/sv-dn1-repository-persistence/receipts/latest.json`

Frozen package:

`~/.stegverse/state/sv-dn1-repository-persistence-package/packages/latest.json`

Both may be relocated through explicit non-secret locators only.

The worker independently verifies:
- persistence receipt state/transition;
- exact target repository/base;
- exact package SHA;
- exact branch prefix;
- 40-character base/head identities;
- positive pull-request number;
- exact frozen package identity and five-file set.

## TVC merge request

Schema:

`stegverse.tvc.sv-dn1-repository-merge-request/v1`

The request binds exactly:
- repository `StegVerse-org/stegverse-demo-suite`;
- base ref `main`;
- pull-request number;
- expected base SHA;
- expected head SHA;
- expected head ref `sv-dn1/publication-*`;
- frozen package SHA;
- `credential_authority=TV/TVC`;
- `consumer_credential_present=false`;
- `secret_values_present=false`;
- `merge_request_grants_authority=false`.

It is written only to the local TVC merge outbox.

## Merge receipt

Required TVC receipt:

`stegverse.tvc.sv-dn1-repository-merge-receipt/v1`

Terminal transition:

`SV_DN1_REPOSITORY_PERSISTENCE_PR_MERGED`

The receipt must bind the exact request, PR/base/head/package identities and prove:
- file_count=5;
- exact_bytes_verified=true;
- credential authority TV/TVC;
- credential value not exposed;
- no non-TV/TVC secret/token;
- deployment_performed=false;
- publication_observed=false.

## Authority boundary

The worker MAY:
- read exact local persistence/package receipts;
- stage one exact non-secret merge request;
- consume one sanitized TVC merge receipt;
- write one bounded local task receipt.

The worker MUST NOT:
- read or receive TVC_EPHEMERAL_GITHUB_TOKEN;
- call GitHub;
- merge a PR;
- deploy Pages;
- observe public artifacts;
- decide publication semantics;
- execute SDK/InTr/governance/custody;
- grant release/certification authority.

## Current state

```text
TVC bounded merge gate: MERGED @ 0e8678e28c78b09932f215bd36a1f15da523a90f
merge dispatch task: IMPLEMENTING
authentic product PR: NOT YET OBSERVED
authentic merge: NOT YET OBSERVED
Pages deployment: NOT YET OBSERVED
public exact-byte observation: NOT YET OBSERVED
```
