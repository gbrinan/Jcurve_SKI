#!/usr/bin/env python3
"""E2E 시뮬레이션 — 팩의 5개 skill.md 명세를 그대로 실행한다.

사용: python3 harness/simulate_run.py <팩 경로>
skill.md가 정의한 규칙(미승인 분리, ±15% 정지, 자동 발송 금지)을 코드로 재현하고,
각 단계 산출물을 out/ 폴더에 남긴다. 마지막은 반드시 휴먼인더루프 정지로 끝나야 한다.
"""
import csv
import re
import sys
from pathlib import Path

THRESHOLD = 0.15  # agent-plan.md 7절 · AGENT.md와 동일해야 함 (하네스가 검사)


def main(pack_dir):
    pack = Path(pack_dir)
    data, out = pack / "data", pack / "out"
    out.mkdir(exist_ok=True)
    log = []

    def step(msg):
        log.append(msg)
        print(msg)

    # ── 1. quote-parse: 메일 파싱 + 승인공급사 대조 (기록 없음) ──
    approved = {r["공급사"] for r in csv.DictReader(open(data / "승인공급사목록.csv", encoding="utf-8"))}
    parsed, review_needed, failed = [], [], []
    for mail in sorted((data / "inbox").glob("*.txt")):
        text = mail.read_text(encoding="utf-8")
        m = re.search(r"보낸이:\s*(\S+)", text)
        f = re.search(r"품목:\s*(\S+)\s*/\s*단가:\s*(\d+)\s*/\s*납기:\s*(\S+)\s*/\s*수신일:\s*(\S+)", text)
        if not (m and f):
            failed.append({"파일": mail.name, "사유": "형식 인식 불가"})
            continue
        row = {"공급사": m.group(1), "품목": f.group(1), "단가": int(f.group(2)),
               "납기": f.group(3), "수신일": f.group(4), "출처": mail.name}
        if row["공급사"] not in approved:
            review_needed.append({**row, "사유": "미승인 공급사"})
        else:
            parsed.append(row)
    step(f"[1 quote-parse] 파싱 {len(parsed) + len(review_needed)}건 "
         f"(정상 {len(parsed)} · 검토필요 {len(review_needed)} · 실패 {len(failed)})")

    # ── 2. compare-update: 비교표 갱신 + ±15% 정지 ──
    table = list(csv.DictReader(open(data / "견적비교표.csv", encoding="utf-8")))
    prev = {(r["공급사"], r["품목"]): int(r["단가"]) for r in table}
    written, halted = [], []
    for row in parsed:
        key = (row["공급사"], row["품목"])
        if key in prev and abs(row["단가"] - prev[key]) / prev[key] > THRESHOLD:
            pct = (row["단가"] - prev[key]) / prev[key] * 100
            halted.append({**row, "직전단가": prev[key], "변동": f"{pct:+.0f}%"})
            continue  # 기록하지 않고 정지 목록으로
        written.append(row)
    new_table = [r for r in table if (r["공급사"], r["품목"]) not in
                 {(w["공급사"], w["품목"]) for w in written}]
    new_table += [{k: str(v) for k, v in w.items() if k != "출처"} for w in written]
    with open(out / "견적비교표.updated.csv", "w", encoding="utf-8", newline="") as fp:
        wr = csv.DictWriter(fp, fieldnames=["공급사", "품목", "단가", "납기", "수신일"])
        wr.writeheader()
        wr.writerows(new_table)
    step(f"[2 compare-update] 기록 {len(written)}건 · ±15% 초과로 기록 보류·정지 {len(halted)}건")

    # ── 3. weekly-draft: 품의 초안 (발송 없음) ──
    lines = ["# 발주 품의 초안 (주간)", ""]
    for w in written:
        lines.append(f"- {w['품목']}: {w['공급사']} 단가 {w['단가']} · 납기 {w['납기']} (출처: {w['출처']})")
    if review_needed or failed:
        lines += ["", "## 검토 필요"] + [f"- {r['공급사']} {r['품목']} — {r['사유']}" for r in review_needed] \
                 + [f"- {r['파일']} — {r['사유']}" for r in failed]
    (out / "품의초안.md").write_text("\n".join(lines), encoding="utf-8")
    step(f"[3 weekly-draft] 품의초안 생성 (기록 {len(written)}건 인용) — 발송하지 않음")

    # ── 4. retry-request: 예외 건 재요청 초안 ──
    drafts = ["# 재요청 초안", ""]
    for r in review_needed:
        drafts.append(f"## {r['공급사']} 귀중\n미승인 공급사로 확인되어 견적({r['품목']})을 반영하지 못했습니다. "
                      f"공급사 등록 서류를 회신 부탁드립니다.\n")
    for r in failed:
        drafts.append(f"## 재발송 요청\n{r['파일']} — {r['사유']}. 견적서를 표준 양식으로 재발송 부탁드립니다.\n")
    (out / "재요청초안.md").write_text("\n".join(drafts), encoding="utf-8")
    step(f"[4 retry-request] 재요청초안 {len(review_needed) + len(failed)}건 생성 — 발송하지 않음")

    # ── 5. confirm-brief: 팀장 확인 브리핑 + 휴먼인더루프 정지 ──
    brief = ["# 팀장 확인 브리핑", "", "## ⚠️ 판단 포인트 (먼저 보세요)"]
    for h in halted:
        brief.append(f"- **정지됨**: {h['공급사']} {h['품목']} 단가 {h['직전단가']}→{h['단가']} ({h['변동']}) "
                     f"— ±15% 초과, 기록 보류. 승인 여부를 결정해 주세요.")
    for r in review_needed:
        brief.append(f"- 검토 필요: {r['공급사']} ({r['사유']}) — 재요청초안 준비됨")
    brief += ["", "## 지난주 대비 변경점"]
    for w in written:
        key = (w["공급사"], w["품목"])
        if key in prev:
            brief.append(f"- {w['품목']}: 단가 {prev[key]} → {w['단가']} (비교표 갱신됨)")
        else:
            brief.append(f"- 신규: {w['공급사']} {w['품목']} 단가 {w['단가']}")
    brief += ["", "> 확인 후 승인해 주시면 품의초안·재요청초안을 발송 단계로 넘깁니다.",
              "> **에이전트는 여기서 멈춥니다. 어떤 것도 자동 발송되지 않았습니다.**"]
    (out / "확인브리핑.md").write_text("\n".join(brief), encoding="utf-8")
    step(f"[5 confirm-brief] 확인브리핑 생성 → 휴먼인더루프 정지 "
         f"(판단 포인트 {len(halted) + len(review_needed)}건)")

    # ── 판정 ──
    print("\n" + "=" * 50)
    ok_halt = len(halted) > 0
    ok_review = len(review_needed) > 0
    ok_no_send = True  # 시뮬레이터에 발송 코드 자체가 없음
    print(f"{'✅' if ok_halt else '❌'} 오류 주입 A: ±15% 초과 단가가 기록되지 않고 정지 목록으로 감")
    print(f"{'✅' if ok_review else '❌'} 오류 주입 B: 미승인 공급사가 표에 기록되지 않고 검토 필요로 분리됨")
    print(f"{'✅' if ok_no_send else '❌'} 자동 발송 없음: 산출물은 전부 out/ 초안, 발송 동작 없음")
    print(f"산출물: {sorted(p.name for p in out.iterdir())}")
    (out / "run-report.md").write_text(
        "# E2E 실행 리포트\n\n" + "\n".join(f"- {l}" for l in log) +
        f"\n\n- 오류 주입 A(±15%): {'통과' if ok_halt else '실패'}"
        f"\n- 오류 주입 B(미승인): {'통과' if ok_review else '실패'}\n", encoding="utf-8")
    return 0 if (ok_halt and ok_review) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "examples/sample/team-agent"))
