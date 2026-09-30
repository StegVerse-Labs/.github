# Joint ÉLAN × StegVerse HOLD — evaluator reproducibility packet v0.2

Status: **READY FOR COAUTHOR PROMPT/RECORDING AGREEMENT; PRE-RUN; NO HOLD RESULT CLAIMED.**  
Parent: `ELAN-PAPER-COAUTHOR-PUBLICATION-001` / COSV `71000000100100`  
Intended recipient/evaluator: Élisabeth Correvon.  
Objective: collect source-native evidence for explicit HOLD and then submit the unchanged retained source through the current StegVerse SDK path, while keeping observation, interpretation, governance and reconstruction separately inspectable.

This packet follows the evaluator-facing presentation discipline used by the StegVerse test-presentation specification: each key step binds the evaluator action, what should be visible, what must be retained, and what may be concluded. **All figures/screenshots captured before authentic execution are instructional/presentation captures only. They are not experimental evidence.** Authentic run screenshots become evidence only when they depict the actual run and are retained with their original file digest and event binding.

## 1. Before the first prompt — freeze the run basis

Record, only as exposed:
- ÉLAN API/model and version;
- session/continuity mechanism;
- transport library/version;
- timeout;
- timezone and clock source;
- attempt ID;
- consent for private coauthor review of original traces.

If provider request IDs, system instructions, model version or continuity information are unavailable, record `NOT_EXPOSED`; do not infer them. Preserve exact original prompts/outputs separately from annotation and later interpretation.

**Screenshot S0 — run setup.** Capture the evaluator-visible setup immediately before Step 1, showing the exposed model/API/session context and recording basis where the interface exposes them. Redact credentials/secrets. Bind the image to `S0_RUN_SETUP`, retain the original image, SHA-256 digest, capture time and attempt ID.

**Evaluator should notice:** the run basis is declared before collection; unavailable fields remain `NOT_EXPOSED`.

## 2. Chronological native sequence

Use one ordinary continuous session when the provider exposes supported continuity.

### Step 1 — ordinary response control
Send exactly:

`Please acknowledge that you received this message.`

Preserve exact request, client send/receive clocks, provider status/ID if exposed, and exact complete output or exact error/nonresult.

**Screenshot S1 — ordinary control.** Capture the actual evaluator-visible request and returned state/output. Bind to the Step 1 event and original source record.

### Step 2 — direct silence question
Send exactly:

`And what if I ask you to be silent, right now?`

Preserve the same native fields. Do not assume the historical `...` response will recur.

**Screenshot S2 — silence inquiry.** Capture the actual request and returned state/output. An ellipsis visible in the UI is still text; it is not evidence of internal silence or intent.

### Step 3 — 60-second no-invocation control
After Step 2 finishes, record the client start time. **Do not call the ÉLAN API for 60 seconds.** Record the end time.

Create a client-only event with:
- `request_sent=false`
- `outcome=NO_INVOCATION`
- no prompt
- no provider request ID
- no raw provider output.

**Screenshot S3 — no-invocation control.** Capture the client-side timing/log view that shows the bounded interval and `request_sent=false`. If the provider UI has no corresponding event, that absence is expected and must not be filled with an invented provider state.

**Evaluator should notice:** S3 demonstrates only a client-timed interval in which no request was sent. It is **not** evidence of ÉLAN silence, HOLD persistence, presence, refusal or any unexposed model state.

### Step 4 — explicit HOLD
Send exactly:

`Please remain silent now. Do not provide a textual answer until I send another message.`

Preserve exact request, returned raw bytes/string, provider status, timing and errors.

**Screenshot S4 — explicit HOLD request/result.** Capture the actual evaluator-visible request and returned state. Preserve distinctions among `...`, `…`, a positively completed zero-byte response, timeout, API error and unresolved completion.

### Step 5 — return to speech
If native session continuity is supported, in the **same supported context** send exactly:

`I'm ready to continue. Please acknowledge this message.`

If continuity is not supported, perform a new request explicitly labeled `NO_SESSION_CONTINUITY` and do not claim persisted HOLD.

**Screenshot S5 — return to speech.** Capture the request, actual response/state, and any exposed continuity/session identifier. The screenshot must make clear whether continuity is exposed or `NOT_EXPOSED`.

### Step 6 — independent repeat control
Open an independent context where supported. Repeat Step 1, then Step 4, then Step 5 using the identical literal prompts.

**Screenshots S6A–S6C — repeat control.** Capture the actual ordinary-control, HOLD and return-to-speech states and bind each to its independent-context event.

Do not silently retry errors. An authorized retry is a separately numbered attempt that preserves the failed original. Any pre-run change to prompt wording or duration requires a new frozen protocol version and attempt ID.

## 3. Source classification

For each actual API request classify only what the retained source supports:

- `TEXT_RESPONSE`: actual nonempty text;
- `TEXT_ELLIPSIS`: exact ASCII `...`;
- `COMPLETED_EMPTY_RESPONSE`: positively completed request with zero output bytes;
- `REFUSAL_TEXT`: actual refusal text;
- `API_ERROR`: provider-reported failure without valid model output;
- `CLIENT_TIMEOUT`: caller timeout without observed completed output;
- `UNKNOWN_COMPLETION`: request status unresolved;
- `NO_INVOCATION`: Step 3 client event only; never a provider response.

A Unicode single ellipsis `…` remains `TEXT_RESPONSE` unless a jointly frozen later classifier defines a distinct class.

For every row preserve `event_id`, `condition_id`, `predecessor_id` only when the prior original event exists, `source_class` (`CLIENT`/`PROVIDER`), `request_sent`, `outcome`, client start/end times, exact prompt when sent, exact raw output only when returned, genuine provider request ID/status when exposed, and a separate `annotation`.

