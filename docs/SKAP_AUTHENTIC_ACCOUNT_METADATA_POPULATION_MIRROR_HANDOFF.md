# SKAP Authentic Account Metadata Population Mirror Handoff

Goal Task ID: `SS-SKAP-AUTHENTIC-ACCOUNT-METADATA-POPULATION-001`
Parent Goal Task ID: `SS-SKAP-ACCOUNT-INVENTORY-PROJECTION-001`
COSV: `40000100100000`
Status: `ACTIVE / CLAIMED_IMPLEMENTATION`

## Scope

Turn independently observed real provider-account bindings into bounded non-secret SKAP account metadata through the existing governed SKAP receipt path. The owner must be able to initiate this from My KV by selecting which observed accounts are admitted. Do not place raw provider account identifiers, credentials, tokens, or secret payloads in public repository state.

## Current evidence

The connected provider surface on 2026-09-10 reports real connected account entries for Facebook, Instagram, LinkedIn, and YouTube. These observations establish candidate external account bindings only; they are not SKAP custody proof. The authenticated KnowledgeVault SKAP receipt/lifecycle surface currently contains only the RC17 synthetic Coinbase test object, so no real SKAP account population is yet claimed.

TVC's SKAP account inventory projection producer is validated independently and deliberately excludes synthetic/test records. Site PR #1192 now implements the requested first-class `Connected Accounts` My KV item on branch `task/my-kv-connected-accounts-20260910`. Selecting it routes to `my-kv-connected-accounts.html`, where the user can discover bounded provider-account observations, individually select accounts, and request non-secret SKAP/KV metadata population. The UI refuses secret-bearing/raw-provider-ID fields and fails closed when the runtime observation/population bridge is unavailable. Site validation is in progress; static UI implementation does not prove live account population.

## Completion predicates

- My KV exposes a validated `Connected Accounts` selectable item.
- The account-selection page requires explicit per-account owner selection before population.
- Normalize an authentic provider-account observation without publicly persisting the raw provider account ID.
- Create a bounded non-secret SKAP account metadata receipt through the existing InTr-governed transition path.
- Preserve transition and source-evidence lineage.
- Refuse synthetic/test observations as authentic population evidence.
- Re-run the parent projection and demonstrate that the populated account is enumerated.

## Current implementation coordinates

- Site PR: `StegVerse-Labs/Site#1192`
- Site branch: `task/my-kv-connected-accounts-20260910`
- Site handoff: `docs/MY_KV_CONNECTED_ACCOUNTS_MIRROR_HANDOFF.md`
- UI route: `my-kv-connected-accounts.html`
- Client contract: `assets/my-kv-connected-accounts.js`
- Landing selector source: `assets/my-kv-directory.js`
- Static guard: `scripts/check_my_kv_directory.py`
- Focused test: `tests/my-kv-connected-accounts.test.cjs`

## Remaining work

1. Finish Site #1192 validation and merge only if green.
2. Implement the runtime `StegVerseKVAccountObservationBridge` producer backed by bounded authenticated provider observations.
3. Bind `populateSelectedAccountMetadata` to the existing SKAP/InTr metadata transition path.
4. Produce one authentic retained non-secret SKAP account receipt from an owner-selected real account.
5. Re-run TVC projection and ERL reconciliation against that authentic receipt.

## Manual work

None.
