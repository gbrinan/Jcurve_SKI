#!/usr/bin/env python3
"""상류 어댑터 — 코치 산출물을 통합 팩으로 변환한다.

사용: python3 check/adapt_upstream.py <와이어프레임 폴더> <ATF html> <출력 팩 경로> [팀흐름표.md]

입력:
  · 와이어프레임 코치 v9.1 → `WFDATA` 블록 (참가자 1인 = 파일 1개)
  · ATF 코치 v3.0 → HTML 안의 `atf-data` JSON
  · (선택) 팀 흐름표 — 스킬 사이를 잇는 정보의 운반책. 원본(디자인캠프 Process Flow)에는
    분기(◆)와 루프백(↩)이 글로 적혀 있는데 와이어프레임 단계에서 죽는다 —
    참가자는 각자 자기 LV6 하나만 그리기 때문이다. 팀 흐름표가 그것을 여기까지 나른다.

팀 흐름표 문법 (한 줄에 하나, 스킬 이름은 WFDATA의 skill과 같아야 한다):
    스킬A -> 스킬B              앞으로 잇기
    스킬A -> 스킬B | 스킬C      갈림길
    스킬A ? <조건 문장>          갈림길 조건 (원본 흐름도의 ◆를 그대로 옮긴다)
    스킬A ↩ 스킬B (탈출: 조건)   루프백 — 반려·재작업으로 되돌아가기

출력: skills/·CONTRACT.md 초안·agent-plan.md 초안을 갖춘 팩.

★ 흐름표가 없으면 chain은 (미정)으로 남는다. 지어내면 통합이 거짓으로 통과한다.
"""
import json
import re
import sys
from pathlib import Path

# 환경 태그(sug) → 우리 팩의 읽기/쓰기 의미
LANE = {"rd": "MCP·조회", "wr": "MCP·작성", "cdx": "코덱스", "api": "API", "hm": "사람"}
# paperthin 사분면 추정 — 상류에 없으므로 노드 구성으로 유추한다
def quadrant(nodes):
    lanes = {n.get("sug") for n in nodes}
    if "wr" in lanes:
        return "breadth"          # 바깥에 쓰는 것이 있으면 여러 산출물을 가로지른다
    if "hm" in lanes:
        return "coil"             # 사람 확인이 끼면 주기적으로 도는 흐름
    return "depth"


def load_wfdata(path):
    m = re.search(r"<!--WFDATA\s*(\{.*?\})\s*-->", path.read_text(encoding="utf-8"), re.S)
    if not m:
        return None, f"{path.name}: WFDATA 블록 없음"
    try:
        return json.loads(m.group(1)), None
    except json.JSONDecodeError as e:
        return None, f"{path.name}: WFDATA가 유효한 JSON이 아님 — {e}"


def load_atf(path):
    m = re.search(r'id="atf-data"[^>]*>\s*(\{.*?\})\s*</script>',
                  path.read_text(encoding="utf-8"), re.S)
    if not m:
        return None, "atf-data 블록 없음"
    try:
        return json.loads(m.group(1)), None
    except json.JSONDecodeError as e:
        return None, f"atf-data가 유효한 JSON이 아님 — {e}"


