# SKAP Account Inventory Projection Runtime Note

Goal Task ID: `SS-SKAP-ACCOUNT-INVENTORY-PROJECTION-001`

The authenticated KnowledgeVault SKAP surface was inspected on 2026-09-10. `_Vault/SKAP` contains distinct `Credentials`, `Receipts`, `Revocations`, `Lifecycle`, and `Sealed` branches. The currently observed `Receipts` and `Lifecycle` content is the RC17 synthetic Coinbase test object only. Its ingress receipt explicitly records `synthetic_material_only=true`; therefore it must not satisfy the real-account enumeration predicate.

The TVC producer must consume only non-secret receipt/lifecycle metadata, must never open credential/sealed payload material, must exclude synthetic/test entries from authentic account inventory, and must fail closed when no real SKAP-maintained account metadata remains after filtering.
