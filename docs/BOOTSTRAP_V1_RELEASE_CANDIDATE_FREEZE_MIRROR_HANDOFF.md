# Bootstrap v1 Release Candidate Freeze Mirror Handoff

Updated: 2026-08-29
Repository: `StegVerse-Labs/.github`

## Goal

Freeze a transport-neutral StegVerse Bootstrap v1 release candidate from the authentic frozen Bootstrap v1 source catalog.

This lane packages **identity and compatibility**, not source bytes and not execution authority.

## Required upstream

```text
~/.stegverse/state/bootstrap-v1-source-identity-freeze/
  catalog/bootstrap-v1-source-catalog.json
  receipts/latest.json
```

Required source freeze transition:

`BOOTSTRAP_V1_SOURCE_IDENTITIES_FROZEN`

## Candidate contract

Schema:

`stegverse.bootstrap.release-candidate/v1`

Candidate version:

`1.0.0-rc.1`

The candidate binds:
- exact frozen source catalog SHA-256;
- exact four-component source identity-set SHA-256;
- `stegverse.source-package/v1 @ 1.0.0`;
- `stegverse.bootstrap.source-catalog/v1 @ 1.0.0`;
- device materialization evidence schema `stegverse.device-node-source-package-bootstrap-evidence/v1`;
- required materialization state `MATERIALIZED_UNADMITTED`;
- execution authority `NONE` before separate admission;
- platform/transport neutrality invariants.

## Explicit non-fields

The canonical release candidate MUST NOT require or encode:
- GitHub repository;
- Git commit;
- pull request;
- URL;
- HTTP host;
- hosting provider;
- package registry;
- cloud provider;
- transport implementation.

Those may exist later as optional distribution observations but are not Bootstrap identity.

## Freeze rule

The first candidate may be created only from a valid frozen source catalog. Re-running against the same catalog is idempotent.

If an existing `1.0.0-rc.1` candidate differs, fail closed. A new identity set requires a new candidate version; it may not mutate rc.1.

## Authority

```text
github_platform_required: false
specific_external_platform_required: false
network_access: false
credential_required: false
package_execution_authority: false
sdk_admission_authority: false
release_activation_authority: false
publication_authority: false
authority_effect: NONE_RELEASE_CANDIDATE_FREEZE_ONLY
```

## Runtime truth

```text
source identity freeze capability: IMPLEMENTED / MERGED
first authentic frozen source catalog: NOT YET OBSERVED
release-candidate freeze worker: IMPLEMENTING
Bootstrap v1 rc.1: NOT YET FROZEN
Bootstrap v1 distribution/runtime proof: NOT YET OBSERVED
Bootstrap v1 release: NOT YET AUTHORIZED
```
