# KV-Bound Ephemeral Browser Projection Mirror Handoff

Updated: 2026-09-09

Goal Task ID: `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`
Parent Goal: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`
Root Goal: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
COSV: `50000010100000`
Canonical issue: `StegVerse-Labs/.github#1299`
Status: `ACTIVE / ARCHITECTURE CANONICALIZED / IMPLEMENTATION NOT YET RECONCILED`

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

But the bootstrap/presentation seam must now be implemented as:

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

## Existing implementation to reconcile

Branch `StegVerse-Labs/StegOS:feat/current-iphone-wasm-static-bootstrap-001` was created while solving exact WASM distribution. Its current contract must be reviewed before continuing so it does not encode Safari ownership, browser-local continuity, or a permanently materialized private presentation.

The validated signer artifact remains:

```text
artifact: stegos-current-iphone-wasm-web
artifact digest: sha256:cef2ef22a42195dced25bca2f9c99fab9f6a32f21062f1576386ee69a25d48ee
wasm sha256: 699dc3054788d779ba7920e332c661ef7eac001156f93ab7b1fe1b64ee5a4b93
wasm bytes: 2277815
glue sha256: 17fe61cfdae43cbe5a1d1b211beb39838f58e982efdba90c7156fc36402f3adb
```

## Next execution sequence

1. Audit the existing StegOS static-bootstrap branch against the KV privacy/continuity contract.
2. Separate minimal public rendezvous source from post-KV private presentation source.
3. Define the KV entry dependency and purpose-bound KV-originating admission artifact required before private browser projection materializes.
4. Define browser/container capability observation as private KV state where possible; expose only opaque commitments/references downstream.
5. Rework signer/WASM delivery so exact static availability can bootstrap first installation without becoming browser/device continuity or public private-state storage.
6. Preserve browser-container neutrality and fail closed on missing required capability rather than user-agent identity.
7. Reconcile StegOS retained-node semantics so device identity is interoperability rather than user continuity and StegBrowser remains capability continuity.
8. Reconcile continuity-vault-kit, StegOS, Site, and global measurement documentation/source contracts.
9. Validate and merge the implementation slice.
10. Continue TVC provider activation, real signing/upload, TestFlight install, retained-node evidence, and exactly one frozen measurement-only convergence pass.

## Runtime truth

No authentic current-iPhone TestFlight install, retained-node materialization, KV-bound browser projection, or global convergence receipt is claimed by this documentation decomposition.

## Manual work

None while source-contract reconciliation remains machine-executable.
