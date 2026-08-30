# Bootstrap v1 Source Package Production Mirror Handoff

Updated: 2026-08-30
Repository: `StegVerse-Labs/.github`
Goal: `BOOTSTRAP-V1-SOURCE-PACKAGE-PRODUCTION-001`

## Goal

Produce the four canonical local `stegverse.source-package/v1` objects directly from one authentic completed `stegverse.sv-dn1.production-source-prep-receipt/v2`.

This lane does not discover source, fetch source, choose an external transport, create source identities, execute packages, admit the SDK, publish artifacts, or grant repository authority.

## Required upstream

Default receipt:

`~/.stegverse/state/sv-dn1-production-source-prep/receipts/latest.json`

Required predicates:

```text
schema = stegverse.sv-dn1.production-source-prep-receipt/v2
state = COMPLETE
transition_id = SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE
source_identity_scheme = sha256-content-manifest
migration_anchors_verified = true
network_source_fetch_performed = false
github_platform_required = false
credential_used = false
github_token_used = false
repository_writeback_performed = false
sdk_admitted = false
```

Required components:

```text
stegverse.sdk
stegverse.stegcore
stegverse.core-lite
stegverse.master-records
```

For each component the receipt must provide:
- one local source root;
- one exact `sha256:<64 lowercase hex>` source identity;
- a matching non-secret `STEGVERSE_*_SOURCE_ROOT` locator.

## Package construction

Canonical worker:

`workers/bootstrap_v1_source_package_production_worker.py`

For each component the worker:

1. opens only the already-local root from the authenticated upstream receipt;
2. enumerates every regular file recursively, excluding only `.git/**`;
3. sorts files by relative POSIX path;
4. recomputes SHA-256 and size for every file;
5. recomputes the canonical content-manifest digest;
6. requires `sha256:<manifest digest>` to equal the upstream source identity exactly;
7. emits `stegverse.source-package/v1 @ 1.0.0` with exact file bytes encoded as base64;
8. validates the package again before persistence;
9. writes it to the local package store;
10. fails closed if an existing package at the canonical path differs.

Canonical local package paths:

```text
~/.stegverse/packages/source/v1/stegverse-sdk/package.json
~/.stegverse/packages/source/v1/stegverse-stegcore/package.json
~/.stegverse/packages/source/v1/stegverse-core-lite/package.json
~/.stegverse/packages/source/v1/stegverse-master-records/package.json
```

## Output

Bound-state receipt:

`~/.stegverse/state/bootstrap-v1-source-package-production/receipts/latest.json`

Terminal transition:

`BOOTSTRAP_V1_SOURCE_PACKAGES_PRODUCED`

The receipt binds:
- exact upstream source-prep receipt digest;
- four component IDs;
- four source identities;
- four package SHA-256 values;
- four package paths;
- package schema/version;
- zero-authority invariants.

## Idempotence

Re-running against the same exact source roots and identities is idempotent.

If an existing canonical package differs from the recomputed package, execution fails closed with `BOOTSTRAP_V1_SOURCE_PACKAGE_CONFLICT`. Package bytes may not silently drift beneath a frozen source identity.

## Authority boundary

```text
credential_authority: TV/TVC
github_platform_required: false
specific_external_platform_required: false
network_access: false
credential_required: false
source_acquisition_authority: false
package_execution_authority: false
sdk_admission_authority: false
repository_writeback_authority: false
release_activation_authority: false
publication_authority: false
heartbeat_dependency: false
second_machine_required: false
authority_effect: NONE_SOURCE_PACKAGE_PRODUCTION_ONLY
```

Package integrity is evidence of source-byte identity only. It confers no execution or governance authority.

## Downstream

This capability can run as soon as authentic production-source preparation completes. It may run independently of the source-identity freeze, because both consume the same source-prep v2 receipt.

The distributable-bundle worker remains gated by its release-candidate dependency and additionally requires these four exact packages to be locally present.

## Completion

`BOOTSTRAP_V1_SOURCE_PACKAGES_PRODUCED` requires all four package objects to validate against the exact upstream source identities with no network, credential, repository, SDK, release, or publication authority.

Source merge, hosted CI, package-source code, and package file existence alone do not prove authentic resident package production.
