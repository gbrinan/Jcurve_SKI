#!/usr/bin/env python3
"""계약 준수 검사 + 분기처리 — 사용자가 자유롭게 만들어 온 스킬을 통합 전에 거른다.

사용: python3 check/check_contract.py <팩 경로> [--run-check]

종료 코드로 분기한다:
  0 = 🟢 GREEN  계약 준수. --run-check를 주면 곧바로 점검기를 실행한다.
  1 = 🟡 YELLOW 이름 표기 어긋남. 교정안을 REMEDIATION.md로 출력한다 (기계가 제안, 사람이 반영).
  2 = 🔴 RED    팀 결정이 필요한 충돌. 결정 요청 목록을 출력한다. 자동 교정하지 않는다.

RED가 하나라도 있으면 YELLOW가 있어도 RED로 판정한다 — 이름부터 고쳐봐야 소용없기 때문.
"""
import re
import subprocess
import sys
from pathlib import Path

GREEN, YELLOW, RED = 0, 1, 2

findings = []  # (level, 항목, 설명, 교정안 or None)


def finding(level, item, desc, fix=None):
    findings.append((level, item, desc, fix))


def norm(s):
    """이름 정규화 — 표기 변형(띄어쓰기·언더스코어·하이픈)을 같은 것으로 본다."""
    return re.sub(r"[\s_\-]", "", s).lower()


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


