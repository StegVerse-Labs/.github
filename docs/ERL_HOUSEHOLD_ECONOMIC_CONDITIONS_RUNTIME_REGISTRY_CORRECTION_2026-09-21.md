# ERL household economic conditions — Task Registry runtime correction

Updated: 2026-09-21
Goal Task ID: `ERL-HOUSEHOLD-ECONOMIC-CONDITIONS-SITE-001`

## Canonical runtime rule reviewed

`data/task-registry-global-invariants.json` applies to this task. Ordinary task progression must not query, inspect, depend on, or report connected-device inventory. Zero connected devices has no task-state meaning. Execution-surface reachability is evidence reachability only and cannot become a blocker, fallback condition, external-device requirement, or reason to stop progression.

The canonical authority chain remains:

```text
Task Registry = work/dependency/coordination truth
Interlock/InTr = governed ingress/transition admission
WorkerCoordinator = executable assignment/claim/fence
TV/TVC = credential/bounded capability authority
Master Records = observed runtime reality/custody/reconstruction
```

Source, merge, CI, runtime-profile compatibility, connector availability, and handoff prose do not prove runtime execution.

## Correction to prior BEA observation

The 2026-09-21 reconciliation recorded zero connected execution devices while assessing BEA readiness. That observation is retained only as historical provenance. It is superseded as a task-progression fact and MUST NOT gate this Goal Task.

The actual unresolved predicate is narrower: authentic TV/TVC resident evidence with schema `stegverse.tvc.bea-credential-readiness/v1` and `decision=READY`. Absence of a repository-visible READY receipt does not prove non-occurrence; it leaves the predicate unresolved until canonical runtime evidence is retained/reconstructed.

## Correct next runtime sequence

```text
canonical Task Registry check-in
-> existing Canonical Work / Interlock-InTr ingress
-> fresh WorkerCoordinator claim/fence
-> existing metadata-only TV/TVC BEA readiness observation
-> if READY: exact one bounded single-use BEA lease and existing provider-operation/vault-broker path
-> retain non-secret result evidence
-> Master Records custody/reconstruction
-> Task Registry reconciliation
```

No new runtime, scheduler, WorkerCoordinator, credential path, request plane, or second user-operated device is permitted.

## Source-path defect discovered

Reviewing runtime composition also exposed that the BEA profile/lease existed but both provider-operation brokers still fell through to model/prompt measurement logic, and the resident vault-agent allowlist did not admit the BEA secret reference. TVC PR #451 and stegfin-governance PR #111 repair only those existing-path seams. They do not establish credential readiness or perform a BEA call.

Authority effect: `NONE_COORDINATION_AND_SOURCE_REPAIR_ONLY`.
