# SV-DN-1 Publication Observer Task Mirror Handoff

Updated: 2026-08-31
Repository: `StegVerse-Labs/.github`
Goal: `SV-DN1-PUBLICATION-OBSERVER-001`
Task: `SV-DN1-PUBLICATION-OBSERVER-001`
Canonical product owner: `StegVerse-org/stegverse-demo-suite`
Canonical product contract: `docs/SV_DN1_PUBLICATION_OBSERVATION_MIRROR_HANDOFF.md`
Credential authority: `TV/TVC`
GitHub token runtime authority: `NONE`
Authority effect: `NONE_PUBLICATION_OBSERVATION_ONLY`

## Goal

Machine-own the final evidence transition after authentic governed SV-DN-1 bytes have
been persisted and deployed to the public static surface.

```text
SV_DN1_REPOSITORY_PERSISTENCE_PACKAGE_READY
-> repository mutation/deployment occurs under separate authority
-> bounded public observer receives independent claim/fence
-> load exact local persistence package
-> invoke canonical product publication observer
-> GET exactly five public HTTPS artifacts without credentials
-> require exact package byte/hash equality
-> emit SV_DN1_AUTHENTIC_PUBLICATION_OBSERVED
```

The task is deliberately retryable while the public surface still contains the prior
WITHHELD projection or any stale deployment. A mismatch does not become success and no
public bytes are rewritten.

## Source-of-truth order

1. `docs/SV_DN1_PUBLICATION_OBSERVER_TASK_MIRROR_HANDOFF.md`
2. `handoffs/SV-DN1-PUBLICATION-OBSERVER-001.json`
3. `workers/sv_dn1_publication_observer_worker.py`
4. `StegVerse-org/stegverse-demo-suite:docs/SV_DN1_PUBLICATION_OBSERVATION_MIRROR_HANDOFF.md`
5. `StegVerse-org/stegverse-demo-suite:scripts/verify_sv_dn1_public_publication.py`
6. exact local `stegverse.sv-dn1.repository-persistence-package/v1`
7. fresh public HTTPS responses

Newer authentic runtime evidence overrides this handoff.

## Required local inputs

Default persistence package:

```text
~/.stegverse/state/sv-dn1-repository-persistence-package/packages/latest.json
```

Canonical product source root:

```text
~/.stegverse/source/stegverse-demo-suite/
```

Both may be relocated only through explicit non-secret locators:

```text
STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_STATE_ROOT
STEGVERSE_SV_DN1_SOURCE_ROOT
```

## Network boundary

Exactly one public origin is admitted:

```text
https://stegverse-org.github.io/stegverse-demo-suite/sv-dn1/
```

Allowed method: `GET`.

No Authorization header, cookie, GitHub token, provider token, API key, or other credential
may be supplied. Redirects away from the exact HTTPS host/path fail closed.

## Runtime semantics

The canonical product observer independently validates the persistence package, including
its package SHA-256 and all five embedded exact-byte payloads, before network access.

If public bytes do not yet match the package, the worker returns `HANDOFF_READY` with
transition:

`SV_DN1_PUBLICATION_NOT_YET_OBSERVED`

This is expected while repository mutation or Pages deployment is still pending and does
not create a failure claim.

When all five public objects return HTTP 200 and match exact governed bytes:

`SV_DN1_AUTHENTIC_PUBLICATION_OBSERVED`

is terminal.

## Authority boundary

The task MAY:
- read the already-local governed persistence package;
- execute the already-local canonical product observer;
- perform credential-free HTTPS GETs only to the exact admitted public surface;
- write one bounded local observation receipt.

The task MUST NOT:
- fetch Hugging Face;
- run InTr, SDK, StegCore, StegGate, Master Records, replay, or reconstruction;
- use GitHub/provider credentials;
- mutate repositories;
- create commits/branches/PRs;
- deploy Pages;
- decide or change publication semantics;
- release/tag/certify.

## Current implementation boundary

```text
product observer source: MERGED
product observer validation: PASS
machine handoff: IMPLEMENTED ON THIS BRANCH
worker/registry/adapter/tests: FOLLOW THIS HANDOFF
authentic SDK first round: NOT YET OBSERVED
repository mutation of authentic result: NOT YET OBSERVED
Pages deployment of authentic result: NOT YET OBSERVED
authentic public exact-byte observation: NOT YET OBSERVED
```
