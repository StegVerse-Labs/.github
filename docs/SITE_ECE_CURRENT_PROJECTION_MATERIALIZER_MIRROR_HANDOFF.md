# Site ECE Current Projection Materializer Mirror Handoff

Updated: 2026-09-12

```text
Goal Task ID: SITE-ECE-CURRENT-PROJECTION-MATERIALIZER-001
Parent Task ID: ECOSYSTEM-CONTINUITY-EVALUATOR-001
COSV: 71000000102000
Repository owner: StegVerse-Labs/Site
State: ACTIVE / SOURCE IMPLEMENTATION STARTING
Authority effect: NONE_COPY_ONLY
GitHub runtime authority: NONE
```

## Goal

Materialize only the exact already-retained Site-safe ECE projection into the served Site data namespace as `data/ecosystem-continuity/current.json`, after verifying the completed resident cycle receipt, projection reference, and SHA-256. The materializer must not calculate continuity, synthesize fallback state, mutate source repositories, or treat publication as recovery proof.

## Frozen chain

```text
SDK diagnostic result -> ECE evaluation -> Master Records custody/reconstruction -> Site-safe projection -> bounded materializer -> served current.json -> read-only Site panel
```

## Required proof

The materializer must require a completed `stegverse.healer-ecosystem-continuity-cycle/v1` receipt whose `site_projection_ref` resolves to the supplied projection and whose `site_projection_sha256` equals the exact input bytes. The projection itself must be `stegverse.site-ecosystem-continuity-projection.v1` with `authority_effect=NONE_READ_ONLY_PROJECTION`, `source_available=true`, `projection_error=null`, and a valid `ece_` source evaluation id.

## Prohibited

- deriving or changing continuity state;
- accepting a projection whose bytes do not match the cycle receipt;
- source-repository writeback as runtime publication;
- stale/browser-local fallback;
- treating materialization as ECE recovery verification;
- GitHub Actions as runtime authority.

## Next

Implement and validate the bounded Site materializer plus Healer invocation binding. Authentic public materialization remains unproven until resident/public runtime evidence exists.
