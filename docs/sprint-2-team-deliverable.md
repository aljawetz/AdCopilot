# AdCopilot — Sprint 2 Team Deliverable

**Problem Validation, Requirements & MVP Scope**  
**Team:** AdDiagnose  
**Members:** Richa Pragat, Lakshita Rahoria, Shatakshi Chaudhri, Aaron Weng, Yongje Shu, Arthur Jawetz  
**Archival PDF:** [Sprint2Deliverable_TeamAdDiagnose.pdf](Sprint2Deliverable_TeamAdDiagnose.pdf)

This markdown is a readable copy of the archival PDF so agents can load full context without parsing the PDF. The PDF also includes a screenshot of the Google Ads Recommendations tab (Figure 1) that is not reproduced here.

When this document conflicts with the Sprint 1 proposal on **scope**, this document wins.

---

## 1. Problem, User & Need Validation

### The Problem

Digital advertisers monitor cost-per-acquisition (CPA), the cost to win one customer, daily, but when it moves sharply, ad platforms report that it changed, not why. A single CPA spike can stem from three unrelated causes, each needing an opposite fix:

- A costlier auction (CPC rose with competition)
- A conversion-quality drop (CVR fell from weak traffic or landing pages)
- A visibility constraint (impressions lost to budget or rank)

On the dashboard all three look identical: a number went up. Yet "raise your bid" fixes a rank problem while worsening a conversion one. Without a diagnosis, advertisers apply the wrong remedy and waste money. This is not a data problem: the platform holds every number needed but never runs the arithmetic to isolate the cause. That missing step is the explainability gap AdCopilot fills.

### Domain Context — Where the Gap Sits

The digital advertising workflow spans campaign setup, automated bidding (e.g., Smart Bidding, Performance Max), performance reporting, and a recommendations engine. These systems are strong at optimization and reporting but weak at diagnosis. The Google Ads Recommendations tab issues generic, one-directional suggestions ("switch to Target CPA," "raise budget") without explaining why a specific campaign moved, showing its confidence, or letting the user interrogate it. Dashboards show the compound metrics but never decompose them. AdCopilot targets this underserved layer between reporting and optimization: automated, transparent root-cause diagnosis.

### 1.1 Evidence the Problem Is Real and Meaningful

- Global digital ad spend is projected to surpass $850 billion in 2026, so even small efficiency gains are economically significant. [1]
- An estimated 37% of digital ad budgets, roughly $293B of $790B, produce no measurable business impact, attributed to poor targeting, attribution failures, ad fraud, and manual optimization gaps; misdiagnosis sits squarely in that last category. [2]
- Waste in programmatic advertising alone rose 34% in two years, to $26.8B (from $20B in June 2023). The problem is growing, not shrinking. [3]
- Manual diagnosis is expensive: routine AdOps tasks consume ~39.75 hours per strategist per month (about 25% of a working year), with the average strategist managing 33 client accounts at once. [4] A separate study found marketers spend ~10 hours weekly on manual tasks like reviewing reports and finding improvements. [5]

### 1.2 Target Users & Stakeholders

**Primary user: PPC Campaign Manager**

Managing multiple Google Search lead-generation accounts for SMB clients. Monitors CPA daily and needs to diagnose sudden changes quickly to explain decisions to clients.

Needs:

- Quickly identify why CPA changed: higher CPC, lower conversion rate, budget constraint, rank constraint, or mixed causes.
- See the evidence behind the diagnosis: metric values, period-over-period change, and confidence level.
- Know when not to act because the movement is too small or ambiguous. Get a cause-matched next step, rather than a generic recommendation.
- Produce a short explanation to share with clients.

**Secondary user: In-house Performance Marketer**

Managing paid acquisition for one business. Determines whether a problem comes from media buying, traffic quality, conversion tracking, or the landing page.

Needs:

