# AdCopilot: Technical Feasibility, Baseline, and Proof of Concept

**Members:** Richa Pragat, Lakshita Rahoria, Shatakshi Chaudhri, Aaron Weng, Yongje Shu, Arthur Jawetz

This report tests two claims in the Sprint 2 MVP. First, that a deterministic split of a CPA change can name the driving cause, or refuse when the data will not support one. Second, that this split beats the rule a strategist can already run from the Google Ads campaign table. The working prototype is `adcopilot/`. Scope is unchanged from Sprint 2.

Results below use seed `20260911` and:

```bash
python -m adcopilot.evaluate --n 100 --sweeps
```

---

## 1. Technical and Data Feasibility

The diagnostic core runs on a laptop. It uses synthetic Search-style campaigns, no live Google Ads connection, no trained model, and no extra Python packages.

|                          | Current build                                                                                                                                                                                                             | Live Google Ads path                 |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| Data                     | Daily impressions, clicks, cost, conversions, Lost IS (budget), Lost IS (rank). CTR, CVR, CPC, CPM, and CPA are computed. The columns match a Search campaign report. The rows are generated, not pulled from an account. | Same columns from the Google Ads API |
| APIs                     | None                                                                                                                                                                                                                      | Google Ads API                       |
| Models                   | None. Diagnosis is arithmetic. An LLM, if added later, only narrates numbers the engine already produced.                                                                                                                 | Optional narration model             |
| Infrastructure and tools | Python 3.11, pytest, this repository                                                                                                                                                                                      | Same                                 |
| Hardware                 | Laptop. No GPU.                                                                                                                                                                                                           | Same for the diagnostic core         |
| Access                   | None required                                                                                                                                                                                                             | Same                                 |
| Dependencies             | Zero runtime packages                                                                                                                                                                                                     | Google Ads client library            |

Two Google constraints change what we can promise later, even though this build does not call the API.

1. Auction Insights (competitor context) appears in the UI and in the API docs, but Google marks those fields "not publicly available." The Sprint 2 Could-Have for competitor context is therefore not buildable. [11] [13]
2. Search Lost IS (budget) is campaign-level only, and impression-share columns arrive 1-2 days late. Budget vs rank cannot be split by ad group, and those fields cannot support a same-day diagnosis. [12]

Live API access remains Won't-Have. Auction Insights moves from Could-Have to Won't-Have.

Three technical risks showed up in the prototype. A click-rate collapse and a costlier auction both present as CPC up in the UI, which is the case the product exists to separate. A 70/40 refuse rule still names a cause on about 70% of campaigns. At very low volume, a 20% CPA alarm fires on noise.

---

## 2. Baseline and Prototype

CPA is the cost of one conversion. When it jumps, Google Ads puts two headline numbers in front of the strategist: cost per click (CPC) and conversion rate (CVR). A more expensive auction raises CPC. A drop in click-through rate also raises CPC. The fixes go in opposite directions.

AdCopilot splits the CPA change with an identity that already holds in the data:

```
CPA = CPM / (1000 × CTR × CVR)
```

The three terms are price (CPM), clicks (CTR), and conversions (CVR). When one term is clearly largest, the engine names it and quotes the numbers. When two terms are close, it reports that the cause is unknown.

The baseline is that dashboard rule: whichever of CPC and CVR moved more, with a CPC rise read as a cost problem. It cannot tell a CPM rise from a CTR collapse. Both look like CPC up. The product claim is that the three-way split can.

The comparison used 700 synthetic campaigns with planted causes and noisy click and conversion counts. One hundred campaigns in each of seven buckets: price doubled, click rate halved, conversion rate halved, budget cap, rank cap, two causes at once (refuse), and noise only (do not flag). Fourteen quiet days, then seven shocked days. Budget and rank shocks leave conversion rate alone, so the delivery path is not picking up a conversion drop.

Both methods use the same alarm: CPA up more than 20%. They differ on the cause.

