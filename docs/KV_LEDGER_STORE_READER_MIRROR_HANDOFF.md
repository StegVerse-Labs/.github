# KV-LEDGER-STORE-READER-001 mirror handoff (PROPOSED identity, registration request only)

This file projects a **request**. It is not the Task Registry, it mints no authority and it bumps no registry generation. `KV-LEDGER-STORE-READER-001` was named by Coordination (StegVerse-org/.github#160 issuecomment-6372216673) and assigned to Lane D. It is `NONE_PROPOSAL_ONLY` until the transition applies it.

- Request: `tests/fixtures/canonical_task_registration/i1-goal-manifests/KV-LEDGER-STORE-READER-001.request.json` (NEW_IDENTITY, parent_task_id `ECOSYSTEM-OWN-KV-001`)
- Allocation request: `control/goal-task-allocation-requests/lane-d-kv-ledger-store-reader-2026-10-23.json`
- Scope: the non-git reader for store_type `GATEWAY_ENCRYPTED_BLOB` over the KV gateway storage adapter, so KV's own ledger (and the SKAP Vault ledger inside KV) is read back from user-owned storage. It reuses Lane B's per-endpoint ledger designation and verifier code unchanged (org#162 issuecomment-6372170864).

## Finish point (acceptance test is PROPOSED, not yet built)
- Acceptance test: `StegVerse-Labs/continuity-vault-kit:tests/test_kv_ledger_store_reader.py::KvLedgerStoreReaderFinishPoint::test_finish_point_verdict`
- Predicate `KV_LEDGER_STORE_READER_FINISH_POINT`: ALLOW only for an exact read-back with a signed head not older than the newest Org-recorded KV head digest; tampered, unsigned, rolled-back (`KV_LEDGER_HEAD_ROLLBACK_DETECTED`), empty/missing-as-genesis, external-record and org-designated inputs each return six-field FAIL_CLOSED.
- Lowest supported mode: E0 (stdlib, no new dependencies).

## Ordering (parent first)
The parent is not on main. The planner at this base does not check parent existence, so this child plans ALLOW on its own. That is the REGISTRATION_PARENT_EXISTENCE_NOT_CHECKED gap (class B; P4 draft StegVerse-Labs/.github#3335), which would refuse it. Apply ECOSYSTEM-OWN-KV-001 first.
