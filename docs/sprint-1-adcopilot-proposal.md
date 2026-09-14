# AdCopilot: An Explainable Diagnostic Copilot for Digital Advertisers

**Sprint 1 proposal** (Problem Discovery & Solution Proposal)  
**Author:** Richa Pragat  
**Archival PDF:** [AdvancedAI_AdCopilotProposal_RichaPragat.pdf](AdvancedAI_AdCopilotProposal_RichaPragat.pdf)

This markdown is a readable copy of the archival PDF so agents can load full context without parsing the PDF.

---

## 1. Problem and Current Landscape

### Problem Definition

Digital advertisers watch metrics like cost-per-acquisition (CPA) shift daily, and the most common operational question they face is: "My CPA just jumped - why?" Ad platforms answer only half of it. They show that CPA moved, but not why.

A single CPA spike can stem from at least three unrelated causes, each demanding a different fix:

- A costlier auction (cost-per-click rose because competition increased)
- A conversion-quality drop (conversion rate fell because traffic or the landing page worsened)
- A visibility constraint (the campaign lost impressions to a budget or ranking limit)

On the dashboard, all three look identical: a number went up. But "raise your bid" fixes a rank problem and actively worsens a conversion-quality problem. Lacking the diagnosis, advertisers routinely apply the wrong remedy and waste money.

This is not a data problem. The platform already has every number needed to make the call. It is an explainability problem: the arithmetic that would isolate the cause is never run and surfaced.

**Who experiences it:** In-house marketers and PPC agency strategists managing paid campaigns on Google Ads, Meta, and similar platforms.

**Context:** Recurring campaign review, daily monitoring and weekly reporting, where a metric moves and a decision must be made under time pressure.

**Why it matters:** Wrong diagnoses waste ad budget directly, and the manual investigation needed to diagnose correctly consumes enormous analyst time.

### Prevalence and Significance

- Global digital ad spend is projected to surpass $850 billion in 2026, making even small efficiency gains economically significant. [1]
- Forrester estimates that 37% of digital advertising budgets, approximately $293 billion annually out of $790 billion total spend, produce no measurable business impact, stemming from poor targeting, attribution failures, ad fraud, and manual optimization gaps. Misdiagnosis of performance changes falls squarely within this "manual optimization gap." [2]
- The problem is worsening: waste in programmatic advertising alone rose 34% in two years, to $26.8 billion (from $20 billion in June 2023). [3]
- The manual investigation that correct diagnosis requires is costly. One 2026 industry survey found that routine AdOps tasks (campaign optimization and budget pacing) consume an average of 39.75 hours per strategist every month, roughly 25% of a full working year, with the average strategist managing 33 client accounts simultaneously. [4]
- A separate study found marketers spend about 10 hours per week on manual tasks such as reviewing performance reports and identifying improvement opportunities. [5]

### Target Users and Stakeholders

- **User** (interacts with it): the PPC strategist or in-house marketer diagnosing a campaign.
- **Customer** (pays for it): the marketing agency or advertising business employing them; in the strategic framing, the ad platform itself, which could ship this to retain advertisers.
- **Beneficiary** (receives the value): the advertiser whose budget stops being wasted on wrong fixes and, indirectly, the platform, since an advertiser who understands their results trusts the platform and keeps spending.

### How the Problem Is Addressed Today

- **Platform recommendation engines** (Google Ads Recommendations tab): Surface generic, one-directional suggestions ("switch to Target CPA," "raise budget") without explaining the reasoning behind a specific campaign's movement, showing confidence, or allowing interrogation.
- **Third-party management tools** (Optmyzr, WordStream): Add automation and reporting, but still report symptoms and prescribe generic actions rather than diagnosing the root cause of a change.
- **Manual investigation** (spreadsheets): The default fallback. Analysts export reports and mentally work through the metric relationships. This is time-consuming and error-prone, requires expertise many teams lack, and is done inconsistently. [6]

**The unmet need:** No tool automatically diagnoses the root cause of a metric change and explains it in plain language, grounded in the specific numbers.

---

## 2. Proposed Solution

AdCopilot is an end-to-end system that detects abnormal movements in a campaign's cost metrics, decomposes the underlying cause, and explains it in plain language, citing the exact numbers and recommending the fix matched to the actual cause.

### Workflow, end to end

- **Input:** daily campaign metrics: impressions, clicks, cost, conversions (and derived CTR, CVR, CPC, CPM, CPA, ROAS).
- **Anomaly detection:** a rule-based expected range flags when CPA deviates meaningfully from its recent trend.
- **Decomposition (the core intelligence):** deterministic logic walks the metric identities `CPA = CPC ÷ CVR` and `CPC = (CPM ÷ 1000) ÷ CTR` to isolate which term drove the change, and classifies any visibility loss as budget-capped vs rank-capped. It assigns a confidence tier based on whether a single term clearly dominates.
- **Explanation:** a language model converts the structured diagnosis into a plain-language, numbers-cited explanation and a recommended action. When multiple factors move together, it explicitly reports low confidence and points to what to investigate rather than guessing.
- **Output / value:** the user sees, in a clean interface, why the metric moved and what to do, in seconds instead of an hour of spreadsheet work.