def load_flow(path):
    """팀 흐름표 파싱 → (next 맵, when 맵, loop 맵). 이름은 공백 무시로 대조한다."""
    nxt, when, loop = {}, {}, {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "↩" in line:
            m = re.match(r"(.+?)↩(.+?)(?:\(탈출:(.+?)\))?$", line)
            if m:
                loop[m.group(1).strip()] = (m.group(2).strip(),
                                            (m.group(3) or "(미정)").strip())
        elif "?" in line and "->" not in line.split("?")[0]:
            a, cond = line.split("?", 1)
            when[a.strip()] = cond.strip()
        elif "->" in line:
            a, bs = line.split("->", 1)
            nxt.setdefault(a.strip(), []).extend(x.strip() for x in bs.split("|") if x.strip())
    return nxt, when, loop


def main(wf_dir, atf_path, out_dir, flow_path=None):
    wf_dir, out = Path(wf_dir), Path(out_dir)
    notes, blockers = [], []

    flow_nxt, flow_when, flow_loop = ({}, {}, {})
    if flow_path:
        flow_nxt, flow_when, flow_loop = load_flow(flow_path)

    atf, err = load_atf(Path(atf_path))
    if err:
        blockers.append(err)
        atf = {}

    frames = []
    for p in sorted(wf_dir.glob("*.md")):
        d, err = load_wfdata(p)
        if err:
            blockers.append(err)
            continue
        frames.append(d)
    if not frames:
        print("❌ 변환할 WFDATA가 없습니다")
        return 1

    out.mkdir(parents=True, exist_ok=True)
    (out / "data").mkdir(exist_ok=True)
    payload_names, skill_names = set(), []

    # 흐름표 이름 대조 준비 — 공백 차이로 못 알아보는 일이 없게 한다
    canon = lambda s: (s or "").replace(" ", "")
    by_canon = {canon(d.get("skill") or d.get("lv6")): d for d in frames}
    lasts = {canon(d.get("skill") or d.get("lv6")):
             (d["N"][-1]["n"] if d.get("N") else "(미정)") for d in frames}

    def flow_lookup(table, name):
        for k, v in table.items():
            if canon(k) == canon(name):
                return v
        return None

    unknown_flow = [k for k in list(flow_nxt) + list(flow_loop)
                    if canon(k) not in by_canon]
    for k, vs in flow_nxt.items():
        unknown_flow += [v for v in vs if canon(v) not in by_canon]
    if unknown_flow:
        blockers.append(f"팀 흐름표에 와이어프레임에 없는 스킬 이름: {sorted(set(unknown_flow))}")

    # 앞선 스킬(preds): 흐름표의 -> 를 뒤집는다. 뒤 스킬의 inputs에 앞 스킬의 끝 노드를 넣어
    # 점검기 L3의 '흐름 정합'(outputs∩inputs)이 실제로 검사되게 한다 — 이름은 지어내지 않고
    # 와이어프레임의 노드 이름을 그대로 쓴다.
    preds = {}
    for a, bs in flow_nxt.items():
        for b in bs:
            preds.setdefault(canon(b), []).append(canon(a))

    for d in frames:
        nodes = d.get("N", [])
        name = d.get("skill") or d.get("lv6")
        skill_names.append(name)
        q = quadrant(nodes)
        sdir = out / "skills" / q / name.replace(" ", "")
        sdir.mkdir(parents=True, exist_ok=True)

        # 인풋/아웃풋: 상류에 정본 이름이 없다. 첫 노드·끝 노드 이름에서 유추하고 (미정) 표시
        first, last = (nodes[0]["n"] if nodes else "(미정)"), (nodes[-1]["n"] if nodes else "(미정)")
        payload_names.update([first, last])
        # 흐름표가 있으면 앞 스킬들의 끝 노드도 입력으로 받는다 (정합 검사를 살리기 위해)
        ins = [first] + [lasts[p] for p in preds.get(canon(name), []) if p in lasts]
        ins = list(dict.fromkeys(ins))

        # ★ 환경 태그는 "어떤 수단으로"이지 "어떤 표에"가 아니다. 표 이름으로 삼지 않는다.
        #   상류에는 표·칸 명세가 없으므로 reads/writes는 비우고, 수단은 environment로 따로 적는다.
        env = sorted({LANE[n["sug"]] for n in nodes if n.get("sug") in LANE})
        reads, writes = [], []
        api_nodes = [n["n"] for n in nodes if n.get("sug") == "api"]
        human_nodes = [n["n"] for n in nodes if n.get("sug") == "hm"]

        body = [f"# {name}", "",
                f"> 상류: 와이어프레임 `{d.get('id')}` · 담당 {d.get('owner')} · "
                f"업무 Lv6 「{d.get('lv6')}」", ""]
        body.append("## 판단기준·예외 (와이어프레임에서 옮김)")
        for n in nodes:
            tag = LANE.get(n.get("sug"), "?")
            body.append(f"- **{n['n']}** [{tag}] — {n.get('rule', '—')}")
            if n.get("exc") and n["exc"] != "—":
                body.append(f"  - 예외: {n['exc']}")
        if api_nodes:
            body += ["", "## ⚠️ 오늘 실행 불가",
                     f"- {', '.join(api_nodes)} — `[API] (IT요청)`. 이 자리는 사람이 수기로 처리한다."]
            notes.append(f"{name}: API 노드 {api_nodes} — 실행 불가 구간 포함")
        if human_nodes:
            body += ["", "## 사람이 확인하고 멈추는 지점",
                     f"- {', '.join(human_nodes)} — 여기서 확인을 요청하고 멈춘다. 자동 발송하지 않는다."]

        nx = flow_lookup(flow_nxt, name)
        lp = flow_lookup(flow_loop, name)
        wh = flow_lookup(flow_when, name)
        fm = ["---", f"name: {name}", f"owner: {d.get('owner')}", f"quadrant: {q}",
              f"environment: [{', '.join(env)}]",
              f"inputs: [{', '.join(ins)}]", f"outputs: [{last}]",
              "reads: []", "writes: []",   # 표 이름은 세션 6 인터뷰에서 확정한다
              # 흐름표가 없으면 (미정) — 지어내지 않는다. 있으면 분기·루프백까지 그대로 옮긴다.
              f"next: {' | '.join(nx) if nx else ('null' if flow_path else '(미정)')}"]
        if lp:
            fm += [f"loop_to: {lp[0]}", f"loop_exit: {lp[1]}"]
        if wh:
            fm.append(f"when: {wh}")
        fm += ["---", ""]
        if lp:
            body += ["", "## 되돌아가기 (루프백)",
                     f"- {lp[0]}(으)로 되돌아갈 수 있다 — 반려·재작업 흐름.",
                     f"- 반복이 끝나는 조건: {lp[1]}"]
        if wh:
            body += ["", "## 갈림길 조건 (팀 흐름표에서 옮김)", f"- {wh}"]
        (sdir / "skill.md").write_text("\n".join(fm + body) + "\n", encoding="utf-8")

    # CONTRACT 초안 — 이을 수 없는 자리는 (미정). 흐름표가 있으면 경로를 펼쳐 적는다.
    if flow_nxt:
        cn = {canon(n): n for n in skill_names}
        fw = {canon(a): [canon(b) for b in bs] for a, bs in flow_nxt.items()}
        tg = {b for bs in fw.values() for b in bs}
        st = [canon(n) for n in skill_names if canon(n) not in tg]
        routes = []
        def walk(c, acc):
            if c in acc:
                routes.append(acc + [c]); return
            acc = acc + [c]
            if not fw.get(c):
                routes.append(acc); return
            for b in fw[c]:
                walk(b, acc)
        for s in st:
            walk(s, [])
        chain_line = "; ".join(" -> ".join(cn.get(c, c).replace(" ", "") for c in r)
                               for r in routes)
        # 끝점 + 사람 확인 스킬을 정지 지점으로
        ends = [cn.get(c, c).replace(" ", "") for c in {r[-1] for r in routes}]
        halt_line = ", ".join(sorted(set(ends)))
    else:
        chain_line = " -> ".join("(미정)" for _ in skill_names)
        halt_line = "(미정)"
    contract = ["# 통합 계약 (어댑터 초안 — 팀이 채워야 함)", "",
                "상류 코치 산출물에서 뽑을 수 있는 것만 채웠다. `(미정)`은 통합 시 팀이 정한다."
                + (" 흐름(chain·halt_at)은 팀 흐름표에서 옮겼다." if flow_nxt else ""), "",
                "```contract", "tables:", "  (미정): (상류에 표·칸 명세가 없음)",
                "writers:", "  (미정): (미정)",
                f"chain: {chain_line}",
                f"payloads: {', '.join(sorted(payload_names))}",
                f"threshold: (미정)", f"halt_at: {halt_line}", "```", ""]
    (out / "CONTRACT.md").write_text("\n".join(contract), encoding="utf-8")

    # agent-plan 초안 — ATF 판정을 그대로 옮긴다
    gates = atf.get("gates", {})
    plan = [f"# {atf.get('process', '(미정)')} 팀 에이전트 기획서 (어댑터 초안)", "",
            f"## 판정 (ATF 코치)", f"- verdict: **{atf.get('verdict', '(미정)')}**",
            f"- 조건: {atf.get('condition') or '—'}",
            f"- 사용 범위: {atf.get('wrap', '(미정)')} · 주당 {atf.get('hoursPerWeek', '(미정)')}시간", "",
            "## 6기준", "| 기준 | 판정 |", "|---|---|"]
    labels = {"G1": "반복성", "G2": "위임 가능성", "G3": "다단계성",
              "G4": "순서 가변성", "G5": "가치", "G6": "검증 가능성"}
    for k, v in gates.items():
        plan.append(f"| {labels.get(k, k)} | {v} |")
    plan += ["", "## 2. 스킬 구성 (와이어프레임에서 옮김)"]
    for d in frames:
        nm = d.get("skill") or d.get("lv6")
        nx = flow_lookup(flow_nxt, nm)
        lp = flow_lookup(flow_loop, nm)
        line = f"- **{nm}** — 담당 {d.get('owner')} · Lv6 「{d.get('lv6')}」"
        if nx:
            line += f" → {' 또는 '.join(nx)}"
        if lp:
            line += f" (↩ {lp[0]}로 루프백, 탈출: {lp[1]})"
        plan.append(line)
    plan += ["", "## 3. 데이터 명세", "| 표 이름 | 칸 이름 | 원본 위치(SSOT) | 읽기/쓰기 |", "|---|---|---|---|",
             "| (미정) | (미정) | (미정) | (미정) |",
             "", "> 상류(와이어프레임·ATF)에는 표·칸 명세가 없다. 세션 6 인터뷰에서 확정한다.", ""]
    if flow_nxt:
        first_frame = frames[0].get("N", [{}])
        start_input = first_frame[0].get("n", "(미정)") if first_frame else "(미정)"
        plan += ["## 4. 대표 시나리오 (팀 흐름표에서 옮김)",
                 f"- 입력: {start_input}"]
        plan += [f"- 경로: {' → '.join(cn.get(c, c) for c in r)}"
                 f" → 산출물: {lasts.get(r[-1], '(미정)')}" for r in routes]
        plan += [""]
    else:
        plan += ["## 4. 대표 시나리오",
                 "- (미정) — 스킬 간 연결 정보가 없음. 팀 흐름표를 주면 채워진다.", ""]
    (out / "agent-plan.md").write_text("\n".join(plan), encoding="utf-8")
    (out / "AGENTS.md").write_text("# 페르소나\n- (미정) — 세션 6에서 작성\n", encoding="utf-8")
    (out / "README.md").write_text(
        f"# {atf.get('process', '팀')} 에이전트\n\n상세는 [agent-plan.md](agent-plan.md) 참조.\n",
        encoding="utf-8")

    print(f"변환 완료: 스킬 {len(frames)}개 → {out}")
    print(f"  스킬: {skill_names}")
    if notes:
        print("\n⚠️ 상류가 실행 불가로 표시한 구간:")
        for n in notes:
            print(f"  - {n}")
    print("\n🔻 어댑터가 채울 수 없어 (미정)으로 남긴 것 — 상류에 정보가 없음:")
    if flow_nxt:
        print("  - chain / halt_at: 팀 흐름표에서 채웠음 ✅"
              + (f" (갈림길 {sum(1 for v in flow_nxt.values() if len(v) > 1)}곳,"
                 f" 루프백 {len(flow_loop)}곳)" if flow_loop or
                 any(len(v) > 1 for v in flow_nxt.values()) else ""))
    else:
        print("  - chain (스킬 사이 순서): 참가자는 각자 LV6 하나만 그린다."
              " 팀 흐름표를 4번째 인자로 주면 채워진다")
    print("  - tables / writers (표 이름·칸·기록자): 상류에 데이터 명세 자체가 없음")
    print("  - threshold: 와이어프레임의 예외 문장에는 있으나 정본 형식이 아님")
    if blockers:
        print("\n❌ 변환 실패 항목:")
        for b in blockers:
            print(f"  - {b}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(*sys.argv[1:5]))
