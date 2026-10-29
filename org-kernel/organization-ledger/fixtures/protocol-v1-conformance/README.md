# Protocol v1.0 packet conformance fixtures

Owner work issue: StegVerse-Labs/.github#3369 (parent #3368). Evidence class: FIXTURE_ONLY_NOT_RUNTIME_RECEIPT.

`packet.json` is one intra-organization packet on the existing `SDK:ManifestIngress` binding
(`org-runtime/interlock-intr.json`, SDK#566): exact manifest bytes and their digest, genesis standing,
and the registered `stegverse-labs.boundary-diagnostic` echo as the bounded effect. `cases/` holds the
positive case and the eight cases from #3369: tamper, replay, forged identity, stale head, wrong
route, missing authority, missing receipts, reconstruction failure. The seven refusals each declare a
DENY or FAIL_CLOSED disposition and the six fields; those are declared expectations. What the test
observes for them is the evaluator's refusal code, compared with the declared `failure_code`, and an
empty temporary ledger root.

Replay (`n2-replay`) is not a refusal in the existing code: `organization_manifest_ingress.receive`
treats a redelivery under another packet id as the same transition and appends nothing more. n2
declares that idempotent acceptance, and its `spec_gap` records the replay refusal #3369 lists as a
six-field gap owned by the ingress lane (`ORGANIZATION-BATCH-CUSTODY-REPLAY-001`).

`tests/test_protocol_v1_conformance_fixtures.py` runs the positive case and the seven refusals through
the existing `sdk_manifest_crossing.py::cross`, `process_boundary.py`, `node_standing.py::require` and
`organization_manifest_ingress.py::{bound_here,reconstruct_closures,ingress_transition_id}`, and
checks that no ledger root is written. n2 runs the real `receive` twice against temporary ledger roots
and checks one receipt per level and the same transition id.

Nothing here admits a task, grants authority, appends to a real ledger or mints a live receipt. The positive
ALLOW is a fixture result, not runtime ALLOW. Admission, the WorkerCoordinator claim/fence and any
protected run stay with the Registry owner.
