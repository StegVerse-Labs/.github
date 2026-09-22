# Public Repository Consumption Attribution Mirror Handoff

Updated: 2026-09-21T22:10:00-05:00
Repository: `StegVerse-Labs/.github`
Branch: `task/public-repository-consumption-attribution-001`
Goal Task ID: `PUBLIC-REPOSITORY-CONSUMPTION-ATTRIBUTION-001`
COSV task.v1: `20010010100000`
State: `ACTIVE / CHECKED_OUT / ATTRIBUTION_IN_PROGRESS`

## Goal

Attribute the September 2026 `StegVerse-Labs/.github` clone spikes against known StegVerse-controlled workflows and public repository events. Classify only what the evidence supports as internal automation, generic external indexing/scanning, or StegVerse-specific external consumption. Clone traffic alone must never be promoted to adoption.

## Canonical policy relationship

This goal is adjacent to the older repository-visibility policy in `docs/REPOSITORY_VISIBILITY_BOUNDARY_MIRROR_HANDOFF.md`. That policy remains useful for the public/private aperture rule and historical-disclosure rule, but it was not present in the current canonical Task Registry when this attribution work was admitted. This task therefore has its own canonical registry identity.

## User-observed traffic basis

The supplied GitHub Traffic screenshot for the 14-day window shows 34,000 clones, 8,089 unique cloners, 9 total repository views, and 4 unique visitors. This establishes a large clone/view asymmetry but does not identify cloners or prove human readership, external adoption, or downstream protocol use.

## GitHub API / connector limitation

The connected GitHub fetch surface does not expose `/traffic/clones`, `/traffic/views`, `/traffic/popular/referrers`, or `/traffic/popular/paths`; those requests are rejected by the connector allowlist before GitHub traffic data is returned. Exact per-day clone/referrer attribution therefore remains unavailable through this session's GitHub connector. Missing source identity remains UNKNOWN rather than being inferred.

## Known StegVerse-controlled activity

Observed `.github` workflow-run counts:

| Date | Workflow runs |
|---|---:|
| 2026-09-07 | 285 |
| 2026-09-08 | 426 |
| 2026-09-09 | 503 |
| 2026-09-10 | 217 |
| 2026-09-11 | 806 |
| 2026-09-12 | 461 |
| 2026-09-13 | 748 |
| 2026-09-14 | 640 |
| 2026-09-15 | 453 |
| 2026-09-16 | 288 |
| 2026-09-17 | 266 |
| 2026-09-18 | 490 |
| 2026-09-19 | 856 |
| 2026-09-20 | 214 |
| 2026-09-21 | 602 |

Total observed workflow runs across those 15 dates: 7,255.

### 2026-09-19
856 runs: KV AI Memory 394; Cross-Task Coordination 175; Purpose-Bound Worker 112; DeepSeek resident 111. Current workflow source proves KV AI Memory and Purpose-Bound Worker contain `actions/checkout`; Cross-Task Coordination and DeepSeek resident do not.

### 2026-09-13
748 runs: organization control plane 245; Heartbeat Worker 235; Deterministic Suite 234. Current workflow source for all three contains no `actions/checkout`.

### Explicit current-main clone producer

Current `.github/workflows/repository-hygiene-reusable.yml` contains `git clone --depth=1 https://github.com/StegVerse-Labs/.github.git .hygiene-control`. The introducing commit `b8674abfd3a6e4090de188d451448d233e4b47b8` is dated 2026-09-21, so it cannot explain the earlier 2026-09-19 spike.

## Repository event intensity

The repository commit API returned 300 commits dated 2026-09-13 and 290 commits dated 2026-09-19. These dates overlap the two visually largest unique-cloner peaks in the supplied screenshot. High change volume can plausibly stimulate CI, mirrors, scanners, indexers, or other automated consumers, but temporal correlation does not identify which class caused the traffic.

## Current classification

- `INTERNAL_AUTOMATION`: **EVIDENCED CONTRIBUTOR, NOT SUFFICIENTLY QUANTIFIED AS THE WHOLE EVENT.** StegVerse-controlled Actions activity is substantial and some workflows definitely check out/clone source. Several of the highest-volume workflow families on peak dates do not check out the repository, so raw workflow-run totals cannot be equated with clone counts.
- `GENERIC_EXTERNAL_INDEXING_OR_SCANNING`: **PLAUSIBLE / UNRESOLVED.** The clone-heavy, view-light pattern is compatible with generic machine indexing/scanning, especially around high repository-change volume, but no referrer or cloner identity is available here.
- `STEGVERSE_SPECIFIC_EXTERNAL_CONSUMPTION`: **EVIDENCE-CONSISTENT / NOT PROVEN.** The pattern is compatible with independent systems intentionally retrieving StegVerse material, but traffic counts alone provide no independent downstream identity, reuse, citation, dependency, fork, import, protocol request, or other adoption evidence.
- `UNATTRIBUTED_REMAINDER`: **UNKNOWN_NOT_AUTHENTICALLY_ATTRIBUTED.** Do not force the unexplained traffic into either generic scanning or StegVerse-specific consumption.

## Next discriminating evidence

1. Obtain authenticated GitHub Traffic clone/referrer/path data through an allowed owner surface or retained export.
2. Correlate exact clone counts with StegVerse jobs that actually perform checkout/clone operations, not merely workflow-run totals.
3. Search for independent public repositories, package manifests, citations, forks, imports, SDK manifests, or protocol requests that reference exact StegVerse canonical artifacts.
4. Preserve independently observed downstream consumers as separate evidence; do not backfill identity from clone volume.

## Authority boundary

Observation/attribution only. No repository mutation, credential, runtime, publication, governance, adoption, or external-consumer authority is granted. TV/TVC remains credential authority. GitHub traffic statistics are evidence inputs only.
