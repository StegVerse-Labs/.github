# ÉLAN HOLD — SDK capability qualification and independent-evaluator preflight

**Date:** 2026-09-25  
**Existing Goal Task:** `ELAN-PAPER-COAUTHOR-PUBLICATION-001` / COSV `71000000100100`  
**Scope:** Source-backed readiness assessment and test specification; **not** proof of a newly executed HOLD experiment, a new runtime, or authentic external InTr execution.  
**Status:** PARTIAL SOURCE CAPABILITY CONFIRMED / HOLD END-TO-END CAPABILITY NOT YET VERIFIED / EVALUATOR PACKET NOT RELEASED.

## Primary scientific boundary

Élisabeth's original and corrected Test 2 PDFs were directly compared under the existing paper task. Her original line about “native presence state maintained” was human-authored, and the corrected source specifies **no API request / no model output** in the timed interval. This is an API-test observability boundary, not a demonstration that ÉLAN lacks internal persistence or that a reproduction attempt failed. The corrected source remains confidential.

A future independent evaluator may assemble client-side timing and native API telemetry, submit the exact source-native data under its own semantic custody, select an installed SDK processing capability and inspect governed evidence. SDK can validate and process submitted representations; it cannot retroactively observe unissued API calls, infer source-native hidden state, or manufacture nonexistent primary evidence.

## Verified current SDK source surfaces

Current main source inspected on September 25:
- `README.md` and `docs/SDK_CONSOLE.md`: `stegverse contract --all`, source-native manifested data, `stegverse manifest build`, `stegverse governance --select 0A/0B`, replay and reconstruction by receipt locator, evaluator-authored `what/how/why` and requested published evidence classes.
- `stegverse/manifest_builder.py` + `stegverse/route_resolution.py`: installed route declarations for `governance`, `ecosystem_diagnostic`, `purpose_bound_worker`, `atomic_task_worker`; declared processing choice is independent of data class and grants no execution authority. Unsupported/missing route fails closed.
- `tests/test_ecosystem_diagnostic_processor.py` and `ECOSYSTEM_DIAGNOSTIC_PROCESSOR_MIRROR_HANDOFF.md`: read-only diagnostic processor accepts source-supplied observations, preserves `NOT_OBSERVED`, and returns `PROBE_REQUIRED` when preregistered evidence is missing. Its existing scope is ecosystem diagnostic transport; it does **not** independently probe an ÉLAN API, authenticate arbitrary input evidence refs, establish live runtime or grant authority.
- `docs/SDK_TT_EVALUATOR_TESTS_1_3_RUN_EVIDENCE.md`: retained evidence of three evaluator-directed public `manifest build -> run-manifest` paths through installed purpose-bound/atomic workers. Those tests are source/local-semantic demonstrations for their own scenarios, **not** proof of HOLD compatibility or of an independent ÉLAN run.
- `scripts/run_elan_stegverse_cross_evaluation.py`: the **historical** runner still hardcodes the original incorrect human-authored “native presence state maintained” text under `elan_response`, declares `native_state_unmodified=True`, uses `fake_intr_resolver`, and constructs an invalid native-resolution comparison if rerun as current science. Do not execute or cite it as a corrected HOLD or corrected Test 2 run. Historical source remains preserved; source successor/guard correction belongs under the existing native SDK owner, not by silently rewriting historical output.

SDK references: https://github.com/StegVerse-org/StegVerse-SDK/blob/main/README.md ; https://github.com/StegVerse-org/StegVerse-SDK/blob/main/docs/SDK_CONSOLE.md ; https://github.com/StegVerse-org/StegVerse-SDK/blob/main/stegverse/route_resolution.py ; https://github.com/StegVerse-org/StegVerse-SDK/blob/main/docs/SDK_TT_EVALUATOR_TESTS_1_3_RUN_EVIDENCE.md ; https://github.com/StegVerse-org/StegVerse-SDK/blob/main/scripts/run_elan_stegverse_cross_evaluation.py .

## Evaluator-controlled qualification: capability-by-capability, never an overall self-attested PASS

