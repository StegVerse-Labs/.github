# Public Repository Consumption Attribution Mirror Handoff

Updated: 2026-09-26T21:59:00-05:00
Repository: `StegVerse-Labs/.github`
Branch: `task/public-repository-attribution-step-proof-20260927`
Goal Task ID: `PUBLIC-REPOSITORY-CONSUMPTION-ATTRIBUTION-001`
COSV task.v1: `20010010100000`
State: `ACTIVE / CHECKED_OUT / ATTRIBUTION_IN_PROGRESS`

## Goal

Attribute the September 2026 `StegVerse-Labs/.github` clone spikes against known StegVerse-controlled workflows, repository events, and independently inspectable downstream references. Classify only what evidence supports as internal automation, generic external indexing/scanning, or StegVerse-specific external consumption. Clone traffic alone must never be promoted to adoption.

## Canonical identity and authority

This remains the existing canonical task. No duplicate attribution task, runtime, credential plane, device requirement, or execution authority is introduced. COSV remains `20010010100000`. Observation and attribution have `authority_effect=NONE`; TV/TVC remains credential authority and traffic statistics remain evidence inputs only.

## Latest user-observed traffic basis

The latest supplied GitHub Traffic screenshots identify the repository as `StegVerse-Labs/.github` and show the rolling 14-day graph spanning 2026-09-10 through 2026-09-23:

| Metric | Latest snapshot |
|---|---:|
| Clones | 37,188 |
| Unique cloners | 7,662 |
| Total views | 24 |
| Unique visitors | 8 |

This supersedes the earlier screenshot retained by this handoff. The ratio is approximately 4.85 clone events per reported unique cloner. GitHub's unique-cloner metric is a rolling-window statistic and does not identify human individuals, organizations, bots, CI jobs, scanners, mirrors, or downstream adopters.

## GitHub Actions reconciliation for the same date window

GitHub Actions API reads were performed date-by-date for 2026-09-10 through 2026-09-23 to avoid large-window pagination ambiguity. Current-main source search identifies 25 workflow files containing `actions/checkout` and/or an explicit `git clone`. The table counts exact workflow runs whose workflow path maps to one of those current source-declared producer paths.

| Date | All workflow runs | Runs mapped to current checkout/clone producer paths |
|---|---:|---:|
| 2026-09-10 | 217 | 2 |
| 2026-09-11 | 806 | 42 |
| 2026-09-12 | 461 | 33 |
| 2026-09-13 | 748 | 10 |
| 2026-09-14 | 640 | 158 |
| 2026-09-15 | 453 | 25 |
| 2026-09-16 | 288 | 33 |
| 2026-09-17 | 266 | 69 |
| 2026-09-18 | 490 | 362 |
| 2026-09-19 | 856 | 566 |
| 2026-09-20 | 214 | 129 |
| 2026-09-21 | 602 | 391 |
| 2026-09-22 | 364 | 232 |
| 2026-09-23 | 231 | 121 |
| **Total** | **6,636** | **2,173** |

The 2,173 figure is **not** a clone count. It is an exact count of workflow runs mapped to workflow paths whose current source declares checkout/clone behavior. A run can stop before the clone step, a single run can perform more than one retrieval, historical workflow content can differ from current main, and GitHub's traffic statistic can include activity not represented by Actions. It therefore bounds demonstrable first-party clone-capable activity without assigning one traffic clone to each run.

### 2026-09-19 peak

The strongest clone spike overlaps a repository day with 856 Actions runs. Exact run enumeration finds 566 runs mapped to current source-declared checkout/clone producer paths. The largest contributors were:

- `.github/workflows/validate-kv-ai-memory-resident.yml`: 394 runs
- `.github/workflows/validate-purpose-bound-worker-derived-lifetime.yml`: 112 runs
- `.github/workflows/test3-richard-seam-acceptance.yml`: 24 runs
- remaining mapped producer paths: 36 runs

This is strong evidence that internal automation contributed materially on the peak date. It is not evidence that all or most of the approximately 6,000 graphed clone events that day came from those runs.

### Explicit repository clone producer

`.github/workflows/repository-hygiene-reusable.yml` contains an explicit clone of `StegVerse-Labs/.github`. Its introducing commit `b8674abfd3a6e4090de188d451448d233e4b47b8` is dated 2026-09-21, so this producer cannot explain the earlier September 13 or September 19 peaks by itself.

## Repository-event correlation

Prior retained evidence records 300 commits on 2026-09-13 and 290 commits on 2026-09-19. Those dates overlap the two visually largest unique-cloner peaks in the earlier supplied graph. High source-change intensity can stimulate CI, mirrors, scanners, indexers, and other automated consumers, but temporal overlap does not identify causation or consumer identity.

No release event has been authenticated as the primary cause of the September 19 clone spike in this attribution pass.

## Public downstream reference search

Public GitHub code search located verifiable StegVerse references outside the primary `StegVerse-Labs` and `StegVerse-org` repositories, including:

- `AdmittedCode/provider-harness`: a portable StegVerse review demo that states it can review a StegVerse-produced packet without importing or running the StegVerse runtime.
- `AdmittedCode/admissibility-receipt`: generates and verifies `stegverse.admissibility_receipt.v1` artifacts.
- `AdmittedCode/coherency-scanner`: contains StegVerse-related governance coherency material.
- `Data-Continuation/core-lite`: contains `.stegverse` identity material and a StegVerse worker.
- `AaCT-E/demo`: documents a developer path via the StegVerse SDK.

