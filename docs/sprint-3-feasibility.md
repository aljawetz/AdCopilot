# AdCopilot — Sprint 3 Team Deliverable

**Technical Feasibility and Baseline**  
**Team:** AdDiagnose  
**Members:** Richa Pragat, Lakshita Rahoria, Shatakshi Chaudhri, Aaron Weng, Yongje Shu, Arthur Jawetz  
**Course:** III 49797, Advanced AI for Industry and Society, Fall 2026  
**Due:** Tuesday, September 15, 2026 (Canvas)

This document is the Sprint 3 feasibility report. The working baseline lives in the project repository (`adcopilot/` package, `tests/`, CLI). Scope remains governed by the Sprint 2 MVP contract; this sprint only proves the highest-risk technical assumption.

---

## 1. Technical and Data Feasibility

### Highest-risk assumptions

| Risk | Why it matters | Mitigation tested this sprint |
| --- | --- | --- |
| Synthetic data may not support real diagnostic logic | Without live Google Ads access, the engine must still isolate causes on representative fields | Seeded shocks use impressions, clicks, cost, conversions, Search Lost IS (budget), and Search Lost IS (rank) |
| Decomposition may not isolate a known driver | The product promise is cause, not just “CPA moved” | Log-share attribution of `Δln(CPA)` across CPM, CTR, and CVR; nested CPC vs CVR shares |
| Ambiguous cases may force a false single cause | False certainty is worse than a refusal for paid media | Confidence rule: High only if leading share ≥ 70% and margin over next ≥ 40 points; else refuse |
| Sparse conversions / zero denominators | CPA and CVR break when clicks or conversions are zero | Safe division; baseline requires conversions; generator keeps positive volumes |
| Threshold sensitivity | A brittle +20% CPA rule could over/under-flag | Documented constants; stable scenario stays unflagged; shocks clear the bar |
| LLM narration drift | Model inventing a cause breaks trust | Deferred. Sprint 3 uses template explanations filled only from structured fields |

### Data, APIs, models, infrastructure

- **Data:** synthetic only. Daily Google Ads-shaped columns; no PII; no real accounts.
- **APIs:** none this semester for ads. No Google Ads API, no partner credentials.
- **Models:** no trained ML. Diagnosis is deterministic arithmetic and rules. An optional LLM for narration remains Sprint 4+ and must not invent causes.
- **Infrastructure:** local Python ≥ 3.11, pytest. No cloud GPU, no paid inference for the baseline.
- **Dependencies:** zero runtime dependencies. Dev: pytest only.
- **Access restrictions:** none for synthetic data. Live platform access remains Won't Have.

### Metric identities (locked)

- `CTR = clicks / impressions`
- `CVR = conversions / clicks`
- `CPC = cost / clicks`
- `CPM = (cost / impressions) × 1000`
- `CPA = cost / conversions = CPC / CVR`
- `CPC = (CPM / 1000) / CTR`
- Log form used for shares: `Δln(CPA) = Δln(CPM) − Δln(CTR) − Δln(CVR)`

Windows: trailing baseline = prior 14 days; current = last 7 days. Anomaly if current CPA exceeds baseline mean by more than 20%. Visibility path: if impressions fall ≥ 15% and Lost IS rises, classify budget-capped vs rank-capped when one Lost IS delta dominates.

---

## 2. Baseline and Feasibility Prototype

### What we built

A reproducible Python package that (1) generates labeled synthetic campaigns, (2) detects abnormal CPA movement, (3) decomposes the change or classifies visibility loss, (4) assigns High confidence or refuses, and (5) emits a numbers-cited template explanation via CLI.

```text
python -m adcopilot.cli --scenario cvr_drop
python -m adcopilot.cli --scenario ambiguous
python -m pytest
```

### Seeded evaluation (ground truth)

| Scenario | Injected shock | Expected | Result |
| --- | --- | --- | --- |
| `cpm_spike` | CPM ×2, CTR/CVR fixed | High, CPM | Pass |
| `cvr_drop` | CVR ×0.5, costs fixed | High, CVR | Pass |
| `budget_capped` | Impressions down, Lost IS (budget) up | High, budget | Pass |
| `rank_capped` | Impressions down, Lost IS (rank) up | High, rank | Pass |
| `ambiguous` | CPM and CVR both move | Refuse (low) | Pass |
| `stable` | No shock | No anomaly | Pass |

**Baseline score:** 5/5 labeled shocks diagnosed or refused correctly; stable not flagged. Refusal correctness on the ambiguous seed: 100%. Identical input yields identical JSON (`tests/test_identical_input_identical_json`).

### Sample diagnosis (CVR drop)

> CPA rose +100.0% ($6.00 → $12.00). CVR drove the change (4.00% → 2.00%; share 100%). CPC held near $0.24 → $0.24. Diagnosis: conversion-quality issue. Confidence: High. Next: Check landing page, offer, and conversion tracking before changing bids.

### Sample refusal (ambiguous)

> CPA rose +101.4% ($6.00 → $12.08). No single driver dominates (CPM 53%, CVR 47%). Confidence: Low. Refusal: do not name one root cause.

### Limitations of this baseline

- No UI (F8), no LLM narration (F6 polish), no multi-campaign scan.
- Visibility shocks also move CVR so CPA rises; the engine prioritizes Lost IS when impressions drop, which matches Google Ads’ budget vs rank framing but is a design choice to revisit in Sprint 4.
- Thresholds (20% CPA, 70%/40% confidence, 15% impression drop) are fixed constants, not learned.
- Synthetic series use a stable-then-shock shape with light hash-seeded day-to-day jitter (±4–5% on rates); not a full noisy PPC simulator.

These limits do not block Proceed: the critical assumption held on the evaluation set.

---

## 3. Findings and Project Decision

### Decision: **Proceed**

Evidence from the POC supports continuing AdCopilot as scoped in Sprint 2.

| Question | Finding |
| --- | --- |
| Can we diagnose without live APIs? | Yes, with Google Ads-shaped synthetic fields and seeded ground truth |
| Can deterministic math isolate CPM vs CVR vs visibility? | Yes on single-cause seeds |
| Can we refuse when mixed? | Yes; ambiguous seed returns low confidence and no single cause |
| Do we need ML or paid infra this semester? | No for the diagnostic core |

### Scope impact

- **Unchanged Must Have:** F1–F6, F8 (UI remains later).
- **Should Have:** F7 remains cause-matched next steps (template lookup already sketches this; not auto-executed).
- **Won't Have holds:** live Google Ads API, real account data, ML forecasting, automated fix execution.
- **Modify (minor, technical only):** lock the Sprint 3 thresholds and log-share method as the Semester 1 diagnostic baseline unless evaluation later shows systematic misses on richer synthetic noise.

### Next sprint implication (Sprint 4)

Architecture and implementation plan should treat this package as the diagnostic core, then add: richer synthetic noise, optional LLM narration constrained to structured JSON, and the F8 interface (trend chart, anomaly list, diagnosis panel).

---

## Appendix: How to reproduce

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
python -m adcopilot.cli --scenario cpm_spike --json
```

Repository paths: `adcopilot/metrics.py`, `adcopilot/generate.py`, `adcopilot/engine.py`, `adcopilot/explain.py`, `adcopilot/cli.py`, `tests/test_engine.py`.
