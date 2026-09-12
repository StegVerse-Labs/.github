# Device Verification / Authority Invariant

## Canonical rule

There is no device verification, device attestation, physical-device identity gate, or device-bound user authority requirement in StegVerse user verification flows.

Devices are interchangeable StegOS transport nodes. A device may carry, transport, or execute bounded work, but it is not the verifier for a user and is not an identity or authority root.

User verification and user authority are maintained through KV/SKAP. Interlock/InTr governs transitions. Client, platform, user-agent, hardware, Secure Enclave, or physical-device metadata may be retained only as non-authoritative transport observation where useful; none may satisfy, replace, widen, or gate user verification or authority.

## Task Registry requirement

All existing and future Task Registry work must preserve this invariant. A task, handoff, test, workflow, verifier, or runtime predicate must not require a specific iPhone or any other physical device identity to establish user verification, signing authority, evidence validity, or transition authority.

Historical device-specific observations remain historical transport observations only and must not be reinterpreted as an architectural requirement.

## Current correction

`SS-EVIDENCE-COMPARISON-001` and StegSocials PR #48 are being corrected accordingly: standard-flow evidence validation binds to canonical KV admission/readback and KV/SKAP authority semantics, with no device-verification gate.
