# ICV standalone commit-time governance product — portability contract candidate

Date: 2026-09-25. Source-only commercial architecture proposal under existing economic-roadmap owner `ECOSYSTEM-ECONOMIC-WHITEPAPER-GATED-ROADMAP-001`, observed canonical Registry generation 245 (PROPOSED; no WorkerCoordinator claim). **This document does not assign ICV implementation ownership, change another repository, publish an artifact, or assert authenticated production execution.**

## User-directed product boundary

Infrastructure Continuity Ventures (ICV) is a self-contained product and sales surface for **portable commit-time governance plus the SDK**. The deployed customer's runtime must not require the ongoing operation or availability of other StegVerse organizations, hosted services, cross-org GitHub repositories, task registry, Publisher, Site, or a separate user-operated computer. A pinned upstream source and independently verified package may be reused; source provenance is not a runtime service dependency. Optional explicit federation is a separately authorized customer choice.

## Existing separately evidenced packages

| Layer | Named source/distribution | What its verified source supports | What is NOT established |
|---|---|---|---|
| Canonical decision runtime | `StegVerse-Labs/StegCore` StegGate product v0.3.0; README advertises distribution `stegverse-stegcore`, import `stegcore`, CLI `steggate`, HTTP `/v1/evaluate` | Python 3.11+, one canonical three-layer evaluator; ALLOW/DENY/REVIEW/FAIL_CLOSED and reason/hash/predicate evidence; documented local API/CLI/HTTP identity independent of hostname. | A portable evaluator alone is not a customer's enforced commit hook, authenticated identity/standing issuance, custody, production consequence execution, or proven live cross-org resident integration. Packaging index availability was not independently checked. |
| Portable manifest ingress and SDK | `StegVerse-org/StegVerse-SDK`; `pyproject.toml` version 1.3.0, distribution `stegverse-sdk`, Python >=3.9; `stegverse/portable_packages.py` S/NS archive verification | Manifest-selected processor/route and return depth, generic ingestion and local tooling. S/NS package catalog asserts one-host topology, but its two release URL and SHA-256 slots are null in observed source; `download_active` is false on this evidence. | An existing SDK installation is not proof that its default canonical governed route is installed or that the complete SOUTH external lifecycle can close without remote InTr, Master Records, Publisher or far-side transitions. Optional pinned Git test dependencies require separate rights/compatibility review; never treat extra installation as mandatory. |
| ICV scoped offline continuity consumer | `Infrastructure-Continuity-Ventures/infrastructure-continuity-core-lite` | Standard-library-only pinned ICV engine/profile validation and deterministic local receipt/portable record for jurisdiction-bound claims; no external services or extra machine required for its declared scope. | It does not contain StegGate governance authority, SDK processing semantics, live TV/TVC standing, or canonical durable custody. It must not be relabeled as the whole commit-time product. |

StegCore `pyproject.toml` currently declares `name=stegcore` v0.3.0 while README advertises PyPI distribution `stegverse-stegcore`. Verify the exact published package identity/version before customer install instructions or release; do not silently assume the metadata and distribution name match.

## Proposed deployable ICV product package (not yet assembled)

One independently installable **ICV Governance Gateway** bundle, versioned as its own product without modifying canonical upstream owner identity:

1. **Pinned StegGate runtime** from the canonical StegCore owner; run the same evaluator for CLI, HTTP, local MyKV and network adapters. No forked policy/admissibility semantics.
2. **Pinned StegVerse SDK** for source-native manifests, deterministic processing route resolution, explicit evidence projections and return assembly. A standalone `LOCAL_ICV_GOVERNED` route (name illustrative until owner registration) must be *actually implemented, versioned and tested*; no silent fallback to the remote canonical-governed route.
3. **ICV engine/workflow/core-lite adapter**, only for ICV-specific asset/jurisdiction transitions; preserve its distinct deterministic-product-evidence authority boundary.
4. **Explicit customer-controlled authority/credentials** with independently verifiable, scope-, target- and time-bound evidence; integrate the canonical TV/TVC/SPE contracts where required and authenticate locally without making a remote StegVerse organization a required availability dependency. No invented signer or simulated standing accepted as production.
5. **Local, append-only durable evidence store and reconstruction/export interface** that preserves original ingress, versioned policy, decision, current-state bindings, executor commit result when observed, and immediate predecessor integrity. This is an ICV product-local custody implementation only if separately admitted as compatible with canonical receipt semantics; do not mislabel it as central Master Records or mint Master Records closure without the authentic service/contract.
6. **A customer-side commit gate and bounded adapters**, so evaluation is actually invoked immediately before a consequential write (git, CI merge, infrastructure change API, database mutation, or industrial approval, each separately scoped). Re-check current policy, standing, target and evidence; fail closed on unknowns/stale binding; only customer-approved execution continues after ALLOW. Produce separate observed outcome and custody receipts; a successful decision never stands in for execution.
7. **Optional network boundary** protected by customer TLS/authn/authorization, with customer-approved remote ingress and egress; optional separately priced federation/updates/StegVerse external services. Disconnect must not alter local governance outcome for configured offline operations.

