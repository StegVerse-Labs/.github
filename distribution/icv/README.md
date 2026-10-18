# ICV distribution: pinned sources, offline lifecycle, compatibility matrix

Workstream B of [StegVerse-Labs/.github#3183](https://github.com/StegVerse-Labs/.github/issues/3183)
(ICV commercial distribution), built by Lane A under
[StegVerse-org/.github#165](https://github.com/StegVerse-org/.github/issues/165).
DRAFT. Non-authorizing: no release, publication, entitlement, legal
determination or customer-runtime claim.

## Files

| File | What it is |
|---|---|
| `package-pins.v1.json` | Package → source `repo@commit`, package-root tree SHAs, per-file git blob SHAs, manifest blob SHAs, declared license with the citing file and blob, rights-clearance state. |
| `compatibility-matrix.v1.json` | Package × declared Python/OS/runtime, what CI runs, what was observed on the Lane A box. |
| `../../scripts/icv_distribution_offline_install.py` | Stdlib-only acquire → verify → offline install / upgrade / uninstall, one receipt per step. |
| `../../tests/test_icv_distribution_offline_install.py` | Hermetic tests (synthetic bytes, no network) and pins/matrix consistency. |

## Where the pins come from

Every SHA was read through the GitHub connector on 2026-10-18 (get_branch,
get_tag, get_git_tree, get_file_contents, list_releases). Package names come
only from #3183, the repo-standards ICV census, the Site ICV catalog mirror
(`data/icv-commercial-catalog-public.json`) and readable manifests.

| Package | Source | License as declared | Rights state |
|---|---|---|---|
| stegverse-sdk 1.3.0 | StegVerse-org/StegVerse-SDK@291ad15b | MIT (`LICENSE` b5b623af; `pyproject.toml` 69a2dc2d) | CLEARED_AS_DECLARED (not a legal determination) |
| stegverse-sdk 1.0.12 | StegVerse-org/StegVerse-SDK@04f77473 (tag v1.0.12) | MIT (`LICENSE` b5b623af; `pyproject.toml` 538d5dd9) | CLEARED_AS_DECLARED |
| stegcore 0.3.0 (`steggate` CLI) | StegVerse-Labs/StegCore@2f7f426c | UNKNOWN_NOT_AUTHENTICALLY_OBSERVED (no LICENSE; candidate doc says "NO GRANT") | NOT_CLEARED → FAIL_CLOSED |
| stegverse-core-lite 0.9.0 | Data-Continuation/core-lite@72bdb0f1 (pinned by the SDK `governed-test` extra) | UNKNOWN_NOT_AUTHENTICALLY_OBSERVED | NOT_CLEARED → FAIL_CLOSED |
| governance-observatory 0.1.0 | StegVerse-Labs/governance-observatory@11eae39a (private) | UNKNOWN_NOT_AUTHENTICALLY_OBSERVED | NOT_CLEARED → FAIL_CLOSED |

The seven Infrastructure-Continuity-Ventures repositories are not readable
through the declared path (TVC read grant), so no ICV byte is pinned:
FAIL_CLOSED `ICV_REPO_BYTES_NOT_AUTHENTICALLY_READABLE`, class B, StegVerse-Labs/TVC#520.

## Run

```
python scripts/icv_distribution_offline_install.py --lifecycle --receipts-out /tmp/icv.jsonl
```

Acquisition downloads `https://github.com/<repo>/archive/<commit>.tar.gz`
(the route `org-runtime-boundary.yml` already uses) and checks the archive's
commit comment. Then every pinned blob and package-root tree SHA is recomputed
from the bytes. Install, upgrade and uninstall run with socket creation
disabled, into a temporary prefix, writing a wheel-style `RECORD`. Uninstall
refuses (and removes nothing) if any recorded file changed. A package whose
license is not declared in its own source is never installed. The summary line
is `ICV_OFFLINE_LIFECYCLE: PASS` only when every cleared step passes and every
refusal is FAIL_CLOSED.

The installed file sets equal the setuptools-built wheel for 1.3.0 (247 files)
and the v1.0.12 release wheel (6 files, sha256 40b6c962… as published), checked
on the Lane A box.

## Open FAIL_CLOSED

| failure_code | failed_predicate | required_evidence_or_repair | retry_entrypoint | owning_existing_goal | next_attempt |
|---|---|---|---|---|---|
| ICV_LIFECYCLE_CI_SURFACE_UNDECIDED | the pinned-bytes lifecycle runs in this repository's CI | a decision on where an external-fetch validation may run: `control/workflow-surface-registry.json` (#3039 H6b) forbids folding an external fetch into a dispatcher and requires registering any new workflow (joint discovery entry, class C) | add the step to the decided surface, then read the run | HYGIENE-CAUSAL-ROOTS-001 / Labs#3039; Labs#3183 workstream B | when the joint discovery queue answers |
| ICV_PIN_STEGCORE_LICENSE_UNDECLARED | see `package-pins.v1.json` | | | | |
| ICV_PIN_CORE_LITE_LICENSE_UNDECLARED | see `package-pins.v1.json` | | | | |
| ICV_PIN_OBSERVATORY_LICENSE_UNDECLARED | see `package-pins.v1.json` | | | | |
| ICV_REPO_BYTES_NOT_AUTHENTICALLY_READABLE | see `package-pins.v1.json` | | | | |
