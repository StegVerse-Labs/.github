# Organization Handoff Control Plane v0.2

**Status:** implementation proposal and minimum-core specification  
**Date:** 2026-08-06  
**Authority target:** `StegVerse-Labs/.github`  
**Human entry/exit surface:** `docs/ORG_MIRROR_HANDOFF.md`

## 1. Governing rule

All organization-scoped work begins by reading the organization handoff and the applicable repository-local handoffs. No work cycle is organizationally closed until its result, evidence, remaining work, and authority state are incorporated through the organization control plane and reflected in the generated organization handoff.

The organization handoff is the primary entry point and sole organizational exit point. Repository-local handoffs remain authoritative for repository-specific implementation evidence.

## 2. Control-plane correction

`StegVerse-Labs/.github` is not a claimable work resource. Tasks may submit only per-task proposals. Authoritative state may be changed only by designated allocator, reconciler, check-in validation, and handoff-rendering workflows.

```yaml
control_plane:
  repository: StegVerse-Labs/.github
  claimable: false
  task_write_paths:
    - tasks/<TASK-ID>.json
    - checkins/pending/<TASK-ID>.json
    - reports/deficiency/<REPORT-ID>.json
  authoritative_writers:
    - allocator_workflow
    - reconciler_workflow
    - checkin_validation_workflow
    - handoff_renderer_workflow
```

## 3. Minimum durable task model

Durable task states are limited to:

```text
proposed → queued → active → checkin_pending → completed
```

Orthogonal flags may coexist:

```text
blocked | suspended | superseded | reconciliation_required
```

Transient allocator and validation phases belong in immutable transaction receipts, not in task state.

## 4. Claims and atomic allocation

Tasks declare the complete mandatory claim set before activation. Claims identify fully qualified repositories, immutable provider IDs where available, paths, contracts, release surfaces, capabilities, and workflows.

Mandatory claims are granted atomically. Partial mandatory acquisition is forbidden. Optional claims are preemptible and may never block a higher-ranked mandatory claim.

The allocator serializes organization-state mutation through a protected control branch. Every grant, renewal, and release is a compare-and-swap operation against the control-branch head. A rejected non-fast-forward push is the abort primitive; the allocator must re-read, recompute, and retry within a bounded limit.

Atomic mandatory acquisition eliminates hold-and-wait repository deadlocks. A separate validator must reject cycles in the task dependency graph.

## 5. Queue activation

A queued task activates only when:

- every dependency is satisfied;
- every mandatory claim is available;
- its repository identities and base commits remain current;
- its scope remains required;
- it has not been superseded;
- the deterministic queue order selects it.

Queue order must be reproducible from published ordered criteria. No unexplained composite rank is authoritative.

## 6. Leases and fencing

Claims carry leases and monotonically increasing per-resource fencing tokens. The allocator workflow is the sole token issuer.

Pre-merge work is detected, not prevented. The enforcement point is a required merge status check that rejects a stale fencing token. Post-merge bypasses create reconciliation work.

Lease renewal requires either durable progress evidence or a still-valid accepted wait condition within a bounded renewal budget. A blocker may renew once by default, after which the task must suspend and release claims.

Default low-contention cadence:

```yaml
lease: 24h
heartbeat: 8h
```

Higher-contention service classes may shorten cadence through an allocator-recorded transition.

## 7. Purpose-bound heartbeat

A heartbeat is a nonce-bound round trip between the center and a claimant. The outbound half is the center's complete assertion of believed state. The return half is the claimant's counter-assertion plus current evidence. The center computes a typed delta vector.

Fields ride the heartbeat only when they exist on both halves and a comparison is defined:

- organization-state epoch;
- claims;
- fencing token;
- granted versus touched scope;
- expected versus actual base commit;
- policy version;
- evidence pointer;
- nonce;
- derived round-trip time.

Deterministic deltas trip immediately for fencing token, claims, scope, policy version, and nonce. Statistical observations such as RTT, jitter, miss rate, and epoch-lag distribution require declared or regime-specific learned baselines.

No composite health score is authoritative.

## 8. Three-channel observability

1. **Heartbeat loop:** center-initiated, symmetric, verified comparison.
2. **Subsystem streams:** continuously written evidence, read when a trigger opens a warrant.
3. **Deficiency reports:** unsolicited testimony that may open a warrant but may not close one or independently authorize a central state transition.

System heartbeat deviation is the rollup of per-claimant, per-field deltas so localization is immediate. Cross-claimant correlation distinguishes shared-path failure from isolated claimant failure.

## 9. Scan warrants and deficiency reports

A detected inconsistency opens or coalesces into a scan warrant. Warrants use their own `SCAN-*` identity space. A remediation task is created only after an actionable finding.

A subsystem may report `observation`, `degradation`, `impairment`, or `trauma`. Trauma causes local self-quarantine and an emergency checkpoint attempt. Central claim release remains allocator-controlled; suspension advances the fencing token.

A deficiency report must include a stream/time/offset locator. It may open a warrant but cannot close it or serve as sole proof of recovery.

## 10. Carrier integrity

Heartbeat transport must make missing and nominal-quiet distinguishable:

- no field has a valid empty default;
- the claimant signs or authenticates the complete outbound payload;
- payload hashes and monotonic sequences detect truncation and stall;
- expected return count measures continuity;
- an independent scheduled watchdog checks expected returns;
- fault-injection tests prove each modeled failure changes at least one measured dimension.

## 11. Check-in and sole exit

Implementation may be recorded as delivered only after merge and required validation. Operational outcomes such as blocked, suspended, rejected, transferred, or abandoned must still be incorporated through the organization exit boundary.

For multi-repository work:

```text
prepare repository check-ins
→ validate combined coherence
→ commit organization exit receipt
→ incorporate organization state
→ release claims atomically
```

Tasks submit per-task check-in proposals; they do not directly edit authoritative claim state or generated handoff sections.

## 12. Initial implementation sequence

### Phase 1 — minimum core

- machine-readable organization state;
- one-file-per-task records;
- active claims registry;
- append-only event log;
- task, claim, heartbeat, and check-in schemas;
- deterministic validator;
- generated handoff verification.

### Phase 2 — allocator and queue

- CAS allocator;
- dependency-cycle rejection;
- atomic claim grant and release;
- deterministic queue activation;
- per-resource fencing generations.

### Phase 2.5 — deterministic signal layer

- outbound assertion and nonce-bound return;
- deterministic delta comparisons;
- expected-return watchdog;
- scan warrant coalescing;
- observation and degradation report intake;
- fault-injection receipts.

### Phase 3 — check-in and reconciliation

- merge and validation checks;
- combined-state check-in barrier;
- organization exit receipts;
- reconciliation for bypasses and stale state;
- generated handoff projection.

### Phase 4 — advanced contention and recovery

- service-class cadence;
- statistical baselines;
- impairment and trauma automation;
- preemption and transfer;
- cross-organization federation.

## 13. Non-claims

This document does not claim the allocator, branch protection, required merge check, heartbeat transport, watchdog, or reconciliation loop is active. Installed state is limited to files and workflows present in Git history and validated by current CI.
