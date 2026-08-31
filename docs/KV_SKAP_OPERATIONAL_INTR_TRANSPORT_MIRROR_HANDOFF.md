# KV -> SKAP Vault Operational InTr Transport Mirror Handoff

Repository: `StegVerse-Labs/.github`
Canonical transport merge: `3ec15ed7937fa621a215f78b4992a6e3af63566f`
Current hardening branch: `fix/kv-skap-exact-byte-transport-20260831`
Updated: 2026-08-31T18:04:00-05:00
State: EXACT_BYTE_TRANSPORT_HARDENING_ACTIVE / AUTHENTIC_RESIDENT_KV_SKAP_EVENT_NOT_YET_OBSERVED
Credential authority: TV/TVC
Authority effect: NONE

## Goal

Make the organization-resident Universal InTr transport layer operational across the complete credential-custody path:

```text
DEVICE_SYSTEM
  -> device-kv
  -> KV / KnowledgeVault:Interlock
  -> kv-skap-custody
  -> SKAP_VAULT / SKAP:Vault
```

The organization `.github` boundary owns transport ingress/egress and bounded event dispatch. TVC remains the double-Interlock, credential, and SKAP custody authority.

## Canonical upstream state

StegOS canonical `kv-skap-custody` profile is merged through:

- initial custody profile: `577f6eceb6238b5b6cb48ab85ae163bb95d4083b`
- exact raw packet extension: `131df2778ff74835f403b210776c498406ec3cc8`
- stage lineage extension: `218a9826d7e95610ff27e9918bd5722fd95cdf31`

Current bounded materialization fields are exactly:

```text
sealed_capsule
sealed_capsule_raw_b64
device_kv_receipt
stage_receipt_digest
```

Canonical profile:

```text
profile_id: kv-skap-custody
request_class: KV_SKAP_CIPHERTEXT_CUSTODY
operation: ADMIT_CIPHERTEXT
source: KV / KnowledgeVault:SKAPClient
destination: SKAP_VAULT / SKAP:Vault
downstream owner: StegVerse-Labs/TVC
custody_mode: EXACT_BYTES
authorization_required: true
credential_authority: TV/TVC
authority_effect: NONE
```

TVC current custody primitives:

- `tools/skap_vault_interlock_gate.py`
- `tools/skap_vault_store.py`
- `tools/validate_coinbase_browser_skap_admission.py`

TVC storage backends must identify as `KV_SKAP_INTR_*`; the compatibility resident backend persists under `<STEGVERSE_KV_ROOT>/_Vault/SKAP`.

## Operational organization transport path

```text
original staged browser packet bytes
+ STAGED_FOR_TVC receipt
  -> scripts/dispatch_kv_skap_custody_materialization.py
     - verify exact stage raw_body_digest
     - verify stage browser_ingress_digest
     - verify embedded DEVICE -> KV Interlock
     - load exact current local StegOS kv-skap-custody profile
     - build canonical KV -> SKAP transport intent
     - payload hash = SHA-256(original raw packet bytes)
     - carry original packet as sealed_capsule_raw_b64
     - carry parsed capsule + DEVICE/KV receipt + stage receipt digest
     - attach HB-derived non-authorizing carrier binding
     - emit TVC_RELAY_EGRESS event
  -> workers/universal_intr_profiled_ingress.py
     - require TVC_RELAY_EGRESS authorization reference
     - validate canonical second-hop materialization
     - persist request and ingress receipt write-once
     - dispatch bounded consumer without minting claim/fence
  -> scripts/consume_kv_skap_custody_materialization_request.py
     - decode original packet bytes
     - require semantic equality with sealed_capsule projection
     - require payload_hash == SHA-256(original bytes)
     - validate DEVICE -> KV raw/body bindings
     - validate current TVC first Interlock receipt
     - create KV -> SKAP receipt chained to first receipt
     - preserve stage_receipt_digest and materialization request hash
     - validate current TVC double-Interlock gate
     - persist ORIGINAL raw packet bytes through TVC SKAP store
     - require exact byte-for-byte readback
     - emit ADMITTED_TO_SKAP_VAULT result
```

No second WorkerCoordinator task exists for this hop. The transport event does not mint a claim or fence and does not grant execution authority.

## Implemented surfaces

- `scripts/dispatch_kv_skap_custody_materialization.py`
- `scripts/consume_kv_skap_custody_materialization_request.py`
- `workers/universal_intr_profiled_ingress.py`
- `tests/test_kv_skap_custody_materialization.py`
- `tests/test_sv002_event_ephemeral_materialization.py`
- this handoff

## Prior source/validation evidence

Initial organization transport PR:

```text
StegVerse-Labs/.github#716
merge: 3ec15ed7937fa621a215f78b4992a6e3af63566f
final source head: 98b717150879913bb84222bac2d0cde4b45d421f
organization control validation: 33448181170 SUCCESS
```

Post-merge handoff reconciliation validations:

```text
organization control: 33448307993 SUCCESS
heartbeat worker project: 33448308097 SUCCESS
```

Those proofs establish transport source/control-plane compatibility. They do not establish production SKAP custody.

## Exact-byte correction

Inspection against current TVC `coinbase_gateway_stage_consumer.py` exposed a correctness gap in the first #716 consumer: it reconstructed canonical JSON from `sealed_capsule` before persistence. That could not prove `custody_mode=EXACT_BYTES` for a browser packet with non-canonical JSON formatting.

The correction now requires the original packet bytes and refuses semantic/hash/first-hop mismatches. No equivalent re-encoding is accepted as exact custody.

## Completion predicates for this hardening

1. original browser packet bytes are transported without reconstruction;
2. stage receipt raw-body and semantic bindings validate before second-hop construction;
3. DEVICE -> KV receipt binds the same original bytes, credential, and operation;
4. canonical StegOS `kv-skap-custody` profile is loaded from the configured StegOS root;
5. HB carrier binding remains non-authorizing;
6. TVC relay is the only accepted KV -> SKAP transport origin;
7. KV -> SKAP receipt preserves stage lineage and chains to DEVICE -> KV;
8. TVC double-Interlock gate validates;
9. TVC store receives original packet bytes;
10. exact byte readback is required before `ADMITTED_TO_SKAP_VAULT`;
11. organization validations pass.

## Runtime activation boundary

No authentic `stegverse.kv-skap-custody.materialization-consumption/v1` receipt with state `ADMITTED_TO_SKAP_VAULT` is currently recorded as production evidence.

After source hardening merges, the next machine goal is to bind TVC's existing event-driven stage drain to this organization transport path so a real `STAGED_FOR_TVC` packet automatically crosses:

```text
TVC stage drain
-> .github KV/SKAP dispatcher
-> .github profiled ingress
-> TVC-gated .github consumer
-> _Vault/SKAP exact custody
```

Only an authentic event and exact readback may upgrade this lane to runtime-observed.
