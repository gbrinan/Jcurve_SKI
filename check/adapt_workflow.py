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
    lv6 = [{"n": m[0], "h": m[1], "s": m[2]}
           for m in re.findall(r'\{n:"([^"]+)",h:"([^"]+)",s:"([^"]*)"\}', b6)]
    return dict(lv4=lv4, lv5=lv5, sel=sel, lv6=lv6, tgt=tgt)


def slug(s):
    return s.replace(" ", "")


def main(html, out_dir):
    d = parse(html)
    out = Path(out_dir)
    (out / "data").mkdir(parents=True, exist_ok=True)
    tasks, names = d["lv6"], [slug(t["n"]) for t in d["lv6"]]
    lv5 = d["lv5"][d["sel"]]

    for i, t in enumerate(tasks):
        name, nxt = names[i], (names[i + 1] if i + 1 < len(tasks) else "null")
        sdir = out / "skills" / "depth" / name
        sdir.mkdir(parents=True, exist_ok=True)
        body = [f"# {name}", "",
                f"> 상류: 워크플로우 설계도 · Lv4 「{d['lv4']}」 · Lv5 「{lv5}」 · Lv6 「{t['n']}」",
                f"> Human 여부: {t['h']} · Skill화 용이성: {t['s'] or '미완료'}", "",
                "## 판단기준 · 예외",
                "(미정 — 세션 4 와이어프레임에서 3단 파고들기로 채운다)", ""]
        if t["h"] == "사람고유":
            body += ["## 사람이 확인하고 멈추는 지점",
                     f"- {t['n']} — 사람이 직접 판단한다. 자동으로 진행하지 않는다.", ""]
        fm = ["---", f"name: {name}", "owner: (미정)", "quadrant: depth",
              f"human: {t['h']}", f"skillability: {t['s'] or '미완료'}",
              f"inputs: [{names[i-1] + '결과' if i else slug(lv5) + '입력'}]",
              f"outputs: [{name}결과]", "reads: []", "writes: []",
              f"next: {nxt}", "---", ""]
        (sdir / "SKILL.md").write_text("\n".join(fm + body) + "\n", encoding="utf-8")

    ai = [t for t in tasks if t["h"] in ("자동", "증강")]
    human_only = [t for t in tasks if t["h"] == "사람고유"]
    halt = [slug(t["n"]) for t in human_only] or [names[-1]]

    payloads = [slug(lv5) + "입력"] + [n + "결과" for n in names]
    contract = ["# 통합 계약 (워크플로우 설계도 변환 초안)", "",
                f"Lv4 「{d['lv4']}」 · Lv5 「{lv5}」의 Lv6 태스크 {len(tasks)}개를 순서대로 이었다.", "",
                "```contract", "tables:", "  (미정): (설계도 단계엔 표·칸 명세가 없음)",
                "writers:", "  (미정): (미정)",
                f"chain: {' -> '.join(names)}",
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
            "## 2-1. 태스크 구성", "| # | Lv6 | Human 여부 | Skill화 |", "|---|---|---|---|"]
    for i, t in enumerate(tasks, 1):
        plan.append(f"| {i} | {t['n']} | {t['h']} | {t['s'] or '미완료'} |")
    plan += ["", f"AI 태스크(자동+증강) {len(ai)}개 · 사람고유 {len(human_only)}개", "",
             "## 3. 데이터 명세", "| 표 이름 | 칸 이름 | 원본 위치(SSOT) | 읽기/쓰기 |",
             "|---|---|---|---|", "| (미정) | (미정) | (미정) | (미정) |",
             "> 설계도에는 표·칸 명세가 없다. 세션 6 인터뷰 Q3에서 확정한다.", "",
             "## 4. 대표 시나리오",
             f"- 입력: {slug(lv5)}입력 → 처리: {' → '.join(names)} → 출력: {names[-1]}결과", "",
             "## 5. 결과물 반영 규칙", "- (미정 — 인터뷰 Q5)", "",
             "## 6. 연동 맵", "- (미정 — 인터뷰 Q6)", "",
             "## 7. 검증·휴먼인더루프 지점"]
    for t in human_only:
        plan.append(f"- {t['n']} — 사람고유. 확인 요청 후 멈춘다.")
    if not human_only:
        plan.append("- (없음) — 사람고유 태스크가 없다. 검수 지점을 하나 세워야 한다.")
    plan += ["", "## 8. 폴더 트리", "```mermaid", "graph TD", '  R["📁 팀-agent/"]',
             '  R --> A["README.md"]', '  R --> B["agent-plan.md · SSOT"]',
             '  R --> C["AGENTS.md"]', '  R --> D["CONTRACT.md"]',
             '  R --> S["📁 skills/depth/"]', '  R --> T["📁 data/"]']
    for n in names:
        plan.append(f'  S --> S_{abs(hash(n)) % 9999}["{n}"]')
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
    print(f"  halt_at: {', '.join(halt)}")
    print("  (미정)으로 남긴 것: 판단기준·예외·환경태그 · 표/칸 이름 · 결과물 반영 · 연동")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
