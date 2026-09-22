# SV002 Frozen Corpus Resident Admission Observation — 2026-09-17

Goal Task ID: `SHWP-SV002-FROZEN-CORPUS-MATERIALIZATION-001`
COSV: `50000000107001`
Tracking issue: `StegVerse-Labs/.github#2064`

## Re-observation performed

The existing TVC private-source path was re-observed without creating a new source-read, credential, host, listener, or runtime path.

Four exact immutable requests remain staged in `StegVerse-Labs/TVC@main` for this Goal:

- `requests/private-source-read/SHWP-SV002-FROZEN-CORPUS-TT.json` -> `Admissible-Existence/TT@ab60b42934222a2cb5335a5a8194f258a491fc57`
- `requests/private-source-read/SHWP-SV002-FROZEN-CORPUS-RTG.json` -> `Admissible-Existence/RTG@ca69954cb3dc4ad073c9244e003bc8f0ef3837e2`
- `requests/private-source-read/SHWP-SV002-FROZEN-CORPUS-GTG.json` -> `Admissible-Existence/GTG@8cdb7bce87bb9f8429c35e9c66cc5dc28a46a225`
- `requests/private-source-read/SHWP-SV002-FROZEN-CORPUS-AE.json` -> `Admissible-Existence/AE@53c8eedddc4e54d8fa0660039d65ab9ac63057a1`

All are `IMMUTABLE_COMMIT`, TTL 600 seconds, consumer task `SHWP-SV002-FROZEN-CORPUS-MATERIALIZATION-001`, and source-read-only under TV/TVC authority.

## Authentic resident evidence result

No authentic host receipt was observed for:

- `/var/lib/stegverse/private-source-read/service-installation-receipt.json`;
- `/var/lib/stegverse/private-source-read/resident-state.json`;
- any of the four SV002 materialization IDs;
- any four-way `authorized_exact_sha == observed_exact_sha` materialization set.

The authorized direct machine connector currently reports no online device. Under StegVerse event-ephemeral semantics, zero standing devices is not itself a failure; it only means direct filesystem observation was unavailable at this instant.

The already-existing machine-owned delivery dependency was re-identified as:

`TVC-PRIMARY-RUNTIME-ACTIVATION-DELIVERY-006 -> TVC-RESIDENT-SERVICE-SELF-HEAL-001`

`TVC-RESIDENT-SERVICE-SELF-HEAL-001` currently remains `SOURCE_REBIND_VALIDATED_AUTHENTIC_HOST_EXECUTION_PENDING` / `SOURCE_REBIND_VALIDATED_RUNTIME_UNOBSERVED`. Its root owner is `stegtvc-primary-runtime.service`, and its machine entrypoint is `scripts/tvc_resident_service_self_heal.py --watch`.

The relevant reusable binding remains `RT-TVC-PRIMARY-RUNTIME-BINDING-001`; it explicitly reuses the existing TVC binder and activation-delivery path and forbids a duplicate host/runtime.

## First concrete blocker

`DEPENDENCY_TVC_RESIDENT_SELF_HEAL_AUTHENTIC_HOST_EXECUTION_NOT_OBSERVED`

This replaces the broader transport wording as the first actionable blocker. The exact source coordinates are already staged. The missing transition is authentic event-ephemeral execution of the existing TVC primary-runtime/self-heal delivery chain so the staged requests can be consumed under genuine TV/TVC credential authority.

Do not:

- create a second private-source implementation;
- use `GITHUB_TOKEN`, `GH_TOKEN`, PAT, provider, connector, or user credentials as a substitute;
- treat GitHub request files, CI, source validation, or preflight receipts as materialization;
- infer credential presence from service source;
- infer four-way materialization until four secret-free execution receipts prove exact SHA equality.

## Required next evidence

1. authentic `SERVICE_INSTALLED_VERIFIED` receipt from the existing TVC resident path;
2. authentic resident-state observation;
3. credential presence observation without credential disclosure;
4. consumption of the four already-staged immutable requests;
5. four receipts with `authorized_exact_sha == observed_exact_sha == requested exact_sha`;
6. only then run the unchanged SV002 native bundle builder and continue the already-proven downstream sandbox chain.

Authority effect: `NONE_COORDINATION_AND_EVIDENCE_OBSERVATION_ONLY`.
