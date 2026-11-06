# Federation directory (H61)

SKAP Vault inside KV is the only PII and credential store for every user, the ecosystem's own included; the ecosystem holds none (HST citation pending P1 #163).

## Owner and canonical file

- **Owner:** Lane B (`lane-b-91117956`) is the single owner of the canonical federation directory. Coordination assigned it at 17:25Z, and P1 logged that on StegVerse-org/.github#163. The goal is StegVerse-org/.github#162.
- **Canonical file:** `StegVerse-Labs/.github:org-boundary/registry/federation.json`
  - Schema: `stegverse.org-federation-directory.v1`
  - Generation 3, denominator 16
  - Generation commit: `4790fa41`
- **Projections:** every other organization holds `org-boundary/registry/federation.json` as a *declared projection*.
  - A projection carries the canonical entries unchanged, plus a `projection` block naming the source commit and sha256.
  - It is updated only by re-projection, and local additions are prohibited.
  - The reference tool is SV-LLM/.github `org-boundary/runtime/federation_projection.py` at `792b5a3b`.
  - That tool is vendored byte-identical under `data/federation-projection-census/reference/` and pinned by sha256.

## Routing

- A crossing resolves its destination through the sender's own projection. The sender's projection must therefore be CURRENT for the destination row to exist.
- A change to the directory (a row added, changed or removed) lands here first, on a pull request whose body opens with the authoring session. Only then is it re-projected.
- Questions, blocks and requests about the directory go to StegVerse-org/.github#162 and carry the six fields:
  - failure_code
  - failed_predicate
  - required_evidence_or_repair
  - retry_entrypoint
  - owning_existing_goal
  - next_attempt

## Projection census

`python org-boundary/runtime/federation_projection_census.py verify` judges each directory row against the copy that organization published. It reads the exact bytes in `data/federation-projection-census/observed/`, which were taken anonymously at a pinned main commit. The census never fetches anything itself: it uses no clock, no network and no git, and its result is sealed.

Census at this commit (canonical generation 3):

| state | organizations |
|---|---|
| CANONICAL | StegVerse-Labs |
| CURRENT (declared projection, entries equal canonical) | StegVerse-org, SV-LLM |
| STALE: undeclared generation-1 copy, missing SV-LLM and SV-011 | AaCT-E, Admissible-Existence, AdmittedCode, Data-Continuation, ECAT-ICAT-Formal, GCAT-BCAT-Engine, StegGhost, StegVerse-002, Triad-Test |
| UNOBSERVED: not anonymously readable | formalism-tests, Infrastructure-Continuity-Ventures, master-records, SV-011 |

**Effect:** a crossing *from* a STALE organization *to* SV-LLM or SV-011 finds no directory row and fails closed.

**Repair:** each owner commits the bytes printed by `python org-boundary/runtime/federation_projection_census.py reproject --organization <ORG>`.
- These bytes are identical to what StegVerse-org and SV-LLM already hold.
- The observation is then re-taken at the next milestone.

## Rebinding only at milestones

The census, its observations and every projection are re-bound only at a milestone, never by polling. The milestones are:
- a canonical generation change landing here;
- an organization's re-projection landing on its main;
- a repository becoming anonymously readable.

Between milestones the committed census is the answer.

## What the census does not do

- It grants no routing, admission or transition authority (`authority_effect: NONE_OBSERVATION_ONLY`).
- It never edits the canonical file or any organization's copy.
- It reads and stores no credential. An authenticated read is never evidence here. Credentials go only through TV/TVC least-privilege issuance, and bots never mint, hold or store them.
