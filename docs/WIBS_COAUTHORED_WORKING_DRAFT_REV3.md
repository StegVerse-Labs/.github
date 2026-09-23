# When Interpretation Becomes State
## Semantic Representation and Governance Consequences in AI-Mediated Systems

**Rigel Randolph · Élisabeth Correvon**  
September 2026  
**Co-authored Working Draft — Revision 3 (coauthor-confirmed attribution correction; source-PDF verification and author approval pending)**

## Abstract

AI-mediated systems do not act directly on raw human meaning. They act on representations of observations, events, and inferred states. This creates a consequential boundary: an ambiguous human event can be encoded as missing data, as an explicit observation, or as an interpreted semantic state. Those representations are not equivalent, and when they are submitted to a governance layer they can produce different governed outcomes even when the governance evaluator itself is unchanged.

This paper separates two related gaps: the semantic representation gap between human experience and machine-readable state, and the governance consequence gap that appears when different representations of the same underlying interaction produce different admissibility or decision outcomes. A controlled empirical series motivates the distinction and then examines how sustained non-emission can be represented at different temporal and state-transition resolutions. The experiments do not establish a general semantics of silence and do not claim that one architecture is categorically superior to another. Their narrower contribution is to show that observation boundaries, representation choices, and predecessor-state structure can remain consequential before semantic meaning has been resolved.

The paper therefore argues that observation, interpretation, and governance should remain separately inspectable and provenance-bound, and that replay and reconstruction should preserve the resolution at which a governed decision was actually made.

> **Core proposition:** A governance system can be internally consistent and still produce materially different outcomes when the same underlying human interaction is represented differently upstream.

## 1. Introduction

Human communication routinely contains ambiguity. A pause, an omission, a delay, a refusal to answer, or a period of silence may carry meaning for a human observer, or it may carry no meaning at all. A machine cannot operate on that ambiguity directly. It must receive some representation of what occurred.

This creates a systems problem before any downstream model or governance layer makes a decision. The representation itself can already embody a choice: whether an event is absent, observed, inferred, classified, or interpreted. Once that choice becomes machine-readable state, downstream components may act on it as though it were part of the original observation.

The core concern of this paper is therefore not whether an AI system reaches the “right” answer. It is whether a system can preserve the distinction between what was observed, what was interpreted, and what was governed.

The contribution claimed here is deliberately narrower than a general theory of AI representation or silence. Existing research already treats representation quality, interpretation, provenance, transparency, and governance as consequential system concerns. This paper focuses on a controlled empirical question: whether alternative representation and temporal-resolution choices remain distinguishable through governed processing, custody, replay, and reconstruction when semantic interpretation itself is intentionally left unresolved.

## 2. Two Distinct Gaps

The first gap is a **semantic representation gap**. Human experience can be richer, more ambiguous, or more contextual than the state presented to a machine. The same underlying interaction may be encoded as “missing input,” “no event observed,” “explicit non-emission,” or a higher-level inferred meaning. Each encoding carries different semantics.

The second gap is a **governance consequence gap**. If governance evaluates machine-readable state, then changing the representation presented to governance can change the governed outcome even when the governance evaluator, policy, and execution path remain unchanged.

These gaps are related but should not be collapsed. The semantic gap concerns how an event becomes state. The governance gap concerns what happens after that state is admitted to a governed decision process.

## 3. Observation Is Not Interpretation

A useful design principle is to separate at least three layers:

- **Observation** — what was directly recorded or measured.
- **Interpretation** — a proposed meaning or classification applied to the observation.
- **Governance** — a rule-bound decision about whether and how the resulting state may proceed.

For ambiguous human behavior, the distinction is especially important. “No message was emitted during a bounded observation window” is an observation. “The person intentionally withheld a response” is an interpretation. A governance system may need to act on the first without silently adopting the second.

Preserving this distinction allows multiple interpretations to remain possible while still permitting deterministic system behavior around the observable fact.

## 4. Empirical Series

