---
name: activity-coach
version: "1.0.0"
description: "Package a team's individual Lv6 task skills into one Lv5 team agent, then verify the result. Use when someone says '스킬들을 하나로 묶어줘', '팀 에이전트로 만들어줘', '통합 점검해줘', '패키징하자', or hands over wireframe outputs, workflow designs, or a folder of skill.md files to be combined."
argument-hint: 'activity-coach ./my-team-pack | activity-coach 이 설계도로 팩 만들어줘'
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
---

# Activity Coach — package Lv6 skills into one Lv5 team agent

Take the skills individual members built for their own Lv6 tasks, wire them into a
single Lv5 workflow, and prove the wiring holds. The deliverable is a **pack**: a
folder that names what the agent does, what it refuses to do, and where a human stops it.

## Where the scripts are

Look for `check/run_check.py` in this order and use the first that exists:

1. `<this skill's folder>/check/` — installed copy
2. `./check/` — working inside the toolkit repo itself

All scripts are Python 3 standard library only. No `pip install`, no network.

## The three verdicts

Never reject a team's work. Classify it and name it accurately.

| Flow | Verdict | ATF gate |
|---|---|---|
| Fewer than 3 AI tasks (자동 + 증강) | `팀 스킬팩 (AI 태스크 N개 — ③다단계성 미충족)` | ③ not met |
| Same order every time | `팀 스킬팩 (순차 실행)` | ④ not met |
| Has a fork | `팀 에이전트 (갈림길 있음)` | ③④ met |
| Has a loopback | `팀 에이전트 (루프백 있음)` | ③④ met |

A straight line is a legitimate outcome. The skills a team built are the agent's parts
either way — a fork appearing later turns the same pack into an agent with no rework.

## Procedure

### 1. Find out what stage the input is at

| Input | Adapter |
|---|---|
| Workflow design HTML (Lv4-Lv5-Lv6, `let lv6=[...]`) | `check/adapt_workflow.py <html> <out>` |
| Wireframe coach output (WFDATA) + ATF report | `check/adapt_upstream.py <wf-dir> <atf.html> <out> [flow-table.md]` |
| A folder that already has `skills/*/*/SKILL.md` | skip adapting, go to step 2 |

Wireframe output carries no links between skills — each member drew only their own Lv6.
Pass a **team flow table** as the fourth argument to supply them. Without it `chain`
stays `(미정)`; never invent the order.

```
SkillA -> SkillB              sequence
SkillA -> SkillB | SkillC     fork
SkillA ? <condition>          fork condition (copy the ◆ line from the source flow)
SkillA ↩ SkillB (탈출: cond)  loopback
```

### 2. Read the pack before changing it

```bash
python3 check/readchk.py <pack>
```

This writes `DECISIONS.md`: a restatement of how the pack reads, and the single
heaviest unresolved question. Answer that one before touching anything else.

**It will not overwrite a DECISIONS.md that already contains `결정됨`** — a decision a
person made outlives a re-run. It writes `DECISIONS.new.md` instead.

### 3. Check the contract, then the pack

```bash
python3 check/check_contract.py <pack> --run-check
python3 check/run_check.py <pack>
```

Layers: L1 structure → L2 context → L3 conflicts and flow → L4 end-to-end.

Three states, not two: ✅ pass, ❌ fail, **⚠️ accepted risk** — a missing review step
passes as ⚠️ only when the team recorded that decision in `DECISIONS.md` and named the
risk in the plan. Missing something unknowingly and accepting something knowingly are
different, and neither disappears.

### 4. Finish what the machine cannot

`run_check.py` prints two items it leaves to a person. Both must actually be done:

- **Run the scenario for real** — end to end, on real or realistic data.
- **Inject an error** — delete a stop instruction, point two skills at the same table,
  break a threshold. Confirm the checker fails. If it still passes, the gate is fake.

## Required files in a pack

| File | Missing means |
|---|---|
| `agent-plan.md` | L1 fails. This is the SSOT — exactly one copy in the tree. |
| `AGENTS.md` | L1 fails. Role, what it does, what it refuses. |
| `README.md` | L1 fails. |
| `CONTRACT.md` | Contract gate blocks before the checker runs. |
| `skills/<quadrant>/<name>/SKILL.md` | Nothing to check. |
| `data/` | L1 fails. |
| `DECISIONS.md` | Optional — but required to accept a risk as ⚠️. |

## Skill frontmatter fields

```yaml
name: 계정검증대사
owner: 결산담당
quadrant: depth              # depth | breadth | coil
human: 증강                   # 자동 | 증강 | 사람고유
skillability: 중간            # 높음 | 중간 | 낮음
inputs: [주석초안작성결과]
outputs: [계정검증대사결과]
reads: [외부확인서.md]
writes: [대사결과.md]
next: 차이분석조정 | 결산마감   # "|" makes this a fork
when: 차이 발견? Yes -> 차이분석조정; No -> 결산마감
loop_to: 계정검증대사          # backward edge — never put it in `next`
loop_exit: 차이가 0이 되면      # without this the loop is infinite → ❌
```

`when` missing on a fork is ⚠️, not ❌ — copy the ◆ line from the source flow.
`loop_exit` missing is ❌.

## Rules that hold everywhere

- **Do not invent.** No table name, no threshold, no reason. Write `(미정)` and say so.
- **One writer per table.** Two skills writing the same table is a hard fail.
- **Every endpoint stops.** A branch that ends without a human looking at it is an
  unsupervised exit — the adapter writes a stop instruction into every terminal.
- **Mid-chain human stops must be in `halt_at`.** L4 only inspects endpoints; a human
  decision in the middle is invisible to it unless the contract names it.
- **Thresholds live in the contract.** When a pack has more than one `±N%` rule, list
  them all on the `threshold:` line — that line becomes the source of truth.

## Worked examples

`examples/sample/` holds packs that pass, one per shape:

| Pack | Shape |
|---|---|
| `team-agent`, `ax-share-agent` | straight line → skill pack |
| `report-wording-pack` | ⚠️ accepted risk (no review step, recorded) |
| `medical-expense-agent` | 3-way fork, runnable, execution mockup |
| `quarterly-close-agent` | fork + loopback, runnable, from real workshop documents |
| `hr-appraisal-agent`, `monthly-close-agent`, `kaizen-review-agent` | fork + loopback |
