# SKAP Authentic Account Metadata Population Mirror Handoff

Goal Task ID: `SS-SKAP-AUTHENTIC-ACCOUNT-METADATA-POPULATION-001`
Parent Goal Task ID: `SS-SKAP-ACCOUNT-INVENTORY-PROJECTION-001`
COSV: `40000100100000`
Status: `ACTIVE / CLAIMED_IMPLEMENTATION`

## Scope

Turn independently observed real provider-account bindings into bounded non-secret SKAP account metadata through the existing governed SKAP receipt path. The owner initiates this from My KV by selecting which observed accounts are admitted. Do not place raw provider account identifiers, credentials, tokens, or secret payloads in public repository state.

## Current evidence

The connected provider surface on 2026-09-10 reports real connected account entries for Facebook, Instagram, LinkedIn, and YouTube. These observations establish candidate external account bindings only; they are not SKAP custody proof. The authenticated KnowledgeVault SKAP receipt/lifecycle surface currently contains only the RC17 synthetic Coinbase test object, so no real SKAP account population is yet claimed.

TVC's SKAP account inventory projection producer is validated independently and deliberately excludes synthetic/test records.

Site PR #1192 implemented the requested first-class `Connected Accounts` My KV item and merged at `b310ff343b70ff7e1125dbbbf25a056a83c4751b` after exact-head Site validation passed. The first validation attempt had failed closed because the branch lacked an active pre-work claim; the claim was added without weakening the orchestrator, after which bootstrap validation, reconciliation, heartbeat-contract validation, and the remaining Site checks completed successfully. The merged UI routes `Connected Accounts` to `my-kv-connected-accounts.html`, where the user can discover bounded provider-account observations, individually select accounts, and request non-secret SKAP/KV metadata population. The UI refuses secret-bearing/raw-provider-ID fields and fails closed when the runtime observation/population bridge is unavailable.

Source/CI/merge establish the UI capability only. They do not prove that a real provider account has yet been written into SKAP.

## Completion predicates

- My KV exposes a validated `Connected Accounts` selectable item. SATISFIED by Site #1192 merge `b310ff343b70ff7e1125dbbbf25a056a83c4751b`.
- The account-selection page requires explicit per-account owner selection before population. SATISFIED in merged Site source/tests.
- Normalize an authentic provider-account observation without publicly persisting the raw provider account ID. PENDING RUNTIME BRIDGE.
- Create a bounded non-secret SKAP account metadata receipt through the existing InTr-governed transition path. PENDING.
- Preserve transition and source-evidence lineage. PENDING AUTHENTIC POPULATION.
- Refuse synthetic/test observations as authentic population evidence. SATISFIED in producer/UI source validation; authentic runtime still pending.
- Re-run the parent projection and demonstrate that the populated account is enumerated. PENDING AUTHENTIC POPULATION.

## Current implementation coordinates

- Site PR: `StegVerse-Labs/Site#1192` — MERGED
- Site merge: `b310ff343b70ff7e1125dbbbf25a056a83c4751b`
- Site handoff: `docs/MY_KV_CONNECTED_ACCOUNTS_MIRROR_HANDOFF.md`
- UI route: `my-kv-connected-accounts.html`
- Client contract: `assets/my-kv-connected-accounts.js`
- Landing selector source: `assets/my-kv-directory.js`
- Static guard: `scripts/check_my_kv_directory.py`
- Focused test: `tests/my-kv-connected-accounts.test.cjs`

## Remaining work

1. Implement the runtime `StegVerseKVAccountObservationBridge` producer backed by bounded authenticated provider observations.
2. Bind `populateSelectedAccountMetadata` to the existing SKAP/InTr metadata transition path.
3. Produce one authentic retained non-secret SKAP account receipt from an owner-selected real account.
4. Re-run TVC projection and ERL reconciliation against that authentic receipt.

## Manual work

None.
