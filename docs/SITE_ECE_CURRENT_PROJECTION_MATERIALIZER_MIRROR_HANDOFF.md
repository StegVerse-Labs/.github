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
```

## Goal

Materialize only the exact already-retained Site-safe ECE projection into the served Site data namespace as `data/ecosystem-continuity/current.json`, after verifying the completed resident cycle receipt, projection reference, and SHA-256. The materializer does not calculate continuity, synthesize fallback state, mutate source repositories, or treat publication as recovery proof.

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

The initial validation failure was caused only by an invalid pre-work claim state (`ACTIVE`). It was repaired to `CLAIMED_FOR_IMPLEMENTATION`; no materializer semantics changed.

The Site claim was terminalized through PR #1276 at merge `808a5ccb6c3d77f7ec16f1b8bbe90900b9ddf332` after Heartbeat `34677412153`, Handoff Orchestrator `34677412156`, and Site Bootstrap `34677412172` PASS.

### Materializer contract

`scripts/materialize_ecosystem_continuity_current.py` requires:

- completed `stegverse.healer-ecosystem-continuity-cycle/v1` receipt;
- exact `site_projection_ref` equality;
- exact SHA-256 equality with `site_projection_sha256`;
- Site-safe projection schema `stegverse.site-ecosystem-continuity-projection.v1`;
- `authority_effect=NONE_READ_ONLY_PROJECTION`;
- `source_available=true` and `projection_error=null`;
- valid `ece_` source evaluation id and safe finding fields.

It atomically copies the exact projection bytes to `<served-site-root>/data/ecosystem-continuity/current.json`. If a Site source root is provided, writing the served root into or under that source repository is forbidden.

The emitted materialization receipt states:

```text
schema = stegverse.site-ecosystem-continuity-materialization-receipt.v1
authority_effect = NONE_COPY_ONLY
exact_bytes_preserved = true
continuity_recalculated = false
source_repository_writeback = false
live_publication_observed = false
recovery_verified = false
```

## Healer binding — merged and validated

Healer PR #66 merged at `be8ed7e5fb5f18602a6519b31aa4080bfd8cdf1b` from exact head `1aee2eae26ab8dfb67e675ae6fa4ea219821f5a9`; Test Readiness `34677527923` PASS.

After the existing SDK diagnostic -> ECE -> Master Records -> Healer intake -> Site-safe projection cycle completes, `app/run_ece_periodic_evaluation.py` optionally invokes the materializer when `STEGVERSE_SITE_SERVED_ROOT` is already locally bound.

```text
no served-root binding -> cycle COMPLETE + site_materialization_state=NOT_BOUND
explicit served-root binding + valid materialization -> MATERIALIZED_PENDING_PUBLIC_OBSERVATION
explicit binding + materialization/receipt/source error -> BLOCKED
```

The binding does not fetch source, create another scheduler, calculate continuity, or claim live page publication.

## Current runtime boundary

Latest re-observation in this implementation session:

```text
authorized remote devices: 0
connected Drive ECE/materialization artifacts: none found
authentic Site-safe current projection materialized: NOT OBSERVED
public page rendering exact current projection: NOT OBSERVED
```

No source merge, CI run, materializer unit test, or absence of errors is being promoted into runtime/publication evidence.

## Remaining predicates

1. Observe one authentic resident `RT-ECOSYSTEM-CONTINUITY-EVALUATION-001` cycle with all required local roots and an already-local `STEGVERSE_SITE_SERVED_ROOT` binding.
2. Require the exact SDK diagnostic result, ECE evaluation, Master Records custody/reconstruction, Healer intake, Site-safe projection, and `site-materialization.latest.json` from that same cycle.
3. Require cycle state `MATERIALIZED_PENDING_PUBLIC_OBSERVATION` and exact current-projection SHA equality.
4. Independently observe the served `data/ecosystem-continuity/current.json` and the Site continuity page rendering those bytes before claiming live projection.
5. Recovery remains unverified until a later independent ECE evaluation observes repaired predicates PASS with acceptable freshness/evidence.

## Documentation maintenance

Site and SDK root README bookkeeping still has patch-safe follow-up items from earlier tranches. Do not replace or truncate large README files merely to satisfy indexing.
