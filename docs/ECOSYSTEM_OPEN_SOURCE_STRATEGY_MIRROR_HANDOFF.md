# Ecosystem Open Source Strategy — Mirror Handoff

Goal Task ID: `ECOSYSTEM-OPEN-SOURCE-STRATEGY-001`
COSV: `task.v1 [L R U I V G O C M T B E A P] = 20010010100000`
Coordination: `ACTIVE / CHECKED_OUT` — verified main Registry generation 236 before successor work; PR #2581 merged 2026-09-23T00:09:23Z as 7818050f67c8192962c1a8fcde3301dd3f45d008. Source-only rights and policy successor in current PR; do not treat as runtime or release authority.
Owner repository: `StegVerse-Labs/.github`
Canonical registry: `data/canonical-task-registry.json`
Sharded task record: `data/canonical-task-records/ECOSYSTEM-OPEN-SOURCE-STRATEGY-001.json`
Inventory: `data/open-source-repository-licensing-inventory.json`

## Purpose and release boundaries
Establish permission clarity early for code others can inspect or fork. Public visibility does not imply open-source permission. Separate OSI-licensed software from StegVerse trademarks and official authority, proprietary operations, personal KV data, credentials, and patent-sensitive material. Existing license grants are not unilaterally revoked. Open-source licenses permit downstream commercial use; no StegVerse-only use restriction may be attached to OSI-covered code.

## Verified source discovery — 2026-09-22
GitHub repository search returned 119 StegVerse-Labs entries across two pages. Snapshot records 46 public, 70 private and 3 internal repositories. As of 2026-09-24 all 119 GitHub license metadata records have now been read through authorized connector access: 2 SPDX MIT, 6 Other/NOASSERTION, 111 with no detected license. Only 46 public repository rows appear in the public inventory; the 73 nonpublic entries are aggregated to avoid leaking private repository names. GitHub classification is not file-level or legal-title verification. Six selected root-license paths were inspected: five license files found, one absent at common root names. Metadata and root text are not copyright or contributor-rights verification.

## Next audit actions
1. The 119-entry metadata census is complete; continue source-level licensing and provenance audits on selected release candidates, and expand organization coverage under separate access-scoped inventories.
2. Inspect actual LICENSE/NOTICE files, SPDX source headers, package manifests, submodules, generated code, contributor history and third-party dependencies for proposed first-wave SDK, schema and verification repositories. Record evidence links and responsible copyright holders; distinguish organizational repository ownership from copyright ownership.
3. Preserve historical licensing and commit dates for clone/reuse ambiguity, but keep traffic attribution independently owned by PUBLIC-REPOSITORY-CONSUMPTION-ATTRIBUTION-001.
4. Draft stage gates and license matrix after the rights audit: SDK/interfaces and verification first, governance reference protocols second, client/financial infrastructure only after separate privacy/security/IP review. Include a commercial services and StegVerse trademark policy; obtain counsel review where ownership, patents, tokens, or existing grants require it.
5. Change licenses only on repository-owned branches after rights review; no automatic bulk relicensing. Publish only after tests, approvals, explicit release evidence and canonical custody prerequisites.

## Authority and evidence
Registry and COSV coordinate the work only; no WorkerCoordinator claim/fence, runtime execution, InTr approval, Master Records closure, source deployment, publication or licensing permission is asserted. TV/TVC only for credentials. No connected-device prerequisite. Maintain `README.md` and this handoff each implementation change.

## Current state
PR #2581 is verified merged, and the source inventory is on main. All 119 repository metadata checks are complete. Initial first-wave license text and dependency triage is documented in `docs/OPEN_SOURCE_FIRST_WAVE_RIGHTS_AUDIT.md`; full contributor chain, third-party rights, and owner release approval remain unverified. Draft policy is `docs/STEGVERSE_STAGED_OPEN_SOURCE_RELEASE_POLICY_DRAFT.md`. Neither document authorizes relicensing or publication.

## Root LICENSE findings and first-wave triage

