# SV-DN-1 Production Source Preparation Mirror Handoff

Updated: 2026-08-29
Repository: `StegVerse-Labs/.github`
Goal: `SV-DN1-PRODUCTION-SOURCE-PREPARATION-001`

## Governing correction

The production bootstrap MUST NOT depend on GitHub or any other external platform for source acquisition.

GitHub repository names and historical commit SHAs are retained only as migration/provenance coordinates. They are not runtime locators, admission authorities, or availability dependencies.

## Canonical runtime contract

```text
already-local verified source
        OR
content-addressed StegVerse source package
        ↓
verify complete manifest + every file hash
        ↓
derive source_identity = sha256:<source_bundle_sha256>
        ↓
verify retained migration anchors
        ↓
materialize local source root
        ↓
emit source-preparation receipt
        ↓
SV-DN1-SDK-FIRST-ROUND-001
```

Required source roots remain:

```text
STEGVERSE_SDK_SOURCE_ROOT
STEGVERSE_STEGCORE_SOURCE_ROOT
STEGVERSE_CORE_LITE_SOURCE_ROOT
STEGVERSE_MASTER_RECORDS_SOURCE_ROOT
```

## Source package

Schema: `stegverse.source-package/v1`
Version: `1.0.0`
Identity scheme: `sha256-content-manifest`

Each package carries:
- component_id
- canonical content-addressed source_identity
- manifest file_count and source_bundle_sha256
- ordered per-file path / SHA-256 / size rows
- exact file bytes
- credential_material_included=false
- authority_effect=NONE_SOURCE_TRANSPORT_ONLY
- optional provenance metadata

The package can arrive through any admitted transport. This worker itself performs no network acquisition.

Default local package store:

```text
~/.stegverse/packages/source/v1/<component-slug>/package.json
```

## Migration anchors

Five pre-existing anchor blob identities remain temporarily as migration trust anchors so the first sovereign package identities can be derived from the already-established source state without trusting a new platform locator.

They are not source locators and do not require GitHub availability.

Historical coordinates retained as optional provenance:

```text
StegVerse-org/StegVerse-SDK       4461a1edf83549c51189ca4217dd75752caf604e
Data-Continuation/core-lite       284ddc21a352ee9c7decdd40dd499b7286710bc8
StegVerse-Labs/StegCore           eb2ef110d09328aa90bf1ed91c18b47a3ba32a71
master-records/orchestration      baf9272f89ebe515fc4c2413b5d951d28f1e4485
```

Once the first complete source package identities are authentically observed and frozen, those SHA-256 package identities become the durable StegVerse source coordinates; historical Git coordinates remain provenance only.

## Explicitly prohibited

```text
HTTP source fetch by this worker
GitHub archive fetch
codeload fetch
git clone/fetch/pull
TVC GitHub repository-operation spool as a bootstrap prerequisite
credential-bearing source acquisition
automatic fallback to any external source platform
repository writeback
```

## Bound state

```text
~/.stegverse/state/sv-dn1-production-source-prep/
  observed/source-roots.json
  requests/source-package-needs.json
  receipts/latest.json
```

A missing component produces `HANDOFF_READY / SV_DN1_SOURCE_PACKAGE_MATERIALIZATION_PENDING` and names the local package-store location required. It does not select or contact an external platform.

## Runtime truth

```text
resident/InTr upstream: OBSERVED
platform-neutral source package schema: IMPLEMENTED
production source worker network source acquisition: REMOVED
GitHub runtime/source dependency: NONE BY CONTRACT
first four canonical SHA-256 source package identities: NOT YET OBSERVED/FROZEN
production source prep receipt v2: NOT YET OBSERVED
SDK first round: NOT YET EXECUTED
```

## Completion

`SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE` requires all four roots to exist, each root to have a `sha256-content-manifest` identity, retained migration anchors to verify, and:

```text
network_source_fetch_performed=false
github_platform_required=false
credential_used=false
github_token_used=false
repository_writeback_performed=false
```

Newer authentic runtime evidence overrides older source/PR/session descriptions.