These are concrete, independently inspectable cross-organization references. This task does **not** infer that the organizations are independent of StegVerse ownership/control, that they account for any particular clone event, or that they constitute market adoption. Their evidentiary status is `PUBLIC_DOWNSTREAM_REFERENCE_VERIFIED / ORGANIZATIONAL_INDEPENDENCE_NOT_AUTHENTICATED`.

Public web search also returns StegVerse-controlled publication and package surfaces such as `stegverse.org`, the StegVerse LinkedIn presence, and PyPI distribution. Those establish discoverability and distribution paths, not independent downstream adoption.

## Current classification

- `INTERNAL_AUTOMATION`: **CONFIRMED MATERIAL CONTRIBUTOR / NOT A COMPLETE ATTRIBUTION.** 6,636 total Actions runs occurred in the graph window and 2,173 map to current source-declared checkout/clone producer paths. This does not equate runs to clone events.
- `GENERIC_EXTERNAL_INDEXING_OR_SCANNING`: **PLAUSIBLE / UNRESOLVED.** The clone-heavy, view-light pattern remains compatible with automated retrieval, but no authenticated referrer/cloner identity is available.
- `STEGVERSE_SPECIFIC_EXTERNAL_CONSUMPTION`: **PUBLIC REFERENCES EXIST / TRAFFIC ATTRIBUTION NOT PROVEN.** Cross-organization references are visible, but no evidence binds them to the GitHub Traffic counts.
- `UNATTRIBUTED_REMAINDER`: **UNKNOWN_NOT_AUTHENTICALLY_ATTRIBUTED.** The unexplained traffic is not forced into either scanning or adoption.

## Remaining discriminating evidence

1. Obtain authenticated owner-visible clone/referrer/path data or a retained export if an allowed interface becomes available.
2. For peak-date producer workflows, inspect historical workflow bytes and step outcomes when necessary to distinguish a workflow run from an actually reached clone step and to identify runs that perform multiple retrievals.
3. Continue searching public package manifests, dependency graphs, citations, forks, imports, SDK manifests, and protocol requests; record exact downstream identities separately from clone counts.
4. Preserve organizational ownership/independence as UNKNOWN unless independently authenticated.
5. Do not convert traffic magnitude, code-search references, or public distribution into an adoption claim.

## Authority boundary

Observation/attribution only. No repository mutation beyond this evidence update, credential, runtime, publication, governance, adoption, or external-consumer authority is granted by the traffic evidence. GitHub Actions and source/CI evidence do not become sovereign runtime authority.


## 2026-09-27 original checkout-step follow-up

The 2026-09-19 UTC PR #2314 head `0cea2567e535eb89e806aa46242b3a11a88b257c` provides **two original step-verified specimens**, not a census of all 566 peak-day source-path-mapped runs.

| Workflow | Historical source | Original run/job | Observed original checkout |
|---|---|---|---|
| KV AI Memory | At both September 19 source commits `12c2527b1397470a5d606b0739ae0422e16530d2` and `aa4bf6fd0b39ae797ea9a49f86db17cc546e1be5`, blob `02792141635c18baba770d115c29eb7f753ea28a` declares `actions/checkout@v4`. | [run 35476732113](https://github.com/StegVerse-Labs/.github/actions/runs/35476732113), job `105987139410` | Checkout step SUCCESS; retained log records `Syncing repository: StegVerse-Labs/.github`, `Fetching the repository` and `Checking out the ref` at 23:39:57–59Z. |
| Purpose-Bound Worker | Earlier historical blob `8cd5a5471269552f1a45463e4fa59a5ff7839ac2`; later `0e3e11a6aa1e534956edb7365914b851c2df61e1`; both declare `actions/checkout@v4`. | [run 35476732118](https://github.com/StegVerse-Labs/.github/actions/runs/35476732118), job `105987139470` | Checkout step SUCCESS; retained log records repository sync, fetch and ref checkout at 23:39:56–57Z. |

These original job logs distinguish **actually reached checkout steps** from current-source declarations. The purpose-bound workflow changed during the sampled day, so current-main source cannot stand in for exact historical bytes. The connector's commit-run listing is first-page PR-triggered only, and run-job listing is first-page/latest-attempt only. Do not extrapolate two observed successes to 566 mapped peak-day runs, count them as two GitHub Traffic clones, or infer cloner identities.

### Newly inspected public references

- [pingoleon150-ctrl/agenttrace](https://github.com/pingoleon150-ctrl/agenttrace/blob/main/ledger/repos/github/stegverse-labs/.github.json) explicitly records `StegVerse-Labs/.github`, 22 observations, last checked August 18, and `no_high_confidence`. It is a public repository-monitoring artifact **predating** the September traffic window, not evidence of September clones or adoption.
- [szabgab/pydigger-data](https://github.com/szabgab/pydigger-data/blob/main/data/pypi/st/stegverse-sdk.json) indexes PyPI metadata for `stegverse-sdk` 1.0.13 and its canonical SDK repository. This is package metadata indexing, not an installation or authenticated downstream use.
- [StegGhost/entity-sandbox-runner](https://github.com/StegGhost/entity-sandbox-runner/blob/main/README.md) declares a StegVerse SDK-bound sandbox route. Actual independent organizational ownership, live usage and September clone contribution remain unverified.

Code search does not exhaust dependency graphs, forks, package downloads, citations or protocol requests. No source authenticates a September traffic consumer. Preserve `UNKNOWN_NOT_AUTHENTICALLY_ATTRIBUTED` for the remainder. Next: obtain fully paginated peak-day runs and original per-attempt job steps/logs, independently inspect downstream ownership and usage, and seek authenticated owner-visible traffic exports. Observation and attribution only; no new authority.
