# MIR leaf v3 conformance fixture mirror handoff

Updated: 2026-09-11
Goal Task ID: `MIR-LEAF-V3-CONFORMANCE-FIXTURE-001`
Parent Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / STEGVERSE + NEUTRAL REPRODUCTION MERGED / MIR REPRODUCTION PENDING`

## Current state

SDK implementation merged through `StegVerse-org/StegVerse-SDK#214` at squash commit `28e56a40dd0f36d14f9c5ec39e37776e11892eb6` after exact-head validation succeeded.

Merged source includes:

- `fixtures/mir_leaf_v3_conformance_fixture_v1.json`
- `fixtures/mir_leaf_v3_conformance_expected_result_v1.json`
- `stegverse/mir_leaf_v3.py`
- `tools/mir_leaf_v3_neutral_reproducer.mjs`
- `tools/compare_mir_leaf_v3_result.py`
- `tests/test_mir_leaf_v3_conformance.py`
- `tests/test_compare_mir_leaf_v3_result.py`
- `docs/MIR_LEAF_V3_COUNTERPART_REPRODUCTION_GUIDE.md`

Frozen outputs:

- Merkle root `sha256:bd0eb01fccc1d88942f2fb465d27f212afb98f5b0aee47faf370ea0bf21a5a94`
- checkpoint tip `sha256:683eac81cfd934700c7ebe8eb4da668f2d44ae95c0cfe74d6d157993324f2ad8`

StegVerse and the neutral JavaScript implementation independently reproduce the same ordered leaf hashes, Merkle root, and checkpoint tip. Mutation and false proof/witness claims fail closed.

## Completion boundary

Section 12.8 remains incomplete until MIR independently consumes the exact frozen fixture bytes and returns matching ordered leaf hashes, Merkle root, and checkpoint tip. The MIR result may not be copied, synthesized, or inferred from the StegVerse/neutral expected vector.

Until 12.5/12.6 ship, proof status remains `NOT_REQUESTED` or `UNAVAILABLE` and `witnesses[]` remains empty.

## Next action

Deliver the exact frozen fixture plus `docs/MIR_LEAF_V3_COUNTERPART_REPRODUCTION_GUIDE.md` to MIR/Richard, retain the authentic MIR result, run `tools/compare_mir_leaf_v3_result.py`, and declare 12.8 complete only if the exact comparison passes.
