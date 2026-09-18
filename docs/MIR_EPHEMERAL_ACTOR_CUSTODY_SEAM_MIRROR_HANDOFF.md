# MIR / Ephemeral Actor Custody Seam mirror handoff

Updated: 2026-09-17
Goal Task ID: `MIR-EPHEMERAL-ACTOR-CUSTODY-SEAM-001`
Parent Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / EPHEMERAL-ACTOR PRESSURE TEST MATERIALIZED / RUNTIME PROOF NOT REQUIRED`

## Trigger

A user-supplied LinkedIn conversation with Richard Whitney presents the spawn case: a subagent exists for roughly forty seconds, receives standing from a root, is attributable at the leaf, remains accountable to a human, and the caller is not permitted to name its own lineage. Richard asks whether the Evidence Custody Seam survives a recorded actor being created and destroyed inside one commitment window and whether Sections 3 or 4 must say so explicitly.

The public short-link itself was not independently resolved by the current web fetch, so this task treats the user-supplied screenshots and quoted scenario as the source for the pressure test rather than claiming independent observation of the LinkedIn post.

## Current conclusion

The seam survives. Actor persistence is not a custody prerequisite. What must persist is the evidence binding the short-lived actor instance to the transition it performed and, where standing or lineage matters, to an externally attributable provenance/authority artifact.

The important distinction is:

```text
root standing / admitted authority
        |
        v
externally attributable spawn or lineage reference
        |
        v
ephemeral actor instance
        |
        v
leaf action / result / transition record
        |
        v
durable custody and reconstruction
```

The ephemeral actor or its caller may carry a reference to lineage, but neither may be the sole authority for that lineage. Evidence custody records the provenance artifact and preserves its proof scope; custody does not create identity, standing, governance, admission, or accountability authority.

## Canonical clarification

The post-freeze reference-architecture draft now states:

1. an actor may be created and destroyed inside one commitment window;
2. when lifecycle matters, the receipt binds actor instance identity plus creation/expiry/termination state;
3. standing or lineage must point to an externally attributable origin/admission artifact rather than caller self-description;
4. destruction of the actor does not weaken a properly retained record;
5. leaf attribution, root standing, and human accountability are separate claims and must not be collapsed into one self-attested field.

This is a clarification of receipt semantics, not a new authority plane and not a requirement for long-lived actor identity.

## Sections 3 and 4 effect

Section 3's existing submitter rule already does most of the work: a submitter may report what it observed but may not smuggle unobserved provenance into custody as fact. The new clarification makes that rule explicit for spawned/ephemeral actors.

Section 4 does not need a new independent receipt class solely because an actor is short-lived. The existing common receipt envelope and Evidence Custody receipt fields need explicit actor-instance, lifecycle-when-material, and externally attributable lineage/standing references.

## Authority boundaries

- Governance/admission may establish standing for exact work.
- Execution/runtime may materialize a short-lived actor and provide execution-time identity.
- The caller may reference, but not invent or self-authorize, lineage.
- Evidence custody retains/reconstructs the resulting artifacts.
- Observability may report lifecycle/timing but grants no standing.
- GitHub/GitHub Actions remain source-validation/evidence-transport only; runtime authority `NONE`.

## Next action

Reconcile this clarification against Richard Whitney's next Evidence Custody Seam revision. If his wording preserves actor ephemerality without allowing self-declared lineage, accept it as a compatible refinement; otherwise propose the minimum normative sentence needed in Sections 3/4 without creating a new receipt class or identity authority.
