#!/usr/bin/env python3
"""Lv.5 통합 패키징 하네스 — 기계 판정 (L1~L3 + L4 일부).

사용:
  python3 harness/run_harness.py <팩 경로>   팀 에이전트 팩을 판정
  python3 harness/run_harness.py --self      이 저장소 자신을 판정 (README ↔ 실제 폴더 일치)

종료 코드 0 = 기계 판정 전체 통과. L4의 [사람 판정] 항목은 별도 수행 필요.
"""
import re
import sys
from pathlib import Path

results = []


def check(layer, name, ok, detail=""):
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


def main(pack_dir):
    pack = Path(pack_dir)

    # ── L1 구조 ──
    for f in ["README.md", "agent-plan.md", "AGENT.md"]:
        check("L1", f"필수 파일 {f}", (pack / f).is_file())
    check("L1", "skills/ 존재", (pack / "skills").is_dir())
    check("L1", "data/ 존재", (pack / "data").is_dir())

    plan_copies = list(pack.rglob("agent-plan.md"))
    check("L1", "agent-plan.md SSOT 유일성", len(plan_copies) == 1,
          f"{len(plan_copies)}개 발견" if len(plan_copies) != 1 else "")

    skills = {}
    for p in sorted(pack.glob("skills/*/*/skill.md")):
        meta, body = parse_skill(p)
        check("L1", f"{p.parent.name}: frontmatter", meta is not None)
        if meta:
            missing = [k for k in ["name", "inputs", "outputs", "reads", "writes", "next"] if k not in meta]
            check("L1", f"{meta.get('name', p.parent.name)}: 헤더 필드 완비", not missing,
                  f"누락: {missing}" if missing else "")
            skills[meta["name"]] = (meta, body, p)
    check("L1", "스킬 1개 이상", len(skills) > 0)

    plan = (pack / "agent-plan.md").read_text(encoding="utf-8") if (pack / "agent-plan.md").is_file() else ""
    agent_md = (pack / "AGENT.md").read_text(encoding="utf-8") if (pack / "AGENT.md").is_file() else ""

    # ── L2 맥락 반영 ──
    plan_tables = set(re.findall(r"[\w가-힣]+\.xlsx", plan))
    for name, (meta, body, p) in skills.items():
        check("L2", f"{name}: 기획서에 언급", name in plan or name in agent_md,
              "agent-plan.md/AGENT.md 어디에도 없음" if name not in plan + agent_md else "")
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
    nexts = {n: m.get("next") for n, (m, _, _) in skills.items()}
    targets = [v for v in nexts.values() if v]
    starts = [n for n in skills if n not in targets]
    chain, cur, seen = [], (starts[0] if len(starts) == 1 else None), set()
    while cur and cur in skills and cur not in seen:
        chain.append(cur)
        seen.add(cur)
        cur = nexts[cur]
    check("L3", "체인: 시작점 1개", len(starts) == 1, f"시작점 {starts}")
    check("L3", "체인: 전체 스킬 포함(고아·순환 없음)", len(chain) == len(skills),
          f"체인 {chain} vs 스킬 {sorted(skills)}")
    for a, b in zip(chain, chain[1:]):
        out, inp = set(skills[a][0].get("outputs", [])), set(skills[b][0].get("inputs", []))
        check("L3", f"체인 정합: {a}→{b}", bool(out & inp),
              f"outputs {sorted(out)} ↛ inputs {sorted(inp)}" if not out & inp else "")

    # 용어 일관: 표 이름 근사 중복(공백/언더스코어 차이) 탐지
    all_text = plan + agent_md + "".join(b for _, b, _ in skills.values())
    names = set(re.findall(r"[\w가-힣_ ]+\.xlsx", all_text))
    normalized = {}
    for n in names:
        key = n.replace(" ", "").replace("_", "")
        normalized.setdefault(key, set()).add(n.strip())
    for key, variants in normalized.items():
        check("L3", f"용어 일관: {min(variants)}", len(variants) == 1,
              f"표기 변형 {sorted(variants)}" if len(variants) > 1 else "")

    # 규칙 일관: ±N% 임계값이 문서 간 동일한가
    thresholds = {src: set(re.findall(r"±\s*(\d+)\s*%", txt))
                  for src, txt in [("agent-plan", plan), ("AGENT", agent_md)] +
                  [(n, b) for n, (_, b, _) in skills.items()]}
    declared = set().union(*thresholds.values())
    if declared:
        conflict = [s for s, v in thresholds.items() if v and v != declared]
        check("L3", "규칙 일관: 임계값 ±%", len(declared) == 1 and not conflict,
              f"발견된 값 {sorted(declared)}" if len(declared) > 1 else "")

    # ── L4 E2E (기계 판정 부분) ──
    if chain:
        first_in = skills[chain[0]][0].get("inputs", [])
        last_meta, last_body, _ = skills[chain[-1]]
        plan_flat = plan.replace(" ", "")
        check("L4", "시작 입력이 시나리오와 일치", any(i.replace(" ", "") in plan_flat for i in first_in),
              f"기획서에 없는 입력 {first_in}")
        check("L4", "끝 출력이 시나리오 산출물",
              any(o.replace(" ", "") in plan_flat for o in last_meta.get("outputs", [])))
        check("L4", "최종 단계: 자동 발송 없음", not last_meta.get("writes"),
              f"최종 스킬이 직접 기록: {last_meta.get('writes')}")
        check("L4", "최종 단계: 휴먼인더루프 명시", "확인" in last_body and "멈" in last_body,
              "최종 스킬 본문에 확인 요청·정지가 없음")

    # ── 리포트 ──
    fails = [r for r in results if not r[2]]
    for layer in ["L1", "L2", "L3", "L4"]:
        rows = [r for r in results if r[0] == layer]
        print(f"\n[{layer}] {sum(1 for r in rows if r[2])}/{len(rows)} 통과")
        for _, name, ok, detail in rows:
            print(f"  {'✅' if ok else '❌'} {name}" + (f" — {detail}" if detail and not ok else ""))
    print(f"\n{'='*50}")
    print(f"기계 판정: {'전체 통과 ✅' if not fails else f'실패 {len(fails)}건 ❌'}")
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
