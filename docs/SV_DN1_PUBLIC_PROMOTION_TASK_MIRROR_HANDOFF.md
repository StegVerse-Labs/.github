# SV-DN-1 Public Promotion Task Mirror Handoff

Updated: 2026-08-30
Repository: `StegVerse-Labs/.github`
Goal: `SV-DN1-PUBLIC-PROMOTION-001`
Task: `SV-DN1-PUBLIC-PROMOTION-001`
Parent task: `SV-DN1-SDK-FIRST-ROUND-001`
Canonical product owner: `StegVerse-org/stegverse-demo-suite`
Canonical promotion contract: `docs/SV_DN1_AUTHENTIC_PUBLIC_PROMOTION_MIRROR_HANDOFF.md`
Credential authority: `TV/TVC`
GitHub token runtime authority: `NONE`
Authority effect: `NONE_STATIC_PROJECTION_ONLY`

## Goal

Own the previously unassigned machine transition immediately after `SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED` without widening the SDK worker's authority.

Canonical progression:

```text
SV-DN1-SDK-FIRST-ROUND-001 COMPLETED
  exact finalized artifacts in its bounded round/
        ↓
SV-DN1-PUBLIC-PROMOTION-001 receives independent fresh claim/fence
        ↓
locate already-local stegverse-demo-suite source
        ↓
invoke already-merged scripts/promote_sv_dn1_public_result.py
        ↓
validate ANALYZED + LIVE + non-WITHHELD identities
        ↓
copy exact bytes into already-local demo-suite public/sv-dn1/
        ↓
verify source/destination SHA-256 equality
        ↓
emit promotion receipt
        ↓
PROMOTION_READY_FOR_REPOSITORY_MUTATION
```

This task ends at local promotion readiness. Repository mutation, merge, Pages deployment, public HTTPS observation, release and certification remain separate lifecycle states.

## Source-of-truth order

1. `docs/SV_DN1_PUBLIC_PROMOTION_TASK_MIRROR_HANDOFF.md`
2. `handoffs/SV-DN1-PUBLIC-PROMOTION-001.json`
3. `workers/sv_dn1_public_promotion_worker.py`
4. `StegVerse-org/stegverse-demo-suite:docs/SV_DN1_AUTHENTIC_PUBLIC_PROMOTION_MIRROR_HANDOFF.md`
5. `StegVerse-org/stegverse-demo-suite:scripts/promote_sv_dn1_public_result.py`
6. `docs/SV_DN1_SDK_FIRST_ROUND_MIRROR_HANDOFF.md`
7. authentic local SDK first-round receipt/artifacts

Newer authentic runtime evidence overrides this handoff.

## Input contract

Required predecessor receipt:

```text
~/.stegverse/state/sv-dn1-sdk-first-round/receipts/latest.json
schema = stegverse.sv-dn1.sdk-first-round-worker-receipt/v1
state = COMPLETE
transition_id = SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED
first_round_analysis = ANALYZED
dashboard_generated = true
dashboard_publicly_hosted = false
repository_writeback_performed = false
credential_used = false
github_token_used = false
authority_effect = NONE
```

Required predecessor artifact directory:

```text
~/.stegverse/state/sv-dn1-sdk-first-round/round/
  first-round-analysis.json
  production-pipeline-observation.json
  result-receipt.json
  report.md
  index.html
```

Required already-local product source contains:

```text
scripts/promote_sv_dn1_public_result.py
public/sv-dn1/
docs/SV_DN1_AUTHENTIC_PUBLIC_PROMOTION_MIRROR_HANDOFF.md
```

The product root may be supplied by non-secret `STEGVERSE_SV_DN1_SOURCE_ROOT`; no remote checkout/fetch is permitted.

## Authority boundary

This task MAY:
- validate predecessor receipt identity/state;
- invoke the canonical local promoter;
- mutate the already-local demo-suite working tree only within `public/sv-dn1/` and a local promotion receipt path;
- record exact hashes and local readiness evidence.

This task MUST NOT:
- fetch any source or repository;
- use GitHub/provider credentials;
- commit, push, merge, release or deploy;
- claim repository writeback;
- invoke SDK/evaluator/custody again;
- change finalized semantics;
- render substitute artifacts;
- grant publication/certification authority.

Local checkout mutation is preparation, not repository persistence. `repository_writeback_performed=false` remains required in this task's terminal receipt.

## Completion

Task completion transition:

`SV_DN1_PUBLIC_PROMOTION_READY`

It requires the canonical promoter to emit:

```text
state = PROMOTION_READY_FOR_REPOSITORY_MUTATION
observation_class = LIVE
publication_state in {PUBLIC_OBSERVED, PUBLIC_WITH_LIMITATIONS}
exact_bytes_preserved = true
semantic_rewrite_performed = false
network_fetch_performed = false
credential_used = false
repository_writeback_performed = false
deployment_performed = false
authority_effect = NONE_STATIC_PROJECTION_ONLY
```

The task also independently rehashes the five source and destination artifacts and requires exact equality.

## Successor boundary

After this task completes, an independently admitted TV/TVC-governed repository-mutation lane may persist the exact promoted files. That successor must consume this task's exact promotion receipt and hashes. GitHub Actions may later deploy checked-in static artifacts but cannot become publication-decision or runtime authority.

No generic repository writeback authority is invented by this task. If no admitted mutation lane exists at runtime, the task still completes only to `PROMOTION_READY_FOR_REPOSITORY_MUTATION` and the repository-persistence lifecycle remains open.

## Runtime truth at creation

```text
HF established-node observation: OBSERVED
Universal InTr hop: OBSERVED
browser evidence continuity defect: SOURCE FIX MERGED
SDK first authentic production round: NOT OBSERVED
canonical demo-suite promoter: MERGED / VALIDATED
public promotion resident task: HANDOFF CREATED / IMPLEMENTATION PENDING
repository persistence of authentic result: NOT OBSERVED
Pages deployment of authentic result: NOT OBSERVED
independent public HTTPS authentic-result observation: NOT OBSERVED
```
