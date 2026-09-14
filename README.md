# AdCopilot

An explainable diagnostic copilot for digital advertisers.

AdDiagnose is a domain analysis of the ad-campaign diagnostic workflow, from metric monitoring to root-cause investigation, plus an AI-driven enhancement that automates the diagnosis platforms leave to manual guesswork. The product built from that analysis is **AdCopilot**: it diagnoses *why* a Google Ads-style campaign's cost-per-acquisition (CPA) moved, instead of only reporting that it moved.

In one line: AdCopilot turns "your CPA went up" into "your CPA went up because CVR fell, here's the fix," through a testable pipeline that computes the diagnosis deterministically and explains it in plain language, refusing to guess when the data will not support a confident answer.

## Contributors

| | |
| --- | --- |
| **Team** | AdDiagnose |
| **Product** | AdCopilot |
| **Members** | Richa Pragat, Lakshita Rahoria, Shatakshi Chaudhri, Arthur Jawetz, Yongje Shu, Aaron Weng |

Design briefs and feasibility notes live in [`docs/`](docs/). [`AGENTS.md`](AGENTS.md) tells coding agents which document wins when they disagree.

## Run locally

Deterministic CPA diagnosis on synthetic campaigns (no live ads API, no LLM). The evaluation harness scores AdCopilot against a dashboard CPC-vs-CVR rival:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
python -m adcopilot.cli --scenario cvr_drop
python -m adcopilot.cli --scenario ctr_drop --campaign-id 1
python -m adcopilot.cli --scenario ambiguous
python -m adcopilot.evaluate --n 100 --sweeps
```

Seeded shocks: `cpm_spike`, `ctr_drop`, `cvr_drop`, `budget_capped`, `rank_capped`, `ambiguous`, `stable`. Report: [`docs/sprint-3-feasibility.md`](docs/sprint-3-feasibility.md).

## The problem

Advertisers watch CPA daily. When it spikes, the platform says it changed. It does not say why.

The same CPA jump can come from three unrelated causes, each needing a different fix:

1. A costlier auction (CPC rose with competition)
2. A conversion-quality drop (CVR fell from weak traffic or landing pages)
3. A visibility constraint (impressions lost to budget or rank)

On a dashboard those three look identical: a number went up. Raising bids can fix a rank problem and make a conversion problem worse. This is not a missing-data problem. The platform already has the numbers. It never runs the arithmetic that isolates the cause. That missing step is the explainability gap AdCopilot fills.

Google Ads is strong at setup, automated bidding, and reporting. The Recommendations tab still issues generic, one-way suggestions ("raise budget," "switch to Target CPA") without citing why *this* campaign moved, without a confidence score, and without a way to interrogate the claim. AdCopilot sits between reporting and optimization: automated, transparent root-cause diagnosis.

### How people handle it today

- **Platform recommendation engines** (Google Ads Recommendations tab): symptoms plus generic actions, no cited cause.
- **Third-party management tools** (Optmyzr, WordStream): more automation and reporting, still not a root-cause diagnosis of a specific change.
- **Manual investigation** (spreadsheets): the default. Analysts export reports and walk the metric relationships by hand. Slow, error-prone, and inconsistent, and it assumes expertise many teams do not have.

The unmet need: no tool automatically diagnoses the root cause of a metric change and explains it in plain language, grounded in the specific numbers.

**Value proposition:** for PPC strategists and marketers who cannot tell why a campaign's cost metrics changed, AdCopilot gives an instant, plain-language root-cause diagnosis with a matched recommended fix, by decomposing the metric math deterministically and narrating the result. Platform engines and spreadsheets report that a metric moved and prescribe generic actions.

## How it works

Architectural rule: the deterministic core computes; the LLM only narrates. Nothing surfaces without a traceable number behind it.

1. **Input.** Daily campaign metrics (impressions, clicks, cost, conversions) and derived CTR, CVR, CPC, CPM, CPA, ROAS.
2. **Anomaly detection.** A rule-based expected range flags when CPA leaves its recent trend.
3. **Decomposition.** Deterministic logic walks the identities `CPA = CPC ÷ CVR` and `CPC = (CPM ÷ 1000) ÷ CTR` to isolate which term drove the change, then classifies visibility loss as budget-capped vs rank-capped, and assigns a confidence tier when one term dominates.
4. **Explanation.** An LLM turns that structured diagnosis into a numbers-cited explanation and a recommended action. Mixed factors get a low-confidence refusal, not a guess.
5. **Output.** The user sees why the metric moved and what to do, in seconds instead of an hour of spreadsheet work.

Example:

> Your CPA rose from $10 to $14 this week. CPC held steady at $0.50, but CVR dropped from 5% to 3.6%. This is a conversion-quality issue, not a cost issue. Investigate recent landing page or targeting changes rather than adjusting your bid. Confidence: High.

## Users

| Role | Who | What they need |
| --- | --- | --- |
| Primary user | PPC campaign manager (agency, SMB lead-gen accounts) | Diagnose a CPA change fast, see the numbers and confidence, know when *not* to act, get a cause-matched next step, share a short client-ready explanation |
| Secondary user | In-house performance marketer | Separate ads vs traffic quality vs tracking vs landing page, route the issue to the right team, protect CPA/CAC while keeping volume |

Buyers are agency owners or in-house growth/marketing leads. Beneficiaries include the advertiser, sales (steadier leads), and account managers who need client-ready explanations. Web/CRO, creative, analytics, and finance sit around the diagnosis but are not day-to-day operators.

## Use cases

- **UC1.** Diagnose an abnormal CPA increase: compare the current period to a baseline, decompose the change, cite the dominant driver (media cost, engagement, conversion efficiency, or delivery constraints).
- **UC2.** Assess confidence and avoid false certainty: when causes are mixed or evidence is weak, refuse a single root cause and say what to investigate next.
- **UC3.** Cause-matched next step (Should Have): a deterministic investigation or proposed action (for example, landing-page and tracking checks for a CVR drop). The system never writes back to campaigns.
- **UC4.** Explain the diagnosis to stakeholders: what changed, why, how confident, what next, with the exact supporting metrics.

## Current MVP

AdCopilot does **not** connect to a live Google Ads account. Google Ads is the research basis for the metric taxonomy (Impression Share, Search Lost IS due to budget, Search Lost IS due to rank, Auction Insights, CPC, CVR, CPM, CTR). The build uses **synthetic data** shaped like those reporting fields. No live account access, no PII.

**Definition of done:** a user loads a campaign, the system flags an abnormal CPA movement, identifies the driving cause (or refuses when ambiguous), and shows a plain-language, numbers-cited diagnosis in a usable interface, across all seeded scenarios. The synthetic generator seeds labeled shock cases (competitor-driven CPM spike, landing-page CVR drop, budget/rank visibility loss, and an ambiguous multi-factor case) so known causes double as evaluation ground truth.

Example:

> CPA rose +64% ($22.57 → $36.90). CPM drove 87% of the change (CTR 7%, CVR 5%); leading driver CPM with margin over next 80%. Confidence: High. Diagnosis: auction price pressure.

### Must Have (F1–F6, F8)

| ID | The system shall |
| --- | --- |
| F1 | Detect abnormal CPA movement against the campaign's trailing baseline |
| F2 | Decompose a flagged CPA change into its driving term (CPC vs CVR, then CPM vs CTR) |
| F3 | Classify visibility loss as budget-capped vs rank-capped |
| F4 | Assign a confidence tier based on whether one term dominates |
| F5 | Return a refusal or low-confidence response when no single cause dominates |
| F6 | Generate a plain-language explanation citing the specific numbers |
| F8 | Present a trend chart, flagged-anomaly list, and diagnosis panel per anomaly |

### Should / Could / Won't

- **Should Have:** F7, cause-matched recommended actions using real Google Ads lever categories (bid strategy, budget, Quality Score, negative keywords).
- **Could Have:** multi-campaign scanning, a second tracked metric such as ROAS. Auction Insights competitor context is Won't-Have (API field is not public; allowlist closed).
- **Won't Have for now:** live Google Ads API, real account data, ML forecasting, automated execution of fixes, Auction Insights.

The diagnostic core is deterministic arithmetic and rules. An LLM only narrates the structured diagnosis. Identical input must produce identical diagnostic output. Diagnoses should return in seconds, using the same metric names a strategist already knows.

## Success bar

| Type | Measure | Target |
| --- | --- | --- |
| Technical | Diagnosis accuracy on seeded scenarios | ≥ 85% |
| Technical | Refusal correctness on seeded ambiguous cases | 100% |
| Technical | Anomaly detection | track true-positive / false-positive rate |
| Impact | Time-to-diagnosis vs manual spreadsheet work | minutes → seconds |
| Impact | Clarity and actionability | small user-feedback rubric |

**We will deliver:** ingest synthetic campaign data, detect abnormal CPA movements, diagnose or refuse, explain in plain language with cited numbers, through a usable UI.

**Workstreams:** data generation, diagnostic engine, explanation layer, interface, plus product (validation, use cases, evaluation design).

**Main risks:** synthetic data that does not look like real PPC; LLM narration drifting off the computed diagnosis (constrain it to structured output); scope creep past the Won't Have line.

## Origin

Started as a team project in Carnegie Mellon University's Integrated Innovation Institute course *Special Topics: Advanced AI for Industry and Society*. Product requirements and feasibility notes in [`docs/`](docs/) reflect that design process.

## Data and privacy

This repository uses **synthetic campaign metrics only**. Do not commit live ad-account data, credentials, API keys, PII, or partner briefs.