- Identify whether a performance issue comes from ads, traffic quality, conversion tracking, or landing page.
- Quickly direct the problem to the right team: paid media, web/product, analytics, or creative.
- Protect CPA/CAC while maintaining conversion volume.
- Explain performance changes to growth and marketing leadership.

**Stakeholders:** Agency paid-media lead, account/client-success manager, and advertiser/business owner. They need clear, credible explanations, but they are not the main day-to-day operators.

| Category | Details |
| --- | --- |
| Customers / buyers | Agency owner or in-house Head of Growth / VP Marketing: buy the tool for team productivity, client retention, and marketing efficiency. Marketing-ops leaders influence adoption, since data and tracking must be reliable. |
| Beneficiaries | The advertiser / business owner (more efficient spend, clearer explanations); sales teams (steadier, better-qualified leads); account managers (client-ready explanations); and indirectly the platform (retained, trusting advertisers). |
| Key collaborators | Web/CRO, creative, and analytics/marketing-ops teams that own the landing pages, ad content, and tracking a diagnosis may point to; finance approves spend changes. |
| Platform / data context | Operates on data structured like major ad platforms (Google Ads, Meta, Microsoft, TikTok, LinkedIn) and connected analytics/CRM sources. |

### 1.3 Core Use Cases

Four situations define the product. Each maps to a Must-Have requirement in Section 2.

**UC1 — Diagnose an abnormal CPA increase**

When CPA rises, the campaign manager needs to know whether the movement is driven primarily by media cost, engagement, conversion efficiency, or delivery constraints.

AdCopilot compares the current period with a baseline, decomposes the CPA change using platform-appropriate metrics, and cites the dominant driver.

**UC2 — Assess confidence and avoid false certainty**

When the cause is mixed or evidence is weak, the manager needs to know whether action is justified.

AdCopilot assigns a confidence tier and explicitly refuses to name a single root cause when no driver dominates, while stating what to investigate next.

**UC3 — Receive a cause-matched next step**

Once a diagnosis is sufficiently supported, the manager needs guidance that matches the evidence.

AdCopilot provides a deterministic next investigation or proposed action, for example landing-page and tracking checks for a CVR decline, without automatically modifying campaigns.

**UC4 — Explain the diagnosis to stakeholders**

The manager needs to justify decisions to clients or internal leaders.

AdCopilot produces a concise, plain-language explanation that states what changed, why, how confident the system is, and what should happen next, with the exact supporting metrics.

---

## 2. Requirements & MVP Definition

### Functional Requirements

AdCopilot does not connect to a live Google Ads account. Google Ads serves as the research basis for the requirements in this document because it already computes and names the metrics required by AdCopilot's diagnostic logic. These metrics include Impression Share, Search Lost Impression Share due to budget, Search Lost Impression Share due to rank, and Auction Insights. Their use establishes that AdCopilot's diagnosis is grounded in a real, industry-standard metric taxonomy rather than one invented for the project. For this semester, AdCopilot replicates this metric structure using synthetic data. It does not read from or write to a real Google Ads account.

**Figure 1 (in the PDF):** The Google Ads Recommendations tab, showing an account's optimization score alongside suggested actions such as raising budgets or adding broad match keywords, each with a projected score improvement but no explanation of why that specific account needs it. This is the exact gap F6 addresses: Google surfaces a suggestion and a percentage; AdCopilot surfaces the suggestion plus the specific numbers that caused it.

Each requirement below is testable against seeded synthetic campaign scenarios.

