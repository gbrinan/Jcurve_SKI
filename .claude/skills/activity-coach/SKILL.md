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

## Visuals — three kinds, three jobs

Do not reach for the heaviest one by default. Each answers a different question.

| Kind | Answers | Made by | When |
|---|---|---|---|
| **mermaid** in `agent-plan.md` §8/§9 | "What is the shape?" | `adapt_workflow.py`, automatically | Always. Costs nothing. |
| **`agent-mockup.html`** | "What does it do?" | `check/make_mockup.py <pack>` | After `run.py` exists and has been run |
| **`agent-plan-deck.html`** | "How do we present it?" | `slide-pack` skill | Only when a team is presenting |

### Execution mockup — two ways to get one

Every mockup is built from `out/trace.json`. There are two ways to produce that file,
and the page states which one it was.

**A. Contract walk — works on any pack, no code to write**

```bash
python3 check/orchestrate.py <pack>                        # walks every branch
python3 check/orchestrate.py <pack> --take 계정검증대사=차이분석조정
python3 check/make_mockup.py <pack>
```

It reads `CONTRACT.md`'s `chain`/`halt_at` and each skill's `next`/`when`/`loop_to`/
`loop_exit`, walks the flow, and records what each step is *supposed* to do (the first
line of its 판단기준). **It does not evaluate anything.** The judgment rules are Korean
prose; whether "차이가 1건이라도 있으면" holds is not something it can decide. So it
reads no data, produces no counts, and at a fork walks **both** branches instead of
choosing. The trace is marked `mode: contract` and the page opens with a banner saying
exactly this.

**B. Real run — the pack has a `run.py`**

```bash
python3 run.py                          # records through check/trace.py, mode: run
python3 check/make_mockup.py <pack>
```

Now the counts are real, because something actually processed the data.

Use A to show a team the shape of what they designed. Use B when the numbers matter.
Never present A as if it were B — that is what the banner is for.

**Every number on that screen comes from `out/trace.json`.** Never hand-edit the HTML —
change the data, re-run, regenerate. A mockup typed from a log drifts the moment the
data changes, silently.

`run.py` records what happened with `check/trace.py`:

```python
from trace import Trace
TR = Trace("의료비 판독 AI", source="Talent AX실 · HR AI", lv5="...")
TR.input("청구접수대장", 11, "2026년 7~8월 접수분")
TR.step("1. 증빙서류판독", "자동", "11건 판독. **1건은 판독불가**입니다.")
TR.warn("금액을 추정하지 않았습니다.")
TR.fork("3. 지급기준대조", "증강",
        [("기준 충족", "자동지급상신", 6), ("증빙 미비", "보완요청작성", 1)],
        note="세 갈래로 갈랐습니다.", taken="자동지급상신")
TR.table("지급대장", rows, cols, mark=lambda r: "diff" if ... else None)
TR.loop("차이분석조정", "계정검증대사", exit_cond="차이가 0이 되면")
TR.halt("7. 지급승인", "사람고유", "여기서 멈췄습니다.", actions=["6건 승인"])
TR.done("경로 A 6건 · B 1건 · C 4건").save(OUT)
```

Colors come from `DESIGN.md` — the mockup never carries its own palette.
Buttons on a halt step are rendered disabled on purpose: the pack has no execution code.

### What the page contains

One page, two halves. The summary comes first because an audience needs to know what
this is before watching it run.

| # | Section | Built from |
|---|---|---|
| — | Hero: agent name, one-liner, **Lv4 › Lv5 › Lv6 path**, four stats | `agent-plan.md` §1–2, skill count |
| ① | **구조 — Lv4 › Lv5 › Lv6** — the Lv4 band, the Lv5 box (what this agent packages), and a card per Lv6 skill with owner and Human 여부 | SKILL.md frontmatter |
| ② | **실행 흐름 설계도** — swimlanes by Human 여부, forward arrows, dashed loopback with its exit condition, the ◆ condition spelled out | `next` / `when` / `loop_to` / `loop_exit` |
| ③ | **원본 대조** — which design-camp item became which file | `source_id` + `agent-plan.md` §8 |
| ④ | **Lv6 스킬 카드** — inputs → outputs, reads/writes, the judgment rule | SKILL.md frontmatter |
| ⑤ | **폴더 트리** | the pack's actual layout |
| ⑥ | **실행** — the playback below | `out/trace.json` |

Lanes and card borders are colored by **Human 여부** (자동 / 증강 / 사람고유), because that
is what our packs actually carry at this stage. Do not color by environment tags
(MCP·조회 and friends) — those live in the wireframe stage and are not in the pack. A
diagram painted with information we do not have is a diagram that lies.

### The mockup plays back

The generated page is not a static screenshot. It runs:

| Control | What it does |
|---|---|
| **▶ 실행** | Reveals steps one at a time from ● 시작 |
| Per step | Shows `처리 중…` with a spinner first, then the result and a duration badge |
| **Rail** | Pinned at the top; the current node pulses, passed nodes light up, unreached stay dim |
| **Progress bar** | Fixed at the bottom, 0 → 100%, with an elapsed clock |
| **다음 단계 ›** | One step at a time |
| **1× / 2× / 4×** | Playback speed |
| Rail click | Jumps to that step — for demoing one part |
| **전체 보기** | Skips playback, shows everything |
| Keyboard | Space = play/pause, → = next, R = restart |

**A human-only step stops playback.** The bar turns orange, the card shows
`⏸ 사람 확인 대기`, and nothing advances until someone presses **확인하고 계속 ▶**.
That is the point of the whole screen — the agent does not pass a human gate by itself,
and the mockup should not either.

Two honesty rules the generator keeps:
- The elapsed clock is labeled **시뮬레이션 값** in the dock. The real run takes under a
  second; the timing exists to make the steps readable, not to claim a measurement.
- With JavaScript off, every step is simply visible. The page degrades to the static
  version rather than showing a blank log.

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

## Tracing back to the source hierarchy

The design-camp documents number everything — `P-A2-1` for the process, `T-A2-1-1` for
each task, `A-A2-1-5-3` for an activity. Those ids used to die at the workflow design,
the same way forks and loopbacks did. Carry them:

```
// in the design HTML
let srcLv3="별도/연결 결산관리";
let srcLv4="P-A2-1 분기/반기 결산";
let lv6=[{src:"T-A2-1-1", n:"결산일정수립", h:"증강", ...}]
```

The adapter writes `source_id:` into each skill and a comparison table into
`agent-plan.md` §8. The mockup renders it as section ③:

| 원본 계층 | 원본 항목 | 우리 계층 | 이 팩의 무엇이 되었나 |
|---|---|---|---|
| Lv3 업무 | 별도/연결 결산관리 | **Lv4** | 문서에만 — 팩 범위 밖 |
| Lv4 프로세스 | `P-A2-1` 분기/반기 결산 | **Lv5** | **이 팩 = 에이전트 1개** |
| Lv5 Task | `T-A2-1-1` 결산일정수립 | **Lv6** | `skills/depth/결산일정수립/SKILL.md` |
| Lv6 Activity | 원본 문서 참조 | 판단기준 | 각 SKILL.md 본문 |

It closes with a coverage line — `원본 ID가 남은 것 6/6`. A pack with no source document
shows `0/N` and says so rather than leaving the reader to guess.

## Skill frontmatter fields

```yaml
name: 계정검증대사
owner: 결산담당
quadrant: depth              # depth | breadth | coil
human: 증강                   # 자동 | 증강 | 사람고유
skillability: 중간            # 높음 | 중간 | 낮음
source_id: T-A2-1-5          # the design-camp id this skill came from
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
