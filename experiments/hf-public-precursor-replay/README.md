# Hugging Face Public Precursor Replay

Goal Task ID: `HF-PUBLIC-PRECURSOR-REPLAY-001`  
COSV: `40000100100001`

This experiment asks a narrow question: if a StegVerse public-observation lane had been continuously watching Hugging Face beginning April 1, 2026, what state changes could it have defensibly recorded before and during the July autonomous-agent intrusion?

The experiment is retrospective, but the observer is not allowed retrospective knowledge. Every record freezes the observer's knowledge at a declared historical cutoff. Later disclosures are stored as overlays only.

## Non-intrusive scope
Allowed evidence includes public Hugging Face pages/API metadata, public account/repository/artifact history, public security disclosures, public source-control history, and later public reporting used solely for retrospective annotation. The experiment does not reproduce exploits, use leaked credentials, probe private endpoints, or scan infrastructure.

## Three-layer state model
1. **Observation** — what was externally visible at the cutoff.
2. **Interpretation** — what, if anything, the visible evidence justified concluding then.
3. **Governance** — whether the evidence justified a change in monitoring/escalation posture, without granting execution or intrusion authority.

`UNKNOWN` is an admissible and expected state.

## Replay phases
- April 1-May 11: establish a normal public baseline.
- May 12-July 8: test for externally observable precursor deviations while keeping private/internal precursor facts hidden from the historical observer.
- July 9-July 13: reconstruct only the public-facing traces that could have been visible while the production intrusion was underway.
- July 16 onward: add disclosures and attribution as new evidence, never as rewrites of earlier observer state.

## Initial source anchors
- Hugging Face, `Security incident disclosure — July 2026`, published 2026-07-16.
- Hugging Face, `Anatomy of a Frontier Lab Agent Intrusion`, published 2026-07-27.
- OpenAI, `The Hugging Face incident and the road ahead`, published 2026-08-26.
- Reuters, `OpenAI's rogue agents probed Hugging Face for weaknesses two months before major hack`, published 2026-09-16.

## Success criteria
The experiment succeeds when it identifies the earliest defensible public `STATE_CHANGED` event and the earliest defensible governance escalation, or proves either remains `UNKNOWN`, while preserving false-positive alternatives and the public/private visibility gap.
