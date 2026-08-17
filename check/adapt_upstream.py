#!/usr/bin/env python3
"""상류 어댑터 — 코치 산출물을 통합 팩으로 변환한다.

사용: python3 check/adapt_upstream.py <와이어프레임 폴더> <ATF html> <출력 팩 경로>

입력:
  · 와이어프레임 코치 v9.1 → `WFDATA` 블록 (참가자 1인 = 파일 1개)
  · ATF 코치 v3.0 → HTML 안의 `atf-data` JSON

출력: skills/·CONTRACT.md 초안·agent-plan.md 초안을 갖춘 팩.

★ 어댑터가 만들 수 없는 것이 있다. 상류에는 **스킬 사이를 잇는 정보가 없다** —
   참가자는 각자 자기 LV6 하나만 그리므로 WFDATA에 next도, 공유 페이로드 이름도 없다.
   그 자리는 (미정)으로 남기고 리포트에 적는다. 지어내면 통합이 거짓으로 통과한다.
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


def main(wf_dir, atf_path, out_dir):
    wf_dir, out = Path(wf_dir), Path(out_dir)
    notes, blockers = [], []

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

        fm = ["---", f"name: {name}", f"owner: {d.get('owner')}", f"quadrant: {q}",
              f"environment: [{', '.join(env)}]",
              f"inputs: [{first}]", f"outputs: [{last}]",
              "reads: []", "writes: []",   # 표 이름은 세션 6 인터뷰에서 확정한다
              "next: (미정)", "---", ""]
        (sdir / "skill.md").write_text("\n".join(fm + body) + "\n", encoding="utf-8")

    # CONTRACT 초안 — 이을 수 없는 자리는 (미정)
    contract = ["# 통합 계약 (어댑터 초안 — 팀이 채워야 함)", "",
                "상류 코치 산출물에서 뽑을 수 있는 것만 채웠다. `(미정)`은 통합 시 팀이 정한다.", "",
                "```contract", "tables:", "  (미정): (상류에 표·칸 명세가 없음)",
                "writers:", "  (미정): (미정)",
                f"chain: {' -> '.join('(미정)' for _ in skill_names)}",
                f"payloads: {', '.join(sorted(payload_names))}",
                "threshold: (미정)", "halt_at: (미정)", "```", ""]
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
    plan += ["", "## 3. 데이터 명세", "| 표 이름 | 칸 이름 | 원본 위치(SSOT) | 읽기/쓰기 |", "|---|---|---|---|",
             "| (미정) | (미정) | (미정) | (미정) |",
             "", "> 상류(와이어프레임·ATF)에는 표·칸 명세가 없다. 세션 6 인터뷰에서 확정한다.", "",
             "## 4. 대표 시나리오", "- (미정) — 상류에 스킬 간 연결 정보가 없음", ""]
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
    print("  - chain (스킬 사이 순서): 참가자는 각자 LV6 하나만 그린다")
    print("  - tables / writers (표 이름·칸·기록자): 상류에 데이터 명세 자체가 없음")
    print("  - threshold / halt_at: 와이어프레임의 예외 문장에는 있으나 정본 형식이 아님")
    if blockers:
        print("\n❌ 변환 실패 항목:")
        for b in blockers:
            print(f"  - {b}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(*sys.argv[1:4]))
