#!/usr/bin/env python3
"""readchk — 팩을 어떻게 읽었는지 먼저 적고, 미결 갈래를 하나만 앞세운다.

사용: python3 check/readchk.py <팩 경로>   → DECISIONS.md 를 쓰고 요약을 출력

paperthin `depth/readchk`의 규칙을 도구에 옮긴 것:
  · 되풀이가 아니라 **재진술** — 필드를 그대로 나열하지 않고 읽은 결과를 문장으로 적는다
  · **맥락이 답하면 조용히** — 파일이 이미 말해주는 것은 묻지 않는다
  · **한 번에 한 갈래** — 미결이 여럿이면 가장 무거운 하나만 앞세운다
  · 범위를 바꾸는 모호함을 **조용히 기본값으로 때우지 않는다** — 기록해서 보이게 둔다
  · 복잡한 작업 전에 **커밋을 남긴다** — DECISIONS.md가 그 기록이다

핵심은 막지 않는 것이다. 미결이 있어도 팩은 그대로 돌아가고, 결정만 눈에 보이게 남는다.
"""
import re
import sys
from pathlib import Path

# 갈래의 무게 — 숫자가 작을수록 먼저 정해야 한다
STAKES = {
    "검수없음": (1, "사람 확인 없이 결과가 나간다"),
    "기록자충돌": (2, "같은 표에 둘이 써서 데이터가 덮인다"),
    "임계값상충": (3, "같은 규칙이 문서마다 다른 값이다"),
    "중간정지누락": (4, "중간 사람 판단이 halt_at에 없다"),
    "데이터미정": (5, "표·칸 이름이 아직 없다"),
    "연동미정": (6, "다른 스킬과의 연결이 미정이다"),
}


def parse_skill(p):
    t = p.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", t, re.S)
    if not m:
        return None, t
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            meta[k.strip()] = ([x.strip() for x in v.strip("[]").split(",") if x.strip()]
                               if v.startswith("[") else (None if v == "null" else v))
    return meta, m.group(2)


