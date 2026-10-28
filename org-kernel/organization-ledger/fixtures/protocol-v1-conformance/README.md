# Protocol v1.0 packet conformance fixtures

Owner work issue: StegVerse-Labs/.github#3369 (parent #3368). Evidence class: FIXTURE_ONLY_NOT_RUNTIME_RECEIPT.

`packet.json` is one intra-organization packet on the existing `SDK:ManifestIngress` binding
(`org-runtime/interlock-intr.json`, SDK#566): exact manifest bytes and their digest, genesis standing,
and the registered `stegverse-labs.boundary-diagnostic` echo as the bounded effect. `cases/` holds the
positive case and the eight negatives from #3369: tamper, replay, forged identity, stale head, wrong
route, missing authority, missing receipts, reconstruction failure. Each negative names its DENY or
FAIL_CLOSED disposition and the six fields.

`tests/test_protocol_v1_conformance_fixtures.py` runs every case through the existing
`sdk_manifest_crossing.py::cross`, `process_boundary.py`, `node_standing.py::require` and
`organization_manifest_ingress.py::{bound_here,reconstruct_closures,ingress_transition_id}`, and
checks that no ledger root is written.

Nothing here admits a task, grants authority, appends to a ledger or mints a receipt. The positive
ALLOW is a fixture result, not runtime ALLOW. Admission, the WorkerCoordinator claim/fence and any
protected run stay with the Registry owner.