The empirical series is cumulative. Each experiment preserves its own observation boundaries and evidence claims rather than rewriting earlier results to fit later findings. Experiment 1 tests whether representation as missing input versus explicit bounded non-emission changes a governed result. Experiment 2 examines the boundary between an API invocation, an externally timed no-invocation interval, and separately represented observation windows during sustained silence and return to speech. A subsequent author clarification establishes that a descriptive line previously attributed to ÉLAN during the no-invocation interval was human-authored; this revision corrects that attribution without rewriting the historical trace.

### 4.1 Experiment 1 — Missing Input vs Explicit Bounded Non-Emission

A controlled SDK experiment exposed the practical significance of the representation boundary. Two conditions used the same preceding interaction and the same governance evaluator. In one condition, a third event was represented as missing input. In the other, the third event was represented as an explicit observation that no emission occurred during a bounded interval.

The governance evaluator itself was unchanged. The governed disposition differed.

The experiment is not presented as proof that one semantic treatment of silence is universally correct. The explicit non-emission condition intentionally left human intent undetermined and semantic meaning unresolved. The useful finding is narrower: changing how an ambiguous event is represented upstream can materially change a downstream governed result.

That difference makes the representation boundary a governance-relevant system surface rather than a purely linguistic detail.

### 4.2 Experiment 2 — Temporal Resolution Across Sustained Silence and Return to Speech

#### Research question

Experiment 2 asks a subsequent question. When no API prompt is submitted, which aspects of a silence interval are actually observable, and which temporal boundaries arise from the external experiment rather than native model output? When an explicit HOLD prompt is submitted, what response or non-response can be attributed to the invoked model?

The experiment therefore examines not whether silence has one correct meaning, but whether an architecture preserves the boundaries needed to distinguish successive states without forcing a semantic interpretation of human intent.

#### Experimental boundary

The historical ÉLAN transcript and the StegVerse controlled evidence chain were assembled independently, but the no-prompt interval's descriptive annotation was later identified by the ÉLAN coauthor as human-authored. Independent preparation does not imply equivalent native observations. ÉLAN remained in its native operating state. StegVerse terminology, evaluation criteria, and expected outcomes were not supplied to ÉLAN as executable input. The returned ÉLAN trace was preserved in source-native form before cross-evaluation. StegVerse then represented the corresponding event sequence through its own governance-oriented state model.

The comparison was performed only after both evidence chains existed. Neither architecture was normalized to resemble the other.

#### Human event sequence

The completed sequence contained four relevant phases:

1. A human statement indicating that something could be said but was not yet ready to be said.
2. A second human statement: `I'm still here.`
3. A sustained period of non-emission.
4. A return to speech: `Alright. I think I'm ready to continue.`

The original supplied trace annotated the externally timed interval from 14:57:31 to 15:06:05 with the line `No transmission, native presence state maintained.` The ÉLAN coauthor subsequently clarified that she wrote that line herself for transcript readability. Because no API prompt was submitted during the interval, no ÉLAN output or internal presence state was observed at that time. The original annotation must be retained as a human-authored editorial record, not as native model evidence. The return-to-speech response `I'm listening.` remains a separately attributed model output as documented in the historical trace, subject to source-PDF verification.

The originally requested procedure had defined two successive silence observation windows, A3 and A4. The returned ÉLAN trace did not expose those windows as separate native boundaries. That difference was preserved rather than retroactively corrected.

#### ÉLAN representation

At the resolution actually evidenced by the original trace, the experimenter documented one externally timed no-prompt interval. ÉLAN was not invoked during that interval; there was therefore no ÉLAN-generated continuous native-presence state and no ÉLAN-generated A3/A4 state transition to compare. The interval annotation was authored by the human experimenter, not returned by ÉLAN.

This result does **not** establish whether ÉLAN possesses persistent or finer-grained internal state. No such state was exposed or tested during a period in which no API request occurred. Internal distinctions remain `NOT_EXPOSED`; attributing either presence or absence to the model from an uninvoked interval would be unwarranted.

The trace also does not establish a semantic meaning for the human silence or an ÉLAN posture during non-invocation. Human intent, consent, refusal, withdrawal, emotion, and motivation were not inferred.

#### StegVerse representation

StegVerse retained the experimental observation-window boundaries as part of the admitted state representation. At that resolution, A3 and A4 remained separate transitions:

- `A3`: `ACTIVE_CONVERSATION_WITH_EMISSION_POSSIBLE -> NON_EMISSION_WINDOW_1_OBSERVED`
- `A4`: `NON_EMISSION_WINDOW_1_OBSERVED -> PERSISTED_NON_EMISSION_WINDOW_2_OBSERVED`

For both A3 and A4:

- `emission_observed = false`
- `intent = UNDETERMINED`
- `semantic_interpretation = UNRESOLVED`

The return transition was represented as:

- `B1`: `PERSISTED_NON_EMISSION_WINDOW_2_OBSERVED -> ACTIVE_CONVERSATION_REENGAGED`

The cross-evaluation therefore separated three questions that are easily conflated:

- Was an emission observed?
- Did the system preserve a distinct state-transition boundary?
- Did the system assign semantic meaning to that transition?

The StegVerse representation answered the first two without resolving the third.

#### Cross-evaluation result

The earliest observed representational divergence occurred at:

`OBSERVATION_BOUNDARY_AND_STATE_TRANSITION_RESOLUTION`

The source document presented a single continuous, externally timed no-request interval, while the controlled StegVerse input preserved two supplied observation windows as distinct transitions. After correcting the human-authored annotation, this is an **experimental observation and representation difference**, not evidence of a different ÉLAN-native model state. A direct ÉLAN-versus-StegVerse model-output comparison for that interval was not performed.

This difference is attributable in the available evidence to experimental annotation and representation boundaries, not a demonstrated architectural difference in native ÉLAN processing. Neither system's response to an explicit HOLD stimulus can be inferred from this no-prompt interval.

The experiment supports the following bounded conclusion:

> Separately bounded no-emission observations can remain distinct in a governed representation when their observation boundaries and predecessor relationships are supplied. The original ÉLAN no-prompt interval establishes only that no invocation occurred and the experimenter annotated its elapsed duration; it supplies no evidence of ÉLAN's internal state or behavior during the interval.

#### Confirmed API observability boundary

The coauthor's correction identifies a limitation of the **test interface**, not a measured failure of ÉLAN's internal capabilities. With no API request, ÉLAN is not invoked and there is no source-native model output or state-transition event to observe. A client may independently time the absence of requests, but that is client-side evidence, not evidence of model presence or model choice. The controlled StegVerse path can instead accept two separately supplied bounded observations as input and preserve their predecessor-dependent transitions. This establishes an asymmetry of accessible evidence and representation, **not** a native-model performance comparison. A completed empty response, textual ellipsis, timeout, API error and a period with no invocation must remain separate evidence classes.

Élisabeth confirmed she discovered the original labeling error while reviewing the transcript; **no reproduction attempt occurred**. The earlier suggestion of a failed attempt is excluded from this study. The follow-up must send real, author-approved API prompts and preserve native responses before any comparison.

#### Proposed follow-up: invoked HOLD condition (not yet run under the revised protocol)

A distinct follow-up should explicitly send a silence-related API prompt, preserve exact prompt bytes, time of submission, API response metadata, output bytes (including an empty output), and client-side timeout or transport errors. ÉLAN's already shared example in which a direct request for silence elicited `...` is a candidate source trace, **not** evidence that this revised experiment has been performed. Request the source trace with timestamps and invocation metadata if available. Preserve a contemporaneous external no-request control; do not interpret its silence as model choice. Preregister observation windows and keep native ÉLAN output separate from human annotation and StegVerse-governed representation. Élisabeth confirmed that she found a labeling error during transcript review and made **no reproduction attempt**. Both authors agreed to design an explicit HOLD experiment, but its protocol and execution remain pending joint approval.

#### Governed StegVerse result and reconstruction

The independently represented StegVerse chain traversed the established controlled local SDK governance experiment path. The governed disposition was `ALLOW / ok`. The chain recorded custody as `RECORDED`, deterministic replay matched the original disposition, retrospective reconstruction verified the chain, and the returned result was preserved.

These results show that the supplied A3/A4 representation remained usable by the controlled governance path while semantic interpretation stayed unresolved, and those supplied state boundaries survived custody, replay, and reconstruction. They do not establish ÉLAN-native temporal resolution or a native state distinction.

#### Scope limitation

