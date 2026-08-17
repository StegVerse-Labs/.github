# iPhone Heartbeat Transition Mirror Handoff

Updated: `2026-08-17T09:52:00-05:00`

## Active goal

```text
goal_id: SHWP-IPHONE-HB30-TRANSITION-CAPSULE-001
originating_goal: eliminate the HB29->HB30 execution initiation deadlock without requiring another machine, hosted runtime, GitHub token, or NON-TV/TVC secret/token
repository: StegVerse-Labs/.github
branch: fix/iphone-hb30-transition-capsule-209
canonical_issue: StegVerse-Labs/.github#209
parent_task: SHWP-DURABLE-RUNTIME-ACTIVATION / G18
canonical_runtime_owner: StegVerse-Labs/.github#59
canonical_inference_owner: StegVerse-Labs/.github#60
credential_authority: TV/TVC
render_production_authority: NONE
github_token_runtime_authority: NONE
active_claim: control/session-integration-claim-2026-08-17-iphone-hb30-transition-capsule.json
claim_state: CLAIMED_FOR_INTEGRATION
```

## Problem established

The v12 source transition producer is complete, but live repository state remains at immutable HB29 and no `control/heartbeat-carrier-runtime-state.json` has been observed. The current transition contract requires the next admitted StegVerse worker/control-plane execution opportunity, while the only permitted user physical carrier is `CURRENT_USER_IPHONE`. The canonical Python producer cannot execute inside iOS Safari, creating a practical initiation seam even though the transition itself is non-authorizing and requires no credential.

This is not solved by GitHub Actions, Render, Vercel, Cloudflare, another machine, or a GitHub token. Those remain prohibited production substitutions.

## Implemented source solution

A portable physical transition capsule contract is installed:

```text
management/SHWP_IPHONE_TRANSITION_CAPSULE_CONTRACT.json
schemas/iphone_heartbeat_transition_receipt.schema.json
scripts/verify_iphone_heartbeat_transition_receipt.py
tests/test_iphone_heartbeat_transition_receipt.py
```

The portable receipt binds:

- repository `StegVerse-Labs/.github`;
- immutable legacy state ref `control/heartbeat-state.json`;
- exact current legacy Git blob `d18d57d83cf19b7799cde1a1b4487e496eca7f76`;
- HB29 / generation 29;
- exact successor HB30 / generation 30;
- authority effect `NONE`;
- `credential_authority=TV/TVC`;
- `credential_requirement=NONE`;
- `github_token_runtime_authority=NONE`;
- no worker/claim/fence/route/wallet/model-output authority;
- physical execution surface `CURRENT_USER_IPHONE`;
- secure `https://stegverse.org` browser + WebCrypto evidence;
- canonical SHA-256 receipt digest.

The verifier fails closed on seed drift, legacy-state drift, wrong successor, authority escalation, protected credential material, non-iPhone user agent, non-StegVerse origin, or digest mismatch.

The optional materializer is intentionally separate from browser execution. It revalidates the current legacy blob, rejects hosted environments, writes only the v12 carrier/cutover/transition surfaces, preserves legacy HB29 bytes exactly, does not mutate worker claims/fences, and leaves release incomplete until independent WorkerCoordinator observation.

## Required Site projection

Canonical public execution must be an exact, credential-free browser capsule under `StegVerse-Labs/Site`. Site is transport/materialization only and must not mint carrier or worker authority.

Required Site surfaces:

```text
heartbeat-transition/index.html
heartbeat-transition/heartbeat-transition.js
docs/IPHONE_HEARTBEAT_TRANSITION_PROJECTION_MIRROR_HANDOFF.md
```

The browser must produce the portable receipt locally and expose it for evidence capture. No Authorization/Bearer header, repository credential, provider token, or wallet material may be used.

## Completion sequence

```text
1 merge/validate this source contract + verifier
2 publish exact Site browser capsule
3 current user iPhone executes capsule on stegverse.org
4 preserve the emitted portable receipt as physical evidence
5 canonical verifier accepts the receipt against current immutable HB29
6 materialize HB30 carrier/cutover/transition state without altering legacy HB29
7 independently admitted WorkerCoordinator observes HB30+
8 reconstruction/no-duplicate-claim predicates PASS
9 G18 releases runtime transition dependency
10 .github#60 continues local-model -> TVC -> LLM-adapter -> Master Records inference chain
```

## Collision boundaries

- G18 remains machine-owned; this source lane does not acquire or rewrite its fence/lease.
- WorkerCoordinator authority remains separate.
- TV/TVC remains credential/route authority.
- GitHub hosting may validate source but cannot produce the physical transition.
- Site publication alone is not HB30 activation.
- Physical receipt alone is not WorkerCoordinator completion.

## Validation

```text
python -m unittest -v tests.test_iphone_heartbeat_transition_receipt
python scripts/verify_iphone_heartbeat_transition_receipt.py <receipt.json>
```

Hosted tests are source-behavior evidence only.

## Completion accounting

```text
canonical contract/schema/verifier/test/handoff: 5/5 implemented on active branch
site browser projection: 0/3
physical iPhone receipt: pending
HB30 materialization: pending
independent WorkerCoordinator observation: pending
source goal activation: 50%
session role: ACTIVE_DISTINCT_SUPPORT
archive condition: source solution transferred + Site projection installed + physical execution handoff durable; product activation may remain machine-owned afterward
```
