# ERL Household Economic Conditions Site Mirror Handoff

## Canonical identity

- Goal Task ID: `ERL-HOUSEHOLD-ECONOMIC-CONDITIONS-SITE-001`
- coordination issue: `StegVerse-Labs/.github#2027`
- ERL implementation/research issue: `StegVerse-Labs/Executive_Rhetoric_Ledger#163`
- Site implementation issue: `StegVerse-Labs/Site#1368`
- canonical ERL household/economic-distribution source: `StegVerse-Labs/Executive_Rhetoric_Ledger/docs/ECONOMIC_DISTRIBUTION_MIRROR_HANDOFF.md`
- existing Site Physical Economics surface: `StegVerse-Labs/Site/Physical-Economics.html`
- COSV task vector: not yet materialized
- coordination state: `ACTIVE`

## Goal

Create a real-time public U.S. economic-conditions page that reports what current evidence supports about household economic condition rather than treating headline spending, GDP, gross real weekly earnings, or aggregate debt-service ratios as household welfare.

The public surface must be a presentation consumer of governed ERL outputs. It may not create findings that are absent upstream.

## Required current-state model

The page must preserve, when evidence exists:

1. gross labor income;
2. estimated net disposable resources / take-home resources;
3. household required-cost burden;
4. debt-service burden by debt class;
5. necessary consumption;
6. discretionary residual;
7. saving or dissaving;
8. new borrowing;
9. delinquency / arrears;
10. unmet or foregone consumption;
11. distribution by income/debt/wealth cohort where available.

The page must not infer household improvement merely because nominal spending rises, average gross real weekly earnings rise, GDP/productivity rises, or an aggregate debt-service ratio remains below a prior crisis peak.

## Longitudinal graph contract

The primary line graph must support range selection such as `1Y`, `5Y`, `10Y`, `2000→Now`, and `Max`, but the displayed start date for each series is governed by comparability rather than by a cosmetic UI promise.

Rules:

- extend to 2000 when the series is directly comparable or can be defensibly reconstructed under an explicit method;
- otherwise begin at the earliest comparable observation and disclose why earlier history is unavailable;
- preserve source vintage and revision date;
- render methodology / structural-break markers;
- never splice incompatible definitions into one continuous line without a visible break;
- same-axis overlays are allowed only when units and definitions are genuinely comparable;
- cross-metric comparison should default to normalized index mode (`selected start = 100`) rather than misleading mixed units;
- avoid dual-axis presentation when it can create a false relationship;
- gaps remain gaps unless a governed historical-proxy method explicitly authorizes reconstruction;
- historical proxies must remain labeled `DERIVED_HISTORICAL_PROXY`, not direct observation.

## Official-series inventory established in ERL PR #164

Initial official source families have now been inventoried on branch `feat/household-economic-conditions-series-163` at head `432697db308fa183a566f69af88219c910e1912c`.

The inventory records source agency, family, native frequency, unit, population scope, earliest comparable date, page display start, revision semantics, structural breaks, household-state role, limitations, source/methodology references, and admission state.

Current bounded findings:

- BLS CPI-U all-items history extends well before 2000; 2000 is a defensible display floor for the selected series.
- BLS CES production/nonsupervisory real earnings extend before 2000; gross earnings remain context only and are not net take-home resources.
- BEA monthly personal-income/disposition series provide pre-2000 history and are revision-sensitive, so source vintage must remain visible.
- Federal Reserve current-method DSR is available from 2005 forward; the archived 1980-2024 prior-method series is a separate methodology segment and must not be silently spliced.
- New York Fed CCP household-debt reporting has main public continuity from 2003 with separately supplied 1999-2003 history; student-loan reporting is reliable from 2003.
- ACS standard 1-year comparisons begin in 2005 for this lane; the 2020 experimental 1-year release is noncomparable, and Census 2000 comparison requires explicit table/universe/question review.

Source artifact: `research-data/household-economic-conditions/official-series-inventory.v1.json`.

## Governed ERL output contract implemented in PR #164

ERL PR #164 also introduces:

- `schemas/household-economic-conditions-output.schema.json`;
- `fixtures/household-economic-conditions/fail-closed.fixture.json`;
- `docs/HOUSEHOLD_ECONOMIC_CONDITIONS_SITE_MIRROR_HANDOFF.md`.

The schema requires evidence state, freshness, the ten household-state components, source-series observations, earliest comparable dates, vintage/revision metadata, comparison mode, structural breaks, interpretation boundaries, and explicit `public_activation_authorized` state.

