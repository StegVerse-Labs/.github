# Bootstrap v1 Source Identity Freeze Mirror Handoff

Updated: 2026-08-29
Repository: `StegVerse-Labs/.github`

## Goal

Freeze the first canonical StegVerse Bootstrap v1 source catalog exclusively from an authentic completed `stegverse.sv-dn1.production-source-prep-receipt/v2`.

This lane does not discover source, fetch source, choose a transport, derive identities from repository coordinates, or invent package identities.

## Required upstream receipt

Default:

```text
~/.stegverse/state/sv-dn1-production-source-prep/receipts/latest.json
```

Required predicates:

```text
schema: stegverse.sv-dn1.production-source-prep-receipt/v2
state: COMPLETE
transition_id: SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE
source_identity_scheme: sha256-content-manifest
network_source_fetch_performed: false
github_platform_required: false
credential_used: false
github_token_used: false
repository_writeback_performed: false
```

Required sovereign components:

```text
stegverse.sdk
stegverse.stegcore
stegverse.core-lite
stegverse.master-records
```

Each must carry exactly one `sha256:<64 hex>` source identity and a local source root.

## Output

Canonical bounded-state catalog:

```text
~/.stegverse/state/bootstrap-v1-source-identity-freeze/
  catalog/bootstrap-v1-source-catalog.json
  receipts/latest.json
```

Catalog schema:

```text
stegverse.bootstrap.source-catalog/v1
```

The catalog stores only:
- Bootstrap catalog version;
- the four sovereign component IDs;
- exact source identities;
- source identity scheme;
- upstream receipt digest;
- compatibility/package schema requirements;
- authority-neutral state.

Repository names, PRs, commit SHAs, URLs, GitHub coordinates, or transport locators are not canonical catalog fields.

## Idempotence

If the catalog already exists with the same four identities and upstream digest, execution is idempotently COMPLETE.

If an existing frozen catalog differs, execution fails closed with `FROZEN_SOURCE_IDENTITY_CONFLICT`. A frozen v1 catalog may not silently drift.

## Authority

```text
credential_authority: TV/TVC
github_platform_required: false
network_access: false
repository_writeback_authority: false
package_execution_authority: false
sdk_admission_authority: false
publication_authority: false
authority_effect: NONE_IDENTITY_FREEZE_ONLY
```

## Runtime truth

```text
freeze worker source: IMPLEMENTED / MERGED
authentic four-source source-prep v2 receipt: NOT YET OBSERVED
first canonical Bootstrap v1 source catalog: NOT YET FROZEN
Bootstrap v1 release/tag: NOT YET AUTHORIZED
```

## Completion

`BOOTSTRAP_V1_SOURCE_IDENTITIES_FROZEN` occurs only after one authentic source-prep v2 receipt freezes the exact four source identities and the generated catalog revalidates deterministically.


## Parallel package production

`BOOTSTRAP-V1-SOURCE-PACKAGE-PRODUCTION-001` is a sibling release-preparation task that consumes the same authentic source-prep v2 receipt. It serializes the already-frozen source bytes into local `stegverse.source-package/v1` objects but does not create or change source identities. Source identity freeze and package production may therefore execute independently after the common source-prep dependency completes.
