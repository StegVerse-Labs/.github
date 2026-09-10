# Device <-> KV <-> SKAP Roundtrip Mirror Handoff

Updated: 2026-09-10

```text
goal_id: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
parent_goal: KV-CONNECTION-REVALIDATION-WORKER-001
cosv_id: 50000000102000
state: ACTIVE
canonical_owner: StegVerse-Labs/.github
implementation_owner: StegVerse-Labs/StegOS
transition_authority: Interlock/InTr
credential_authority: TV/TVC
github_runtime_authority: NONE
hosted_runtime_fallback: NONE
second_user_operated_device_required: false
```

## Goal

Make the current single-device StegOS path genuinely bidirectional across the whole local trust chain:

```text
StegOS Device / DEVICE_SYSTEM
 -> KV / KnowledgeVault:Interlock
 -> SKAP_VAULT / SKAP:Vault
 -> KV / KnowledgeVault:Interlock
 -> StegOS Device / DEVICE_SYSTEM
```

A completion claim requires one authentic current-device operation lineage, not independent source checks for DEVICE_KV and KV_SKAP.

## Source status

StegOS PR #326 merged at `2339f2f2fc8c28eb4d63077387013154dac9b75c` after exact-head StegOS CI run `34517908014` succeeded.

The merged composer `stegos/device_kv_skap_roundtrip.py` binds the existing canonical `device-kv` and `kv-skap` / `kv-skap-custody` profiles into one four-leg receipt lineage. It re-hashes the current bytes of every prepared packet at final verification; a stale valid intent/receipt chain cannot hide mutated in-memory bytes.

Canonical chain:

```text
DEVICE->KV terminal receipt
 -> KV->SKAP prior_transport_receipt_hash
KV->SKAP terminal receipt
 -> SKAP->KV prior_transport_receipt_hash
SKAP->KV terminal receipt
 -> KV->DEVICE prior_transport_receipt_hash
```

The final KV->DEVICE leg is deliberately cross-connector and must descend from the terminal SKAP->KV receipt. Two disconnected request/response pairs cannot satisfy the roundtrip predicate.

## Existing operational substrate

Already merged before this child:

- StegOS Universal InTr transport and connector registry with bidirectional `device-kv`, `kv-skap`, and `kv-skap-custody` profiles;
- `.github` profiled Universal InTr ingress and event dispatch;
- `.github` KV->SKAP ciphertext materialization dispatcher and consumer;
- TVC double-Interlock validation and exact ciphertext SKAP custody;
- Site/current-iPhone DEVICE_KV request/query-return surfaces;
- continuity-vault-kit provider-neutral multi-instance KV source;
- continuity-vault-kit PR #205 at `5ad01e04d6693b2ab8e19e9214e318d91d6dad74`, binding the authentic Google Drive KV #2 adoption request to governed CONNECT/VERIFY requests.

## Current authentic evidence

Current-device KV #1 remains owner-observed installed with exact readback. The existing Google Drive KV instance remains exact-byte identified but is not yet materialized as KV #2. The owner-generated adoption request `SITE-CLOUD-KV-4347408852127319cbda574f02e03edb` reached resident ingress but its Google Drive provider CONNECT/VERIFY operations are not yet proven executed.

The existing DEVICE_KV and KV->SKAP lanes have source/merge evidence, but the repository does not currently contain one authentic terminal four-leg Device->KV->SKAP->KV->Device receipt chain. That runtime predicate therefore remains UNSATISFIED.

## Runtime completion contract

The lane becomes runtime-functional only after all are observed from one exact operation lineage:

```text
1 DEVICE->KV admitted adjacent-hop receipt
2 KV->SKAP admitted adjacent-hop receipt chained to #1
3 SKAP->KV admitted adjacent-hop receipt chained to #2
4 KV->DEVICE admitted adjacent-hop receipt chained to #3
current bytes match each packet intent hash
Interlock/InTr verification present for every hop
TV/TVC credential authority preserved
secret plaintext absent from transport/evidence
no authority transfer
same resident KV root preserved
SKAP terminal object/ciphertext exact readback verified
KV terminal state/reference exact readback verified
roundtrip verifier returns PASS
```

Source, CI, GitHub transport, HB carrier state, Site display, or provider-request creation cannot substitute for those observations.

## Current iOS serialization boundary

`control/current-user-ios-interaction-queue.json` is currently `HOLD_UI_ORCHESTRATION_CONFLICT` for true human-authority mutations, but explicitly states that machine-owned resident/service-worker/entity transitions are outside that queue and remain governed by their own contemporaneous Interlock/InTr authority. Therefore this task must not ask the user to perform a new UI mutation while that hold remains, but machine-governed runtime work is not blocked by the human queue.

## Current blockers

```text
AUTHENTIC_CURRENT_DEVICE_FOUR_LEG_INTR_ROUNDTRIP_NOT_YET_OBSERVED
AUTHENTIC_SKAP_KV_RETURN_RECEIPT_NOT_YET_OBSERVED
KV_SKAP_TERMINAL_EXACT_READBACK_NOT_YET_OBSERVED
```

Google Drive KV #2 provider execution/materialization is adjacent parent work and remains pending, but a bounded non-destructive Device<->KV<->SKAP roundtrip may use an already-authorized reference/ciphertext operation and does not need to fabricate Google Drive provider completion.

## Next implementation

Bind the existing resident DEVICE_KV and KV_SKAP receipt producers to one runtime roundtrip verifier. The verifier must consume evidence; it cannot mint or upgrade hop receipts. Then execute the already-governed machine-owned path when a resident execution surface emits all required inputs and retain exact readback.

## Manual work

None at this source/reconciliation stage. Do not ask the user to perform a new state-mutating iPhone action while the human interaction queue remains on hold.
