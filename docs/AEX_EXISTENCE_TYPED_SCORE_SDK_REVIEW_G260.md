# Existence RC1 typed-score contract review — 2026-09-27

Existing coordination task: `ADMISSIBLE-EXISTENCE-MATHEMATICAL-PROCESSING-INTEGRATION`, COSV `10111110111000`. Source mathematics remains owned by `Admissible-Existence/Existence`; existing source completeness and Tri-Form claims are released. This document requests separate source-owner review, not mutation of the source repository or admission of a new task.

## Original source identities and conflicting domains

- `Admissible-Existence/Existence/schemas/existence-profile.schema.json` Git blob `7f509f720f6d148e9ebc86f1407d4c344a63ccd2`: each ECAT, ICAT, BCAT and GCAT score is JSON Schema `number`; JSON Boolean is not `number`.
- `Admissible-Existence/Existence/tools/validate_existence.py` Git blob `531156481081c205a9ac2fa4092118553ee51b29`: `isinstance(value, (int,float))` accepts Python Boolean, since `bool` subclasses `int`. It also applies the same broad numeric test to percentage inputs.
- `Admissible-Existence/Existence/formalism/principle-registry.yaml` Git blob `9708b63ce59d66a59f0cfd85a9497df2dfbc0958`, EXIST-03 and EXIST-04: four normalized real-valued review lenses `s_E,s_I,s_B,s_G in [0,1]`, percentage `100*(sum(scores)/4)`. Equal weighting is an RC1 policy, not a universal theorem.

## Bounded mathematical obligation and counterexample

For four finite real scores in [0,1], unrounded percentage P = 25(s_E+s_I+s_B+s_G) lies in [0,100]. Replacing one score s_i by s_i+delta while keeping all scores in [0,1] changes P by exactly 25*delta. The implemented two-decimal rounding preserves nondecrease for nonnegative delta but may erase strict increase.

The source validator's Boolean type predicate accepts `scores={ECAT: true, ICAT:false, BCAT:false, GCAT:false}` as Python numeric values (1,0,0,0). If `percent_existence=25.0` and the other required profile keys are populated, it does not report an invalid score for these values. This conflicts with the source JSON schema's score type `number`, not with the arithmetic formula. The original validator must also be reviewed for non-finite float inputs, since JSON's numeric domain and Python float acceptance differ.

The source-owner falsification control should use one schema-valid four-real-score profile and one otherwise identical profile with Boolean ECAT; the schema and native validator must agree on admissibility. Also test NaN/Infinity rejection, score bounds, percent mismatch, and rounding ties, with exact original source/fixture hashes. The integration owner does not assert that the source owner has approved a correction.

## SDK boundary

Current `validate(path: Path)` reads a filesystem path and emits validation results; it does not accept `(native_input, *, original_specimen_bytes)` or return the generic SDK's canonical `result_sha256`. An independently admitted original-owner adapter must bind exact frozen profile bytes and typed `native_input`, reject contradictory data, preserve source results and canonical native digest, and declare `authority_effect=NONE_SOURCE_RESULT_ONLY`. Reuse existing `stegverse.route.source-native-math.v1` only after owner admission and verified installed distribution/source blob. Negative controls must include Boolean/nonfinite typed rejection, forged specimen, forged installed blob, forged expected result and request/specimen contradiction. Exact original-source, specimen, native-result, manifest, request and pre-enrichment hashes must be obtained from actual invocation. Existence remains `NOT_ESTABLISHED` for SDK invocation; no source result is an InTr disposition or governed runtime proof.
