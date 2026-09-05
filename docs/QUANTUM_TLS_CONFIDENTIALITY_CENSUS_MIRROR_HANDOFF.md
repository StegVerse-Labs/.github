# Quantum TLS / Confidentiality Census Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Parent: `QUANTUM-RESILIENCE-001` / `.github#1008`  
Issue: `#1014`  
Subgoal: `QUANTUM-TLS-CONFIDENTIALITY-CENSUS-001`  
State: `PARTIAL_SOURCE_CENSUS_BUILT / RUNTIME_NEGOTIATION_AND_BROADER_INVENTORY_REQUIRED`

## Purpose

Inventory consequence-bearing TLS/WebPKI, service-to-service key exchange, certificate and long-lived confidentiality surfaces without treating TLS version, certificate presence, source validation or provider claims as evidence of post-quantum protection.

## Canonical census

`control/quantum-tls-confidentiality-census.json`

Current concrete source-evidenced surfaces:

1. `STEGTALK-ST034-PUBLIC-TLS-CLIENT`
   - source: `StegVerse-Labs/StegTalk` ST-034;
   - Python `ssl` client with platform trust store or explicit non-secret CA file;
   - certificate-chain verification required;
   - hostname verification required;
   - minimum TLS version TLSv1.2;
   - no insecure mode;
   - negotiated certificate and key-exchange algorithms are not pinned/evidenced by source;
   - real admitted public TLS execution remains unproven;
   - quantum state: `QUANTUM_SAFETY_UNKNOWN`.

2. `TVC-SERVICE-GATEWAY-TLS-MATERIAL`
   - source: `StegVerse-Labs/TVC` Service Gateway TLS material adoption lane;
   - TV/TVC retains credential authority;
   - source validates already-materialized certificate/private-key material without exporting private-key bytes;
   - authentic TLS-material adoption and public Gateway runtime remain unobserved;
   - certificate algorithm and negotiated key-exchange group remain unknown until runtime evidence exists;
   - quantum state: `QUANTUM_SAFETY_UNKNOWN`.

Both surfaces are classified harvest-now/decrypt-later relevant because their consequence-bearing confidentiality lifetimes are not yet canonically bounded and the negotiated asymmetric properties are not proven post-quantum.

## Source validator

- `scripts/validate_quantum_tls_confidentiality_census.py`
- `tests/test_quantum_tls_confidentiality_census.py`

The validator requires:

- no PQC deployment claim;
- no quantum-safe claim;
- no authority effect;
- TV/TVC credential authority;
- explicit runtime evidence requirements;
- `QUANTUM_SAFETY_UNKNOWN` for both current concrete surfaces;
- unresolved scope remains explicit.

## Remaining inventory scope

- other StegVerse TLS/WebPKI clients and servers;
- service-to-service TLS negotiation outside the two evidenced surfaces;
- certificate issuance/renewal paths;
- provider-managed edge TLS where negotiated asymmetric properties are not represented;
- long-lived stored ciphertext and archive encryption;
- actual runtime protocol/cipher/certificate/key-exchange observations for admitted consequence-bearing paths.

## Runtime evidence rule

For a TLS path, source code that sets `TLSv1.2` or later, validates certificates, or enables hostname checks is useful transport-hardening evidence but is not sufficient quantum evidence. A quantum migration disposition requires observed or otherwise authoritative algorithm facts for the certificate public key and key-exchange group, plus a bounded confidentiality lifetime.

If a consequence-bearing path is observed using classical-only asymmetric authentication/key establishment and long-lived confidentiality matters, it must receive a hybrid/ML-KEM migration disposition where feasible. No source or CI result may transition a surface directly to `PQC_VALIDATED`.

## Authority invariants

- credential authority: `TV/TVC`;
- GitHub token runtime authority: `NONE`;
- TLS/PQ validity grants no transition authority;
- InTr/Interlock remains the transition boundary;
- no second user-operated machine is introduced;
- census work is non-authorizing.

## Completion gate

Issue #1014 remains open until the consequence-bearing TLS/WebPKI and long-lived confidentiality inventory is bounded, CRITICAL unresolved scope has explicit dispositions, and runtime negotiation/storage evidence exists where source alone cannot establish the actual algorithms in use.