| ID | Requirement: "The system shall..." | Grounded in Google Ads precedent | Test |
| --- | --- | --- | --- |
| F1 | Detect abnormal CPA movement against the campaign's trailing baseline | Cost and conversions, which are standard reporting columns in Google Ads | Flags all seeded anomalies with a low false positive rate on stable synthetic data |
| F2 | Decompose a flagged CPA change into its driving term, CPC vs CVR, then CPM vs CTR | Mirrors the metric identity behind Google's own CPC, CVR, CPM, and CTR columns | Correct injected driver identified in each seeded scenario |
| F3 | Classify visibility loss as budget capped vs rank capped | Directly modeled on Google Ads' own Search Lost IS (budget) and Search Lost IS (rank) metrics | Correct classification on scenarios seeded with each cause |
| F4 | Assign a confidence tier to each diagnosis based on whether one term dominates the change | Novel to AdCopilot; this is the layer Google Ads does not provide | High confidence on single-cause cases, low confidence on multi-factor cases |
| F5 | Return a refusal or low confidence response when no single cause dominates | Novel to AdCopilot | Correctly declines on the ambiguous seeded scenario(s) |
| F6 | Generate a plain language explanation citing the specific numbers behind the diagnosis | Contrasts with Google's Recommendations tab, which surfaces suggestions without a cited cause | Output names the metrics and exact values behind the diagnosis |
| F7 | Pair each diagnosis with a cause-matched recommended action | Action vocabulary drawn from real Google Ads levers: bid strategy, budget, Quality Score, negative keywords | Recommendation differs appropriately by diagnosed cause |
| F8 | Present a trend chart, flagged anomaly list, and diagnosis panel per anomaly | UI only | User can view a campaign and open any anomaly's diagnosis |

### 2.1 Non-Functional Requirements

- **Explainability.** Every claim must trace to a named metric and value. The system should use the same terminology as Google Ads, including CPC, CVR, CPM, CTR, and Lost Impression Share, so that a strategist can check the explanation against familiar reporting concepts.
- **Responsiveness.** A diagnosis should return within seconds. This is intended to replace the manual cross-referencing of Impression Share and Auction Insights reports, which can take a strategist tens of minutes.
- **Reliability.** The deterministic diagnostic core must return identical output for identical input on every run.
- **Usability.** The interface and explanations must be readable and actionable for a non-technical marketer without specialized training.
- **Data handling.** The semester implementation must use synthetic data only. The data should be structured to match real Google Ads reporting fields. The system must not use live account access or personally identifiable information (PII).

### 2.2 Prioritization (MoSCoW)

**Must Have** (required for the core MVP)

- F1–F6: detect anomalies and decompose CPA changes
- Classify visibility loss by budget versus rank
- Assign confidence and refuse ambiguous diagnoses
- Use CPC, CVR, CPM, CTR, and Impression Share
- F8: interface: trend chart, flagged-anomaly list, and diagnosis panel per anomaly

**Should Have** (important supporting functionality)

- F7: cause-matched recommendations
- Map actions to real Google Ads lever categories

**Could Have** (optional extensions if time permits)

- Multi-campaign anomaly scanning
- Second tracked metric, such as ROAS
- Competitor-pressure context (Auction Insights overlap and outranking concepts)

**Won't Have** (outside the semester scope)

- Live Google Ads API integration
- Real account data
- Machine-learning forecasting
- Automated execution of fixes

### End-to-End MVP

**Definition of done:** a user loads a campaign, the system flags an abnormal CPA movement, identifies the driving cause (or refuses when ambiguous), and presents a plain-language, numbers-cited diagnosis in a usable interface demonstrated across all seeded scenarios.

Example:

> CPA rose +64% ($22.57 → $36.90). CPM drove 87% of the change (CTR 7%, CVR 5%); leading driver CPM with margin over next 80%. Confidence: High. Diagnosis: auction price pressure.

---

## 3. Feasibility & Success Measures

### Why This Is Feasible in One Semester

- **No data-access risk.** Real campaign data is not public; a synthetic generator with seeded, known causes removes the biggest blocker and doubles as ground truth for evaluation.
- **The core is deterministic.** Diagnosis is arithmetic and rule logic derived from metric identities: testable and reliable, with no model to train. The LLM only narrates, which is prompt engineering, not research.
- **Parallelizable across 6 people.** Data generation, the diagnostic engine, the explanation layer, and the interface are independent workstreams, with product owning validation, use cases, and evaluation design.

