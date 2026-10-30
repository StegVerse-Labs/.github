# TVC537 current-source containment integration — local proposal only

TVC main read at 6458d28510e0044d946111e3a2b4046e0d23313d; original537 remains draft/unmerged c87272cfccdcd731eb8cca6133a6596b389ff218. Latest discussion return remains https://github.com/StegVerse-Labs/TVC/pull/537#issuecomment-6506866521; no owner integration witnessed. Complete fresh main tree contains no AGENTS.md. No remote mutation or merge performed.

## New source and execution

Current chain50802baf changes the consumed CVK pin in documentation; no new authority guard. Readerba4bb0be replaces the obsolete adapter431 genesis instruction with existing Lane D plan_genesis_pin LC-KV-27/28. Configf59ac945 now validates CVK288/f3f8a2dd snapshot files, including new contract and designation pins. This review preserves these changes and fetched their current four-file snapshot; it does not overwrite current main with old cdc50149 artifacts. Fifteen relevant current source/config blobs verified in current-source-blobs.json. Actual537 issuer remains byte-identical to prior verified blob95511a1f.

New tests exercise real issuer through read_through_chain and place_through_chain, with only existing synthetic ledger/signer/producer/client fixtures. They require typed six-field authenticity refusal and zero client requests. Baseline read reaches synthetic client and returns SKAP_CUSTODY_RECORD_ABSENT; baseline place succeeds without refusal. These are test-fixture effects only. Existing seven regressions remain intact; focused contract is now nine cases. Neither fake verifier nor native credential is used by this real-module contract.

Final expanded run: real contract + existing test_skap_custody_chain + existing test_kv_custody_ledgers_config (59 cases). Current baseline: 6 failed, 53 passed (39.41s); all six failures are desired new reference-only rejection contracts, including both client entry points. Candidate with two focused expectation migrations: 7 failed, 52 passed (41.80s). Its nine actual-issuer contracts pass; all seven failures are remaining existing mock-positive/downstream expectations. Logs preserved. No missing-file/collection failures in final runs. The config wording scan operates only over this downloaded closure, not the full repository.

Temporary test runner pytest9.2.0 was installed under /tmp/tvc-review-pytest because both available interpreters lacked pytest; no repo dependency/lockfile changed. Invocation: PYTHONPATH=/tmp/tvc-review-pytest python -m pytest -q test_real_issuance_chain_contract.py tests/test_skap_custody_chain.py tests/test_kv_custody_ledgers_config.py --tb=short.

## Patch and migration scope

current-containment-and-migration.patch applies the original unconditional post-verify authenticity refusal before any client use and migrates two direct gate assertions: fake verifier ALLOW is now refusal/no admission/no client request, and missing-client case now observes earlier authenticity refusal. No production bypass, caller BOUND flag, new signer, purpose or task field was invented. The real issuer issue/verify semantics remain untouched. Candidate source is in ../runtime-review-current-contained; pristine baseline in this directory.

Seven remaining failing owner tests, intentionally retained rather than skipped or weakened:
- test_layer2_consumes_the_ledger_read_layer1: preserve reader/layer positive at read_custody_receipts component boundary; gate itself refuses issuance authority.
- test_custody_result_must_be_read_back_from_the_skap_vault_ledger
- test_place_and_read_round_trip_and_never_request_deletion
- test_read_absent_and_tampered_readback
- test_placement_receipt_must_echo_digest_and_admission
- test_kv_and_skap_digests_cross_digest_only_with_the_supplied_hb_epoch
- test_missing_or_bad_epoch_fails_closed_class_b_with_six_fields

The middle four require explicit unit-level client/result-check isolation or owner-authenticated admission fixtures. Last two should test crossing helpers independently while preserving gate refusal. No current authentic ALLOW witness exists; cannot label a monkeypatched gate as native positive. Other22 fixture consumers still require full owner audit; this run proves only these seven remaining gate-suite failures, not a count of wider failures. Proposal is not merge-ready/full-suite green.

## Proposed README / canonical handoff append

README.md: “Custody chain containment review against main6458d285 and TVC537 c87272cf reproduces reference-only acceptance through gate/read/place. Local source proposal rejects this before client use. Nine real-issuer negative/control cases pass, but the expanded affected suites retain seven mock-positive/downstream expectation failures after two direct expectation migrations. Native issuance authority, full test migration, and exact-head CI remain original TV/TVC owner work. No native admission or runtime ALLOW is established.”

Append the same paragraph as a labeled consumed-dependency observation in docs/TVC_INTR_SKAP_CREDENTIAL_ENFORCEMENT_MIRROR_HANDOFF.md, preserving its distinct TVC-INTR-SKAP-CREDENTIAL-ENFORCEMENT-001 identity/status. Link TVC537 and Labs docs/KV_SKAP_VAULT_FUNCTIONAL_MIRROR_HANDOFF.md. Do not relabel reference receipts as authenticated authority. Existing README/handoff blobs remain9d2340aa/3a4353e9.

## Hashes

chain SHA256 before dcc4202f8bc30d961049c1f45a1235224dd234c30624271aa257f8866cc89b3f; after e99bd6454aea2aca7296cd21eb60fc4cf4cd9e6f0bb67d12a97ddad7c9d46080.
Gate test SHA256 before6b43eb33c5d8c0c84fa805267bae691619ccbd1b15fca78c9882ad626fb3b24d; after b415d547e45151e795b34ef52c76815cd96e3694324a0e7c14b7b6cc583288e5.
