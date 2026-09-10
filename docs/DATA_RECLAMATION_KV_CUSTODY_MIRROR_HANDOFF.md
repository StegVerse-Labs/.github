# Data Reclamation KnowledgeVault Custody Mirror Handoff

Goal Task ID: `SS-DATA-RECLAMATION-KV-CUSTODY-001`
Parent Goal Task ID: `SS-EVIDENCE-COMPARISON-001`
COSV: `40000100100000`
Status: `ACTIVE / CLAIMED_INTEGRATION`

## Scope

Bind the Personal Data Inventory, authorized SKAP account/provider topology, and deterministic `stegverse.reclamation-target-set/v1` output to authentic KnowledgeVault writes, exact-byte readback, writer/readback receipts, and reconstructable Master Records custody.

## Canonical starting evidence

- Executive_Rhetoric_Ledger PR #147 merged at `c78b2fe4be29dc4e9e15167281b35be8105a922a` with deterministic target reconciliation.
- Executive_Rhetoric_Ledger PR #148 merged at `e0c026f6147f5628b6201ee5de93951816e99a2e` after both PR checks passed.
- StegVerse-Labs/.github PR #1311 merged at `7c27980b1f885d17177a3dc587dbc917472dd96c`, canonicalizing this child task and the five sibling reclamation lanes.
- StegVerse-Labs/.github PR #1312 merged at `5751467fa1aa39ffba0e40a67d2d83cea0898db6`, moving the parent task's separate current-iPhone standard-flow predicate to its own successor.
- Existing ERL KV writer/readback and Master Records custody patterns must be reused; do not create a parallel KV authority model.

## Completion predicates

1. Generated target set is written to the authorized KnowledgeVault path with subject binding.
2. Independent exact-byte readback matches the writer commitment.
3. Writer and readback receipts are retained with provider/resource identity and proof class.
4. Master Records custody reconstructs the exact target-set commitment and receipts without relying on chat history.
5. No provider metadata observation is promoted into a native-writer or deletion-success claim.

## Current execution state

The task is claimed by the current session for integration. Repository implementation and validation may proceed immediately. Authentic KnowledgeVault success is not claimed until a real write and independent readback receipt exist. Master Records custody is not claimed until the exact receipt chain is imported and reconstructs.

## Authority invariant

KnowledgeVault custody does not authorize provider deletion. Graph membership does not authorize execution. Interlock/InTr remains state-transition authority. The Task Registry coordinates work but does not mint execution authority.

## Manual work

None at current implementation stage.
