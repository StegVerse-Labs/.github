# SV-011 Phase-5 Source Materialization Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Issue: `#806`  
Final implementation PR: `#807`  
State: SOURCE_CONTROL_MERGED_VALIDATED / AUTHENTIC_RESIDENT_MATERIALIZATION_PENDING  
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


## Source/control completion — 2026-09-02

Final implementation:
- issue `#806`
- PR `#807`
- merge `dccf1015eff9bcc398b43a7e9dd4a4ff1c53111e`

Installed:
- exact seven-file source bundle under `source-bundles/sv011-phase5/`;
- manifest pinned to `SV-011/.github@cf2777d9d21a97289f4ec7b0d9b0b21597047666`;
- worker `SHWP-SV011-PHASE5-SOURCE-MATERIALIZATION-001`;
- intent request `RESIDENT-EXEC-SV011-PHASE5-SOURCE-MATERIALIZATION-001`;
- process adapter and at-most-once resident consumer;
- dispatcher order `sv011_phase5_source_materialization -> sv011_phase5`;
- source-refresh carriage of `source-bundles`;
- source-refresh watcher coverage for bundle changes;
- Admissible-Existence binding at `ADMISSIBLE`;
- COSV vector `50000000101000`;
- Phase-5 worker support for either a clean pinned Git checkout or a verified materialized tree.

Exact-head validation before merge:
- Cross-Framework Current-Basis Resident Request Validation run `33683287492`: SUCCESS
- Validate organization control plane run `33683287217`: SUCCESS
- Heartbeat Worker Project run `33683287285`: SUCCESS

Post-merge:
- resident-request validation run `33683404724`: SUCCESS
- Heartbeat Worker Project run `33683404628`: SUCCESS
- Workspace DEVICE_KV validation run `33683404742`: SUCCESS

These are source/control results only. No authentic resident filesystem materialization is inferred.

## Remaining machine-owned transition

The existing resident refresh/dispatcher can now:
1. carry the exact source bundle into resident WorkerCoordinator source;
2. visit `sv011_phase5_source_materialization`;
3. materialize and post-write verify the seven files locally;
4. then visit `sv011_phase5` in the same dispatcher pass.

Authentic evidence still required:
- materialization request-consumption receipt;
- `SHWP-SV011-PHASE5-SOURCE-MATERIALIZATION-001` COMPLETED receipt;
- then the existing Phase-5 boundary ALLOW/DENY receipts.

No human source-copy step is required.