- `ara-admissibility-interop`: root MIT License, copyright notice `StegVerse-Labs` (2026). Candidate for source/contributor/third-party audit, **not** rights-cleared.
- `Fin-Co`: root declares Apache 2.0 (GitHub detection: Other); inspect completeness and proprietary financial interfaces before any release change.
- `hybrid-collab-bridge`: root MIT text, copyright `StegVerse` (2025); rights chain still unverified.
- `continuity-vault-kit`: GitHub Other; root LICENSE includes Markdown/code-fence formatting and unnamed copyright owner; normalize only after rights confirmation.
- `Trumpality`: root declares CC BY-SA 4.0; do not call its software OSI-open-source merely from this declaration.
- `Randolph_Geneaology_Hub`: GitHub Other but no LICENSE / LICENSE.md / LICENSE.txt at root; inspect subdirectories and history separately.

No source repository was relicensed, no legal owner independently verified, no release published, and no outside reuse identity inferred from clones.

## 2026-09-24 source continuation

Reconciled against main Registry generation 240; proposed generation 241. Successor branch `feat/open-source-strategy-rights-audit-20260924` contains an aggregate-safe 119-repository metadata census (46 public, 70 private, 3 internal; 2 SPDX MIT, 6 Other, 111 without detected license). The first-wave SDK/ARA/hybrid-bridge/continuity-vault source audit discovered an additional restrictive custom `LICENSE.txt` beside the hybrid bridge's root MIT `LICENSE`; that scope contradiction requires the source owner's review. SDK optional test extras refer to Git-based dependencies whose availability and grants must be reviewed. Sampled commits are not a complete authorship census. Full ownership verification: zero. Release-policy draft prepared but neither published nor approved. No licenses were changed and no private repository names were added to the public inventory.

Exact evidence: `data/open-source-repository-licensing-inventory.json`, `docs/OPEN_SOURCE_FIRST_WAVE_RIGHTS_AUDIT.md`, `docs/STEGVERSE_STAGED_OPEN_SOURCE_RELEASE_POLICY_DRAFT.md`. Reconcile only validated source and exact-PR evidence into task state; any consequential release remains governed by existing InTr and Master Records.

## PR #2703 validation and custody

Draft PR: https://github.com/StegVerse-Labs/.github/pull/2703. Initial exact-head STCM witness source-registration validation found a README replacement regression: a preceding canonical STCM task reference was lost. The README was restored byte-for-byte from the PR base/current main and the new open-source section **prepended**, preserving the STCM and all other existing sections. Added `tests/test_open_source_strategy_inventory.py` checking counts, public-only inventory rows, registry/shard equality and release nonclaim. These changes are source-validation work only; record exact-head workflow verdict before merging. A stale PR validation run is not evidence of current head. No WorkerCoordinator, InTr, Master Records or published-release receipt has been observed.

## Verified merge readback — September 24, 2026

