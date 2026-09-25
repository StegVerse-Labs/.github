# First-wave open-source rights and dependency audit (source observations)

Goal: ECOSYSTEM-OPEN-SOURCE-STRATEGY-001 | COSV: 20010010100000
Observed: 2026-09-24. This is a repository-source review, not legal title verification, an authorization to relicense, or runtime/publication evidence.

| Candidate | Current observed license | Source/dependency observations | Contributor/ownership state | Disposition |
|---|---|---|---|---|
| StegVerse-org/StegVerse-SDK | Root MIT; pyproject declares MIT, version 1.3.0 | Core dependencies requests>=2.28, PyYAML>=6, python-dotenv>=0.19; optional governed-test and manifold-test directly pin three other Git repositories; their accessibility, license compatibility and dependency/redistribution terms need separate checks. requirements.txt self-references stegverse-sdk>=1.0.0; validate reproducible packaging. | LICENSE names StegVerse (2026), package metadata StegVerse. A sample recent commit attributes StegVerse. No exhaustive author census, contributor grants, vendor provenance, software bill of materials, or assignments verified. | EXISTING_LICENSE_OBSERVED / ADDITIONAL_RELEASE_NOT_CLEARED |
| StegVerse-Labs/ara-admissibility-interop | Root MIT (2026, StegVerse-Labs) | Root release-manifest reports release candidate 0.2.0, not evidence of publication closure. Broad docs, Python tools, schemas and CI require dependency/embedded-content scan before repackaging. | Sample commit StegVerse; neither full contributor inventory nor all imported code provenance verified. | EXISTING_LICENSE_OBSERVED / ADDITIONAL_RELEASE_NOT_CLEARED |
| StegVerse-Labs/hybrid-collab-bridge | Root LICENSE is MIT (2025, StegVerse); separate LICENSE.txt describes custom StegVerse Constitutional License (2026, StegVerse Labs/AaCT-E) requiring paired approval and preservation on redistribution. | Dual license texts are potentially inconsistent; clarify which governs which files, whether they are alternatives, and whether any code is subject to constraints incompatible with OSI open-source software. requirements-style-api lists FastAPI, Pydantic and Uvicorn; audit pinned transitive licenses before distribution. | Latest sampled commit attributed StegVerse Bot, not independent proof of rights or contributor agreement. | LICENSE_SCOPE_CONFLICT_REQUIRES_OWNER_REVIEW |
| StegVerse-Labs/continuity-vault-kit | Root LICENSE contains Markdown wrapper around MIT text and copyright year without named owner; GitHub reports Other/NOASSERTION. | Extremely broad source tree; security, credentials, generated files and third-party code must be scoped before any additional public release packaging. | Sample commit attributed StegVerse; full chain and contributing authors unverified. | LICENSE_FORMAT_AND_OWNERSHIP_REVIEW_REQUIRED |

## Evidence and limits

- SDK: https://github.com/StegVerse-org/StegVerse-SDK/blob/main/LICENSE and https://github.com/StegVerse-org/StegVerse-SDK/blob/main/pyproject.toml
- ARA: https://github.com/StegVerse-Labs/ara-admissibility-interop/blob/main/LICENSE and https://github.com/StegVerse-Labs/ara-admissibility-interop/blob/main/release-manifest.json
- Hybrid bridge: https://github.com/StegVerse-Labs/hybrid-collab-bridge/blob/main/LICENSE and https://github.com/StegVerse-Labs/hybrid-collab-bridge/blob/main/LICENSE.txt
- Continuity vault: https://github.com/StegVerse-Labs/continuity-vault-kit/blob/main/LICENSE

GitHub contributors endpoint is unavailable through the connected public fetch allowlist. Search-based recent commit snippets omit author fields; individually retrieved sampled commit objects are evidence of a few named commits only, not the complete contributor inventory or copyright assignment. Full commit history, third-party source headers, vendored assets, patents, employment/contractor agreements and import provenance are outstanding. Public license notices should not be unilaterally withdrawn. Do not reinterpret repository forks/clones as rights or adoption evidence.

## Independent remediation predicates

1. For each proposed release, produce an exact-commit code/content inventory and complete author-attribution ledger from reachable repository history, including coauthors, imported files and any original upstream licenses.
2. Produce an SBOM over direct, optional, transitive, vendored and generated dependencies; verify compatibility of the contemplated license and redistribution method.
3. Reconcile dual or ambiguous license files in the *source owner's* repository under documented copyright-holder authority; preserve old versions and commit history.
4. Inventory credentials, key materials, KV data and operational details. Exclude and rotate sensitive material as appropriate before authorizing publication of anything currently nonpublic.
5. Require attributable owner approval and legal review where IP chain, patents, entity ownership, economic rights or custom terms are uncertain. CI PASS is not legal approval.