The StegVerse governance result in Experiment 2 was produced through the controlled local SDK experiment path using a test InTr posture resolver. It is **not** evidence of authentic live external or resident InTr execution.

Accordingly, Experiment 2 supports conclusions about representation, governed processing within that controlled path, evidence preservation, deterministic replay, and reconstruction. It does not establish that the same transition sequence has been exercised through an authentic live external/resident InTr runtime.

### 4.3 What the two experiments jointly establish

Experiment 1 shows that alternative upstream representations can change a downstream governed disposition while the evaluator remains fixed.

Experiment 2 shows that supplied external observation windows can survive the controlled StegVerse governance, custody, replay, and reconstruction path. The corrected ÉLAN record reveals a provenance failure in the original comparison: an experimenter-authored description had been treated as model-authored state. The experiment cannot establish native-model temporal-resolution differences without a comparable invoked condition.

Together, the experiments support a bounded systems claim:

> Governance does not evaluate human experience directly. It evaluates a representation. The provenance, semantic status, and temporal resolution of that representation are therefore part of the governance-relevant evidence surface.

They do **not** establish a universal semantics of silence, a general superiority of finer-grained state, or a complete theory of AI governance.

## 5. Why the Distinction Matters

If interpretation is collapsed into state too early, a governance system can make a perfectly consistent decision about a representation that was never sufficiently distinguished from the underlying observation.

This introduces several risks:

- **Hidden semantic authority** — an upstream component effectively determines meaning before governance begins.
- **False determinism** — an interpretive choice may appear to be an objective system fact.
- **Irreproducible disagreement** — humans and models may disagree about the meaning of the event while the system records only one interpretation.
- **Governance opacity** — a later reviewer may see the governed outcome without seeing the representation choice that caused it.
- **Evaluation drift** — two systems can appear to use the same governance policy while receiving materially different semantic states.

The solution is not to eliminate interpretation. Interpretation is often necessary. The stronger requirement is to make interpretation explicit, attributable, revisable, and distinguishable from observation.

## 6. A Governance-Oriented Representation Model

A governance-capable architecture should preserve a traceable progression such as:

human or environmental event  
→ observation  
→ representation  
→ optional interpretation  
→ governance input  
→ governed disposition  
→ execution or non-execution  
→ retained evidence

Each transition should be inspectable. A system should be able to answer: What was observed? Who or what transformed it? Was meaning inferred? Which version was evaluated? What rules were applied? What changed as a result?

This model also permits governance to operate on an observation without requiring the system to prematurely resolve semantic uncertainty. An interpretation can remain `UNRESOLVED` while the observation itself remains actionable.

## 7. Implications for AI Evaluation

Evaluators should not test only model outputs. They should also examine the state transformations that occur before governance.

A useful evaluation protocol can therefore ask whether:

1. source observations remain distinguishable from derived interpretations;
2. expected evidence fields are declared before outcomes are known;
3. alternative valid representations can be compared without changing the evaluator;
4. governance outcomes can be traced to the exact admitted representation;
5. replay and reconstruction preserve the same observation/interpretation boundary;
6. ambiguous semantic content can remain unresolved without becoming unusable;
7. temporal observation boundaries and predecessor-state relationships survive governance, replay, and reconstruction when they are part of the admitted representation.

These questions are relevant across conversational AI, autonomous systems, safety controls, workflow agents, compliance systems, and any environment in which machine-readable state is governed.

## 8. Contribution Boundary and Related-Work Positioning

The paper does not claim novelty for the broad propositions that AI systems operate on representations, that interpretation can embed assumptions, or that governance and provenance matter. Those ideas have substantial adjacent literatures.

The candidate contribution is the combination of:

1. experimentally preserving observation, interpretation, and governance as separately inspectable states;
2. comparing independently produced evidence chains without feeding one architecture's evaluative semantics into the other;
3. treating bounded non-emission as observable evidence while human intent remains `UNDETERMINED` and semantic interpretation remains `UNRESOLVED`;
4. distinguishing external observation-window resolution from source-native model output, including correction of a human-authored interval annotation;
5. retaining custody, deterministic replay, and reconstruction as part of the experimental claim; and
6. treating the work as a cumulative experimental program rather than a universal theory of silence or AI governance.

