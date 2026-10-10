# HCB existing-goal Registry reconciliation

Goal Task ID: `HCB-VERSIONED-CONTRACT-038`
Canonical work Registry: `StegVerse-Labs/.github:data/canonical-task-registry.json`
Record projection: `data/canonical-task-records/HCB-VERSIONED-CONTRACT-038.json`
Canonical repository handoff: `StegVerse-Labs/hybrid-collab-bridge:HYBRID_COLLAB_BRIDGE_MIRROR_HANDOFF.md`
Coordination: CLOSED; checkout: RETIRED; COSV: `71000000100100`.
Evidence class: CI_VALIDATED source scope; no runtime activation or release.

## Why registration is required

The existing goal was absent from both the canonical Registry (generation 304)
and the organization summary registry. The canonical Registry explicitly owns
work intent and coordination; shards only enrich registered identities. This
change registers the existing owner-authorized goal at generation 305 and keeps
its shard identical. It creates no second Registry or WorkerCoordinator claim.
The owner's 2026-10-10 instruction authorizes resolution and terminal reconciliation.

## Evidence

HCB PRs #40–#46 are merged. Current source is
`0fd716a14bcf7dc04012926bac3d65022b23dcd6`; PR #46 head
`cbdacb6d448fcfacd5be473206919dcec94422d6` passed all five applicable workflows,
including hybrid-bridge-ci run `38029178254`. The 17 stdlib contract tests pass.
The optional versioned contract and source conformance are the terminal scope.
Canonical `scripts/cosv.py::encode_task` produces `71000000100100` with activation
and propagation false. Closure is source coordination, not runtime authority.

LLMA's separate disclosure ledger commit
`98738ceb6feee16a3de935319ec307c31719ba9d` verifies two chained organization receipts
and their retained sources. It is shared-path evidence, not an HCB invocation.
Master Records reconstruction is not claimed and does not gate source closure.
Provider execution, Sandbox activation, release and downstream propagation are
outside this task's authorized scope. No tag is authorized by source closure.

## Continuation

After exact-head validation and merge, reconcile the HCB root handoff to this
canonical location and close the source issue. Reopen only for new scoped evidence.
Manual work: None.
