#!/usr/bin/env python3
"""Lv.5 통합 패키징 통합 점검기 — 기계 판정 (L1~L3 + L4 일부).

사용:
  python3 check/run_check.py <팩 경로>   팀 에이전트 팩을 판정
  python3 check/run_check.py --self      이 저장소 자신을 판정 (README ↔ 실제 폴더 일치)

종료 코드 0 = 기계 판정 전체 통과. L4의 [사람 판정] 항목은 별도 수행 필요.
"""
import re
import sys
from pathlib import Path

results = []


def check(layer, name, ok, detail=""):
    """ok=True 통과 · ok=False 실패 · ok=None 명시적으로 수용된 위험(⚠️, 실패로 세지 않음)."""
    results.append((layer, name, ok, detail))


def parse_skill(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("["):
            meta[k.strip()] = [x.strip() for x in v.strip("[]").split(",") if x.strip()]
        else:
            meta[k.strip()] = None if v == "null" else v
    return meta, m.group(2)


def _topo(skills, nexts):
    """위상 정렬 — 분기가 있어도 실행 순서를 하나 뽑는다 (시작·끝 판정용)."""
    order, seen = [], set()
    def walk(n):
        if n in seen:
            return
        seen.add(n)
        for m_ in nexts.get(n, []):
            if m_ in skills:
                walk(m_)
        order.append(n)
    for n in skills:
        walk(n)
    return list(reversed(order))


def main(pack_dir):
    pack = Path(pack_dir)

    # ── L1 구조 ──
    for f in ["README.md", "agent-plan.md", "AGENTS.md"]:
        check("L1", f"필수 파일 {f}", (pack / f).is_file())
    check("L1", "skills/ 존재", (pack / "skills").is_dir())
    check("L1", "data/ 존재", (pack / "data").is_dir())

    plan_copies = list(pack.rglob("agent-plan.md"))
    check("L1", "agent-plan.md SSOT 유일성", len(plan_copies) == 1,
          f"{len(plan_copies)}개 발견" if len(plan_copies) != 1 else "")

    skills = {}
    for p in sorted(pack.glob("skills/*/*/[sS][kK][iI][lL][lL].md")):
        meta, body = parse_skill(p)
        check("L1", f"{p.parent.name}: frontmatter", meta is not None)
        if meta:
            missing = [k for k in ["name", "inputs", "outputs", "reads", "writes", "next"] if k not in meta]
            check("L1", f"{meta.get('name', p.parent.name)}: 헤더 필드 완비", not missing,
                  f"누락: {missing}" if missing else "")
            skills[meta["name"]] = (meta, body, p)
    check("L1", "스킬 1개 이상", len(skills) > 0)

    plan = (pack / "agent-plan.md").read_text(encoding="utf-8") if (pack / "agent-plan.md").is_file() else ""
    agent_md = (pack / "AGENTS.md").read_text(encoding="utf-8") if (pack / "AGENTS.md").is_file() else ""

    # ── L2 맥락 반영 ──
    plan_tables = set(re.findall(r"[\w가-힣]+\.(?:xlsx|docx|pptx|pdf|csv)", plan))
    for name, (meta, body, p) in skills.items():
        check("L2", f"{name}: 기획서에 언급", name in plan or name in agent_md,
              "agent-plan.md/AGENTS.md 어디에도 없음" if name not in plan + agent_md else "")
        used = set(meta.get("reads", []) + meta.get("writes", []))
        outside = used - plan_tables
        check("L2", f"{name}: 데이터가 명세 안", not outside,
              f"명세 밖 표: {sorted(outside)}" if outside else "")
        check("L2", f"{name}: 본문 존재", len(body.strip()) > 50)

    # ── L3 충돌·일관성 ──
    writers = {}
    for name, (meta, _, _) in skills.items():
        for t in meta.get("writes", []):
            writers.setdefault(t, []).append(name)
    for t, ws in writers.items():
        check("L3", f"단일 기록자: {t}", len(ws) == 1, f"복수 기록자 {ws}" if len(ws) > 1 else "")

    # 체인: next 링크가 모든 스킬을 한 줄로 잇는가
    # 흐름은 직선일 수도, 갈림길이 있을 수도 있다. 둘 다 유효한 산출물이다 —
    # 직선이면 '스킬 묶음', 갈림길이 있으면 '에이전트'로 분류만 하고 통과시킨다.
    # (ATF의 ④순서 가변성이 바로 이 차이다. 거부가 아니라 이름을 정확히 붙이는 것이 우리 일이다.)
    nexts = {n: [x.strip() for x in re.split(r"[|,]", m["next"]) if x.strip()] if m.get("next") else []
             for n, (m, _, _) in skills.items()}
    targets = {t for vs in nexts.values() for t in vs}
    starts = [n for n in skills if n not in targets]

    # 시작점에서 도달 가능한 스킬 (BFS — 분기 허용, 순환 감지)
    reached, frontier = set(starts), list(starts)
    while frontier:
        cur = frontier.pop()
        for nxt in nexts.get(cur, []):
            if nxt in skills and nxt not in reached:
                reached.add(nxt)
                frontier.append(nxt)

    def has_cycle():
        state = {}
        def walk(n):
            if state.get(n) == 1:
                return True
            if state.get(n) == 2:
                return False
            state[n] = 1
            for m_ in nexts.get(n, []):
                if m_ in skills and walk(m_):
                    return True
            state[n] = 2
            return False
        return any(walk(n) for n in skills)

    # 루프백(되돌아가기): next와 별도의 뒤로 가는 화살표.
    # 원본 업무(디자인캠프 Process Flow)에는 루프백이 실제로 있다 — 반려·재작업·재대사.
    # next에 섞으면 순환 검사가 무의미해지므로 loop_to라는 다른 칸으로 받는다.
    loops = {n: m["loop_to"].strip() for n, (m, _, _) in skills.items()
             if m.get("loop_to") and str(m.get("loop_to")).strip() not in ("", "null")}
    for src, dst in loops.items():
        check("L3", f"루프백: {src}↩{dst} 대상 실재", dst in skills,
              f"없는 스킬로 되돌아감: {dst}" if dst not in skills else "")
        # 루프백은 반드시 '뒤로' 가야 한다. 앞으로 가는 화살표를 loop_to에 숨기면
        # 순환 검사를 우회하게 되므로, 대상에서 next만 따라 자신에게 돌아올 수 있어야 한다.
        if dst in skills:
            seen_, q_ = set(), [dst]
            while q_:
                c = q_.pop()
                for nx2 in nexts.get(c, []):
                    if nx2 in skills and nx2 not in seen_:
                        seen_.add(nx2); q_.append(nx2)
            check("L3", f"루프백: {src}↩{dst} 방향", src in seen_,
                  f"{dst}에서 next로 {src}에 닿지 않음 — 루프백이 아니라 앞으로 가는 화살표"
                  if src not in seen_ else "")
        # 탈출 조건 없는 루프는 무한반복이다. 없으면 실패, (미정)이면 수용된 위험으로 남긴다.
        ex = (skills[src][0].get("loop_exit") or "").strip()
        if not ex:
            check("L3", f"루프백: {src}↩{dst} 탈출 조건", False,
                  "loop_exit 없음 — 언제 반복이 끝나는지 아무도 모른다")
        elif ex.startswith("(미정"):
            check("L3", f"루프백: {src}↩{dst} 탈출 조건", None,
                  "탈출 조건 (미정) — 와이어프레임·인터뷰에서 채워야 한다")
        else:
            check("L3", f"루프백: {src}↩{dst} 탈출 조건", True)

    # 갈림길 조건: 어느 쪽으로 갈지 정하는 규칙. 원본(디자인캠프)에는 ◆ 조건이 글로 있다.
    # 없다고 막지는 않는다 — 수용된 위험(⚠️)으로 남겨 사라지지 않게 한다.
    for n, vs in nexts.items():
        if len(vs) > 1:
            when = (skills[n][0].get("when") or "").strip()
            covered = when and all(t in when for t in vs)
            check("L3", f"갈림길 조건: {n}", True if covered else None,
                  "" if covered else
                  f"when 칸에 {vs} 각각의 조건이 없음 — 원본 흐름도의 ◆ 조건을 옮겨 적으십시오")

    check("L3", "흐름: 시작점 1개", len(starts) == 1, f"시작점 {starts}")
    check("L3", "흐름: 모든 스킬에 도달(고아 없음)", reached == set(skills),
          f"도달 못 함: {sorted(set(skills) - reached)}")
    check("L3", "흐름: 순환 없음", not has_cycle())
    dangling = [(a, t) for a, vs in nexts.items() for t in vs if t not in skills]
    check("L3", "흐름: next가 실재하는 스킬을 가리킴", not dangling,
          f"없는 스킬 지목: {dangling}" if dangling else "")
    for a, vs in nexts.items():
        for b in vs:
            if b not in skills:
                continue
            out, inp = set(skills[a][0].get("outputs", [])), set(skills[b][0].get("inputs", []))
            check("L3", f"흐름 정합: {a}→{b}", bool(out & inp),
                  f"outputs {sorted(out)} ↛ inputs {sorted(inp)}" if not out & inp else "")

    # ── 산출물 유형 분기 ──
    # 두 가지를 본다: AI에 맡길 태스크가 몇 개인가(ATF ③다단계성), 갈림길이 있는가(ATF ④순서 가변성).
    # 어느 쪽도 탈락 사유가 아니다. 이름을 정확히 붙이고 다음 걸음을 알려줄 뿐이다.
    # 갈림길뿐 아니라 루프백도 순서를 바꾼다 — 반려가 나면 같은 일을 다시 돈다.
    branching = any(len(v) > 1 for v in nexts.values()) or bool(loops)
    humans = {n: (m.get("human") or "").strip() for n, (m, _, _) in skills.items()}
    ai_tasks = [n for n, h in humans.items() if h in ("자동", "증강")]
    human_only = [n for n, h in humans.items() if h == "사람고유"]
    known_human = any(humans.values())          # human 필드가 하나라도 적혀 있는가
    too_few = known_human and len(ai_tasks) < 3  # ATF ③다단계성 기준선

    if too_few:
        pack_kind = f"팀 스킬팩 (AI 태스크 {len(ai_tasks)}개 — ATF ③다단계성 미충족)"
        kind_note = [
            f"  · AI에 맡길 태스크(자동·증강)가 {len(ai_tasks)}개입니다. 에이전트가 대신할 일 자체가 적습니다.",
            "    다음 중 하나를 고르십시오 — 태스크를 더 쪼개 3개 이상으로 만들거나, 이대로 스킬 묶음으로 씁니다.",
        ]
    elif branching:
        why = []
        if any(len(v) > 1 for v in nexts.values()):
            why.append("갈림길")
        if loops:
            why.append("루프백")
        pack_kind = f"팀 에이전트 ({'·'.join(why)} 있음)"
        kind_note = []
    else:
        pack_kind = "팀 스킬팩 (순차 실행)"
        kind_note = [
            "  · 순서가 매번 같은 흐름입니다. 지금 만든 것은 스킬 묶음이고,",
            "    갈림길이 생기는 순간 그대로 에이전트가 됩니다 — 부품은 이미 다 만들었습니다.",
        ]

    # 체인 중간의 사람고유 지점은 L4가 보지 못한다(끝점만 검사). 여기서 알려준다.
    # next가 없으면 끝점이다. 루프백만 있는 스킬도 끝점으로 본다 —
    # 탈출 조건이 차면 흐름이 거기서 끝나므로, 끝점의 검사(사람 확인·자동 발송 금지)를 받아야 한다.
    terminals = [n for n in skills if not nexts.get(n)]
    mid_human = [n for n in human_only if n not in terminals]
    chain = [n for n in _topo(skills, nexts)] if reached == set(skills) else []

    # 용어 일관: 표 이름 근사 중복(공백/언더스코어 차이) 탐지
    all_text = plan + agent_md + "".join(b for _, b, _ in skills.values())
    names = set(re.findall(r"[\w가-힣_ ]+\.(?:xlsx|docx|pptx|pdf|csv)", all_text))
    normalized = {}
    for n in names:
        key = n.replace(" ", "").replace("_", "")
        normalized.setdefault(key, set()).add(n.strip())
    for key, variants in normalized.items():
        check("L3", f"용어 일관: {min(variants)}", len(variants) == 1,
              f"표기 변형 {sorted(variants)}" if len(variants) > 1 else "")

    # 규칙 일관: ±N% 임계값.
    # 한 팩에 서로 다른 규칙이 여럿일 수 있다(예: 이상 잔액 ±30%, 주석 설명필요 ±20%).
    # 그럴 때는 CONTRACT.md의 threshold가 정본이다 — 거기 적힌 값들만 쓸 수 있다.
    # 계약이 임계값을 말하지 않으면 예전대로 "전부 한 값이어야 한다"로 본다.
    contract_f = pack / "CONTRACT.md"
    contract_txt = contract_f.read_text(encoding="utf-8") if contract_f.is_file() else ""
    m_thr = re.search(r"^threshold:\s*(.+)$", contract_txt, re.M)
    allowed = set(re.findall(r"±\s*(\d+)\s*%", m_thr.group(1))) if m_thr else set()

    thresholds = {src: set(re.findall(r"±\s*(\d+)\s*%", txt))
                  for src, txt in [("agent-plan", plan), ("AGENT", agent_md)] +
                  [(n, b) for n, (_, b, _) in skills.items()]}
    declared = set().union(*thresholds.values())
    if declared and allowed:
        stray = declared - allowed
        check("L3", "규칙 일관: 임계값 ±% (계약이 정본)", not stray,
              f"계약(threshold)에 없는 값 {sorted(stray)} — 계약에 적거나 문서를 고치십시오"
              if stray else "")
    elif declared:
        conflict = [s for s, v in thresholds.items() if v and v != declared]
        check("L3", "규칙 일관: 임계값 ±%", len(declared) == 1 and not conflict,
              f"발견된 값 {sorted(declared)} — 서로 다른 규칙이라면 CONTRACT.md의 "
              f"threshold에 전부 적으십시오" if len(declared) > 1 else "")

    # ── L4 E2E (기계 판정 부분) ──
    if chain:
        first_in = skills[chain[0]][0].get("inputs", [])
        plan_flat = plan.replace(" ", "")
        check("L4", "시작 입력이 시나리오와 일치", any(i.replace(" ", "") in plan_flat for i in first_in),
              f"기획서에 없는 입력 {first_in}")
        # 갈림길이 있으면 끝점이 여럿이다. 모든 끝점이 조건을 지켜야 한다.
        for t in terminals:
            t_meta, t_body, _ = skills[t]
            tag = f"끝점 {t}" if len(terminals) > 1 else "최종 단계"
            check("L4", f"{tag}: 출력이 시나리오 산출물",
                  any(o.replace(" ", "") in plan_flat for o in t_meta.get("outputs", [])),
                  f"기획서에 없는 출력 {t_meta.get('outputs')}")
            check("L4", f"{tag}: 자동 발송 없음", not t_meta.get("writes"),
                  f"끝점이 직접 기록: {t_meta.get('writes')}")
            # 검수 지점이 없을 때: 팀이 그것을 알고 기록해 두었는가를 본다.
            # 기록이 있으면 ⚠️ 수용된 위험으로 남긴다 — 실패로 세지 않되 **결코 사라지지 않는다**.
            # 기록이 없으면 그냥 ❌다. 모르고 빠뜨린 것과 알고 감수한 것은 다르게 다뤄야 한다.
            has_halt = "확인" in t_body and "멈" in t_body
            if has_halt:
                check("L4", f"{tag}: 휴먼인더루프 명시", True)
            else:
                decisions = (pack / "DECISIONS.md")
                dtext = decisions.read_text(encoding="utf-8") if decisions.is_file() else ""
                acknowledged = ("결정됨" in dtext and t in dtext
                                and ("검수" in plan or "검수" in agent_md))
                check("L4", f"{tag}: 휴먼인더루프 명시", None if acknowledged else False,
                      "검수 지점 없음 — 팀이 위험으로 수용하고 DECISIONS.md에 기록함"
                      if acknowledged else
                      "본문에 확인 요청·정지가 없음 (수용하려면 DECISIONS.md에 결정을 기록하십시오)")

    # ── 리포트 ──
    fails = [r for r in results if r[2] is False]
    accepted = [r for r in results if r[2] is None]
    for layer in ["L1", "L2", "L3", "L4"]:
        rows = [r for r in results if r[0] == layer]
        print(f"\n[{layer}] {sum(1 for r in rows if r[2])}/{len(rows)} 통과")
        for _, name, ok, detail in rows:
            mark = "✅" if ok is True else ("⚠️" if ok is None else "❌")
            print(f"  {mark} {name}" + (f" — {detail}" if detail and ok is not True else ""))
    print(f"\n{'='*50}")
    verdict = "전체 통과 ✅" if not fails else f"실패 {len(fails)}건 ❌"
    if accepted and not fails:
        verdict += f" (수용된 위험 {len(accepted)}건 ⚠️ — 사라지지 않습니다)"
    print(f"기계 판정: {verdict}")
    print(f"산출물 유형: {pack_kind}")
    for line in kind_note:
        print(line)
    if not known_human:
        print("  · 스킬에 human 필드(자동·증강·사람고유)가 없어 태스크 수 판정을 건너뛰었습니다.")
    if mid_human:
        print(f"  ⚠️ 사람고유 지점이 체인 중간에 있습니다: {mid_human}")
        print("     L4는 끝점만 검사하므로, CONTRACT.md의 halt_at에 이 이름을 반드시 넣으십시오.")
    print("주의: L4의 [사람 판정] 2개(실제 실행, 오류 주입)는 별도 수행 필요")
    return 1 if fails else 0


def self_check(repo_dir):
    """저장소 자신을 검사: README 구조도가 실제 최상위 폴더를 전부 안내하는가.

    L2("기획서가 모르는 스킬은 반영 안 된 맥락")와 같은 논리를 저장소에 적용한 것.
    폴더를 추가하고 README를 안 고치면 여기서 실패한다.
    """
    repo = Path(repo_dir)
    readme = (repo / "README.md")
    if not readme.is_file():
        print("❌ README.md 없음")
        return 1
    text = readme.read_text(encoding="utf-8")

    actual = {p.name for p in repo.iterdir()
              if p.is_dir() and not p.name.startswith((".", "__"))}
    # 구조도 블록 안에서 `이름/` 형태로 언급된 폴더만 인정한다
    documented = set(re.findall(r"[│├└─\s]([\w.-]+)/", text))

    # 반대 방향(README에만 있고 실재하지 않는 폴더) 검사는 두지 않는다.
    # 중첩 폴더 표기와 한국어 문장의 '/'를 최상위 폴더와 구별할 수 없어 오탐만 냈다 — 제거 우선.
    missing = sorted(actual - documented)
    check("SELF", "README가 모든 최상위 폴더를 안내", not missing,
          f"구조도에 없는 폴더: {missing}" if missing else "")
    for tool in ["prompts", "harness"]:
        if tool in actual:
            check("SELF", f"{tool}/ 사용법 섹션 존재", f"{tool}/" in text and text.count(tool) >= 3,
                  f"{tool}/가 구조도에만 있고 사용법 설명이 없음")

    rows = [r for r in results if r[0] == "SELF"]
    print(f"\n[SELF] {sum(1 for r in rows if r[2])}/{len(rows)} 통과")
    for _, name, ok, detail in rows:
        print(f"  {'✅' if ok else '❌'} {name}" + (f" — {detail}" if detail and not ok else ""))
    fails = [r for r in rows if not r[2]]
    print(f"\n{'='*50}")
    print(f"저장소 자기 판정: {'통과 ✅' if not fails else f'실패 {len(fails)}건 ❌'}")
    return 1 if fails else 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "."
    if arg == "--self":
        sys.exit(self_check(Path(__file__).resolve().parent.parent))
    sys.exit(main(arg))
