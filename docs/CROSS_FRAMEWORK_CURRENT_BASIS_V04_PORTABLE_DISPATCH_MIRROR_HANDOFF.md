# Cross-Framework Current-Basis v0.4 Portable Dispatch Mirror Handoff

Updated: 2026-08-30
Repository: `StegVerse-Labs/.github`
Parent execution issue: #478
Bounded issue: #550
Branch: `fix/current-basis-v04-targeted-portable-dispatch-20260830`

## Goal

Provide the narrowest portable one-shot execution bridge for the already-queued frozen v0.4 experiment without creating a second dispatcher, scheduler, heartbeat, credential path, claim/fence path, or runtime authority.

## Current source state

The generic resident dispatcher remains the single dispatcher. It now supports an optional exact consumer selector. When no selector is supplied, existing all-consumer behavior is preserved. Unknown selectors fail before any consumer is invoked.

The portable bridge `scripts/refresh_and_dispatch_resident_requests.py` retains the
experiment consumer as its historical default and supplies exactly:

```text
--only-consumer cross_framework_current_basis_v04
```

The portable bridge therefore performs:

```text
already-local sovereign source refresh
-> preserve mutable resident runtime state
-> exact generic-dispatcher consumer selection
-> visit cross_framework_current_basis_v04 only
-> retain dispatcher receipt
-> retain resident-refresh-dispatch receipt
```

It MUST NOT visit Ecosystem Chat, G18, HIL, evaluator InTr, SV002, ARA Graph, CMC-028, SV-DN1, bootstrap release prep, TVC broker validation, or any other resident request during this experiment-only one-shot path. A separate explicit `--only-consumer hil` invocation is admitted for the HIL request lane and does not alter this default or visit the experiment consumer.

## Authority and transport boundary

```text
network source fetch: false
credential acquisition: false
GitHub token runtime authority: NONE
credential authority: TV/TVC
scheduler created: false
heartbeat created: false
claim/fence minted by bridge: false
request dispatcher grants authority: false
second machine required: false
```

## Validation requirements

- existing all-consumer dispatcher behavior remains unchanged when no selector is supplied;
- exact selector visits only the named registered consumer;
- unknown selector fails before any consumer call;
- portable bridge requires dispatcher receipt `selection_scope=EXACT_SELECTOR`;
- portable bridge requires `selected_consumers=[cross_framework_current_basis_v04]` and `consumer_count=1`;
- portable bridge receipt asserts `unrelated_consumers_dispatched=false`;
- current-basis workflow runs dispatcher and portable bridge regression tests.

## Runtime truth

This source change does not execute the experiment. Authentic completion remains:

```text
resident request consumption: NOT OBSERVED
S1 observation: NOT OBSERVED
post-observation S0->S1 receipt: NOT OBSERVED
Master Records custody: NOT OBSERVED
replay: NOT OBSERVED
reconstruction: NOT OBSERVED
RUN_COMPLETE.json: NOT OBSERVED
PUBLICATION_READY.json from authentic run: NOT OBSERVED
```

The next state-changing event after validation/merge must still originate from an eligible non-hosted sovereign resident.
