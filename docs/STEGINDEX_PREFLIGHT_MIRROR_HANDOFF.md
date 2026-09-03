# StegIndex Mandatory Preflight Mirror Handoff

Status: IMPLEMENTED_SOURCE_BRANCH
Updated: 2026-09-02
Repository: StegVerse-Labs/.github
Origin: StegVerse-Labs/.github#841
Index owner: StegVerse-Labs/StegIndex
Index integration owner: StegVerse-Labs/StegIndex#1

## Goal

Require a StegIndex capability/predicate resolution before a StegVerse session, worker, or build lane treats an unresolved condition as a generic implementation/runtime-evidence blocker or creates duplicate capability work.

## Implementation

- `control/stegindex-preflight-policy.json`
- `scripts/run_stegindex_preflight.py`
- `tests/test_stegindex_preflight.py`

The preflight consumes an already-local canonical StegIndex source rooted by:

`STEGVERSE_STEGINDEX_SOURCE_ROOT`

It performs no network fetch and requires no GitHub/provider credential.

## Resolution semantics

The result distinguishes:
- matching reusable capabilities;
- current lifecycle/evidence posture;
- exact missing predicate;
- canonical satisfier/owner;
- invocation surface;
- whether machine continuation is required;
- whether a generic blocker is even permitted.

An unavailable StegIndex source is `PREFLIGHT_UNAVAILABLE`, not evidence that the requested capability is unimplemented.

## Authority

StegIndex and this preflight grant NO execution, admission, claim/fence, credential, routing, transition, publication, custody, or consequence authority.

`credential_authority: TV/TVC`
`github_token_runtime_authority: NONE`
`authority_effect: NONE_READ_RESOLVE_ONLY`

## Completion boundary

Source completion requires deterministic tests and merge.

Operational adoption additionally requires materializing canonical StegIndex source into the applicable resident/session execution surface and invoking this preflight from the entry paths that create new work or blocker classifications.

No source/CI/merge result constitutes runtime evidence.
