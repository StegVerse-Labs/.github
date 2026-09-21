# SDK Public Developer Wiki Mirror Handoff

Updated: 2026-09-21
Goal Task ID: `SDK-PUBLIC-DEVELOPER-WIKI-001`
Canonical repository: `StegVerse-org/StegVerse-SDK`
Target public origin: `https://sdk.stegverse.org/`
Status: `ACTIVE / SDK SOURCE MERGED + PAGES DEPLOYED / DNS VERIFIED / HTTPS ENFORCED / SITE PROPAGATION IN PROGRESS`

## Goal

Publish a developer-facing SDK wiki directly from the canonical StegVerse SDK repository. The public surface must explain and demonstrate the actual programmatic contract already present in the SDK:

```text
source-native manifested data
-> stegverse.ingress-manifest.v1
-> caller-selected processing capability
-> declared installed runtime route
-> processor-specific evaluation
-> canonical Master Records custody
-> caller-selected return projection
-> returned artifact + manifest_receipt_id
-> replay / reconstruction where applicable
```

The public wiki is a documentation and navigation projection only. It must not become governance, execution, transition, credential, custody, evidence, processor-selection, or publication-transition authority.

## Canonical source model

The SDK repository itself remains the source of truth. The public wiki should be generated or maintained from existing SDK documentation, schemas, examples, and retained evidence rather than copying those materials into a second canonical repository.

Initial source set:

- `README.md`
- `SDK_MIRROR_HANDOFF.md`
- `docs/GENERIC_MANIFEST_PROCESSING_CONTRACT.md`
- `docs/MANIFEST_RECEIPT_NAVIGATION_MIRROR_HANDOFF.md`
- `schemas/stegverse.ingress-manifest.v1.schema.json`
- `inspection/examples/external-framework-generic-manifest.json`
- manifest-builder and run-manifest documentation/examples

## Public information architecture

The first public projection should expose:

1. **Start here** — what the SDK is and is not.
2. **Manifest ingress** — submit manifested source-native data.
3. **Processing / governance route selection** — capability vs route vs authority.
4. **Schemas** — canonical ingress and extension schemas.
5. **Examples and demos** — runnable, evaluator-neutral examples.
6. **Receipts** — manifest receipt navigation and result lineage.
7. **Replay / reconstruction** — evidence retrieval without consequence re-execution.
8. **External frameworks** — provider/framework-neutral integration contract.
9. **Authority boundaries** — SDK, Interlock/InTr, Master Records, Publisher, TV/TVC.
10. **Current implementation status** — distinguish merged source, semantic validation, authentic governed runtime evidence, release candidates, and public releases.

## Publication architecture

Preferred architecture:

```text
StegVerse-org/StegVerse-SDK main
-> repository-local public-wiki projection
-> GitHub Actions Pages deployment
-> sdk.stegverse.org
-> Site wiki/developer directory link
```

Do not create a duplicate SDK authority repository merely for presentation.

## Required validation gates

- canonical Task Registry registration merged;
- repository-local handoff created and kept current;
- README updated with the public-wiki contract;
- Pages source/workflow is repository-local and reproducible;
- public content is derived from current canonical SDK source;
- authority-boundary language is preserved;
- schema/example links resolve from the deployed site;
- `sdk.stegverse.org` custom-domain configuration is represented by repository source and validated publicly;
- Site links to the branded SDK developer wiki without duplicating SDK content;
- public HTTPS root and representative schema/example/document pages are observed after deployment.

## Adjacent governed publication path

This task is adjacent to, but does not replace, the governed submission/publication-transition work in Admissibility/Publisher. A submitter may propose manifested state through SDK ingress, but this documentation surface itself never performs a consequential publication mutation.

## Current evidence — 2026-09-21

Canonical registration merged via `StegVerse-Labs/.github#2490` as `608c104f45db5dbe9c29d498881fb3267c562cc7`. SDK implementation merged via `StegVerse-org/StegVerse-SDK#300` as `e454dfa9042884939a0e6cde3c15a2fd2e386be5`. Exact-head SDK public-wiki validation passed after repair, and the main `Publish SDK Developer Wiki` workflow completed successfully.

Earlier user-supplied Pages evidence showed `InvalidDNSError`, and Cloudflare showed the `sdk` CNAME incorrectly pointed to `stegverse-org.stegverse.org`. The user corrected the existing DNS-only record to `stegverse-org.github.io`. Subsequent GitHub Pages evidence now reports `Your site is live at https://sdk.stegverse.org/`, `DNS check successful`, and `Enforce HTTPS` enabled. Site propagation is being implemented under Site PR #1446.

## Current next executable step

Complete exact-head validation and merge of Site PR #1446, then observe the deployed Site wiki directory linking to `https://sdk.stegverse.org/`. Representative SDK subresource observation is still unverified by this session's external web tool and must not be fabricated.
