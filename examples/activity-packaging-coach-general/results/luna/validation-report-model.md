# Validation report

Run mode: batch/evaluation. All fixture values are fictional and confirmed by the supplied context. No external connector, email, purchase order, ERP write, or supplier contact was used.

## Verdict summary

| Gate | Status | Evidence |
|---|---|---|
| L0 contract | PASS | `CONTRACT.md` names the five canonical artifacts, exact columns, three single writers, exact payload chain, threshold, and every declared halt. |
| L1 structure | PASS | Required README, plan, AGENTS, CONTRACT, report, deck, `skills/{depth,breadth,coil}` tree (coil intentionally empty), and `data/{input,output,reference}` tree exist; exactly one `agent-plan.md` exists. |
| L2 context preservation | PASS | Three supplied task skills are packaged; all WFDATA owners, rules, exceptions, and gates are represented in `agent-plan.md`, packaged skills, and `AGENTS.md`. |
| L3 consistency | PASS | Start is `quote-intake-normalizer`; all three tasks are reachable; no cycle/orphan; each `next` target exists; adjacent payload names match; final `human` stop is explicit. |
| L4 end to end | PASS | Five rows are retained. Q-001–Q-003 complete ordinary flow; Q-004 failed parse and Q-005 missing policy match remain `review`; brief stops at buyer confirmation. |
| 27-screen visual QA | 미실행 (blocker) | Chromium emitted and visually inspected 27 bitmap captures at the requested pixel sizes, but its headless CSS viewport bottoms out around 480–500px; a truthful 375px CSS-emulation pass was unavailable. The package does not claim this gate as PASS. |

## L0–L3 checks

- Canonical tables: `incoming-quotes.csv`, `sourcing-policy.csv`, `normalized-quotes.csv`, `comparison-table.csv`, and `sourcing-review-brief.md` are spelled identically in the plan and contract.
- Writers are unique: `quote-intake-normalizer` writes only `normalized-quotes.csv`; `quote-variance-analyzer` writes only `comparison-table.csv`; `sourcing-review-brief` writes only the brief artifact.
- Threshold text is identical in the plan, contract, skill, and deck: price variance **above 12%** or lead-time variance **above 7 days**.
- Three packaged tasks form one linear chain ending at `human`; there is no coil task because no recurring retry loop was supplied.

## L4 ordinary scenario evidence

The output fixtures contain five quote IDs. Q-001, Q-002, and Q-003 match policy and have parsed prices. Q-002 has 10% price and 1-day lead variance, both below the strict “above” thresholds. The brief names all three as ordinary/pass rows.

## L4 adversarial scenario evidence

Q-004 has a missing `unit_price`; `normalized-quotes.csv` retains it with `parse_status=review`, `comparison-table.csv` records failed-parse evidence, and the brief leaves it unresolved. Q-005 uses item code `IT-404`, which has no policy row; it is retained with a missing-match review status and evidence. The agent stops before any buyer selection or purchase order.

## Human gates and remaining risk

1. Missing quote or policy files stop intake; the next action is to provide the complete bundle.
2. Buyer confirms Q-004 and Q-005 exceptions or supplies the missing evidence.
3. Buyer selects a supplier after review. No production or external write is approved.

The fixture intentionally contains no currency needing conversion, so no exchange rate was invented. A future run with another currency must provide a confirmed rate or remain `review`.

## Visual QA evidence and blocker

The deck is self-contained semantic HTML/CSS/JavaScript with no network requests. Local Chromium emitted 9 × 3 = 27 captures with exact bitmap dimensions and the captures were visually inspected. However, Chrome reported a CSS viewport of approximately 500px for a nominal 375px window, so those small captures cannot prove the required 375px responsive behavior. The true 375px browser gate is therefore `미실행`, not a pass. A follow-up operator should use a browser with CSS device emulation or an interactive browser surface and re-run all nine screens at 375×667; 768×720 and 1280×720 should be rechecked in the same session.
