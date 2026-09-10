# SKAP Authentic Account Metadata Population Mirror Handoff

Goal Task ID: `SS-SKAP-AUTHENTIC-ACCOUNT-METADATA-POPULATION-001`
Parent Goal Task ID: `SS-SKAP-ACCOUNT-INVENTORY-PROJECTION-001`
COSV: `40000100100000`
Status: `INACTIVE / UNCLAIMED`

## Scope

Turn independently observed real provider-account bindings into bounded non-secret SKAP account metadata through the existing governed SKAP receipt path. Do not place raw provider account identifiers, credentials, tokens, or secret payloads in public repository state.

## Current evidence

The connected provider surface on 2026-09-10 reports real connected account entries for Facebook, Instagram, LinkedIn, and YouTube. These observations establish candidate external account bindings only; they are not SKAP custody proof. The authenticated KnowledgeVault SKAP receipt/lifecycle surface currently contains only the RC17 synthetic Coinbase test object, so no real SKAP account population is yet claimed.

TVC's SKAP account inventory projection producer is validated independently and deliberately excludes synthetic/test records. Once this task creates at least one authentic non-secret SKAP account receipt, the parent projection can enumerate it and feed the merged ERL SKAP-to-evidence reconciler.

## Completion predicates

- Normalize an authentic provider-account observation without publicly persisting the raw provider account ID.
- Create a bounded non-secret SKAP account metadata receipt through the existing InTr-governed transition path.
- Preserve transition and source-evidence lineage.
- Refuse synthetic/test observations as authentic population evidence.
- Re-run the parent projection and demonstrate that the populated account is enumerated.

## Manual work

None at task creation.
