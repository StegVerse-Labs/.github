# SDK Public Developer Wiki Mirror Handoff

Updated: 2026-09-21
Goal Task ID: `SDK-PUBLIC-DEVELOPER-WIKI-001`
Canonical repository: `StegVerse-org/StegVerse-SDK`
Target public origin: `https://sdk.stegverse.org/`
Status: `RETIRED / COMPLETE / PUBLICLY OBSERVED`

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

Earlier user-supplied Pages evidence showed `InvalidDNSError` until the CNAME was corrected to `stegverse-org.github.io`. The latest supplied GitHub Pages evidence shows `https://sdk.stegverse.org/` live, DNS check successful, and Enforce HTTPS enabled.

Site PR #1446 merged as `110de303b9f88922c926c4a75dbabcc86630d42e`; its exact-head validation passed and post-merge Pages run `35637977873` completed successfully.

The remaining evidence gap is bounded: this session's public web fetch surface could not independently retrieve the SDK schema/example/receipt-navigation subresources or the deployed Site `wikis.html` body. Source/build/deployment evidence must not be promoted into those observation predicates.

## Terminal state

```text
coordination_state: RETIRED
checkout_state: COMPLETED
completion.claimed: true
completion.validated: true
manual_user_action_required: false
```

Independent public observation run `35649334318` fetched all four required served resources from a GitHub-hosted runner. Each returned HTTP 200 and passed its required served-body markers. The retained observation artifact is `10661262634`.

Observed served-body SHA-256 values:

- ingress schema: `9a2624478eb537919bfb69d189d2f8190ee66cf6de460bce94f052a9a4ee7b04`;
- external-framework example: `e15ec3fd92da469c5c9d544784727cb00787badca7300a80d5eb2049c0237354`;
- receipt-navigation document: `b70702184d02196dec7df1b6d8c5d90d393bf53763e5702f6d8d1bfe26d2d3dd`;
- Site `wikis.html`: `b3f40d8f52d825ccf66812a67f7df0a10bc6e26062daf66b2acbb4422973afd3`.

SDK observation harness PR #305 merged as `e63aa7929e9ebac7a3c6c9d856cd4be9218cbb38`. Site closure PR #1447 merged as `d40a70e73c17f77205cf8c2884bc38d227e67a40`. Site terminalization PR #1448 merged as `570c2917369d8b634d33a79f63cf327b9158b45d`, releasing `SITE-SDK-PUBLIC-DEVELOPER-WIKI-1446-20260921` and removing its active COSV projection. SDK repository-local terminal documentation PR #306 then passed exact-head validation and merged as `96f434a2cda2c8c544b76d2feacbd501c8e5d783`.

No SDK, governance, execution, transition, credential, custody, evidence, processor-selection, or publication-transition authority is created by this closure.