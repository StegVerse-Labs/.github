# KV-Bound Ephemeral Browser Projection Mirror Handoff

Updated: 2026-09-09

Goal Task ID: `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`
Parent Goal: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`
Root Goal: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
COSV: `50000010100000`
Canonical issue: `StegVerse-Labs/.github#1299`
Active implementation PR: `StegVerse-Labs/StegOS#314`
Status: `ACTIVE / KV PROJECTION GATE IMPLEMENTED / PRODUCER BINDING + BRANCH RECONCILIATION PENDING`

## Purpose

Continue the current-iPhone/TestFlight/global-measurement pathway while implementing the clarified KV-centered continuity/privacy architecture before further bootstrap materialization bakes browser/device assumptions into runtime source.

## Canonical architecture

The canonical privacy and continuity contract is `StegVerse-Labs/continuity-vault-kit/docs/KV_PRIVACY_STATE_TRANSITION_CONTINUITY.md`.

Required invariants:

- KV is the private governed state-transition continuity boundary for user-associated state.
- Continuity follows admitted KV state-transition lineage, not persistence of a device, browser, carrier, network, provider, or storage medium.
- A physical device is an interchangeable interoperability node after proof of control and successful reconstruction/validation of an existing KV.
- StegOS is the runtime node associated with an admitted device relationship.
- StegBrowser is the browser-capability node; Safari, Chrome, Opera, Google-app browsers, ChatGPT internal browser/webviews, and comparable browser containers are ephemeral transition/presentation surfaces.
- Browser-local IndexedDB, service workers, cookies, browser profiles, and historical bootstrap stores are not sovereign identity roots.
- Browser/container observations, device/carrier/network/provider/session metadata, and other correlatable information remain behind KV whenever technically possible.
- Outside entities require fresh purpose-bound admission material whose provenance resolves to admitted state inside KV; externally observable identity alone is insufficient.
- Substantive browser UI/code/WASM presentation materializes only after the KV entry transition dependency is satisfied and actual browser/container capability is observed.
- A minimal public rendezvous may exist only to initiate discovery/confirmation; it is not the private environment, continuity root, or authority plane.
- Presentation packets are ephemeral, integrity-bound, purpose-scoped, and non-authorizing.

## State-transition continuity

For prior KV state `S_n`, an observation/proposal `O_n` is resolved against KV governance, constraints, admissibility, permitted-action matrices, and consequence-state rules. Observation alone does not advance state. Admitted, denied, retained, deferred, or reconstructed outcomes preserve continuity only through the resulting transition commitment.

## Current source trajectory retained

The current TestFlight pathway remains valid in principle:

```text
current-iPhone bootstrap/rendezvous
-> exact signer/WASM availability
-> TVC provider operation
-> ephemeral current-iPhone signing + same-session verification
-> TVC Build Upload
-> TestFlight install
-> retained runtime/node observation
-> one measurement-only global convergence run
```

The bootstrap/presentation seam is now being implemented as:

```text
minimal rendezvous
-> KV/device continuity confirmation
-> KV entry transition/admission
-> browser/container capability observation
-> ephemeral private projection materialization
-> governed action
-> consequence-state commitment
-> projection/session disposal
```

Static signer/WASM source may still need to be distributable before the first TestFlight installation, but static availability does not make the public bootstrap a persistent private presentation or identity root.

## 2026-09-09 branch audit and repair

Audited `StegVerse-Labs/StegOS:feat/current-iphone-wasm-static-bootstrap-001` against this architecture.

Observed mismatch before repair:

- `mobile/web-bootstrap/current-iphone-testflight.html` directly invoked the complete static TestFlight signing bootstrap from the public page.
- `mobile/web-bootstrap/current-iphone-testflight-bootstrap.js` accepted only fetch/provider parameters and did not require a KV-originating admission predicate or browser-capability observation before private signing materialization.
- The branch was 24 commits ahead and 1 commit behind `main` at audit time, so it is not yet ready for promotion without branch reconciliation.

Implemented repair in PR #314 branch:

- `mobile/web-bootstrap/kv-bound-ephemeral-projection-context.js` now validates a purpose-bound `CURRENT_IPHONE_TESTFLIGHT_SIGNING` context.
- The gate requires `entry_state=ADMITTED`, an opaque KV transition commitment, an opaque admission commitment, `browser_capability_state=OBSERVED_COMPATIBLE`, and an opaque browser-capability commitment.
- The gate declares `persistence_effect=NONE_EPHEMERAL_CONTEXT_ONLY` and `authority_effect=NONE_PROJECTION_GATE_ONLY`.
- The injected projection context is consumed from `window.__STEGVERSE_KV_PROJECTION_CONTEXT__` and deleted immediately; the gate itself does not use localStorage, sessionStorage, IndexedDB, cookies, user-agent identity, or browser-local persistence.
- `current-iphone-testflight-bootstrap.js` validates the projection context before loading/materializing the unsigned IPA.
- The public TestFlight page now fails closed when a valid ephemeral KV projection context is absent.
- `tests/test_kv_bound_ephemeral_projection_gate.py` adds deterministic source-level regression coverage for the admission/capability gate and no-browser-storage-root semantics.
- PR #314 metadata was reconciled from the exhausted parent goal to this successor Goal Task ID.

Implementation commits:

```text
829b979959837b0dc8f834a53a379d3f86af4023  add KV-bound ephemeral projection gate
0de7050ba9c9a1949f524a8ea19fa757104f027a  require gate before TestFlight materialization
747d20c9ab7e9ce06b09c67dff604ebe06847670  consume ephemeral KV projection context in public page
2b5cc7bd8886309bc1a228d8d03b58f83233a887  add projection-gate regression coverage
```

## Preserved exact signer artifacts

The validated signer artifact remains unchanged by this reconciliation:

```text
artifact: stegos-current-iphone-wasm-web
artifact digest: sha256:cef2ef22a42195dced25bca2f9c99fab9f6a32f21062f1576386ee69a25d48ee
wasm sha256: 699dc3054788d779ba7920e332c661ef7eac001156f93ab7b1fe1b64ee5a4b93
wasm bytes: 2277815
glue sha256: 17fe61cfdae43cbe5a1d211beb39838f58e982efdba90c7156fc36402f3adb
```

## Remaining source sequence

1. Bind the producer that creates the purpose-bound KV transition/admission commitment and browser-capability commitment consumed by the new gate; do not synthesize those values in the public page.
2. Reconcile/rebase PR #314 against current `main` without dropping the exact static artifact or the new KV gate.
3. Run exact-head CI and remediate any regression from the gate or rebase.
4. Reconcile StegOS retained-node semantics so device identity remains interoperability rather than user continuity and StegBrowser remains capability continuity.
5. Reconcile continuity-vault-kit, StegOS, Site, and global measurement source/docs around the same admission/projection contract.
6. Merge only after source validation is green.
7. Continue TVC provider activation, real signing/upload, TestFlight install, authentic retained-node evidence, and exactly one frozen measurement-only convergence pass.

## Runtime truth

No authentic current-iPhone TestFlight install, retained-node materialization, KV-bound browser projection runtime, or global convergence receipt is claimed by this source reconciliation.

## Manual work

None while producer binding, branch reconciliation, CI, and source integration remain machine-executable.
