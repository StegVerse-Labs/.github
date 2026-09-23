# Organization Batch Custody and Replay

Goal Task ID: ORGANIZATION-BATCH-CUSTODY-REPLAY-001
COSV ID: 10000000100000
Status: ACTIVE / HANDOFF_READY; canonical registration merged in PR #2582 (ed49711678dc9ffb0627a65e66a1d83110f9afc4).

## Purpose
Clarify the existing organizational receipt hierarchy: individual state transitions remain replayable at organization level; independently verified bounded organization batches are delivered to Master Records for cross-organization custody and complex reconstruction. This is a refinement of previous documentation, not a new authority plane or production execution claim.

## Ownership
WorkerCoordinator retains worker claim/fence, expiry and reassignment. Task Registry owns durable task state and successor obligations. Interlock/InTr owns transition governance; TV/TVC owns credentials. The existing organization ledger owns exact locally reconstructable worker/task/sequence receipts and hash-linked batches. Master Records verifies batches, preserves durable global custody and reconstructs cross-organization histories without acquiring transition authority.

## Failure and expiry
A genuinely irrecoverable worker failure must preserve its exact evidence and last closed transition, expire the existing fenced assignment through WorkerCoordinator, update canonical Task Registry with durable failure and successor owner, record the worker-expiry receipt in the existing organization ledger, and trigger immediate batch closure. An individual blocked work item does not automatically expire a worker with other lawful work. When custody itself fails, preserve the incident on existing durable worker/task failure surfaces, with pending custody explicitly marked; do not fabricate a completed state transition or introduce another failure mailbox.

## Batch boundaries
Use one ordered hash-linked organization ledger. Batch closure may be routine (time/size after measurement), task closure, worker expiry, consequential governed transition, recovery of pending custody, or inter-organization handoff. Batch classification is metadata, not separate ledgers. A batch commits exact organization identity, contiguous sequence range, prior batch hash, first/last org receipt hashes, ordered receipt hashes/commitment, required-evidence commitment, cross-boundary predecessors, closure reason and Master Records acknowledgement status. Validate no omission, duplication, broken predecessor or reorder; retain unacknowledged batches locally and use existing authorized transport with idempotent retry.

## Replay
Local organization replay must reconstruct individual worker, task and sequence receipts and required evidence without requiring Master Records to be online. Master Records must independently verify organization batches and reconstruct relationships spanning organizations. Where a transition contract explicitly requires immediate Master Records acknowledgement, local-only replay or queued batch submission cannot authorize progression.

## Existing code and evidence boundary
Reconcile resident-runtime/aggregate_repo_transition.py, .stegverse/transition-ledger/org-contract.json, workers/canonical_state_transition_custody.py, the existing WorkerCoordinator expiry and Task Registry paths, master-records/orchestration/services/ecosystem_transition_ledger.py, and services/canonical_state_transition_custody.py. Existing Master Records receipt-set commitments do not themselves establish organizational batch delivery. Source/CI is not runtime proof. Require authentic retained organization and Master Records receipts for runtime closure, including RECORDED, reconstruction PASS, required-evidence PASS and exact digest equality where required.

## Scope
Register canonical Goal and COSV, verify existing source seams, define minimal existing-surface batch ingress, add positive/negative replay and failure tests, and reconcile live receipts. No new ledger, runtime, scheduler, dispatcher, WorkerCoordinator, custody store, authority plane, source transport, credential route, device or manual device step.
