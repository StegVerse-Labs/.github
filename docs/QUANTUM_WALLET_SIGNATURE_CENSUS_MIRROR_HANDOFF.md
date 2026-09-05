# Quantum Wallet / Transaction Signature Census Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Parent: `QUANTUM-RESILIENCE-001` / `.github#1008`  
Issue: `#1013`  
Subgoal: `QUANTUM-WALLET-SIGNATURE-CENSUS-001`  
State: `PARTIAL_SOURCE_CENSUS_BUILT / ACTIVE_SIGNER_ALGORITHM_AND_CHAIN_CONSTRAINTS_REQUIRED`

## Purpose

Inventory wallet and transaction-signature primitives while preserving the existing authority rule that wallet signing and broadcast remain explicit `USER_ONLY` actions. The census must distinguish wallet-provider/chain cryptography from StegVerse-controlled verification, capability and projection surfaces.

## Canonical census

`control/quantum-wallet-signature-census.json`

Current source-evidenced surfaces:

1. `STEGFIN-EIP1193-USER-WALLET-HANDOFF`
   - explicit wallet review/sign/broadcast handoff;
   - signer lives in an external injected EIP-1193 wallet provider;
   - StegVerse does not receive private-key or seed material;
   - automatic signing/broadcast remain false;
   - current handoff requires Base `0x2105` for the governed path;
   - the actual signature algorithm/key type is not established by StegVerse source and therefore remains `QUANTUM_SAFETY_UNKNOWN`.

2. `STEGID-DEVICE-WALLET-CAPABILITY`
   - device-specific capability decision for OBSERVE/PREPARE/SIGN/BROADCAST eligibility;
   - capability decisions do not themselves sign or broadcast;
   - identity continuity and device admission do not grant wallet authority;
   - wallet key export authority remains `NONE`;
   - decision receipts use SHA-256 commitments according to the current StegID handoff.

Repository references to `ecdsa_secp256k1` in other contexts are explicitly non-authoritative for the active USER_ONLY wallet signer unless a current wallet/runtime handoff or observed wallet evidence binds that primitive to the actual signer.

## Validator

- `scripts/validate_quantum_wallet_signature_census.py`
- `tests/test_quantum_wallet_signature_census.py`

Validation requires:

- wallet signing authority `USER_ONLY`;
- wallet broadcast authority `USER_ONLY`;
- wallet key export authority `NONE`;
- TV/TVC credential authority;
- no PQ deployment or quantum-safe claim;
- the EIP-1193 wallet signer algorithm remains unknown unless separately evidenced;
- separate secp256k1/schema references cannot be promoted into active-wallet runtime evidence.

## Remaining inventory scope

- actual signature algorithm and key type used by each admitted external wallet provider;
- chain-level account/signature constraints for all supported networks;
- repository-controlled wallet verification/projection cryptography;
- transaction-signature historical verification and migration semantics;
- non-wallet receipt signatures that may reuse blockchain-style curves.

## Migration rule

A chain- or wallet-mandated classical signature primitive is a protocol constraint, not a reason to move signing authority into StegVerse. Any mitigation must preserve explicit USER_ONLY review/sign/broadcast and separate chain constraints from StegVerse-controlled cryptography, continuity and admissibility controls.

## Completion gate

Issue #1013 remains open until active wallet/transaction signature primitives and custody semantics are bounded with current evidence and every migration disposition preserves USER_ONLY signing/broadcast authority.