| Predicate | Current evidence | Qualification |
|---|---|---|
| Discover published SDK contract and installed processing routes | Public console/route-source evidence | SOURCE-SUPPORTED; independently invoke current release before promising deployment |
| Accept arbitrary source-native ÉLAN/client observation class via manifested input | Generic manifest builder, source/route separation | SOURCE-SUPPORTED |
| Bind request ID, original payload and evaluator-declared protocol/expectations | Builder, schema, evaluator declaration; hash/source binding | SOURCE-SUPPORTED; test concrete HOLD fixture |
| Preserve `NO_INVOCATION`, `COMPLETED_EMPTY_RESPONSE`, `TEXT_ELLIPSIS`, `CLIENT_TIMEOUT`, `API_ERROR` as distinct **source-native classes** | Generic data accepts source-native classes; no installed HOLD-specific semantic validator verified | GENERIC CARRIAGE SUPPORTED; HOLD attribution guard NOT YET VERIFIED |
| Distinguish experimenter annotation from model output; reject forged ÉLAN response during no-request | Historical source violates it; corrected publication erratum exists | DENY CURRENT HISTORICAL FIXTURE AS A HOLD EVIDENCE SOURCE; add regression guard before release |
| Evaluate submitted observations under a declared installed governance route | Controlled local SDK experiments and current source | CONTROLLED PATH SOURCE-SUPPORTED; current exact HOLD fixture not executed |
| Yield explicit correctable denial for missing or malformed evidence without inventing model output | SDK route validator, ecosystem diagnostic tests | SOURCE-SUPPORTED; targeted adversarial fixture required |
| Preserve original and predecessor-linked custody; replay and reconstruct exact HOLD result | Historical controlled tests and SDK console | CONTROLLED PRECEDENT EXISTS; exact HOLD receipt/replay/reconstruction NOT YET VERIFIED |
| Execute through authentic external ingress, Interlock/InTr, Master Records and far-side return | Separate resident/SDK owner evidence required | NOT AUTHENTICALLY OBSERVED FOR HOLD; do not substitute local fixture or CI |
| Run a privately hosted or third-party ÉLAN system or infer latent state without invocation | Not provided by SDK | OUT OF SCOPE / UNSUPPORTED; must not become SDK qualification criteria |

## Reusable evaluator capability diagnostic: proposed non-authorizing procedure

**D0 — Freeze declaration.** Evaluator records its own purpose, source/framework, protocol version, ordered conditions, expected observation/evidence classes, exact payload/protocol hashes and selected return depth. SDK validates only *published* capability identifiers. No expected observation enters governance as authority.

**D1 — Contract and route probe.** Call the installed `stegverse contract --all` and request the current installed processor list. Verify exact package/release, current schema, `processing.capability`, `processing.route_id`, runtime binding and bounded-consequence policy. A claimed but non-installed route must return explicit unsupported/denial; do not silently install, simulate or substitute it.

**D2 — Attribution-negative control.** Submit a client-timed interval with `request_sent=false`, no provider request ID and no native response field. The fixture with `elan_response="native presence maintained"` or any other model-authored text for the same non-invocation must be rejected as a provenance violation or identified as HUMAN annotation; never let it pass as native source output. Distinguish genuine source log from a self-declared unsupported claim; independently verify its telemetry when available.

**D3 — Positive HOLD source fixture.** Use only a preregistered **actual API invocation** (from Élisabeth or an openly labeled synthetic fixture for local semantics). Preserve exact prompt, request ID, timestamps, HTTP/completion metadata, raw output or documented nonresult, and source-native session continuity *when exposed*. An ellipsis is `TEXT_ELLIPSIS`, not proof of intent; timeout and a successful empty response are not equivalent.

**D4 — Fixed-route semantic differential.** Construct two source-native manifested test cases using the same installed governance route and policy: (a) a genuinely missing required invoked response, (b) an explicitly bounded client-observed no-request window. Include an ordinary-response control. Compare exact dispositions and reason codes only; the evaluator declares the comparison, not an SDK hardcoded ÉLAN answer.

**D5 — Adversarial cases.** Tamper one payload digest, one predecessor reference, one source attribution label and one requested processor/route binding separately. Each must yield an explicit distinct DENY/FAIL_CLOSED/PROBE_REQUIRED result appropriate to its layer, never silent repair or a falsely successful result. Preserve original failed attempts.

**D6 — Replay and independent reconstruction.** Freeze exact manifest/result hashes and receipt identifiers; replay without reinvoking ÉLAN, reconstruct complete recorded predecessors and custody using only retained evidence. If a public/local-only run lacks authentic external Master Records evidence, report `CONTROLLED_LOCAL_ONLY` rather than `AUTHENTIC_RUNTIME_PASS`.

**D7 — Return the capability report.** Produce one manifest-bound result with a row for each requested capability: `SUPPORTED_AND_OBSERVED`, `SOURCE_ONLY`, `UNSUPPORTED`, `PROBE_REQUIRED`, `NOT_OBSERVED` or `STALE`, with evidence refs, exact failing transition and permitted correction. Do not assign one aggregate PASS that disguises a failed required capability. The evaluator independently decides whether its test design is feasible and whether to proceed; the qualification report grants no runtime authority.

## HOLD release criterion

Prepare Élisabeth's chronological execution packet only after D0–D6 are executed on the **same evaluator-visible public SDK interface**, with exact-result and negative-case artifacts and the first actual failure disposition. A source-only result may qualify a controlled SDK teaching demo if disclosed but not a claim of authentic external/resident governance or source-native insight unavailable from ÉLAN. Joint approval is still required for exact prompts and release of private traces. Until then the canonical HOLD protocol remains PROPOSED / NOT EXECUTED.

## Ownership and non-duplication

Use existing canonical paper goal for publication coordination and existing SDK generic evaluator/route owners for source repair. The SDK ecosystem diagnostic processor remains the existing read-only diagnostic transport owner; this proposal does **not** create a second processor, scheduler, resident runtime, authority source or device dependency. Current historical cross-evaluation source-provenance defect should be routed to its existing SDK owner before rerun. No manual second-device requirement is introduced.