**Architectural principle:** the deterministic core computes; the LLM only narrates; nothing surfaces without a traceable number behind it. This is what makes the output trustworthy enough to act on with real money.

**Example output:**

> Your CPA rose from $10 to $14 this week. CPC held steady at $0.50, but CVR dropped from 5% to 3.6%. This is a conversion-quality issue, not a cost issue. Investigate recent landing page or targeting changes rather than adjusting your bid. Confidence: High.

### Value Proposition

For PPC strategists and marketers, who struggle with knowing why a campaign's cost metrics changed, AdCopilot provides an instant, plain-language root-cause diagnosis with a matched recommended fix, by decomposing the metric math deterministically and narrating the result in plain language, unlike platform recommendation engines and manual spreadsheet analysis, which report only that a metric moved and prescribe generic actions without explaining the specific cause or their confidence.

### Why Choose It Over Alternatives

Existing tools tell you what changed. AdCopilot tells you why, and shows its work. Every diagnosis points to the exact numbers behind it, marks how confident it is, and says so plainly when the data isn't clear enough to call. That combination, a real answer you can trust, is what neither black-box recommendations nor manual spreadsheet work offers today.

---

## 3. Measuring Impact

### Technical

1. **Diagnosis accuracy:** % of seeded test scenarios where the system identifies the true root cause (measurable because the synthetic dataset has known causes).
2. **Refusal correctness:** % of genuinely ambiguous scenarios where the system correctly declines a single-cause diagnosis rather than guessing.
3. **Anomaly detection reliability:** true-positive / false-positive rate on flagged metric movements.

### User / Business

4. **Time-to-diagnosis:** reduction versus manual spreadsheet investigation (target: minutes → seconds).
5. **Diagnosis clarity & actionability:** user-feedback rubric score on whether the explanation is understandable and the recommendation is actionable.

---

## 4. Feasibility and Scope

This is realistically buildable end-to-end by a team of 4–5 in one semester:

- **No external data dependency.** Real campaign data is not publicly available, so the system runs on a synthetic dataset generator that seeds 5–8 labeled "shock" scenarios (a competitor-driven CPM spike, a landing-page CVR drop, budget/rank visibility loss, and an ambiguous multi-factor case). The system is real even though the data is generated and the known causes double as evaluation ground truth.
- **A verifiable core with an AI explanation layer.** The diagnosis is computed directly from the metric identities: transparent, testable logic that always traces to real numbers. An LLM turns that result into a clear, plain-language explanation. Computation stays auditable; AI does what it's best at, communicating.
- **The LLM layer is prompt engineering, not research,** a well-understood, low-risk task.
- **Stages are independent,** so work parallelizes cleanly across data generation, the diagnostic engine, the explanation layer, and the interface, plus product workstreams (defining correct diagnoses and the evaluation rubric).

**Must-have (core value):** synthetic data → anomaly detection → deterministic decomposition → LLM explanation → interface, delivering a correct, cited diagnosis for each seeded scenario including the refusal case.

**Explicitly out of scope:** live platform integration, ML forecasting, and auto-execution of fixes. A smaller system that works end-to-end is the goal.

**In one line:** AdCopilot turns "your CPA went up" into "your CPA went up because CVR fell, here's the fix," through a real, testable pipeline that computes the diagnosis deterministically and explains it in plain language, refusing to guess when the data won't support a confident answer.

---

## References

1. Marketing LTB. "Digital Advertising Statistics 2026: 92+ Stats & Insights." https://marketingltb.com/blog/statistics/digital-advertising-statistics/ (Statistics aggregator; underlying forecasts typically derive from eMarketer / Statista / Dentsu projections.)
2. Get-Ryze. "The Cost of Bad Ad Management: How Much Wasted Spend Hurts ROI." April 2026. https://www.get-ryze.ai/blog/cost-bad-ad-management-wasted-spend-impact (Figure attributed to Forrester Research via secondary source; primary report not independently verified.)
3. EMARKETER. "Wasted Ad Spend - Reports, Statistics & Marketing Trends." 2026. https://www.emarketer.com/topics/category/wasted%20ad%20spend (Primary source: Association of National Advertisers (ANA), Q2 2025 Programmatic Transparency Benchmark Report.)
4. PPC Land. "71% of ad agencies say manual work is putting campaigns at risk." March 2026. https://ppc.land/71-of-ad-agencies-say-manual-work-is-putting-campaigns-at-risk/ (Primary source: Fluency 2026 AdOps survey; Fluency provides advertising-automation software.)
5. PPC Land. "DoubleVerify study reveals marketers spend 10 hours weekly on manual tasks." July 2025. https://ppc.land/doubleverify-study-reveals-marketers-spend-10-hours-weekly-on-manual-tasks/ (Primary source: DoubleVerify study; DoubleVerify provides ad measurement and optimization solutions.)
6. DashThis. "PPC Reporting Guide: Key Metrics + Templates." https://dashthis.com/blog/ppc-reporting/
