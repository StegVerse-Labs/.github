# Exact-source first-wave licensing follow-up — 2026-09-25

Canonical owner: `ECOSYSTEM-OPEN-SOURCE-STRATEGY-001` / COSV `20010010100000`.
Scope: evidence-only continuation of the merged first-wave audit, **not** a new goal, independent legal opinion, source-repository relicensing, or publication approval.

## Exact observed heads

| Repository | main HEAD observed | Source observations | Next verified predicate |
| --- | --- | --- | --- |
| `StegVerse-org/StegVerse-SDK` | `9cf1d69c770ea92048a0883adf6ff0dfa09797db` | Root MIT `LICENSE`, blob `b5b623afb77d40e5673d4075cfd4591251b802f0`; `pyproject.toml`, blob `5745f50c100b175e6850ff3ea8c64247f820ecc7`, declares MIT and direct requests, PyYAML, python-dotenv. Optional test extras refer to two pinned StegCore commits and one pinned commit each in core-lite and master-records. | Complete cross-repository dependency licenses and exact-package import/content SBOM; confirm optional/private dependencies are not implied public redistributables. |
| `StegVerse-Labs/ara-admissibility-interop` | `bb798d58af24c8dc64b7a509d2641f38fbbfbb33` | Root MIT `LICENSE`, blob `83ec0e7c01d663a0558a1fe4aaba45fd8833a01d`. `docs/dependency-policy.md`, blob `7fcca2e5d30545cdb6b0a15d3161a44987a841b3`, declares dependency-free default baseline with optional `jsonschema`. | Verify full git attribution/import provenance and distribution content; optional package/version and upstream rights before release. |
| `StegVerse-Labs/hybrid-collab-bridge` | `aa4094e76b24aa42b683835562e5b3d90daa7155` | Root `LICENSE` blob `1c4c28c7d0a0c74956cf9879c79e3839b26e83a0` grants MIT (2025 StegVerse). `LICENSE.txt` blob `5964d71d4b4e7843216233a86dc2d0aafa84dfbc` carries custom constitutional redistribution and paired-approval terms. README License section names only Constitutional License. | Native source-owner scope/rights clarification: [hybrid-collab-bridge#32](https://github.com/StegVerse-Labs/hybrid-collab-bridge/issues/32). No retrospective restriction of prior MIT grants; no OSI claim for custom conditions before review. |
| `StegVerse-Labs/continuity-vault-kit` | `6801ca76f935715b7dffc3bfe04fa7bd60e98062` | Root `LICENSE` blob `2b1d66612d6dbdd7c6756a5ae2516e941a924367` embeds MIT text in Markdown with unnamed copyright owner. | Establish exact rights holder, attribution and file-level coverage; check private material and imported dependencies before repackaging. |

## SDK optional exact-pinned Git dependency check

The following four **exact commit objects resolve** through connected GitHub at the time of this audit. Resolution and sampled Git commit author `StegVerse` do not prove ownership, a license grant, public accessibility or redistribution rights.

| Git dependency | Referenced SHA | GitHub visibility at review | Root LICENSE evidence |
| --- | --- | --- | --- |
| StegCore (governed-test) | `ef38410505b0ef3e84148892b1d6e3cdef20f300` | Private | No root LICENSE found by exact-path read on current default branch. |
| StegCore (manifold-test) | `99397392462b8e39a510ec6d9e543551270bd402` | Private | Same StegCore repository; exact historical file-level grant at each pinned commit remains unverified. |
| core-lite | `72bdb0f110031ccc2cd98b8ebb7c22b1ab7326f8` | Public | No root LICENSE found by exact-path read on current default branch. |
| master-records/orchestration | `03312236c115bc814024d700810391340648601f` | Private | No root LICENSE found by exact-path read on current default branch. |

The three package build files read expose different Python support floors: SDK >=3.9, StegCore >=3.11, core-lite >=3.11, and master-records >=3.11. Therefore optional extras must not be represented as universally installable on every SDK-supported Python version. This is an identified package-metadata compatibility check, **not** a test-run result. A missing root LICENSE is not evidence that no permissions exist elsewhere, and a license at HEAD would not by itself prove terms for the pinned historical SHA.

## Contributor and downstream rights evidence boundary

A sample of individual Git commits attributes StegVerse or StegVerse Bot; that is a source attribution observation, not a complete contributor census. The connected GitHub public fetch allowlist does not expose its contributors endpoint. No assignments, contractor rights, file-level imported upstream attestations, vendored asset inventory, patent clearance or complete dependency SBOM have been verified. Release decision remains `NOT_AUTHORIZED` until the relevant source owners document these predicates.

## Owner coordination

The hybrid license scope issue is a scoped clarification within this existing goal, not a second Goal Task ID. The separate clone-attribution owner continues independently. Preserve earlier LICENSE blobs and issue provenance; no source-owner license file was edited during this audit.

## September 25 — current upstream direct-license scope and generated-page hold

Source-only SDK [PR #333](https://github.com/StegVerse-org/StegVerse-SDK/pull/333) merged as `175c1fa11967d14986682a72efb4171afe40aece` from exact-head 12/12 passing CI. Root LICENSE reads through the connected GitHub app identify the current upstream direct-package grants, not the eventual resolved/version-frozen dependency SBOM:

| SDK baseline requirement | Current upstream license | LICENSE blob SHA | Remaining redistribution evidence |
| --- | --- | --- | --- |
| requests >=2.28.0 | Apache-2.0, `psf/requests` | `67db8588217f266eb561f75fae738656325deac9` | Exact resolved distribution, notices, patent terms and transitive components. |
| PyYAML >=6.0 | MIT, `yaml/pyyaml` | `2f1b8e15e5627d92f0521605c9870bc8e5505cb4` | Exact package version and applicable copyright/permission notice. |
| python-dotenv >=0.19.0 | BSD-style three-clause, `theskumar/python-dotenv` | `3a97119010ac82e15e917a69b7b8f9f59b5a4601` | Exact distribution, source/binary notice and SDK >=3.9 Python-compatibility testing against newer upstream releases. |

The four historical optional Git-pinned dependency LICENSE reads remain unresolved at their respective exact references: 404 cannot distinguish path absence from access limitations. SDK root MIT is not a blanket license for those packages or for automatically generated public DeepWiki content. Cognition's [current terms](https://cognition.com/legal/platform-terms-of-service), section 3.1, are customer-output-specific and do not establish rights in this public auto-indexed result for StegVerse. The 38-page raw generated text and citation-corrected quarantine derivative are audit artifacts only. Reuse of their actual prose/diagrams requires an attributable grant or rights-holder determination; source-only first-party wording is kept separate. Existing owner, no new release or license changes.