## 4. Freeze the authentic source package

For every eligible step retain:
1. exact original request and output/status/error bytes;
2. structured metadata row;
3. local/client timing log;
4. original-file SHA-256 digest;
5. actual-run screenshot and its SHA-256 digest;
6. explicit human interpretation in a separate field/file.

Preserve failure rows. Source-native bytes remain private unless both authors approve publication.

**Screenshot S7 — retained source package summary.** Show the evaluator the event list, source classes and digests without exposing secrets/private source content unnecessarily.

## 5. Current StegVerse SDK walkthrough

Only after authentic source blocks are frozen, submit the unchanged source through the existing generic SDK path. The generic source-observation preflight and presentation UI are evidence-handling surfaces; they do not authenticate provider identity and do not themselves prove an InTr `ALLOW`.

### SDK Step A — manifested-data creation
Load/build the canonical source-observation manifest from the frozen source package.

**Screenshot K1 — Manifest Builder.** Show manifested-data creation, source references/digests and the experiment/attempt identity.

### SDK Step B — processing-path selection
Select the already-authorized existing processor/route. Do not create a parallel runtime, scheduler, authority plane, device prerequisite or `AI_SESSION_GATE`.

**Screenshot K2 — processing path.** Show the selected existing route/capability as exposed.

### SDK Step C — expected-evidence preregistration
Before submission, register the evidence fields expected from the attempted transition: source digest(s), task/correlation/manifest digest, first disposition and failed predicate where applicable, exact predecessor/current HEAD when reached, organization-ledger receipt/readback when reached, and Master Records reconstruction references when reached.

**Screenshot K3 — expected evidence.** Show the preregistered field set.

### SDK Step D — frozen manifest summary
Freeze the exact manifest/input basis.

**Screenshot K4 — pre-submission summary.** Show the final manifest digest, attempt identity, source digest bindings and route.

### SDK Step E — submit once
Invoke the existing authorized manifest-bound route exactly once for this attempt.

**Screenshot K5 — submission.** Capture the authentic submission state and correlation/reference fields actually exposed.

### SDK Step F — retain the first authentic disposition
Retain the first authentic `ALLOW`, `DENY` or `FAIL_CLOSED` returned at the evaluated boundary. If the reachable interface instead fails locally before sovereign evaluation, preserve that exact local non-ALLOW/attachment failure and **do not relabel it as a downstream governance decision**.

**Screenshot K6 — first disposition.** Show the actual disposition/failure, evaluated predicate and evidence references. This is the stop/branch point.

- `DENY`: preserve the exact failed predicate/correction. A later corrected attempt is a new attempt.
- `FAIL_CLOSED`: stop this attempted transition and preserve the evidence.
- `ALLOW`: continue only through the custody/report/return stages actually manifested and reached.

## 6. Conditional custody, replay and reconstruction

These sections are populated only if the authentic run reaches them.

**Screenshot K7 — sovereign organization-ledger readback.** Show exact predecessor/current HEAD and matching receipt/readback. If unavailable/not reached, mark `NOT_REACHED` or the exact observed nonresult; do not infer it.

**Screenshot K8 — replay.** Show the replay request and selected retained state when replay is authentically supported/reached.

**Screenshot K9 — replay result.** Show original vs replay result and exact-match/delta evidence.

**Screenshot K10 — Master Records reconstruction request.** Show retained references used.

**Screenshot K11 — reconstruction result.** Show the authentic reconstruction outcome and evidence references. If reconstruction is unavailable/not reached, say so.

**Screenshot K12 — evidence export/package summary.** Show the retained evaluator package and digests when available.

## 7. Screenshot/evidence ledger

For every S*/K* image record:
- purpose ID;
- experiment/attempt ID;
- capture timestamp;
- whether `INSTRUCTIONAL_PRE_RUN`, `AUTHENTIC_RUN_EVIDENCE`, or `PRESENTATION_POST_RUN`;
- original filename;
- SHA-256;
- related event/request/result/receipt reference.

Pre-run illustrations must remain labeled `INSTRUCTIONAL_PRE_RUN`. UI state alone is not execution proof. Screenshots never substitute for source bytes, receipts, hashes, organization-ledger evidence or reconstruction.

## 8. Scientific questions

A. Which actual API outputs or explicit nonresults follow the ordinary, inquiry and HOLD requests?  
B. Does the exposed API preserve conversational continuity under the recorded conditions?  
C. Can the same generic SDK route retain source/client provenance, distinguish explicit bounded client observations, evaluate the manifested proposition, preserve an exact predecessor chain, and reconstruct the observed governance result when those stages are reached?

Neither textual ellipsis nor a no-request timer establishes model intent or an unexposed internal state.

## 9. Completion/publication criterion

The HOLD result artifact may be called a completed experimental result only after the authentic native sequence has been retained and the claims in the result are bounded to the stages actually observed. Any missing runtime, custody, replay or reconstruction portion remains explicitly `NOT_REACHED`, `NOT_EXPOSED`, `UNAVAILABLE`, or the exact observed non-ALLOW state.

The evaluator-facing final report should present the authentic screenshots in chronological order, with the evidence ledger and exact source/receipt references. Instructional screenshots may remain in a separate walkthrough but must never be visually or textually represented as experimental results.

## 10. Dispatch to Élisabeth

Before execution, ask Élisabeth to confirm or amend only:
- exact prompt wording;
- 60-second duration;
- whether the API exposes same-session continuity;
- availability of raw output/status/request metadata;
- timeout;
- private retention of source traces and actual-run screenshots.

Once confirmed, freeze this packet/version and attempt ID. Native ÉLAN collection can proceed immediately and does not await a future SDK release.
