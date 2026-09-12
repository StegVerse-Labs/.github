# Site ECE Current Projection Materializer Mirror Handoff

Updated: 2026-09-12

```text
Goal Task ID: SITE-ECE-CURRENT-PROJECTION-MATERIALIZER-001
Parent Task ID: ECOSYSTEM-CONTINUITY-EVALUATOR-001
COSV: 71000000102000
Repository owner: StegVerse-Labs/Site
State: ACTIVE / MATERIALIZER + HEALER BINDING MERGED+VALIDATED / AUTHENTIC MATERIALIZATION PENDING
Authority effect: NONE_COPY_ONLY
GitHub runtime authority: NONE
User verification authority: KV/SKAP Vault
Device verification policy/process: NONE / PROHIBITED
```

## Goal

Materialize only the exact already-retained Site-safe ECE projection into the served Site data namespace as `data/ecosystem-continuity/current.json`, after validating the completed resident cycle receipt, projection reference, and SHA-256. The materializer does not calculate continuity, synthesize fallback state, mutate source repositories, or treat publication as recovery proof.

## Mandatory no-device-verification invariant

This task inherits `docs/DEVICE_VERIFICATION_AUTHORITY_INVARIANT.md` and `data/task-registry-global-invariants.json`.

- KV/SKAP Vault is the sole user-verification authority.
- StegOS devices are interchangeable transport/execution nodes.
- There is no device-verification policy, device-attestation gate, physical-device identity gate, or device-bound user-authority requirement.
- Connector/device-list observations describe only execution-surface connectivity/liveness. They do **not** mean authorized, verified, trusted, user-verified, or authority-bearing.
- Interlock/InTr remains governed transition authority; TV/TVC remains credential authority.

## Frozen chain

```text
SDK diagnostic result
-> ECE evaluation
-> Master Records custody/reconstruction
-> Site-safe projection
-> bounded exact-byte materializer
-> served current.json
-> read-only Site panel
```

No stage in this chain requires device identity or device verification.

## Canonical registration

`.github` PR #1581 merged at `a72868cbf61982298e8526b3a6009653eb13b2e5` from exact head `32a13eeef92da2723b448f40b2582495fbd5e4ef`.

```text
Heartbeat: 34677323438 PASS
Deterministic Repository Suite: 34677323346 PASS
Organization Control: 34677323338 PASS
```

Canonical issue: `.github#1577`.

## Site materializer — merged and validated

Site PR #1275 merged at `76f914cac2fc725141e1704ec50a20020d7124ee` from exact head `4019ac3711a82933dfbcdc1bf12d1e4d422b53c5`.

```text
Ecosystem Heartbeat Orchestration: 34677359459 PASS
Site Handoff Orchestrator: 34677359423 PASS
Site Bootstrap Validate: 34677359421 PASS
```

The Site claim was terminalized through PR #1276 at merge `808a5ccb6c3d77f7ec16f1b8bbe90900b9ddf332` after Heartbeat `34677412153`, Handoff Orchestrator `34677412156`, and Site Bootstrap `34677412172` PASS.

The materializer requires a completed `stegverse.healer-ecosystem-continuity-cycle/v1` receipt, exact `site_projection_ref`, exact SHA-256 equality, Site-safe projection schema `stegverse.site-ecosystem-continuity-projection.v1`, `authority_effect=NONE_READ_ONLY_PROJECTION`, `source_available=true`, `projection_error=null`, and a valid `ece_` source evaluation id. It atomically copies exact projection bytes to `<served-site-root>/data/ecosystem-continuity/current.json` and forbids source-repository writeback.

## Healer binding — merged and validated

Healer PR #66 merged at `be8ed7e5fb5f18602a6519b31aa4080bfd8cdf1b` from exact head `1aee2eae26ab8dfb67e675ae6fa4ea219821f5a9`; Test Readiness `34677527923` PASS.

After the SDK diagnostic -> ECE -> Master Records -> Healer intake -> Site-safe projection cycle completes, `app/run_ece_periodic_evaluation.py` optionally invokes the materializer when `STEGVERSE_SITE_SERVED_ROOT` is locally bound.

```text
no served-root binding -> cycle COMPLETE + site_materialization_state=NOT_BOUND
explicit served-root binding + valid materialization -> MATERIALIZED_PENDING_PUBLIC_OBSERVATION
explicit binding + materialization/receipt/source error -> BLOCKED
```

## Current runtime boundary

Latest evidence-surface observation:

```text
remote execution connector surfaces observed: 0
connector observation authority effect: NONE_CONNECTIVITY_OBSERVATION_ONLY
connected Drive ECE/materialization artifacts: none found
authentic Site-safe current projection materialized: NOT OBSERVED
public page rendering exact current projection: NOT OBSERVED
```

The first line is **not** a device-verification or authorization predicate. It only states that the external remote-execution connector exposed no callable execution surface to this session. ECE proof does not require a particular device identity.

No source merge, CI run, materializer unit test, connector device list, or empty search result is promoted into runtime/publication evidence.

## Remaining predicates

1. Observe one authentic resident `RT-ECOSYSTEM-CONTINUITY-EVALUATION-001` cycle from any eligible interchangeable StegOS execution node with all required already-local roots and a locally bound `STEGVERSE_SITE_SERVED_ROOT`.
2. Require the exact SDK diagnostic result, ECE evaluation, Master Records custody/reconstruction, Healer intake, Site-safe projection, and `site-materialization.latest.json` from that same cycle.
3. Require cycle state `MATERIALIZED_PENDING_PUBLIC_OBSERVATION` and exact current-projection SHA equality.
4. Independently observe the served `data/ecosystem-continuity/current.json` and the Site continuity page rendering those bytes before claiming live projection.
5. Recovery remains unverified until a later independent ECE evaluation observes repaired predicates PASS with acceptable freshness/evidence.

There is no required iPhone identity, pinned device, device verifier/sign gate, device attestation, or device-verification process anywhere in these predicates.