|                     | When it names a cause, how often is it right? | How often does it name a cause? |
| ------------------- | --------------------------------------------- | ------------------------------- |
| Dashboard rule (B1) | 34%                                           | 85%                             |
| AdCopilot (B2)      | 96%                                           | 70%                             |

On the 100 campaigns where click rate collapsed, the dashboard rule called every one a cost problem. AdCopilot named CTR on 95 of them. Price-up and conversion-drop are already visible in CPC vs CVR. Click-rate collapse is the case that needs the extra split.

The engine stayed quiet on 94% of mixed cases (Sprint 2 targeted 100%). Sprint 2 also targeted 85% accuracy across the whole set. Those two targets conflict. Two hundred of the 700 campaigns should not receive a named cause, so a perfect run still only reaches 71% if silence counts as a miss. Of the 500 campaigns with a single planted cause, the engine recovered 94%.

Two ablations sit between B1 and B2: blaming the metric with the largest relative change, and running the three-way split with the refuse rule off. With refusal off, the split is right 80% of the times it speaks. With refusal on, 96%. Loosening 70/40 to 55/15 answers a little more often and only refuses 57% of mixed cases. The shipped gate stays 70/40.

At about 300 impressions a day, a 20% CPA rule produces 38% false alarms. Around 6,000 a day the series is still noisy. At 15,000 it settles. Below roughly 6,000 impressions/day the prototype should refuse and say the window is too thin.

Worked example, `ctr_drop` campaign 1. CPA went from $6.68 to $13.28. Google Ads shows CPC from $0.26 to $0.58, so B1 says cost. Price only moved from $11.93 to $12.70. Click rate halved, 4.5% to 2.2%. Raising bids here spends more against the same weak ads.

```bash
python -m adcopilot.cli --scenario ctr_drop --campaign-id 1
python -m adcopilot.cli --scenario ambiguous
python -m pytest -v
```

---

## 3. Findings and Decision

Click-rate collapse is the case that justified the tool, and the evaluation recovered it. API access, GPUs, and paid datasets do not block the rest of the semester.

The Sprint 2 success pair (85% overall accuracy and 100% refusal) cannot be one score once refusals exist. Auction Insights is not available through the API. Tiny accounts will look broken if a 20% CPA flag always fires.

**Decision: Proceed with Modification.**

1. Report three rates: how often we answer (aim 60% or more), how often those answers are right (aim 95% or more), how often we refuse mixed cases (aim 90% or more). Keep 70/40.
2. Below about 6,000 impressions/day, refuse and say the window is too thin.
3. Move Auction Insights from Could-Have to Won't-Have.
4. Sprint 4: the UI (F8), and a check that every number in LLM text already sits in the diagnosis object.

Must-haves F1 to F6 and F8 stay. Cause-matched next step (F7) stays Should-Have.

All figures come from the generator. Live accounts will score lower. Calling a dominant CTR term "fix the ads" is a label we assigned; nobody in this study confirmed it. Detection is one-sided (CPA up). This sprint has no UI.

---

## References

Sprint 2 references [1] to [9] still apply.

**[10]** Google Ads API, access levels: test tokens stay on test accounts; Explorer 2,880/day on production; Basic 15,000/day; Standard unlimited after review. [https://developers.google.com/google-ads/api/docs/api-policy/access-levels](https://developers.google.com/google-ads/api/docs/api-policy/access-levels)

**[11]** Google Ads API Forum, 3 Nov 2025: Auction Insights is not public in the API for any campaign type; whitelist closed. [https://groups.google.com/g/adwords-api/c/xhwhOAA5854](https://groups.google.com/g/adwords-api/c/xhwhOAA5854)

**[12]** Google Ads Help, impression share: Lost IS (budget) is campaign-level; those columns update in 1-2 days. [https://support.google.com/google-ads/answer/7103314](https://support.google.com/google-ads/answer/7103314)

**[13]** Google Ads API Metrics: `auction_insight_search_` marked "not publicly available." [https://developers.google.com/google-ads/api/reference/rpc/v23/Metrics](https://developers.google.com/google-ads/api/reference/rpc/v23/Metrics)
