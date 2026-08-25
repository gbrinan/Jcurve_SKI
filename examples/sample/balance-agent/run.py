#!/usr/bin/env python3
"""재무1조 계정별 잔액 확인 에이전트 — 스킬 3개를 이어 실제로 실행한다.

skills/depth/{잔액표준화기, 이상잔액플래거} + skills/coil/잔액브리핑초안기 가
agent-plan.md 4절의 순서(1→2→3)대로 이어져, data/의 입력 하나에서 out/의 결과
하나를 낸다는 것을 증명하는 실행기다.

판단 기준은 CONTRACT.md의 threshold(±10%)를 그대로 따른다. 이상 여부의 확정과
발송은 사람 몫이므로 3단계에서 멈춘다.
"""
import csv, glob, os
from pathlib import Path

HERE = Path(__file__).parent
THRESHOLD = 0.10  # CONTRACT.md threshold: ±10%


def read_rows(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    data, out = HERE / "data", HERE / "out"
    out.mkdir(exist_ok=True)

    # ── 1) 잔액표준화기 — 원장 기준으로 계열사 잔액을 합산 ──────────────
    ledger_path = sorted(data.glob("원장잔액_*.csv"))[0]
    ledger = read_rows(ledger_path)
    std = {r["계정코드"]: {"계정코드": r["계정코드"], "계정명": r["계정명"],
                          "당기잔액": int(r["당기잔액"]), "전기잔액": int(r["전기잔액"]),
                          "출처수": 1} for r in ledger}

    affiliates = sorted(data.glob("계열사잔액_*.csv"))
    unmatched = []
    for ap in affiliates:
        for r in read_rows(ap):
            code = r["계정코드"]
            if code in std:                       # 판단기준: 원장에 있으면 합산
                std[code]["당기잔액"] += int(r["당기잔액"])
                std[code]["전기잔액"] += int(r["전기잔액"])
                std[code]["출처수"] += 1
            else:                                  # 판단기준: 없으면 미매칭 분리
                unmatched.append((ap.name, code, r["계정명"]))

    with open(out / "표준잔액표.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["계정코드", "계정명", "당기잔액", "전기잔액", "출처수"])
        w.writeheader()
        for v in std.values():
            w.writerow(v)
    with open(out / "미매칭목록.md", "w", encoding="utf-8") as f:
        f.write("# 미매칭 계정 — 원장에 없어 표에 넣지 않았습니다\n\n")
        for src, code, nm in unmatched:
            f.write(f"- {code} {nm} (출처: {src})\n")
        if not unmatched:
            f.write("- 없음\n")
    print(f"[1 잔액표준화기] 원장 {len(ledger)}계정 + 계열사 {len(affiliates)}개 파일 병합 "
          f"→ 표준 {len(std)}계정 · 미매칭 {len(unmatched)}건")

    # ── 2) 이상잔액플래거 — ±10% 초과 · 부호 반전 · 신규 ────────────────
    flagged = []
    for v in std.values():
        cur, prev = v["당기잔액"], v["전기잔액"]
        if prev == 0:
            flagged.append({**v, "증감률": "신규", "사유": "전기 값 0 — 신규 계정"})
            continue
        if (cur >= 0) != (prev >= 0):              # 판단기준: 부호 반전
            flagged.append({**v, "증감률": f"{(cur - prev) / abs(prev) * 100:+.1f}%",
                            "사유": "부호 반전"})
            continue
        rate = (cur - prev) / abs(prev)
        if abs(rate) > THRESHOLD:                  # 판단기준: ±10% 초과
            flagged.append({**v, "증감률": f"{rate * 100:+.1f}%",
                            "사유": f"증감률 ±{int(THRESHOLD*100)}% 초과"})

    with open(out / "이상후보목록.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["계정코드", "계정명", "전기", "당기", "증감률", "사유"])
        for r in flagged:
            w.writerow([r["계정코드"], r["계정명"], r["전기잔액"], r["당기잔액"],
                        r["증감률"], r["사유"]])
    print(f"[2 이상잔액플래거] {len(std)}계정 검사 → 이상 후보 {len(flagged)}건 "
          f"(임계 ±{int(THRESHOLD*100)}%)")

    # ── 3) 잔액브리핑초안기 — 초안까지. 발송하지 않는다 ─────────────────
    sign_first = sorted(flagged, key=lambda r: 0 if r["사유"] == "부호 반전" else 1)
    lines = ["# 계정별 잔액 검토 브리핑", "",
             "## ⚠️ 판단 포인트 (먼저 보세요)"]
    if sign_first:
        for r in sign_first:
            lines.append(f"- **{r['계정명']}**({r['계정코드']}) "
                         f"{r['전기잔액']:,} → {r['당기잔액']:,} ({r['증감률']}) — {r['사유']}")
    else:
        lines.append("- 이상 없음")
    lines += ["", "## 요약",
              f"- 표준 잔액표 {len(std)}계정 · 계열사 파일 {len(affiliates)}개 병합",
              f"- 이상 후보 {len(flagged)}건 (임계 ±{int(THRESHOLD*100)}%)",
              f"- 미매칭 계정 {len(unmatched)}건 — 미매칭목록.md 참조", "",
              "> 원인 확인과 확정은 결산담당이 합니다.",
              "> **에이전트는 여기서 멈춥니다. 어떤 것도 자동 발송되지 않았습니다.**"]
    (out / "검토브리핑.md").write_text("\n".join(lines), encoding="utf-8")

    (out / "메일초안.md").write_text(
        "제목: [분기결산] 계정별 잔액 확인 — 이상 후보 "
        f"{len(flagged)}건 검토 요청\n\n받는사람: 회계관리팀장\n\n"
        "안녕하십니까,\n분기 결산 잔액 확인 결과를 공유드립니다. "
        "이상 후보 항목은 첨부 브리핑을 참고 부탁드립니다.\n\n"
        "첨부:\n- 검토브리핑.md\n- 이상후보목록.csv\n\n감사합니다.\n",
        encoding="utf-8")
    print(f"[3 잔액브리핑초안기] 브리핑·메일 초안 생성 — 판단 포인트 {len(flagged)}건. 발송하지 않음")

    print("\n" + "=" * 52)
    print(f"산출물: {sorted(p.name for p in out.iterdir())}")
    print("자동 발송 여부: 없음 (out/ 에 초안만 존재)")
    print("다음: 결산담당이 검토브리핑.md 를 확인하고 직접 공유합니다")


if __name__ == "__main__":
    main()
