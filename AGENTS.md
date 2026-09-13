# Agent instructions

This repository is **Team AdDiagnose**'s private workspace for **AdCopilot** in CMU III 49797 (Special Topics: Advanced AI for Industry and Society, Fall 2026).

## Read this context before implementing

Load these in order. Prefer the markdown copies; PDFs are the submitted originals.

1. [README.md](README.md): orientation, team, current MVP summary.
2. [docs/sprint-1-adcopilot-proposal.md](docs/sprint-1-adcopilot-proposal.md): Richa Pragat's Sprint 1 proposal. Problem, landscape, metric identities, original solution shape, value proposition.
3. [docs/sprint-2-team-deliverable.md](docs/sprint-2-team-deliverable.md): team Sprint 2 deliverable. Authoritative for users, use cases, functional requirements, MoSCoW, MVP contract, success bar.
4. [docs/sprint-3-feasibility.md](docs/sprint-3-feasibility.md): Sprint 3 feasibility + baseline POC. Risks, Proceed decision, seeded evaluation results. Working code: `adcopilot/` package.

If Sprint 1 and Sprint 2 disagree on **scope**, follow Sprint 2. Use Sprint 1 for rationale, examples, and the metric identities (`CPA = CPC ÷ CVR`, `CPC = (CPM ÷ 1000) ÷ CTR`) when Sprint 2 is silent. Use Sprint 3 for diagnostic thresholds, log-share method, and baseline accuracy evidence; it does not expand product scope past Sprint 2.

Original PDFs:

- [docs/AdvancedAI_AdCopilotProposal_RichaPragat.pdf](docs/AdvancedAI_AdCopilotProposal_RichaPragat.pdf)
- [docs/Sprint2Deliverable_TeamAdDiagnose.pdf](docs/Sprint2Deliverable_TeamAdDiagnose.pdf)

## Non-negotiable product rules

- Synthetic campaign data only. No live Google Ads (or other ad-platform) API. No real account data. No PII.
- Deterministic core computes the diagnosis. An LLM may narrate structured output only. Do not let the model invent a cause.
- Identical input must produce identical diagnostic output.
- Every claim in an explanation must cite named metrics and values.
- Do not auto-execute bid, budget, or campaign changes.
- Hold the Won't Have line unless the team explicitly expands scope: live platform integration, ML forecasting, automated fixes.

## What "done" means this semester

A user loads a campaign. The system flags an abnormal CPA movement, identifies the driving cause or refuses when ambiguous, and shows a plain-language, numbers-cited diagnosis in a usable interface, across all seeded scenarios (including the refusal case).

Success bar from Sprint 2: ≥ 85% diagnosis accuracy on seeded scenarios; 100% refusal correctness on seeded ambiguous cases.