### Actual placement

- **Single customer host or server:** install ICV Gateway, SDK and the canonical StegGate runtime on that host, attach its commit adapters to authorized customer systems, and store receipts in customer-controlled local custody. One physical machine may run isolated local processes. No mandatory second device or cross-org hosted control plane.
- **Customer network:** expose a narrowly scoped authenticated evaluation endpoint on the customer-controlled host; the network calls the installed Gateway before authorized commits. Never require installing StegGate on every client.
- **MyKV:** retain private customer state, consented manifest inputs and receipt references; call a trusted installed local/device-capable Gateway when available. A browser-only KV entry or iPhone does not imply Python 3.11/SDK/StegGate executes natively on iOS. Native iPhone packaging requires separate target-compatible implementation and actual installation tests; remote customer-controlled gateway access, when explicitly selected, is a different mode.

## Portable and commercially releasable acceptance test

1. On a clean **single supported host**, install only customer-delivered, pinned ICV Gateway + StegGate + SDK + declared local runtime dependencies; demonstrate **no runtime network traffic** to other StegVerse organizations.
2. Offline identity, package-hash and policy-version verification, same semantics across local CLI and HTTP, exact original manifest and fresh commit-state binding.
3. Exercise ALLOW, DENY, REVIEW, FAIL_CLOSED and tampered/missing/stale standing; prove no executor is called on non-ALLOW.
4. With a real customer-owned bounded test executor, prove exactly one permitted commit, separately observed side effect, replay refusal and durable local predecessor-linked receipt reconstruction from another process on the **same physical host**.
5. Prove a clean reinstallation and independent read-only receipt verifier can reconstruct retained evidence after process restart; simulate remote GitHub/StegVerse-hosted services unavailable.
6. Scope and verify network authn/authorization, TLS, storage permissions, operational maintenance and upgrade/rollback without altering pinned historical receipts.
7. Resolve upstream code redistribution and historical commit-license rights before distributing proprietary or mixed-license bundles; existing SDK MIT declaration does not clear optional downstream Git dependency rights.
8. Separately verify any **federated** SDK SOUTH lifecycle or central Master Records claims with original far-side evidence; do not make external Publisher/InTr mandatory in offline-local SKU.

The existing ICV core-lite is portable for **its narrow deterministic evidence scope**. The complete user-requested portable governance + SDK product is **NOT_YET_PROVEN_AS_ONE_DISTRIBUTION** until these tests and native owner authorizations complete. Marketing may describe current offline evidence verification honestly, but must not assert end-to-end customer commit enforcement in production before its test.

## Ownership / roadmap boundaries

- StegCore owns the StegGate evaluator and its canonical semantics; the SDK owner owns manifest semantics. ICV packages released upstream components without redefining them. ICV owner must register/claim its native adapter and customer commit gate under the central collision/authorized workflow before mutation.
- Existing economic-roadmap source PR #2730 may describe the envisioned sale; Publisher #72, Site #1458, 16 technical benchmarks and current registry/COSV are not altered by this proposal.
- The product commercial surface is ICV; other StegVerse organizations may be optional source and federation partners **but not runtime prerequisites**. A release must freeze upstream source with verifiable redistribution rights, reproducible install, local operation and independently retained evidence.


## Original native-source continuation — 2026-09-25 (separate owner, not a distributed product)

Canonical central collision/admission request: [StegVerse-Labs/.github#2731](https://github.com/StegVerse-Labs/.github/issues/2731). Native ICV issue: [ICV infrastructure-continuity-engine#2](https://github.com/Infrastructure-Continuity-Ventures/infrastructure-continuity-engine/issues/2). Draft ICV source-only adapter: [ICV engine PR #3](https://github.com/Infrastructure-Continuity-Ventures/infrastructure-continuity-engine/pull/3). This is a source test candidate, not Task Registry registration, authentic owner checkout, or production integration. It imports installed canonical SDK and StegCore, refuses an absent trusted verifier and incorrect local route, retains an ICV-only predecessor-linked journal, and tests adapter behavior with explicit doubles. No original credential proof, authenticated customer commit, verified installed local route, independent checkpoint, rights-cleared bundle or production release has been observed.

Exact rights metadata reconfirmed against existing open-source owner `ECOSYSTEM-OPEN-SOURCE-STRATEGY-001` (COSV `20010010100000`): the SDK current root is MIT, optional Git extras' pinned history/redistribution rights are unresolved; StegCore has no retrievable root LICENSE on current main. `StegCore/pyproject.toml` names `stegcore==0.3.0`, whereas README advertises `stegverse-stegcore`. `StegVerse-SDK/pyproject.toml` names `stegverse-sdk==1.3.0`; externally indexed PyPI release 1.0.13 is not the current source package. No package artifact equivalence or redistribution right may be inferred. A clean pinned install is therefore a release prerequisite, not a completed task.
