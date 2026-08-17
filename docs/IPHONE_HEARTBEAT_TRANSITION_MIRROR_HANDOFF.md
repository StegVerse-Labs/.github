# iPhone Heartbeat Transition Mirror Handoff

Updated: `2026-08-17T14:02:00-05:00`

## Active goal

```text
goal_id: SHWP-IPHONE-HB30-TRANSITION-CAPSULE-001
originating_goal: eliminate the HB29->HB30 execution initiation deadlock without requiring another machine, hosted runtime, GitHub token, or NON-TV/TVC secret/token
repository: StegVerse-Labs/.github
branch: main
canonical_issue: StegVerse-Labs/.github#209
parent_task: SHWP-DURABLE-RUNTIME-ACTIVATION / G18
canonical_runtime_owner: StegVerse-Labs/.github#12 + G18
canonical_inference_owner: StegVerse-Labs/.github#60
credential_authority: TV/TVC
render_production_authority: NONE
github_token_runtime_authority: NONE
source_claim: control/session-integration-claim-2026-08-17-iphone-hb30-transition-capsule.json
source_claim_state: COMPLETE_RELEASED
inline_support_claim: control/session-integration-claim-2026-08-17-iphone-hb30-inline-capsule.json
inline_support_claim_state: COMPLETE_RELEASED
product_activation_state: PHYSICAL_RECEIPT_PENDING
```

## Problem and resolved source seam

The canonical v12 transition producer is source-complete, but live repository state remains at immutable HB29 and no `control/heartbeat-carrier-runtime-state.json` has been observed. The only permitted user physical carrier is `CURRENT_USER_IPHONE`; hosted CI, another machine, Render, Vercel, Cloudflare hosted runtime, GitHub-token runtime authority, and NON-TV/TVC secret/token substitution remain prohibited.

The source initiation seam is resolved by two compatible browser transports under the same canonical portable receipt contract:

1. published Site capsule source under `StegVerse-Labs/Site/heartbeat-transition/`;
2. publication-independent inline capsule `capsules/iphone-hb30-inline-capsule.js` for an existing secure `https://stegverse.org` Safari page on CURRENT_USER_IPHONE.

Neither transport materializes HB30 or grants worker/route/provider/wallet/model authority.

## Implemented source solution

Canonical `.github` surfaces:

```text
management/SHWP_IPHONE_TRANSITION_CAPSULE_CONTRACT.json
schemas/iphone_heartbeat_transition_receipt.schema.json
scripts/verify_iphone_heartbeat_transition_receipt.py
tests/test_iphone_heartbeat_transition_receipt.py
capsules/iphone-hb30-inline-capsule.js
scripts/check_iphone_hb30_inline_capsule.py
tests/test_iphone_hb30_inline_capsule.py
handoffs/SHWP-IPHONE-HB30-INLINE-CAPSULE-002.json
```

The portable receipt binds:

- repository `StegVerse-Labs/.github`;
- immutable legacy state ref `control/heartbeat-state.json`;
- exact legacy Git blob `d18d57d83cf19b7799cde1a1b4487e496eca7f76`;
- HB29 / generation 29;
- exact first separated-v12 successor HB30 / generation 30;
- authority effect `NONE`;
- `credential_authority=TV/TVC`;
- `credential_requirement=NONE`;
- `github_token_runtime_authority=NONE`;
- no worker/claim/fence/route/wallet/model-output authority;
- physical execution surface `CURRENT_USER_IPHONE`;
- secure `https://stegverse.org` browser + WebCrypto evidence;
- canonical SHA-256 receipt digest.

The verifier fails closed on seed drift, legacy-state drift, wrong successor, authority escalation, protected credential material, non-iPhone user agent, non-StegVerse origin, or digest mismatch.

The materializer is separate from browser execution. It revalidates the current legacy blob, rejects hosted environments, writes only v12 carrier/cutover/transition surfaces, preserves legacy HB29 bytes exactly, does not mutate worker claims/fences, and leaves release incomplete until independent WorkerCoordinator observation.

## Released Site projection

Canonical Site source is COMPLETE_RELEASED:

```text
StegVerse-Labs/Site#358 CLOSED_COMPLETED
Site PR #368 merge: 37c8ac81b8b00e22310b8f03687f4b9f42581d31
Site final head: 0b1f7f741fe71057bea93241ad74b5b72f1cc20d
Site handoff: docs/IPHONE_HEARTBEAT_TRANSITION_PROJECTION_MIRROR_HANDOFF.md
released route contract: stegverse.org/heartbeat-transition/
```