The fixture is UI-only. It carries `evidence_state=FIXTURE_ONLY`, contains illustrative normalized-index values only, and sets `public_activation_authorized=false`.

ERL exact-head validation evidence:

- PR: `StegVerse-Labs/Executive_Rhetoric_Ledger#164`;
- head: `432697db308fa183a566f69af88219c910e1912c`;
- `Validate Ledger Schemas` run `35162542553`: `SUCCESS`.

No live source binding, deployment, or public activation is claimed from this validation.

## Site page shell implemented in PR #1369

Site branch `feat/household-economic-conditions-site-1368` now contains:

- `Household-Economic-Conditions.html`;
- `data/household-economic-conditions.fixture.json`;
- `docs/HOUSEHOLD_ECONOMIC_CONDITIONS_SITE_MIRROR_HANDOFF.md`;
- `data/session-work-claims.d/site-household-economic-conditions-1368.json`.

The page shell provides:

- current-state cards for the ten required household components;
- `1Y`, `5Y`, `10Y`, `2000→Now`, and `Max` controls;
- normalized-index trajectory comparison;
- absolute-value mode that refuses mixed-unit overlays;
- visible Federal Reserve DSR, New York Fed CCP, and ACS methodology/coverage boundaries;
- explicit interpretation prohibitions;
- fail-closed fixture/public-activation state.

The first Site validation attempt failed because the branch had no exact active pre-work claim. That condition was repaired by adding the bounded session-work claim fragment. No application or authority semantics were changed by that repair.

Current Site exact-head evidence:

- PR: `StegVerse-Labs/Site#1369`;
- head: `fe9df5aabd715c0957e34db5d37665a1e7f1e417`;
- Site Handoff Orchestrator run `35162631957`: `SUCCESS`;
- Ecosystem Heartbeat Orchestration run `35162632000`: `SUCCESS`;
- Node IndexedDB Schema Migration run `35162631871`: `SUCCESS`;
- Site Bootstrap Validate run `35162631877`: `SUCCESS`.

No deployment or served-body/public activation is claimed from these validations.

## Public page behavior

Current-state section:

- timestamp / data vintage;
- freshness state;
- high-level household-condition summary with explicit evidence coverage;
- cards for the governed state components above;
- cohort selector where data supports it;
- visible `UNKNOWN`, `NOT_COMPARABLE`, `PROXY`, and `STALE` states.

History section:

- interactive line graph;
- range control;
- metric selector;
- absolute-value mode for genuinely comparable same-unit series;
- normalized-index mode for cross-metric trajectory comparison;
- source/methodology notes linked to each series;
- structural-break and revision markers.

Interpretation section:

- separate `what changed` from `what that may mean`;
- do not convert correlation into causation;
- distinguish household distribution from national aggregate condition;
- show evidence gaps instead of filling them rhetorically.

## Existing Site relationship

`Physical-Economics.html` already exists and remains the broader report-request / evidence-bounded presentation surface. The new page does not duplicate its report engine. The economic-conditions page is a persistent current-state consumer and may link into Physical Economics for deeper question-specific reports.

## Current state

- canonical Goal Task record: PRESENT / ACTIVE
- coordination issue: OPEN
- ERL issue: OPEN
- Site issue: OPEN
- ERL official-series inventory: IMPLEMENTED ON PR #164 / VALIDATED
- historical comparability output schema: IMPLEMENTED ON PR #164 / VALIDATED
- ERL fail-closed fixture: IMPLEMENTED ON PR #164 / VALIDATED
- Site page shell: IMPLEMENTED ON PR #1369 / VALIDATED
- Site session work claim: IMPLEMENTED / ORCHESTRATION VALIDATED
- README reconciliation in ERL/Site branches: PENDING
- exact official agency-series identifier bindings: PENDING
- automated official-data acquisition: PENDING
- real-time household-state endpoint/output: NOT YET IMPLEMENTED
- governed live-data binding: NOT YET IMPLEMENTED
- current-iPhone Safari validation: PENDING
- public activation: NOT CLAIMED

## Next work

Keep both implementation PRs open until repository README reconciliation is included. Then re-run exact-head validation, merge only with expected-head protection when all applicable gates remain green, bind exact source-series identifiers and deterministic acquisition/normalization, and connect Site only to authentic governed ERL output. Public activation remains separately gated on fresh governed output plus served-body verification.
