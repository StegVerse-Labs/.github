# Bootstrap v1 Distributable Bundle Mirror Handoff

Updated: 2026-08-29
Repository: `StegVerse-Labs/.github`

## Goal

Build one self-contained, content-addressed Bootstrap v1 bundle from:

1. frozen `1.0.0-rc.1` release candidate;
2. frozen four-component source catalog;
3. four exact `stegverse.source-package/v1` objects matching that catalog.

The bundle is a transport-neutral object. How its bytes arrive is outside its identity and authority.

## Bundle contract

Schema:

`stegverse.bootstrap.bundle/v1`

Bundle version:

`1.0.0-rc.1`

Canonical bundle identity:

`sha256:<canonical bundle body digest>`

The bundle contains:
- exact rc.1 candidate;
- exact frozen source catalog;
- four source packages;
- deterministic component ordering;
- compatibility contract;
- explicit zero-authority state.

## Required source packages

Exactly:

```text
stegverse.sdk
stegverse.stegcore
stegverse.core-lite
stegverse.master-records
```

Each package must:
- use `stegverse.source-package/v1 @ 1.0.0`;
- have `source_identity` equal to its frozen catalog entry;
- verify every file SHA-256 and complete manifest digest;
- contain no credential material;
- have `authority_effect=NONE_SOURCE_TRANSPORT_ONLY`.

## Transport neutrality

Bundle construction and verification require no:
- GitHub;
- Git;
- package registry;
- HTTP;
- DNS;
- hosting provider;
- cloud provider;
- platform account;
- credential.

The same bundle bytes are canonical regardless of whether moved by local file, node-to-node InTr, removable media, web download, QR/chunk transport, or another future transport.

## Authority

```text
bundle_integrity_confers_execution_authority: false
release_activated: false
publication_performed: false
github_platform_required: false
specific_external_platform_required: false
network_locator_required: false
credential_required: false
execution_authority: NONE
authority_effect: NONE_BUNDLE_BUILD_ONLY
```

## Runtime truth

```text
source package v1 producer: IMPLEMENTED / MERGED
source package v1 device receiver: IMPLEMENTED / MERGED
source identity freeze capability: IMPLEMENTED / MERGED
rc.1 freeze capability: IMPLEMENTED / MERGED
authentic source catalog: NOT YET OBSERVED
authentic rc.1 candidate: NOT YET FROZEN
authentic four-package bundle: NOT YET BUILT
device bundle materialization proof: NOT YET OBSERVED
Bootstrap v1 release: NOT YET AUTHORIZED
```


## Canonical package producer — 2026-08-30

The four required local `stegverse.source-package/v1` objects are now owned by the separate authority-neutral machine task:

`BOOTSTRAP-V1-SOURCE-PACKAGE-PRODUCTION-001`

That producer consumes the same authentic production-source-prep v2 receipt used by the source-identity freeze, recomputes every file/content manifest from the already-local verified roots, requires exact equality with the upstream source identities, and writes the canonical local package paths.

The distributable-bundle worker does not produce, fetch, or repair packages itself. It remains a pure integrity/bundle composition gate. Missing package objects therefore identify the package-production task as the canonical continuation rather than an unspecified transport or external platform.
