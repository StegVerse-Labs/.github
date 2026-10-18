# Lane D NWI-S0 migration fixtures

These are MIGRATED_HISTORICAL SV_ISSUE and SV_CHANGE records. The issues come from Lane D's six-field FAIL_CLOSED/DENY records in lane file §14 to §26. The changes come from the 11 open Lane D PRs. A work-items record covers both. All of it is built with P1's in-repo rules from `p1/sv-native-work-items` (StegVerse-Labs/.github#3264).

- **Never admissible.** A migrated record becomes NATIVE only through a SUPERSEDE whose successor holds observed values.
- **Unknown values.** These are `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED`, appear only at the schema's allowed pointers, and are listed in `unknown_fields`. Branch writers evidence is UNKNOWN (JDQ Q-WRITER-IDENTITY).
- **Surfaces.** These come from P1's pinned `data/sv-work-items/surface-aliases.json`. Lane D's alias proposals are in `PROPOSED_SURFACE_ALIASES.json` and are not applied.
- **Rebuild and test.** Rebuild with `python3 scripts/build_lane_d_s0_migration_fixtures.py`, or verify with `--check`. Test with `python3 -m unittest tests.test_s0_lane_d_migration_fixtures`.
