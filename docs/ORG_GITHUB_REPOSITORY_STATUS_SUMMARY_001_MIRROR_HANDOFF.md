# Organization GitHub Repository Status Summary Mirror Handoff

Status: ACTIVE / CHECKED_OUT
Repository: `StegVerse-Labs/.github`
Task ID: `ORG-GITHUB-REPOSITORY-STATUS-SUMMARY-001`
COSV profile: `task.v1`
COSV vector: `20010000100000`
Goal: provide an abbreviated status summary of all repositories in the StegVerse-Labs organization.

## Deterministic lookup contract

The compact continuation pointer is:

```text
ORG-GITHUB-REPOSITORY-STATUS-SUMMARY-001
20010000100000
```

Do not depend on GitHub code search to resolve this task.

Given the Task ID, derive and fetch the canonical pointer entry directly at:

```text
control/task-vector-index.d/ORG-GITHUB-REPOSITORY-STATUS-SUMMARY-001.json
```

Verify the COSV vector matches exactly, then follow its `registry_ref` directly to:

```text
data/canonical-task-records/ORG-GITHUB-REPOSITORY-STATUS-SUMMARY-001.json
```

The Task ID determines the sharded pointer path. Search-index freshness is not part of task resolution.

## Status-response contract

For a status request carrying this exact Task ID + COSV pair, first resolve the deterministic pointer and canonical record above.

If canonical state is ACTIVE / CHECKED_OUT, the entire user-facing status response MUST be exactly:

```text
currently active - checked out

Task ID: ORG-GITHUB-REPOSITORY-STATUS-SUMMARY-001
COSV ID: 20010000100000
```

Do not add repository counts, progress percentages, estimated completion, archival commentary, inferred evidence, or other status prose unless those values are explicitly present in the canonical completed summary.

If canonical state is COMPLETED, return the completed abbreviated summary report plus the same Task ID and COSV ID.

If canonical state is RETIRED, RETIRED is terminal and provenance-only. Historical resurrection is review-only and cannot resume execution.

A status query does not itself perform or claim repository-census work and does not create progress evidence.

## Work scope

1. Enumerate all repositories in the `StegVerse-Labs` GitHub organization.
2. Determine a compact current status for each repository using repository metadata and available canonical handoffs/evidence.
3. Produce an abbreviated organization-wide report.
4. Record completion state and summary evidence in this handoff/task record.

## Current state

- lifecycle: ACTIVE
- checkout: CHECKED_OUT
- report_complete: false
- terminal: false
- history_review_only: false

## Next admissible work

Enumerate the StegVerse-Labs organization repositories and begin the abbreviated status census.
