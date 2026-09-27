# StegVerse staged open-source release policy — DRAFT FOR RIGHTS REVIEW

Goal Task ID: ECOSYSTEM-OPEN-SOURCE-STRATEGY-001 | COSV 20010010100000
Status: PROPOSED_SOURCE_ONLY — no new license grant, release, trademark authorization, governance authority or production deployment.

## Purpose
Clarify what developers may reuse while preserving distinctions between code rights, brand identification, official governance and runtime authority, sovereign personal information, commercial contracts and economic participation. The official ecosystem can accept independently implemented protocols without treating implementations as authorized governance nodes.

## Publication classes
- **Open-source code**: only when an exact scope and version carry valid OSI-compliant grant(s), full modifiable source and required notices. Commercial reuse and forks must remain permitted under those terms.
- **Public specification or documentation**: publication alone is not an open-source software license. Identify document copyright and any explicitly granted document reuse rights independently.
- **Official StegVerse identity**: names, logos, certification marks and service designations remain separately governed by a trademark-use policy. Avoid falsely implying endorsement of forks while honoring required license notices.
- **Official production authority**: publishing code does not provide credentials, resident claims/fences, canonical Master Records authority, InTr admission or organization governance membership.
- **Sovereign private information**: user KV contents, keys, private receipts, credentials, personal data and contractual access never become public merely because client implementations are open source.
- **Commercial services and economic assets**: hosting, support, service levels, infrastructure, token ownership and compensated participation are separate rights, subject to applicable law and contractual arrangements.

## Staged sequence and gates

**Stage 0 — freeze evidence and rights baseline.** Preserve exact source SHA, existing grants, release notes, available histories, contributor attestations, upstream origin and dependencies. Establish a per-repository matrix without conflating public visibility or GitHub license detection with legal entitlement. Existing downstream open-source permissions remain intact.

**Stage 1 — independently usable SDK, schemas and validators.** Audit StegVerse-SDK and ARA first. Establish exact release manifest, permitted third-party dependencies, optional private Git dependency behavior, build/test reproducibility and compatible notices. Public verification must not rely on private source for its claimed self-contained scope. Explicit owner authorization and repository-owned release workflow required before a new release or license change.

**Stage 2 — governance interfaces and reference verifiers.** Publish public protocol and evidence formats with portable reference implementations, separating protocol conformance from official adjudication and Master Records closure. Any change in standards governance follows existing canonical owners.

**Stage 3 — client and financial infrastructure.** Review MyKV, StegTalk, economic primitives and other selected components only after data/key isolation, export-safe secret scan, privacy and patent exposure analysis, commercial boundary review and relevant legal approval. Internal or private repositories must not become public as a side effect of inventorying.

## License-selection decision record (not preapproved)
MIT or Apache 2.0 may support permissive SDK/reference code; MPL 2.0 or AGPLv3 may be considered only when copyleft effects and dependency compatibility are intentionally assessed. Never add field-of-use, StegVerse-only, royalty-for-licensed-code or mandatory official-governance restrictions to a purported OSI-approved release. A separate trademark and official-service policy may distinguish authenticated official deployments from third-party forks without altering source permissions.

## Release authorization evidence
For each exact source release: rights-holder declaration and contributor/import audit; licensing and NOTICE compatibility; SBOM/security scan; reproducible tests and distribution manifest; explicit sign-off by owner and appropriate counsel; unchanged history of earlier grants; repository PR and exact-head validation; governed publication request and applicable InTr + Master Records closure when consequential. Only then tag/release under the authorized repository owner; separately register propagation verification for applicable public sites and wikis. Until all predicates pass, classify as CANDIDATE, not published.

## Independent work
Continue clone-attribution questions under PUBLIC-REPOSITORY-CONSUMPTION-ATTRIBUTION-001; this task only resolves future licensing ambiguity and preserves historical evidence. No new runtime, credential plane, device, scheduler or authority is introduced.
