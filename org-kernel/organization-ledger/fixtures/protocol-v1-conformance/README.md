# Protocol v1.0 packet conformance fixtures

Owner work issue: StegVerse-Labs/.github#3369 (parent #3368). Evidence class: FIXTURE_ONLY_NOT_RUNTIME_RECEIPT.

`packet.json` is one intra-organization packet on the existing `SDK:ManifestIngress` binding
(`org-runtime/interlock-intr.json`, SDK#566): exact manifest bytes and their digest, genesis standing,
and the registered `stegverse-labs.boundary-diagnostic` echo as the bounded effect. `cases/` holds the
positive case and one case per #3369 item. Each case names its mutation, what it actually exercises
(`covers`), the #3369 item it is filed under (`issue_3369_item`) and an honest status
(`COVERED`, `COVERED_WITH_SPEC_GAP` or `SPEC_GAP`).

| Case | Covers | #3369 item | Status |
|---|---|---|---|
| `positive` | the positive packet crosses and echoes the bounded effect | POSITIVE | COVERED |
| `n1-tamper` | payload altered after the crossing, `payload_hash` recomputed from the altered bytes | TAMPER | COVERED_WITH_SPEC_GAP |
| `n2-replay` | redelivery under another packet id is idempotent acceptance | REPLAY | SPEC_GAP |
| `n3-wrong-receiving-operation` | the request names a receiving operation owned by another repository | FORGED_IDENTITY | SPEC_GAP |
| `n4-generation-not-successor` | VERIFY_EXISTING standing whose predecessor generation is not generation - 1 | STALE_HEAD_OR_FENCE | SPEC_GAP |
| `n5-wrong-route` | `completion.egress` declares a surface the registry does not expose | WRONG_ROUTE | COVERED |
| `n6-ingress-resolution-absent` | the request carries no organization ingress resolution | MISSING_AUTHORITY | SPEC_GAP |
| `n7-missing-receipts` | the crossing returns no boundary receipt chain | MISSING_RECEIPTS | COVERED |
| `n8-reconstruction-failure` | the terminal boundary receipt is dropped; `receive()` refuses (gating) | RECONSTRUCTION_FAILURE_GATING | COVERED |
| `n9-non-gating-propagation-failure` | Master Records propagation fails closed; the transition stays recorded | RECONSTRUCTION_FAILURE_NON_GATING | COVERED |

`tests/test_protocol_v1_conformance_fixtures.py` drives every negative through the real
`resident-runtime/organization_manifest_ingress.py::receive` against temporary ledger roots. Only the
absent SDK's `derive_execution_request` and `admit_runtime_result` are supplied. `receive()` records each
refusal at both ledger levels as `ORGANIZATION_SDK_MANIFEST_INGRESS_REFUSED` (record disposition DENY)
and returns FAIL_CLOSED with `received: false`, `refusal_recorded: true` and
`authority_effect: NONE_REFUSAL_ONLY`. The test asserts that shape, reads both refusal receipts back from
the temporary roots, recomputes their digests, checks that they carry the case's failure code and
predicate, and checks that no ingress transition receipt was written.

A negative's `expected` and `expected_refusal_record` are generated, not hand-written:
`python3 -m tests.test_protocol_v1_conformance_fixtures --regenerate`, run from the repository root,
writes them from a live `receive()` run, and the test asserts the committed values equal a live run.
`receive()` does not emit `required_evidence_or_repair`, `retry_entrypoint`, `owning_existing_goal` or
`next_attempt` on these refusal paths, so no case claims them as observed.

n2 runs the real `receive` twice and asserts ALLOW on the first delivery, the same transition id on the
second, and the receipts read back from both roots. n9 receives the positive packet, runs the real
`resident-runtime/submit_org_transition_to_master_records.py` on the appended organization receipt with no
materialized mesh location (FAIL_CLOSED, `MESH_LOCATION_REQUIRED_FROM_MATERIALIZER`), and asserts both
ledger levels are byte-identical afterwards and a redelivery replays the same transition --
`propagation_gates_organization_runtime_reality` is false in `.stegverse/transition-ledger/org-contract.json`.

Items the real path cannot express are six-field `spec_gap` entries, each checked to name a code absent
from the ingress, crossing and standing sources:

- `REPLAY_REFUSAL_NOT_IMPLEMENTED_BY_INGRESS` (n2)
- `PAYLOAD_HASH_NOT_RECOMPUTED_FROM_MANIFEST_AT_INGRESS` (n1): an echo or manifest altered with
  `payload_hash` unchanged is not detected at ingress
- `SENDER_IDENTITY_NOT_AUTHENTICATED_AT_INGRESS` (n3)
- `STALE_HEAD_OR_FENCE_NOT_COMPARED_AT_INGRESS` (n4)
- `AUTHORITY_NOT_CHECKED_AT_INGRESS` (n6)

Nothing here admits a task, grants authority, appends to a real ledger or mints a live receipt. ALLOW on
these temporary roots is a fixture result, not runtime ALLOW. Admission, the WorkerCoordinator
claim/fence and any protected run stay with the Registry owner.