def parse_contract(path):
    """CONTRACT.md의 ```contract 블록을 읽는다."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"```contract\n(.*?)```", text, re.S)
    if not m:
        return None
    body = re.sub(r"#.*", "", m.group(1))  # 주석 제거
    c = {"tables": {}, "writers": {}, "chain": [], "payloads": [],
         "threshold": None, "halt_at": None}
    section = None
    for line in body.splitlines():
        if not line.strip():
            continue
        if re.match(r"^\w+:", line):
            key, val = line.split(":", 1)
            key, val = key.strip(), val.strip()
            if key in ("tables", "writers") and not val:
                section = key
                continue
            section = None
            if key == "chain":
                # 직선: 'a -> b -> c'
                # 갈림길: 경로를 ';'로 여러 개 적는다 'a -> b -> d; a -> c -> d'
                c["chain"] = [[s.strip() for s in path.split("->") if s.strip()]
                              for path in val.split(";") if path.strip()]
            elif key == "payloads":
                c["payloads"] = [s.strip() for s in val.split(",") if s.strip()]
            elif key in ("threshold", "halt_at"):
                c[key] = val
        elif section and ":" in line:
            k, v = line.split(":", 1)
            if section == "tables":
                c["tables"][k.strip()] = [x.strip() for x in v.split(",") if x.strip()]
            else:
                c["writers"][k.strip()] = v.strip()
    return c


def main(pack_dir, run_harness=False):
    pack = Path(pack_dir)
    contract_path = pack / "CONTRACT.md"
    if not contract_path.is_file():
        # 교안 폴더 트리에는 CONTRACT.md가 없다. 막기만 하지 말고 만드는 법을 보여준다.
        print(f"🔴 CONTRACT.md 없음: {pack}\n")
        print("   이름을 대조하려면 계약이 하나 필요합니다. 아래를 CONTRACT.md로 저장하고 채우세요:\n")
        print("   ```contract")
        print("   tables:")
        print("     표이름.xlsx: 칸1, 칸2")
        print("   writers:")
        print("     표이름.xlsx: 그 표에 기록하는 스킬 하나")
        print("   chain: 첫스킬 -> 다음스킬 -> 끝스킬     # 갈림길이면 ';'로 경로를 나눠 적습니다")
        print("   payloads: 주고받는 이름들")
        print("   threshold: ±15%")
        print("   halt_at: 사람이 확인하고 멈추는 스킬")
        print("   ```\n")
        print("   인터뷰 6문항의 ③데이터·④시나리오·⑥연동 답이 그대로 이 자리에 들어갑니다.")
        return RED
    c = parse_contract(contract_path)
    if not c:
        print("🔴 CONTRACT.md에 ```contract 블록이 없음")
        return RED

    skills = {}
    for p in sorted(pack.glob("skills/*/*/[sS][kK][iI][lL][lL].md")):
        meta, body = parse_skill(p)
        if meta is None:
            finding(RED, p.parent.name, "frontmatter 없음 — 계약 대조 불가")
            continue
        skills[meta.get("name", p.parent.name)] = (meta, body, p)
    if not skills:
        print("🔴 스킬을 찾지 못함 (skills/<사분면>/<이름>/skill.md)")
        return RED

    t_canon = {norm(t): t for t in c["tables"]}
    p_canon = {norm(x): x for x in c["payloads"]}

    # ── 1. 표 이름 대조 (frontmatter + 본문 둘 다 본다) ──
    for name, (meta, body, path) in skills.items():
        for field in ("reads", "writes"):
            for t in meta.get(field, []):
                if t in c["tables"]:
                    continue
                if norm(t) in t_canon:
                    finding(YELLOW, name, f"{field}의 표 이름이 계약과 표기가 다름: {t}",
                            (str(path), t, t_canon[norm(t)]))
                else:
                    finding(RED, name, f"{field}에 계약에 없는 표: {t} — 팀이 계약에 추가할지 결정 필요")
        # 이름은 반드시 문자로 시작한다 — 마크다운 불릿('- ')을 이름으로 삼지 않기 위함
        for t in set(re.findall(r"[\w가-힣]+(?:[ _\-][\w가-힣]+)*\.(?:xlsx|docx|pptx|pdf|csv)", body)):
            if t not in c["tables"] and norm(t) in t_canon:
                finding(YELLOW, name, f"본문의 표 이름 표기가 다름: {t}",
                        (str(path), t, t_canon[norm(t)]))

    # ── 2. 단일 기록자 (정규화해서 비교 — 표기 차이에 가려진 충돌을 잡는다) ──
    writers = {}
    for name, (meta, _, _) in skills.items():
        for t in meta.get("writes", []):
            writers.setdefault(norm(t), []).append(name)
    for nt, ws in writers.items():
        canon = t_canon.get(nt, nt)
        declared = c["writers"].get(canon)
        if len(ws) > 1:
            finding(RED, canon, f"기록자가 {len(ws)}명: {ws} — 계약상 기록자는 "
                                f"{declared or '미지정'}. 팀이 한 명으로 정해야 함")
        elif declared and ws[0] != declared:
            finding(RED, canon, f"계약상 기록자는 {declared}인데 {ws[0]}가 씀 — 담당 재확인 필요")

    # ── 3. 페이로드 이름 대조 ──
    for name, (meta, _, path) in skills.items():
        for field in ("inputs", "outputs"):
            for v in meta.get(field, []):
                if v in c["payloads"]:
                    continue
                if norm(v) in p_canon:
                    finding(YELLOW, name, f"{field}의 이름 표기가 다름: {v}",
                            (str(path), v, p_canon[norm(v)]))
                else:
                    finding(RED, name, f"{field}에 계약에 없는 이름: {v} — 팀이 페이로드를 정의해야 함")

    # ── 4. 흐름 (직선·갈림길 모두 허용) ──
    # 계약의 chain은 'a -> b -> c' 또는 갈림길이면 'a -> b | c' / 여러 줄을 ';'로 잇는다.
    edges, nodes_in_chain = set(), set()
    for path in c["chain"]:
        nodes_in_chain.update(path)
        edges.update(zip(path, path[1:]))

    for s in [s for s in skills if s not in nodes_in_chain]:
        finding(RED, s, "계약 흐름에 없는 스킬 — 어디에 넣을지 팀이 결정 필요")
    for s in [s for s in nodes_in_chain if s not in skills]:
        finding(RED, s, "계약에 있으나 제출되지 않은 스킬 — 담당자 확인 필요")
    for a, b in edges:
        if a in skills and b in skills:
            actual = [x.strip() for x in re.split(r"[|,]", skills[a][0].get("next") or "") if x.strip()]
            if b in actual:
                continue
            lvl = YELLOW if any(norm(x) == norm(b) for x in actual) else RED
            finding(lvl, a, f"next가 계약과 다름: {actual or '(없음)'} (계약: {b})",
                    (str(skills[a][2]), f"next: {skills[a][0].get('next')}",
                     f"next: {b}") if lvl == YELLOW else None)

    # ── 5. 임계값 (자유 서술도 잡는다) ──
    if c["threshold"]:
        want = re.sub(r"[^\d]", "", c["threshold"])
        for name, (_, body, _) in skills.items():
            nums = set(re.findall(r"(\d+)\s*%", body))
            wrong = nums - {want}
            if wrong:
                finding(RED, name, f"임계값이 계약({c['threshold']})과 다름: {sorted(wrong)}% "
                                   f"— 어느 값이 맞는지 팀이 정해야 함")
            elif nums and not re.search(r"±\s*" + want, body):
                finding(YELLOW, name, f"임계값 표기가 계약 형식(±{want}%)과 다름")

    # ── 6. 정지 지점 ──
    if c["halt_at"]:
        h = c["halt_at"]
        if h in skills:
            meta, body, _ = skills[h]
            if meta.get("writes"):
                finding(RED, h, f"정지 지점인데 표에 기록함: {meta['writes']} — 자동 발송 위험")
            if not ("확인" in body and "멈" in body):
                finding(YELLOW, h, "정지 지점인데 본문에 확인 요청·정지 문구가 없음")

    # ── 리포트 + 분기 ──
    reds = [f for f in findings if f[0] == RED]
    yellows = [f for f in findings if f[0] == YELLOW]

    print(f"계약: {contract_path}")
    print(f"제출 스킬 {len(skills)}개: {sorted(skills)}\n")
    if reds:
        print(f"🔴 팀 결정 필요 {len(reds)}건")
        for _, item, desc, _ in reds:
            print(f"  - [{item}] {desc}")
    if yellows:
        print(f"\n🟡 표기 교정 가능 {len(yellows)}건")
        for _, item, desc, _ in yellows:
            print(f"  - [{item}] {desc}")
    if not reds and not yellows:
        print("🟢 계약 준수 — 위반 없음")

    print("\n" + "=" * 55)
    if reds:
        verdict, code = "🔴 RED", RED
        print(f"{verdict} — 팀이 {len(reds)}건을 결정한 뒤 재검사하세요. 자동 교정하지 않습니다.")
        print("     (이름부터 고쳐도 소용없으므로 YELLOW 교정안도 만들지 않습니다)")
    elif yellows:
        verdict, code = "🟡 YELLOW", YELLOW
        rem = pack / "REMEDIATION.md"
        lines = ["# 계약 표기 교정안", "",
                 "기계가 제안하는 치환입니다. **확인 후 반영**하고 재검사하세요.", ""]
        for _, item, desc, fix in yellows:
            lines.append(f"- **{item}**: {desc}")
            if fix:
                lines.append(f"  - `{fix[0]}`: `{fix[1]}` → `{fix[2]}`")
        rem.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{verdict} — 교정안을 {rem}에 썼습니다. 반영 후 재검사하세요.")
    else:
        verdict, code = "🟢 GREEN", GREEN
        print(f"{verdict} — 계약 준수. 통합 점검기로 진행합니다.")

    if code == GREEN and run_harness:
        print("\n" + "─" * 55)
        print("→ 통합 점검기 실행\n")
        r = subprocess.run([sys.executable, str(Path(__file__).parent / "run_check.py"), str(pack)])
        return r.returncode
    if code != GREEN and run_harness:
        print("→ 계약 미준수이므로 점검기를 실행하지 않습니다.")
    return code


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.exit(main(args[0] if args else ".", "--run-check" in sys.argv))
