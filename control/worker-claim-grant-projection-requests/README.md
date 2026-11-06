# Worker claim grant projection requests

One `stegverse.worker-claim-grant-projection-request/v1` manifest per Organization
claim-allocator GRANTED receipt to project into `control/worker-registry.json`
(schema: `schemas/worker-claim-grant-projection-request.schema.json`, contract:
`contracts/worker-claim-grant-projection-transition.v1.json`).

The worker registry is never hand-edited for a grant. Commit the manifest
together with the bytes `python scripts/worker_claim_grant_projection_transition.py apply`
derives; `.github/workflows/worker-claim-grant-projection-transition.yml` re-derives
from the base and the Organization ledger and fails closed on any divergence.

No manifest exists yet: none of the pending allocator requests has a GRANTED receipt.