**Indicative plan:** Weeks 1–2 validate use cases and build the synthetic dataset + engine skeleton; Weeks 3–4 complete decomposition + confidence logic and the explanation layer; Weeks 5–6 integrate the interface, run evaluation against seeded scenarios, and polish.

### 3.2 Success Criteria

| Type | Measure |
| --- | --- |
| Technical | Diagnosis accuracy: % of seeded scenarios where the true root cause is identified. Target: ≥ 85%. |
| Technical | Refusal correctness: % of ambiguous scenarios correctly declined rather than force-diagnosed. Target: 100% on seeded ambiguous cases. |
| Technical | Anomaly detection reliability: true-positive / false-positive rate on flagged movements. |
| Impact | Time-to-diagnosis: reduction versus manual spreadsheet investigation (target: minutes → seconds). |
| Impact | Diagnosis clarity & actionability: score from a small user-feedback rubric on whether the explanation is understandable and the recommendation actionable. |

### Semester MVP Contract

What the team commits to deliver by the end of semester.

| Category | Details |
| --- | --- |
| We WILL deliver | An end-to-end system that ingests synthetic campaign data, detects abnormal CPA movements, deterministically diagnoses the root cause (or refuses when ambiguous), and explains it in plain language with cited numbers, through a usable interface. (Must-Have F1–F6, F8.) |
| We will NOT do | Live ad-platform integration, ML forecasting, automated fix execution, or use of real user data. |
| Use cases covered | UC1 (diagnose a cost spike), UC2 (signal vs noise / refusal), UC4 (plain-language explanation); UC3 (matched recommendation) targeted as Should-Have. |
| Definition of done | Correct, cited diagnosis across all seeded scenarios including the ambiguous/refusal case, viewable end-to-end in the interface. |
| Success bar | ≥ 85% diagnosis accuracy and 100% refusal correctness on the seeded evaluation set. |
| Team & roles | Product: problem/user validation, use cases, evaluation design, coordination. Engineering: data generation, diagnostic engine, explanation layer, interface. |
| Key risks | (1) Synthetic data too unrealistic → ground scenario design in PPC research / interviews. (2) LLM narration drifts from the computed diagnosis → constrain it to the structured output only. (3) Scope creep → hold the Won't-Have line. |

---

## References

1. Marketing LTB. "Digital Advertising Statistics 2026." https://marketingltb.com/blog/statistics/digital-advertising-statistics/
2. Get-Ryze. "The Cost of Bad Ad Management." 2026. https://www.get-ryze.ai/blog/cost-bad-ad-management-wasted-spend-impact (figure attributed to Forrester Research).
3. Association of National Advertisers (ANA). "The ANA Q2 2025 Programmatic Transparency Benchmark Finds $26.8B in Wasted Programmatic Spend." August 14, 2025. https://www.ana.net/content/show/id/pr-2025-08-programmatictrans
4. PPC Land. "71% of ad agencies say manual work is putting campaigns at risk." 2026. https://ppc.land/71-of-ad-agencies-say-manual-work-is-putting-campaigns-at-risk/ (source: Fluency survey).
5. PPC Land. "DoubleVerify study reveals marketers spend 10 hours weekly on manual tasks." 2025. https://ppc.land/doubleverify-study-reveals-marketers-spend-10-hours-weekly-on-manual-tasks/
6. DashThis. "PPC Reporting Guide: Key Metrics + Templates." https://dashthis.com/blog/ppc-reporting/
7. Google Ads Help. "Get impression share data." https://support.google.com/google-ads/answer/7103314 (Defines Search Lost IS (budget) and Search Lost IS (rank), the basis for F3's classification logic.)
8. Google Ads Help. "About recommendations." https://support.google.com/google-ads/answer/3448398 (Describes how the Recommendations tab surfaces suggestions without a cited causal explanation; supports the contrast in F6 and the domain-gap argument.)
9. Google Ads Help. "Use auction insights to compare performance." https://support.google.com/google-ads/answer/2579754
