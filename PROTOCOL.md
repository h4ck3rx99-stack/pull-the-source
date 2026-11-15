# PULL THE SOURCE — Protocol (frozen before evaluation runs)

Apart Research AI × Epistemics Sprint, 15 Nov 2026. Focused pilot. Synthetic data.

## Question
When a source supporting an AI's recommendation is withdrawn, does the model revise its recommendation exactly when the remaining valid evidence no longer supports it — and does asking it to keep an explicit dependency table change this?

## Task
Fictional consumer-purchase scenarios. Each has a buyer, a product, three explicit requirements (R1–R3), and six short numbered sources (S1–S6). The model judges whether the recommendation "<buyer> should buy <product>" is justified **solely by currently valid supplied sources**, with one label: `Supported`, `Contradicted`, `Insufficient evidence`. Withdrawal makes a source unusable; it does not prove the opposite. Full rules: `RULES` in `pts.py` (identical in both conditions).

## Dataset (synthetic, authored for this sprint; all brands fictional)
- 3 practice scenarios (P01–P03), 12 evaluation scenarios (E01–E12). Generator: `build_dataset.py` (fixed seed).
- Hidden source roles per evaluation scenario: one sole support for requirement *a* (essential); two independent supports for *b* (redundant pair); one sole support for *c*; one irrelevant source; one near-miss lure (another model, or a vague claim, on the topic of *a*).
- Requirement order and source order are shuffled, so ID/position does not reveal role. Branch letters X/Y/Z are also shuffled.
- Public files `data/*.json` contain no roles or labels. Answer keys are in `keys/*.json` and are read only by the scorer. During collection the keys and generator were moved out of the project folder.

## Answer key rule (single, mechanical)
Given the set of valid sources: if any valid source contradicts a requirement → `Contradicted`; else if every requirement has ≥1 valid supporting source → `Supported`; else `Insufficient evidence`. All 12 evaluation scenarios are initially `Supported`.

## Branches (each starts from the same recorded initial exchange; never sequential)
1. **Essential**: the sole support of a requirement is withdrawn → gold `Insufficient evidence`.
2. **Irrelevant**: the irrelevant source is withdrawn → gold `Supported`.
3. **Redundant**: one of two independent supports is withdrawn → gold `Supported`.

Control against always abstaining: 24 of 36 post-update golds and 12 of 12 initial golds are `Supported`; an always-`Insufficient evidence` policy scores 0/12 initial and 12/36 post-update. An always-`Supported` policy scores 24/36 post-update.

## Conditions
- **A (ordinary)**: rules + evidence + output format.
- **B (dependency table)**: identical rules and evidence; additionally asked to write a table (Requirement | Source IDs it depends on | Are those sources currently valid?) before deciding, and to update it after a withdrawal.
- Both end with `RELIES_ON:` and `DECISION:` lines. B is not told the decision policy beyond the shared rules. Note: asking A for `RELIES_ON` makes A a slightly stronger baseline (conservative for any B effect).

## Procedure
1. Initial call per scenario × condition (24 calls).
2. Three branch calls per scenario × condition (72 calls). Each branch prompt replays the initial prompt and the model's own recorded initial reply as a transcript, then the withdrawal notice.
3. Each call is a fresh model context that reads one prompt file and writes one response file.
Model: Claude Haiku via sub-agent calls (alias `haiku`; exact model ID not exposed), harness default settings, temperature not controllable, one sample per cell.

## Scoring (deterministic, `pts.py score`)
Decision = last `DECISION:` line, matched to the three labels. Missing or unparseable = incorrect and listed. No model judge.
Reported with counts and denominators, per condition, on all cases and on initially-correct cases:
initial accuracy; essential branch: correct and "retained Supported"; irrelevant branch: unnecessary withdrawal; redundant branch: correct retention; overall post-update accuracy; scenarios with all three branches correct.
Branches of one scenario are related, so the comparison unit is the scenario: paired A-vs-B table of "all three branches correct" with an exact two-sided sign test. n = 12; this pilot is not powered for small effects.
Exploratory only: whether initial `RELIES_ON` equals the key's support set, includes the lure, and whether decisions change when a withdrawn source was or was not in the stated set. This says nothing certain about internal reasoning.

## Changes made before freezing (from the practice round, disclosed)
Practice round v0 (kept in `runs/practice_v0_superseded/`): the model answered `Insufficient evidence` on P01 because rule 2 said "explicitly establishes" and one practice source required a small inference (base diameter vs cup holder). Rule 2 was reworded for **both** conditions to allow a stated measurement meeting a threshold by simple comparison, and that practice source was rewritten. No evaluation scenario had been run at that point.

## Fixed in advance
No evaluation prompt, key or scoring rule is changed after `FREEZE.json` is written. Failed, missing or deviating calls are logged, not replaced. Any rerun is stored separately and reported.