def main(pack_dir):
    pack = Path(pack_dir)
    skills = {}
    for p in sorted(pack.glob("skills/*/*/[sS][kK][iI][lL][lL].md")):
        meta, body = parse_skill(p)
        if meta:
            skills[meta["name"]] = (meta, body)
    if not skills:
        print("🔴 스킬을 찾지 못했습니다 — 읽을 것이 없습니다")
        return 2

    plan = (pack / "agent-plan.md").read_text(encoding="utf-8") if (pack / "agent-plan.md").is_file() else ""
    contract = (pack / "CONTRACT.md").read_text(encoding="utf-8") if (pack / "CONTRACT.md").is_file() else ""

    # ── 재진술: 읽은 결과를 문장으로 ──
    nexts = {n: [x.strip() for x in re.split(r"[|,]", m["next"]) if x.strip()] if m.get("next") else []
             for n, (m, _) in skills.items()}
    targets = {t for vs in nexts.values() for t in vs}
    starts = [n for n in skills if n not in targets]
    terminals = [n for n in skills if not nexts.get(n)]
    humans = {n: (m.get("human") or "").strip() for n, (m, _) in skills.items()}
    ai = [n for n, h in humans.items() if h in ("자동", "증강")]
    human_only = [n for n, h in humans.items() if h == "사람고유"]
    lv4 = (re.search(r"Lv4: (.+)", plan) or [None, "(미정)"])[1].strip()
    lv5 = (re.search(r"Lv5: (.+)", plan) or [None, "(미정)"])[1].strip()

    order = []
    cur, seen = (starts[0] if len(starts) == 1 else None), set()
    while cur and cur in skills and cur not in seen:
        order.append(cur); seen.add(cur)
        cur = nexts[cur][0] if nexts[cur] else None

    branching = any(len(v) > 1 for v in nexts.values())
    # human 필드가 하나도 없으면 태스크 수를 "0개"라고 단정하지 않는다 — 모르는 것과 없는 것은 다르다.
    known_human = any(humans.values())
    if branching:
        kind = "팀 에이전트(갈림길 있음)"
    elif known_human and len(ai) < 3:
        kind = f"팀 스킬팩(순차 실행) — AI 태스크 {len(ai)}개"
    else:
        kind = "팀 스킬팩(순차 실행)"

    restate = [
        (f"- 출처 업무: Lv4 「{lv4}」 › Lv5 「{lv5}」" if lv4 != "(미정)" or lv5 != "(미정)"
         else "- 출처 업무: 기획서에 Lv4·Lv5가 적혀 있지 않다"),
        f"- 스킬 {len(skills)}개를 " + ("갈림길이 있는 흐름으로" if branching else "한 줄로") +
        " 이었다: " + (" → ".join(order) if order else "(순서 확정 안 됨)"),
        (f"- AI가 맡는 태스크 {len(ai)}개, 사람이 직접 하는 태스크 {len(human_only)}개"
         + (f" ({', '.join(human_only)})" if human_only else ""))
        if known_human else
        "- 태스크별 Human 여부(자동·증강·사람고유)가 스킬에 적혀 있지 않아 판정하지 않았다",
        f"- 산출물 유형: {kind}",
        f"- 흐름의 끝: {', '.join(terminals)}",
    ]

    # ── 미결 갈래 수집 ──
    forks = []

    # ① 끝에 사람 확인이 있는가
    for t in terminals:
        meta, body = skills[t]
        if humans.get(t) != "사람고유" and not ("확인" in body and "멈" in body):
            forks.append(("검수없음", t,
                          f"흐름이 「{t}」에서 끝나는데 사람 확인 단계가 없습니다. "
                          f"결과가 틀렸을 때 알아챌 사람이 흐름 안에 없습니다.",
                          ["끝에 사람 검토 태스크를 하나 추가한다 (권장)",
                           "뒤따르는 다른 Lv5가 검수 지점임을 기록한다",
                           "검수 없이 나가는 설계임을 위험으로 명시하고 그대로 둔다"]))

    # ② 중간 사람 판단이 halt_at에 들어 있는가
    halt = set()
    m = re.search(r"halt_at:\s*(.+)", contract)
    if m:
        halt = {x.strip() for x in re.split(r"[,;]", m.group(1)) if x.strip()}
    for n in human_only:
        if n not in terminals and n not in halt:
            forks.append(("중간정지누락", n,
                          f"「{n}」은 사람이 판단하는데 흐름 중간에 있습니다. "
                          f"통합 점검기의 L4는 끝점만 보므로 이 자리는 검사되지 않습니다.",
                          [f"CONTRACT.md의 halt_at에 「{n}」을 추가한다"]))

    # ③ 표·칸이 정해졌는가
    if "(미정)" in plan and "데이터 명세" in plan:
        forks.append(("데이터미정", "데이터 명세",
                      "표 이름과 칸 이름이 아직 없습니다. 설계도 단계에는 데이터 정보가 없어서 "
                      "인터뷰에서 채워야 합니다.",
                      ["팀이 실제로 쓰는 엑셀/시트 이름부터 받아 채운다",
                       "실습용 가상 값으로 채우고 실도입 전 교체한다"]))

    # ④ 연동
    if re.search(r"## 6\. 연동 맵\s*\n- \(미정", plan):
        forks.append(("연동미정", "연동 맵",
                      "다른 스킬·에이전트와 붙는지 아직 정해지지 않았습니다.",
                      ["연동 지점과 주고받는 형식을 적는다", "「현재는 독립」으로 확정한다"]))

    forks.sort(key=lambda f: STAKES.get(f[0], (99, ""))[0])

    # ── DECISIONS.md ──
    doc = ["# 이 팩을 어떻게 읽었는가 (readchk)", "",
           "> 작업을 시작하기 전에 남기는 기록입니다. 나중에 읽는 사람이 "
           "\"이 팩이 의도대로 만들어졌는지\"를 이 문서와 대조해 확인할 수 있습니다.", "",
           "## 이해한 바", ""] + restate + ["", "## 아직 정해지지 않은 것", ""]

    if not forks:
        doc += ["정해지지 않은 것이 없습니다. 모든 항목이 파일에서 확정되었습니다.", ""]
        print("🟢 미결 없음 — 파일이 모든 것을 답했습니다")
    else:
        k, item, why, opts = forks[0]
        w = STAKES.get(k, (99, ""))[1]
        doc += [f"### ① 가장 먼저 정할 것 — {item}", "",
                f"**무엇이 문제인가**: {why}", "",
                f"**왜 이것부터인가**: {w}", "", "**선택지**", ""]
        doc += [f"{i}. {o}" for i, o in enumerate(opts, 1)]
        doc += ["", "> 이 결정은 **기본값으로 채우지 않았습니다.** 팀이 고른 뒤 이 문서에 답을 적으십시오.", ""]
        if len(forks) > 1:
            doc += ["### 그 밖에 (①을 정한 뒤 순서대로)", ""]
            doc += [f"- **{it}** — {wy}" for _, it, wy, _ in forks[1:]]
            doc += [""]
        print(f"🟡 미결 {len(forks)}건 — 가장 먼저 정할 것: 「{item}」")
        print(f"   {why}")
        if len(forks) > 1:
            print(f"   나머지 {len(forks)-1}건은 DECISIONS.md에 순서대로 적어두었습니다.")

    doc += ["---", "", "이 미결이 남아 있어도 팩은 그대로 돌아갑니다. "
            "결정이 나면 해당 파일을 고치고 이 문서를 갱신하십시오.", ""]
    (pack / "DECISIONS.md").write_text("\n".join(doc), encoding="utf-8")

    print()
    for line in restate:
        print(line)
    print(f"\n→ {pack / 'DECISIONS.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
