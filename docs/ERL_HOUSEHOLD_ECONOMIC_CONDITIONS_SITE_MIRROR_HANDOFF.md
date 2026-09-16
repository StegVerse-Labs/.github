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

## Candidate source families

Initial public-data families expected to contribute, subject to ERL evidence admission and exact series review:

- BLS earnings and CPI components;
- BEA personal income, disposable income, PCE, and saving;
- Federal Reserve household debt-service / financial-obligation series where methodologically appropriate;
- New York Fed household debt balances and delinquency by debt class;
- Census / ACS household income, housing-cost and demographic distribution measures;
- other official sources required for taxes, insurance, housing, food, energy, medical costs, and cohort distribution.

No source is admitted merely by appearing in this list.

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

`Physical-Economics.html` already exists and remains the broader report-request / evidence-bounded presentation surface. The new page should not duplicate its report engine. The economic-conditions page should consume the same governed ERL semantics for a persistent current-state view and may link into Physical Economics for deeper question-specific reports.

## Implementation sequence

1. Define the ERL historical-comparability / household-state output contract.
2. Identify each source series, native frequency, earliest comparable date, revisions, and structural breaks.
3. Implement deterministic normalization / index-mode rules.
4. Build Site page shell and graph against fixtures only.
5. Bind the page to governed ERL output.
6. Validate fail-closed handling for missing, stale, incompatible, or ungoverned data.
7. Validate mobile Safari / current-iPhone behavior.
8. Merge only after exact-head validation.
9. Public activation requires authentic governed output and served-body verification; source merge alone is insufficient.

## Current state

- canonical Goal Task record: PRESENT
- coordination issue: OPEN
- ERL issue: OPEN
- Site issue: OPEN
- household/economic-distribution semantic parent: PRESENT
- existing Physical Economics Site surface: PRESENT
- historical comparability output contract: NOT YET IMPLEMENTED
- real-time household-state endpoint/output: NOT YET IMPLEMENTED
- Site graph/page implementation: NOT YET IMPLEMENTED
- governed live-data binding: NOT YET IMPLEMENTED
- public activation: NOT CLAIMED

## Next work

Continue without human action by inventorying the relevant official series and their comparability windows, then implement the output contract and Site page shell in parallel while preserving the fail-closed boundary.
