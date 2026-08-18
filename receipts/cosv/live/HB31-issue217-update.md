# Issue #217 live integration update

Direct live state now satisfies the former #122 dependency for first packet emission.

Evidence:
- `control/heartbeat-carrier-runtime-state.json`: ACTIVE, epoch/generation 31/31.
- `control/worker-runtime-state.json`: independently observed carrier 31/31.
- `receipts/heartbeat-transition-continuity/latest.json`: `CARRIER_TRANSITION_COMPLETE`, `RELEASE_COMPLETE`, all release predicates true.
- `receipts/cosv/live/HB31.json`: first live authority-neutral FULL COSV packet.
- packet SHA-256: `618ca9d0b8d6a2dbd661378b8ca9814dd9b882efb40d351c0d517bff8f4e17bd`.
- validation: `receipts/cosv/live/HB31-validation.json`, PASS local deterministic + direct live evidence.

The packet remains authority-neutral; credential authority is TV/TVC; no NON-TV/TVC secret/token or GitHub-token runtime authority was introduced; StegVerse remains primary and third parties fallback-only.

This closes the first-live-packet integration obligation for #217. Downstream is still nonterminal: next changed admitted carrier reference -> DELTA packet against HB31 -> StegBrain#861 live gradient -> StegBrain#865 same-reference precommitted expectation residual -> #863/#865 ordered matrix/residual-series evidence. The broader session must remain open under the governing completion rule until those required live outcomes and sovereign inference activation are terminal.
