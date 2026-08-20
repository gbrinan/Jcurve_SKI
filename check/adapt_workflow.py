#!/usr/bin/env python3
"""워크플로우 설계도(HTML) → 통합 팩 변환.

사용: python3 check/adapt_workflow.py <워크플로우.html> <출력 팩 경로>

입력은 세션 4 와이어프레임보다 **한 단계 앞선** 산출물이다. Lv4-Lv5-Lv6 계층과
Human 여부·Skill화 용이성만 있고, 판단기준(rule)·예외(exc)·환경 태그는 아직 없다.
없는 것은 지어내지 않고 `(미정)`으로 남긴다.

★ `add5()`/`add6()` 함수의 기본값("새 워크플로우"/"새 태스크")을 실제 데이터로 세지 않는다.
   ATF 코치가 경고한 함정이다 — 빈 행을 실태스크로 세면 다단계성이 잘못 충족된다.
"""
import re
import sys
from pathlib import Path


def parse(path):
    t = Path(path).read_text(encoding="utf-8")
    lv4 = re.search(r'id="t4"[^>]*>([^<]+)<', t).group(1).strip()
    sel = int(re.search(r"let sel=(\d+)", t).group(1))
    tgt = int(re.search(r"tgt=(\d+);", t).group(1))
    # 선언 블록만 읽는다 (add5/add6 함수 본문 제외)
    b5 = re.search(r"let lv5=\[(.*?)\];", t, re.S).group(1)
    b6 = re.search(r"let lv6=\[(.*?)\];", t, re.S).group(1)
    lv5 = re.findall(r'\{n:"([^"]+)"\}', b5)
    # nx는 뒤늦게 생긴 칸이다. **칸이 아예 없는 것**(예전 설계도 → 다음 줄로 이음)과
    # **칸은 있는데 비어 있는 것**(이 갈래는 여기서 끝)은 서로 다르다. 그래서 None과 ""를 구분한다.
    lv6 = []
    for ent in re.findall(r"\{[^{}]*\}", b6):
        m = re.search(r'n:"([^"]+)",h:"([^"]+)",s:"([^"]*)"', ent)
        if not m:
            continue
        nx = re.search(r'nx:"([^"]*)"', ent)
        lv6.append({"n": m.group(1), "h": m.group(2), "s": m.group(3),
                    "nx": nx.group(1) if nx else None})
    return dict(lv4=lv4, lv5=lv5, sel=sel, lv6=lv6, tgt=tgt)


def slug(s):
    return s.replace(" ", "")


def wire(tasks, names):
    """각 태스크의 다음 태스크를 정한다.

    nx 칸이 **없으면**(예전 설계도) 바로 다음 줄로 잇는다 — 기존 파일이 그대로 동작한다.
    nx 칸이 **비어 있으면** 그 갈래는 거기서 끝난다. 갈림길에서 갈라진 짧은 갈래가 흐름 중간에
    적혀 있어도 끝으로 남길 수 있어야 한다.
    nx에 이름이 둘 이상이면 그 자리가 갈림길이고, 그때 비로소 산출물이 에이전트가 된다.
    """
    known = set(names)
    out = []
    for i, t in enumerate(tasks):
        raw = t.get("nx")
        if raw is None:                                   # 칸 자체가 없다 → 다음 줄
            out.append([names[i + 1]] if i + 1 < len(tasks) else [])
            continue
        picked = [slug(x.strip()) for x in raw.split("|") if x.strip()]
        unknown = [x for x in picked if x not in known]
        if unknown:
            raise SystemExit(f"설계도 오류: 「{t['n']}」의 다음 태스크에 없는 이름 {unknown}")
        out.append(picked)                                # 비어 있으면 끝점
    return out


def paths(names, nexts, start):
    """갈림길을 끝까지 펼쳐 경로 목록을 만든다 (CONTRACT.md의 chain 표기용)."""
    done, idx = [], {n: i for i, n in enumerate(names)}

    def walk(cur, acc):
        if cur in acc:                      # 순환은 여기서 끊고 점검기가 잡게 둔다
            done.append(acc + [cur]); return
        acc = acc + [cur]
        nx = nexts[idx[cur]]
        if not nx:
            done.append(acc); return
        for n in nx:
            walk(n, acc)

    walk(start, [])
    return done


