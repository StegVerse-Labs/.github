# SV-DN-1 Production Source Preparation Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Goal: `SV-DN1-PRODUCTION-SOURCE-PREPARATION-001`

## Governing correction

The production bootstrap MUST NOT depend on GitHub or any other external platform for source acquisition.

GitHub repository names and historical commit SHAs are retained only as migration/provenance coordinates. They are not runtime locators, admission authorities, or availability dependencies.

Source preparation is also not semantically dependent on route-specific InTr completion. It is pure local source verification/materialization under independent task control. The former `SV-DN1-INTR-RUNTIME-001 -> SV-DN1-PRODUCTION-SOURCE-PREP-001` execution gate was sequencing for the original first-round chain, not a source-safety predicate, and is removed from source-prep admission. `SV-DN1-SDK-FIRST-ROUND-001` retains its own separate InTr and source-prep prerequisites before that production round may execute.

This allows the same verified SDK / StegCore / Core-Lite / Master Records roots to be reused by other separately admitted sovereign consumers without granting those consumers SDK, governance, provider, or execution authority.

## Canonical runtime contract

```text
already-local verified source under the canonical materialization tree
        OR
already-local verified source referenced by the canonical non-secret component locator
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
separately admitted consumer may use exact roots
```

For the original SV-DN-1 production chain:

```text
source-preparation COMPLETE
+
SV-DN1-INTR-RUNTIME-001 COMPLETE
-> SV-DN1-SDK-FIRST-ROUND-001 may become dependency-complete
```

Required source locators remain:

```text
STEGVERSE_SDK_SOURCE_ROOT
STEGVERSE_STEGCORE_SOURCE_ROOT
STEGVERSE_CORE_LITE_SOURCE_ROOT
STEGVERSE_MASTER_RECORDS_SOURCE_ROOT
```

When any of these locators already names a local directory, the worker verifies that directory directly: migration anchor(s) must match and a complete `sha256-content-manifest` identity is recomputed from the local bytes. A configured local root is not copied merely to satisfy a preferred directory layout. Only a truly absent component falls through to the local content-addressed package store.

## Independent task-control admission

`SV-DN1-PRODUCTION-SOURCE-PREP-001` is eligible for its own fresh WorkerCoordinator claim/fence whenever it is `HANDOFF_READY`. It no longer requires a parent task to be `COMPLETED` before source verification/materialization can begin.

This does not let HeartBeat grant execution authority and does not bypass WorkerCoordinator:

```text
execution_admission_mode: INDEPENDENT_TASK_CONTROL
fresh_fence_required: true
carrier_trigger_required: false
heartbeat_grants_execution_authority: false
parent terminalization required for source prep: false
```

The semantic parent lineage to the original SV-DN-1 workstream is retained as provenance. Only the runtime dependency is removed.

## Source package

Schema: `stegverse.source-package/v1`
Version: `1.0.0`
Identity scheme: `sha256-content-manifest`

Required sovereign component IDs:

```text
stegverse.sdk
stegverse.stegcore
stegverse.core-lite
stegverse.master-records
```

Repository names are not component identities.

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
route-specific InTr terminalization prerequisite for source prep: REMOVED
platform-neutral source package schema: IMPLEMENTED
production source worker network source acquisition: REMOVED
GitHub runtime/source dependency: NONE BY CONTRACT
first four canonical SHA-256 source identities: NOT YET OBSERVED/FROZEN
production source prep receipt v2: NOT YET OBSERVED
SDK first round: NOT YET EXECUTED
```

The separate current registry for `SV-DN1-INTR-RUNTIME-001` still reports its own authentic runtime blockers. Removing it as a source-prep prerequisite does not claim that InTr task complete.

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

## Local-root and v2 chain reconciliation — 2026-08-30

The runtime contract is source-identity based, not directory-layout based. The production-source worker therefore accepts three equivalent local inputs, all subject to the same migration-anchor and complete-content verification:

```text
1. canonical /var/lib/stegverse/source/components/<component> root
2. canonical non-secret STEGVERSE_*_SOURCE_ROOT locator to already-local source
3. local stegverse.source-package/v1 materialized into the canonical component root
```

No path receives trust merely because it was supplied through an environment variable. A configured locator with a missing or mismatched migration anchor fails closed as source drift.

The sovereign first-round orchestrator must validate the actual `stegverse.sv-dn1.production-source-prep-receipt/v2` contract. Retired receipt fields such as `public_source_roots_verified`, `private_source_roots_verified`, and `runtime_anchor_blobs_verified` are not part of v2 and may not be required for completion.

For v2, durable receipt acceptance requires:
- exactly four canonical component source identities;
- every identity is `sha256:<64 lowercase hex>`;
- exactly four canonical source roots;
- exactly four canonical non-secret root locators;
- root/locator equality component by component;
- `migration_anchors_verified=true`;
- `network_source_fetch_performed=false`;
- `github_platform_required=false`;
- `credential_used=false`;
- `github_token_used=false`;
- `repository_writeback_performed=false`;
- `sdk_admitted=false`.

This correction removes false runtime blockers without creating any new source-acquisition or credential authority.