The Site browser surface creates the portable receipt locally and exposes copy/share/save operations. It does not create GitHub, provider, wallet, route, worker, claim, fence, or model authority.

## Released publication-independent inline path

`SHWP-IPHONE-HB30-INLINE-CAPSULE-002` is COMPLETE_RELEASED:

```text
PR #214 merge: c079216deeaa8fa5d049f6c634d829bde5689596
final source head: e4aba9859f2deed5f626723dfd7faa1ee4720a5e
claim release: f640aef00beb0fd586be8299ae9347537f316c6f
scoped handoff finalization: e56aa8c69c8505d0cf2c392b9a41410ef9aaf1d4
canonical Heartbeat Worker validation: run 32056394503 / job 95467436421 SUCCESS
repository deterministic suite: 345/345 PASS
```

This removes a dependency on a newly published path or hosted deployment credential for physical initiation.

## Completion sequence

```text
1 canonical contract/schema/verifier/materializer source COMPLETE
2 exact Site browser capsule source COMPLETE_RELEASED
3 publication-independent inline Safari capsule COMPLETE_RELEASED
4 CURRENT_USER_IPHONE executes one released capsule while HB29 remains canonical
5 preserve the emitted portable receipt as physical evidence
6 canonical verifier accepts the receipt against current immutable HB29
7 materialize HB30 carrier/cutover/transition state without altering legacy HB29
8 independently admitted WorkerCoordinator observes HB30+
9 reconstruction/no-duplicate-claim predicates PASS
10 G18 releases runtime transition dependency
11 .github#60 continues local-model -> TVC -> LLM-adapter -> Master Records inference chain
```

No hosted workflow result alone may satisfy steps 4-9.

## Validation

```text
python -m unittest -v tests.test_iphone_heartbeat_transition_receipt
python scripts/check_iphone_hb30_inline_capsule.py
python -m unittest -v tests.test_iphone_hb30_inline_capsule
python scripts/verify_iphone_heartbeat_transition_receipt.py <receipt.json>
```

Hosted tests are source-behavior evidence only.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.json
collision_scope: source reconciliation only; no session may mint HB30, alter G18 fence/lease, or impersonate CURRENT_USER_IPHONE
release_condition: source claims are already COMPLETE_RELEASED; no chat/session implementation claim remains
next_executable_action: the physical CURRENT_USER_IPHONE boundary executes a released browser capsule; this is not delegated to a chat or hosted worker
```

### WORKER-OWNED / DO NOT COMPETE

- `SHWP-DURABLE-RUNTIME-ACTIVATION` / G18 owns canonical HB30 materialization and runtime release after a valid physical receipt.
- WorkerCoordinator independently owns HB30+ observation and reconstruction evidence.
- `.github#60` owns sovereign inference after carrier/recovery release.

### ESCALATED / AUTHORITY-OWNED

- `CURRENT_USER_IPHONE` owns the physical browser execution boundary; receipt authority effect is `NONE`.
- TV/TVC retains all credential/route authority.
- USER_ONLY retains wallet signing/broadcast authority.

### COMPLETED / SUPERSEDED

- source contract/schema/verifier/materializer: COMPLETE_RELEASED.
- Site browser capsule source: COMPLETE_RELEASED.
- `SHWP-IPHONE-HB30-INLINE-CAPSULE-002` source: COMPLETE_RELEASED.
- requirement for another physical machine: SUPERSEDED / PROHIBITED.
- requirement for always-on external host: SUPERSEDED / NOT A CONTINUITY PREREQUISITE.
- GitHub-token or NON-TV/TVC credential substitution: PROHIBITED.

## Completion accounting

```text
canonical contract/schema/verifier/materializer: complete
site browser projection source: complete released
inline browser transport source: complete released
source validation: PASS
physical iPhone receipt: pending
HB30 materialization: pending
independent WorkerCoordinator observation: pending
source implementation: 100%
product activation: incomplete
session role: MERGED_INTO_CANONICAL_WORKSTREAMS
archive condition: satisfied for chat-owned source work; product continuation is durable under CURRENT_USER_IPHONE -> .github#209 -> G18 -> WorkerCoordinator -> .github#60
```
