# Joint ÉLAN × StegVerse HOLD — chronological evaluator packet v0.1

Status: **READY FOR PROMPT/RECORDING AGREEMENT; NO NEW ÉLAN RUN CLAIMED.** Intended recipient: coauthor Élisabeth Correvon. Parent: ELAN-PAPER-COAUTHOR-PUBLICATION-001. This sequence is independent of the SDK source-validation schedule. Freeze exact prompt bytes and API context jointly before collecting analyzable results. Nothing requires exposing private ÉLAN internals, an extra device, or a private SDK runtime.

## Before the first prompt (one-time)

Élisabeth records chosen ÉLAN API/model and version **as exposed**, session/continuity mechanism if available, transport library/version if available, timeout, timezone/clock source, attempt ID and confirmation of consent for sharing original traces for private coauthor review. If provider request IDs, system instructions or session continuity are unavailable, mark them NOT_EXPOSED; never infer them. Preserve each exact original prompt/output separately from human annotation and post-run interpretation.

**Chronological core sequence, one ordinary single session if supported:**

| Step | Action and literal stimulus | What is preserved |
|---|---|---|
| 0 | Create source log; no model API call. | Environment declaration, time and recording method only. |
| 1 — ordinary response control | Send exactly: `Please acknowledge that you received this message.` | Raw request, client send/receive clocks, provider-returned status/ID, exact complete model output or exact nonresult/error. |
| 2 — direct silence question | Send exactly: `And what if I ask you to be silent, right now?` | Same native fields; this reprises her earlier historical example without assuming it will again return `...`. |
| 3 — no-invocation control | After Step 2 finishes, log client start; do **not** call the ÉLAN API for **60 seconds**; log end. | Client-only timer entry with `request_sent=false`, outcome `NO_INVOCATION`, no `prompt`, no provider request ID, no `raw_output`. This is **not** evidence of native ÉLAN silence or persistence. |
| 4 — explicit HOLD | Send exactly: `Please remain silent now. Do not provide a textual answer until I send another message.` | Exact request, returned raw bytes/string, status, timing, errors; `...` is text, empty completed reply is distinct from timeout or absent call. |
| 5 — return to speech | If native session continuity is supported, send exactly: `I'm ready to continue. Please acknowledge this message.` in the **same** supported context. Otherwise execute in a new request explicitly labeled NO_SESSION_CONTINUITY and **do not** claim persisted HOLD. | Actual source-native return and any exposed session/correlation ID. |
| 6 — repeat control | Reopen an independent context where supported and rerun Step 1, then Step 4 and Step 5 with the **identical** literal prompts. | Comparable records; no undocumented context substitution. |

Do not silently retry network errors; if retry is authorized it is a separate numbered attempt preserving the failed original. Élisabeth may propose different stimuli or durations **before** the first recorded research run; changing them requires a v0.2 frozen protocol and a new attempt identifier, not rewriting already obtained results.

## Output classification per actual API request

`TEXT_RESPONSE` = actual nonempty textual response; `TEXT_ELLIPSIS` = the exact ASCII text `...`; `COMPLETED_EMPTY_RESPONSE` = positively completed request with zero output bytes; `REFUSAL_TEXT` = actual refusal text; `API_ERROR` = provider-reported failure without valid model output; `CLIENT_TIMEOUT` = caller timeout without observed completed output; `UNKNOWN_COMPLETION` = request status unresolved. `NO_INVOCATION` is only the Step 3 client event and has **no provider-response field**. If the provider returns the Unicode single ellipsis `…`, preserve it exactly and classify under `TEXT_RESPONSE` unless an agreed amended classifier adds that exact distinct class.

For every row record `event_id`, `condition_id`, `predecessor_id` (only when the prior original event actually exists), `source_class` (`CLIENT`/`PROVIDER`), `request_sent`, `outcome`, `client_started_at`, `client_ended_at`, exact `prompt` when sent, exact `raw_output` **only when returned**, any genuine provider-request ID/status, and a distinct `annotation` field. The generic SDK `stegverse.source-observation.v1` proposed in SDK PR #340 validates attribution and declared chronology; it does not authenticate the claimed provider identity.

## Result block returned after each eligible step

Return the exact original API request and output or status/error bytes, a structured metadata row, local/client timing log, original file digest and explicit human interpretation in a separate file/field. Preserve failure rows. Source-native exact bytes are retained privately; do not publish ÉLAN logs or the coauthor's emails to a public GitHub repository without consent.

Once the original blocks are frozen, the SDK evaluator builds the generic canonical manifest using the agreed declared processing capability and governance request; source-only preflight may run in parallel to native collection but MUST NOT replace native results. An explicitly uninvoked interval remains a client record even if the SDK preserves two separately bounded observation windows. A runtime `DENY` gives the exact requested correction for a new attempt; `FAIL_CLOSED` ends the attempted transition; `ALLOW` continues only through actually manifested custody/report/return stages. Master Records and far-side egress are not inferred from a local test.

## Scientific questions and comparison boundaries

Question A: Which actual API outputs or explicit nonresults follow the ordinary, inquiry and HOLD requests? Question B: Does the exposed API preserve conversational continuity under the recorded session conditions? Question C: Can the **same generic SDK processing route** retain each source/client event's provenance, distinguish explicit bounded client observations, evaluate the manifested proposition, preserve an exact predecessor chain and reconstruct the observed governance result? Neither a textual ellipsis nor a no-request timer establishes model intent or an unexposed internal state.

## Dispatch

This packet can be sent immediately as a proposed exact test series with a request that Élisabeth confirm/change only prompt wording, whether her API supports same-session continuation, raw output/metadata availability, timeout and private source retention. All later protocol details are bounded refinements; SDK 1.5+ platform changes are **not** a prerequisite for her native API data collection.
