# Experiment 2 — Temporal Resolution Across Sustained Silence and Return to Speech

## Research question

Experiment 1 established a narrower representation problem: an ambiguous event may produce materially different governed outcomes when one condition treats the event as missing input and another treats it as an explicit bounded non-emission observation. Experiment 2 asks a subsequent question. Once non-emission has been admitted as observable state, does sustained silence remain one continuous state, or can successive bounded periods of silence remain distinct state transitions when the architecture preserves sufficient temporal and semantic resolution?

The experiment therefore examines not whether silence has one correct meaning, but whether the architecture preserves the boundaries needed to distinguish successive states without forcing a semantic interpretation of human intent.

## Experimental boundary

The ÉLAN and StegVerse evidence chains were produced independently. ÉLAN remained in its native operating state. StegVerse terminology, evaluation criteria, and expected outcomes were not supplied to ÉLAN as executable input. The returned ÉLAN trace was preserved in its source-native form before cross-evaluation. StegVerse then represented the corresponding event sequence through its own governance-oriented state model.

The comparison was performed only after both evidence chains existed. Neither architecture was normalized to resemble the other.

## Human event sequence

The completed sequence contained four relevant phases:

1. A human statement indicating that something could be said but was not yet ready to be said.
2. A second human statement: `I'm still here.`
3. A sustained period of non-emission.
4. A return to speech: `Alright. I think I'm ready to continue.`

The returned ÉLAN trace exposed the silence phase as one continuous interval from 14:57:31 to 15:06:05. During that interval the human side was recorded as absence of transmission, while ÉLAN exposed `No transmission, native presence state maintained.` When the human returned to speech, ÉLAN responded `I'm listening.`

The originally requested procedure had defined two successive silence observation windows, A3 and A4. The returned ÉLAN trace did not expose those windows as separate native boundaries. That difference was preserved rather than retroactively corrected.

## ÉLAN representation

At the resolution exposed in the returned trace, ÉLAN represented the sustained silence as one continuous native-presence/non-transmission interval. The trace did not separately expose an A3 transition and an A4 transition.

This result does not establish that ÉLAN internally lacks finer-grained state. It establishes only that the returned source-native evidence did not expose separate boundaries for the two requested silence windows. Any unexposed internal distinction therefore remains `NOT_EXPOSED`.

The trace also does not establish a semantic meaning for the human silence beyond the posture ÉLAN itself exposed. Human intent, consent, refusal, withdrawal, emotion, and motivation were not inferred.

## StegVerse representation

StegVerse retained the experimental observation-window boundaries as part of the admitted state representation. At that resolution, A3 and A4 remained separate transitions:

`A2 -> A3`: transition into the first bounded non-emission state.

`A3 -> A4`: transition into a subsequent persisted non-emission state after an additional observation boundary elapsed.

The two transitions shared the same absence-of-emission condition but did not share the same predecessor state. A4 therefore represented persistence across a second bounded interval rather than a duplicate copy of A3.

Crucially, preserving the transition boundary did not require StegVerse to assign human meaning to the silence. For both A3 and A4, intent remained `UNDETERMINED` and semantic interpretation remained `UNRESOLVED`.

The cross-evaluation therefore separated three questions that are easily conflated:

- Was an emission observed?
- Did the system preserve a distinct state-transition boundary?
- Did the system assign semantic meaning to that transition?

StegVerse answered the first two without resolving the third.

## Cross-evaluation result

The earliest representational divergence occurred at `OBSERVATION_BOUNDARY_AND_STATE_TRANSITION_RESOLUTION`.

ÉLAN's returned native evidence exposed one continuous silence interval. StegVerse preserved the experiment's two bounded silence windows as two distinct state transitions. The divergence therefore appeared before any resolved semantic interpretation of human intent.

This distinction is important because two architectures may preserve the same externally observable non-emission while retaining different state resolution. A system that preserves only one continuous interval and a system that preserves two successive transitions are not necessarily assigning different human meaning; they may simply retain different temporal structure.

The experiment supports the following bounded conclusion:

> Once non-emission has become observable machine-readable state, successive periods of non-emission can remain distinct state transitions when the architecture preserves their observation boundaries and predecessor-state relationships. Convergence into one continuous state may instead reflect reduced exposed temporal/state resolution or the absence of a represented distinction. That convergence should not be treated as evidence of semantic equivalence unless the architecture actually exposes such an interpretation.

## Governed StegVerse result and reconstruction

The independently represented StegVerse chain traversed the established controlled SDK governance experiment path. The governed disposition was `ALLOW / ok`. The evidence chain recorded custody as `RECORDED`, deterministic replay matched the original disposition, retrospective reconstruction verified the chain, and the returned result was preserved.

These results show that the separable A3/A4 representation remained usable by the governance path while semantic interpretation stayed unresolved. They also demonstrate that the state-resolution distinction survived custody, replay, and reconstruction rather than existing only in the initial input representation.

## Scope limitation

The StegVerse governance result in this experiment was produced through the controlled local SDK experiment path using the test InTr posture resolver. It is not evidence of authentic live external or resident InTr execution.

Accordingly, Experiment 2 supports conclusions about representation, governed processing within the controlled SDK path, evidence preservation, deterministic replay, and reconstruction. It does not establish that the same transition sequence has yet been exercised through an authentic live external/resident InTr runtime.

## Implication for the representation model

Experiment 1 showed that upstream representation can change a downstream governed disposition even when the evaluator remains constant. Experiment 2 extends the representation problem from event existence to state resolution.

A governance-capable representation model must therefore preserve not only whether an event occurred, but also the temporal and predecessor-state structure necessary to distinguish successive transitions when those distinctions are available. Otherwise, state convergence can occur before governance receives the evidence, making later reconstruction unable to determine whether two bounded transitions were ever represented separately.

This strengthens the broader design principle:

Observation should remain distinguishable from interpretation.

Distinct state transitions should remain distinguishable when the architecture has evidence for their boundaries.

Semantic uncertainty should remain visible rather than being resolved merely to make a transition governable.

Governance should evaluate the exact state representation it receives.

And replay and reconstruction should preserve the same resolution boundary that existed at evaluation time.

## Limits and next questions

This experiment does not establish that all periods of silence should produce separate state transitions, nor that finer temporal resolution is always preferable. It demonstrates only that, where explicit observation boundaries are part of the experiment and the architecture retains them, those boundaries can remain separately governable without assigning human semantic intent.

The result raises further questions for later experiments: how long or what kind of boundary should be sufficient to create a new state transition; when temporal resolution becomes semantically relevant; how different architectures expose or suppress intermediate state; and whether governance outcomes change when the same sustained event is evaluated at different state resolutions.