def main(html, out_dir):
    d = parse(html)
    out = Path(out_dir)
    (out / "data").mkdir(parents=True, exist_ok=True)
    tasks, names = d["lv6"], [slug(t["n"]) for t in d["lv6"]]
    lv5 = d["lv5"][d["sel"]]

    nexts = wire(tasks, names)
    targets = {x for nx in nexts for x in nx}
    starts = [n for n in names if n not in targets]
    preds = {n: [names[i] for i, nx in enumerate(nexts) if n in nx] for n in names}

    for i, t in enumerate(tasks):
        name = names[i]
        nxt = " | ".join(nexts[i]) if nexts[i] else "null"
        # 갈림길에서 합류하는 태스크는 앞선 태스크가 여럿이다. 그 모두를 입력으로 받는다
        # (점검기 L3의 '흐름 정합'은 앞 outputs와 뒤 inputs가 겹치는지를 본다).
        ins = [p + "결과" for p in preds[name]] or [slug(lv5) + "입력"]
        sdir = out / "skills" / "depth" / name
        sdir.mkdir(parents=True, exist_ok=True)
        body = [f"# {name}", "",
                f"> 상류: 워크플로우 설계도 · Lv4 「{d['lv4']}」 · Lv5 「{lv5}」 · Lv6 「{t['n']}」",
                f"> Human 여부: {t['h']} · Skill화 용이성: {t['s'] or '미완료'}", "",
                "## 판단기준 · 예외",
                "(미정 — 세션 4 와이어프레임에서 3단 파고들기로 채운다)", ""]
        if len(nexts[i]) > 1:
            body += ["## 갈림길",
                     f"이 태스크의 결과에 따라 다음이 갈린다: {' 또는 '.join(nexts[i])}.",
                     "어느 쪽으로 갈지 정하는 판단기준은 (미정) — 와이어프레임에서 채운다.", ""]
        if t["h"] == "사람고유":
            body += ["## 사람이 확인하고 멈추는 지점",
                     f"- {t['n']} — 사람이 직접 판단한다. 자동으로 진행하지 않는다.", ""]
        elif not nexts[i]:
            # 갈래의 끝. 여기서 결과가 밖으로 나간다 — 사람이 보지 않고 나가는 출구를 만들지 않는다.
            body += ["## 사람이 확인하고 멈추는 지점",
                     f"- {t['n']} — 이 갈래의 끝이다. 결과를 사람이 확인할 때까지 멈춘다.",
                     "  (검수 없이 내보내기로 정했다면 DECISIONS.md에 그 결정을 기록한다)", ""]
        fm = ["---", f"name: {name}", "owner: (미정)", "quadrant: depth",
              f"human: {t['h']}", f"skillability: {t['s'] or '미완료'}",
              f"inputs: [{', '.join(ins)}]",
              f"outputs: [{name}결과]", "reads: []", "writes: []",
              f"next: {nxt}", "---", ""]
        (sdir / "SKILL.md").write_text("\n".join(fm + body) + "\n", encoding="utf-8")

    ai = [t for t in tasks if t["h"] in ("자동", "증강")]
    human_only = [t for t in tasks if t["h"] == "사람고유"]
    terminals = [names[i] for i, nx in enumerate(nexts) if not nx]
    branching = any(len(nx) > 1 for nx in nexts)
    # 끝점은 모두 정지 지점이다. 사람고유 지점은 중간에 있어도 반드시 넣는다.
    halt = list(dict.fromkeys([slug(t["n"]) for t in human_only] + terminals))

    if len(starts) != 1:
        raise SystemExit(f"설계도 오류: 시작 태스크가 {len(starts)}개입니다 {starts} — "
                         "아무도 가리키지 않는 태스크가 정확히 하나여야 합니다.")
    routes = paths(names, nexts, starts[0])

    payloads = [slug(lv5) + "입력"] + [n + "결과" for n in names]
    contract = ["# 통합 계약 (워크플로우 설계도 변환 초안)", "",
                f"Lv4 「{d['lv4']}」 · Lv5 「{lv5}」의 Lv6 태스크 {len(tasks)}개를 이었다."
                + (f" 갈림길이 있어 경로가 {len(routes)}개다." if branching else " 갈림길 없는 직선이다."), "",
                "```contract", "tables:", "  (미정): (설계도 단계엔 표·칸 명세가 없음)",
                "writers:", "  (미정): (미정)",
                "chain: " + "; ".join(" -> ".join(r) for r in routes),
                f"payloads: {', '.join(payloads)}",
                "threshold: (해당 없음)",
                f"halt_at: {', '.join(halt)}",   # 중간 지점도 전부 넣는다
                "```", ""]
    (out / "CONTRACT.md").write_text("\n".join(contract), encoding="utf-8")

    plan = [f"# {lv5} 팀 기획서 (워크플로우 변환 초안)", "",
            "## 1. 팀과 목적", f"- Lv4: {d['lv4']}", f"- Lv5: {lv5}", "",
            "## 2. 역할 정의", "- 한 문장: (미정 — 인터뷰 Q2)",
            "- 하는 일: " + " · ".join(t["n"] for t in ai),
            "- 하지 않는 일: " + (" · ".join(t["n"] for t in human_only) or "(없음)"), "",
            "## 2-1. 태스크 구성", "| # | Lv6 | Human 여부 | Skill화 | 다음 태스크 |",
            "|---|---|---|---|---|"]
    for i, t in enumerate(tasks):
        nx = " 또는 ".join(nexts[i]) if nexts[i] else "(끝)"
        plan.append(f"| {i+1} | {t['n']} | {t['h']} | {t['s'] or '미완료'} | {nx} |")
    plan += ["", f"AI 태스크(자동+증강) {len(ai)}개 · 사람고유 {len(human_only)}개"
             + (f" · 갈림길 있음(경로 {len(routes)}개)" if branching else " · 갈림길 없음"), "",
             "## 3. 데이터 명세", "| 표 이름 | 칸 이름 | 원본 위치(SSOT) | 읽기/쓰기 |",
             "|---|---|---|---|", "| (미정) | (미정) | (미정) | (미정) |",
             "> 설계도에는 표·칸 명세가 없다. 세션 6 인터뷰 Q3에서 확정한다.", "",
             "## 4. 대표 시나리오", f"- 입력: {slug(lv5)}입력"]
    for r in routes:
        plan.append(f"- 경로: {' → '.join(r)} → 출력: {r[-1]}결과")
    plan += ["", "## 5. 결과물 반영 규칙", "- (미정 — 인터뷰 Q5)", "",
             "## 6. 연동 맵", "- (미정 — 인터뷰 Q6)", "",
             "## 7. 검증·휴먼인더루프 지점"]
    for t in human_only:
        plan.append(f"- {t['n']} — 사람고유. 확인 요청 후 멈춘다.")
    for t in terminals:
        if t not in [slug(x["n"]) for x in human_only]:
            plan.append(f"- {t} — 흐름의 끝. 결과를 사람이 확인하고 멈춘다.")
    if not human_only:
        plan.append("- 사람고유 태스크가 없다. 위 끝점이 유일한 검수 지점이다.")

    plan += ["", "## 8. 흐름도", "```mermaid", "graph TD"]
    ids = {n: f"T{i}" for i, n in enumerate(names)}
    for i, t in enumerate(tasks):
        n = names[i]
        shape = (f'{ids[n]}{{"{n}"}}' if len(nexts[i]) > 1
                 else f'{ids[n]}["{n}"]')
        plan.append(f"  {shape}")
        if t["h"] == "사람고유":
            plan.append(f"  style {ids[n]} stroke:#EA002C,stroke-width:2px")
    for i, nx in enumerate(nexts):
        for m in nx:
            plan.append(f"  {ids[names[i]]} --> {ids[m]}")
    plan += ["```", "",
             "- 마름모 = 갈림길 · 빨간 테두리 = 사람이 직접 판단하는 지점", "",
             "## 9. 폴더 트리", "```mermaid", "graph TD", '  R["📁 팀-agent/"]',
             '  R --> A["README.md"]', '  R --> B["agent-plan.md · SSOT"]',
             '  R --> C["AGENTS.md"]', '  R --> D["CONTRACT.md"]',
             '  R --> S["📁 skills/depth/"]', '  R --> T["📁 data/"]']
    for i, n in enumerate(names):
        plan.append(f'  S --> S{i}["{n}"]')      # 인덱스로 식별 — hash()는 실행마다 달라진다
    plan += ["```", ""]
    (out / "agent-plan.md").write_text("\n".join(plan), encoding="utf-8")
    (out / "AGENTS.md").write_text(
        f"# {lv5} 에이전트\n\n- 역할: (미정 — 인터뷰 Q2)\n"
        f"- 하는 일: {' · '.join(t['n'] for t in ai)}\n"
        f"- 하지 않는 일: {' · '.join(t['n'] for t in human_only) or '(없음)'}\n", encoding="utf-8")
    (out / "README.md").write_text(f"# {lv5}\n\n상세는 [agent-plan.md](agent-plan.md).\n",
                                   encoding="utf-8")

    print(f"변환: {d['lv4']} › {lv5}")
    print(f"  스킬 {len(tasks)}개 · AI 태스크 {len(ai)}개 · 사람고유 {len(human_only)}개")
    if len(ai) < 3:
        print(f"  ⚠️ AI 태스크가 3개 미만 → 점검기가 '팀 스킬팩'으로 분기합니다 (ATF ③다단계성)")
    elif branching:
        print(f"  ✅ 갈림길 {sum(1 for nx in nexts if len(nx) > 1)}곳 · 경로 {len(routes)}개 "
              f"→ '팀 에이전트'로 판정됩니다 (ATF ④순서 가변성)")
    else:
        print("  · 갈림길 없음 → '팀 스킬팩(순차 실행)'으로 판정됩니다. "
              "설계도의 '다음 태스크' 칸을 다시 보십시오.")
    print(f"  끝점: {', '.join(terminals)}")
    print(f"  halt_at: {', '.join(halt)}")
    print("  (미정)으로 남긴 것: 판단기준·예외·환경태그 · 표/칸 이름 · 결과물 반영 · 연동")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