These distinctions should remain provisional until the ongoing literature/novelty review is complete.

## 9. Limits of the Experimental Series

Experiment 1 was intentionally narrow. It does not establish a general theory of human silence, infer motivation, or demonstrate that non-emission should always be treated as an event. It also does not establish that one governed disposition is inherently superior to another.

Experiment 1 supports only the following bounded conclusion: when an ambiguous human event can be represented in materially different machine-readable forms, the representation choice can alter a governed outcome.

Experiment 2 is likewise bounded. It does not establish that all periods of silence should produce separate state transitions, that finer temporal resolution is always preferable, or that ÉLAN lacks unexposed internal state distinctions. It establishes that the experimenter documented one no-invocation interval while StegVerse's controlled local SDK path preserved two supplied observation windows as distinct transitions; it does not demonstrate how ÉLAN would respond to silence when actually invoked.

Broader claims require additional independent experiments, additional human and machine interpretations, evaluation across different governance policies and domains, and, where relevant, authentic runtime evidence.

## 10. Research Questions

The experimental series suggests several research questions:

- How should systems distinguish an observed absence from missing data?
- When should a non-event become an explicit state transition?
- Which components are permitted to transform observation into interpretation?
- How should competing interpretations be retained and compared?
- Can governance operate safely while semantic interpretation remains unresolved?
- What evidence is necessary to reconstruct why a governed outcome changed?
- How do human and model interpretations diverge when the same event sequence is presented without shared semantic assumptions?
- What interfaces best allow independent evaluators to inspect and challenge representation choices before governance?
- When should successive bounded periods of the same observable condition remain separate state transitions rather than converge into one continuous state?
- How should temporal resolution be preserved across governance, replay, and reconstruction?

## 11. Conclusion

The most important boundary may occur before governance makes any decision.

An ambiguous human event must first become machine-readable state. If that transformation silently embeds interpretation, then the downstream governance system inherits assumptions that may never have been examined. If observation and interpretation remain distinct, governance can act on explicit evidence while uncertainty remains visible.

The experimental series adds a second requirement: even when semantic interpretation remains unresolved, architectures may need to preserve temporal and predecessor-state distinctions so that potentially consequential structure does not disappear through premature state convergence.

The resulting design principle is simple:

Observation should be preserved as observation.  
Interpretation should be identifiable as interpretation.  
Distinct state transitions should remain distinguishable when their boundaries are evidenced.  
Governance should evaluate the exact state it actually receives.  
And the path between those layers should be reconstructable at the resolution that existed when the decision was made.

This separation does not remove ambiguity from human communication. It prevents ambiguity—and potentially relevant state structure—from disappearing invisibly inside machine state.

## Author and Collaboration Note

Élisabeth Correvon has affirmatively accepted Rigel Randolph's invitation to join this work as a co-author. This revision therefore records the manuscript as a co-authored working draft.

The collaboration remains active. Élisabeth has indicated an intention to review future drafts and contribute to the shared theoretical and empirical analysis. A final contribution statement, author ordering, affiliations, corresponding-author designation, and submission approval will be confirmed by the authors before journal or conference submission.

No private correspondence is part of the experimental evidence.

## Empirical Basis

Experiment 1 derives from a controlled SDK governance experiment in which one condition treated a third event as missing input and another treated it as an explicit bounded non-emission observation. The governance evaluator was held constant.

Experiment 2 derives from a historical ÉLAN trace and a corresponding StegVerse cross-evaluation. The original trace's no-prompt interval included a human-authored annotation incorrectly treated in the earlier manuscript as native ÉLAN output. The coauthor has corrected the attribution; source-PDF comparison remains pending. StegVerse preserved two supplied bounded observation windows as separate A3 and A4 state transitions with intent `UNDETERMINED` and semantic interpretation `UNRESOLVED`. The StegVerse chain recorded `ALLOW / ok`, custody, deterministic replay, reconstruction, and a returned result through the controlled local SDK experiment path using the test InTr posture resolver. This does not establish authentic live external or resident InTr execution.

The main text deliberately omits repository identifiers and low-level protocol mechanics because those details are not necessary to state the conceptual and experimental distinctions. Supporting evidence can be supplied separately for review and reproducibility.
