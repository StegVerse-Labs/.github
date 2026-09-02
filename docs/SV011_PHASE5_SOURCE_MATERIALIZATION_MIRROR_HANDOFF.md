# SV-011 Phase-5 Source Materialization Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Issue: `#806`  
Branch: `feat/sv011-phase5-source-materialization-806`  
State: SOURCE_IMPLEMENTATION_ACTIVE  
Authority effect: NONE_SOURCE_MATERIALIZATION_ONLY  
Activation effect: false

## Goal

Materialize the seven exact SV-011 Phase-5 organization-boundary source files on the sovereign resident node before `SHWP-SV011-PHASE5-BOUNDARY-001` runs, without network source fetch, credentials, a second scheduler, or authority widening.

## Why this lane is distinct

The Phase-5 boundary worker is intentionally forbidden from acquiring source. Its current clean-Git-checkout requirement therefore leaves a real execution prerequisite when `SV-011/.github` is not already present locally.

This lane owns only:

```text
exact-byte source bundle carried with canonical WorkerCoordinator source
-> Git-blob identity verification
-> atomic local materialization
-> post-write verification
-> source-materialization receipt
```

It does not execute the Phase-5 ALLOW/DENY probes.

## Canonical source identity

Repository: `SV-011/.github`  
Source-basis commit: `cf2777d9d21a97289f4ec7b0d9b0b21597047666`

Required files and Git blob SHA-1:
- `resident-runtime/run_phase5_probe.py` -> `bb66bb78e458bae91c71eaabc8d15724c8bf8cba`
- `resident-runtime/requests/phase5-allow.json` -> `b17f563acc051d45ca988b139ccc3d9321123251`
- `resident-runtime/requests/phase5-deny.json` -> `185f174d01a52e6db72dab60072ba429386311bb`
- `org-boundary/runtime/intr_transport.py` -> `c52bde0587f3203a7d77789d8735007a25bb6267`
- `org-boundary/runtime/process_boundary.py` -> `4a167a3af36f894e45362ee67f0a9050dca287fb`
- `org-boundary/runtime/denial_adapter.py` -> `207e9e9fab484ed3c3a2bdf622ba1580e354c6b8`
- `org-boundary/registry/services.json` -> `08bd4ba431a071a17abba76ac45536f92ebb7f6e`

## Resident destination

Default:
`~/.stegverse/source/SV-011/.github`

Optional non-secret override:
`STEGVERSE_SV011_MATERIALIZED_ROOT`

The destination is runtime materialization, not repository writeback.

## Authority / transport constraints

- `credential_authority = TV/TVC`
- no GitHub token
- no network fetch
- no repository mutation
- no provider operation
- no heartbeat authority
- no request-granted execution authority
- no publication/proof/autonomy authority
- GitHub Actions validation is source/test evidence only

## Ordering

The resident dispatcher must visit:

```text
sv011_phase5_source_materialization
-> sv011_phase5
```

The second consumer may proceed only after the first has materialized a verified tree or an independently verified clean Git checkout already exists.

## Completion predicate

Materialization is COMPLETE only when all seven bundle files match their pinned Git blob identities before and after atomic installation and a secret-free receipt records the selected local root.

That completion is a source prerequisite only. It does not close Phase 5.