Source-only census and rights-review [PR #2703](https://github.com/StegVerse-Labs/.github/pull/2703) merged as `57ff52b5ba23fd8df2b727471bdb25f17eb2558c` from exact validated head `4d41365bfcf1f664eba29dddf44474fede5c17ba`. All six applicable pull-request workflows passed, including STCM witness task-registration validation after the README preservation repair. Canonical main Registry generation 241 includes the complete metadata census, rights triage, draft policy and unchanged ACTIVE/CHECKED_OUT COSV. The custom-license ambiguity, comprehensive contributor and third-party audits, copyright-holder authorization and legal review remain open. No licensing change, hosted runtime, publication, or new release is claimed. `tests/test_open_source_strategy_inventory.py` is committed; the six passing workflows are not asserted to have executed that specific new test.

## 2026-09-25 SDK public DeepWiki discovery pilot — review-only

Registry generation 243 read back on 2026-09-25: existing open-source goal `ECOSYSTEM-OPEN-SOURCE-STRATEGY-001`, COSV `20010010100000`, remains ACTIVE / CHECKED_OUT. The original SDK public developer-wiki goal `SDK-PUBLIC-DEVELOPER-WIKI-001` is RETIRED / COMPLETED; its historical served-body observation and public `https://sdk.stegverse.org/` publication **predate** the new DeepWiki pilot. The exact repository-local wiki builder, tests, Pages workflow and six-source manifest were inspected. Independent new source-linked pilot: `docs/OPEN_SOURCE_SDK_DOCUMENTATION_PILOT_20260925.md` on documentation-only branch `docs/open-source-sdk-dependency-pilot-20260925` (PR/merge/CI not yet established). GitDiagram and owner-supplied DeepWiki screenshots were cross-checked against manifest, Universal Entry, transition-table, Site processing, Publisher and execution-boundary source. SDK checked-in joint boundary JSON currently reports VERIFIED and status-only propagation allowed with all production/release/execution/custody/admissibility expansion flags false; no fresh live propagation is inferred. Official current DeepWiki docs require both `repo_notes` and complete nonempty `pages`, with only enumerated pages retained, so the previously suggested repo-notes-only configuration must **not** be used. Full current DeepWiki page inventory and Markdown export remain unavailable through this execution context (no DeepWiki MCP connector; direct DNS to its public endpoint failed). Do not assume whole-wiki import or deploy. Integrate only vetted exported Markdown through the existing SDK-owned wiki builder and an applicable existing publication owner; do not re-open retired goal or duplicate the SDK wiki. Open-source contributor/third-party rights and owner release approval remain separate outstanding work. No Devin installation required.

### Draft pilot PR and exact-head validation

[Documentation-only draft PR #2713](https://github.com/StegVerse-Labs/.github/pull/2713) opened for the source-linked matrix and preserved README/handoff additions. Initial exact head `4cf428369c213a05b8b8a031b97e27511f684bab`; two early applicable workflow observations (KV AI Memory Resident Binding, validate-deepseek-resident) were `in_progress` at inspection. This handoff addition changes the PR head; recheck **new exact head** workflows before claiming validation or merging. No PR merge, live DeepWiki export, `.devin/wiki.json` installation, new SDK Pages deployment, release or propagation proof is established.

## 2026-09-25: public SDK DeepWiki export captured — later evidence supersedes earlier access limitation

Retain existing owner `ECOSYSTEM-OPEN-SOURCE-STRATEGY-001` / COSV `20010010100000`, ACTIVE/CHECKED_OUT at last authoritative Registry generation 243. SDK source-only draft [PR #322](https://github.com/StegVerse-org/StegVerse-SDK/pull/322) added a no-auth read-only public DeepWiki MCP exporter and a seven-to-ninety-day review artifact retention correction. Actual [GitHub Actions run 36104137361](https://github.com/StegVerse-org/StegVerse-SDK/actions/runs/36104137361) passed 3 parser/nonpublishing tests, fetched both structure and full contents from the official MCP, and uploaded [artifact 10850037472](https://github.com/StegVerse-org/StegVerse-SDK/actions/runs/36104137361/artifacts/10850037472). The returned 38-page hierarchy contains 8 root + 30 nested pages, matched one-for-one by all 38 full-text section headers, no duplicates, omissions, or extras **relative to the returned structure**. SDK branch retains a source-linked `docs/deepwiki-review/INDEX.md` with all titles, sha256, and artifact references; raw full text remains review-only artifact pending legal/source correctness checks. Current official `.devin/wiki.json` standard explicit page limit is 30; do not truncate 38 existing pages to steer generation. Keep auto-generated DeepWiki unchanged and adapt only the existing SDK Pages builder after verified review. Original developer wiki remains historically RETIRED/COMPLETED; no new Pages deployment/merge/release/propagation established by this documentation pilot. Central documentation draft [PR #2713](https://github.com/StegVerse-Labs/.github/pull/2713) remains separate; exact new head validation and existing-owner approval required. No Devin installed, no extra runtime or device.
