#!/usr/bin/env python3
"""E2E 시뮬레이션 — 7개 SKILL.md의 명세를 그대로 실행한다.

사용: python3 examples/sample/medical-expense-agent/run.py

한 묶음의 청구 건이 「지급기준대조」에서 **셋으로 갈라져** 서로 다른 out/ 파일로 떨어지는 것을
눈으로 확인하는 것이 목적이다. 지급 실행·발송 코드는 없다 — 사람고유 지점에서 멈춘다.
"""
import csv
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
DATA, OUT = PACK / "data", PACK / "out"

for cand in (PACK.parents[2] / "check", PACK.parent / "check", PACK / "check"):
    if (cand / "trace.py").is_file():
        sys.path.insert(0, str(cand))
        break
else:
    sys.exit("trace.py를 찾지 못했습니다 — 툴킷의 check/ 폴더가 있어야 합니다.")
from trace import Trace   # noqa: E402

TR = None           # main()에서 Trace로 채운다. 목업 화면이 읽는 기록.


def step(skill, msg):
    print(f"  [{skill}] {msg}")


def load(name):
    with (DATA / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(name, rows, cols):
    OUT.mkdir(exist_ok=True)
    with (OUT / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"  → out/{name} ({len(rows)}건)")


# ── 1. 증빙서류판독 [자동] ─────────────────────────────────────────────
def 증빙서류판독(claims):
    out = []
    for c in claims:
        판독불가 = ("영수증" not in c["증빙유형"]) or not c["증빙파일"].strip() \
                   or int(c["청구금액"]) <= 0
        out.append({**c,
                    "중증후보": "Y" if c["진단코드"].startswith("C") else "N",
                    "상태": "판독불가" if 판독불가 else "판독완료"})
    n = sum(1 for r in out if r["상태"] == "판독불가")
    step("증빙서류판독", f"{len(out)}건 판독 · 판독불가 {n}건 (금액을 추정하지 않음)")
    TR.step("1. 증빙서류판독", "자동",
            f"{len(out)}건 판독. 그중 **{n}건은 판독불가**입니다 — 증빙유형에 「영수증」이 없거나 "
            f"증빙파일 칸이 비어 있습니다.")
    TR.warn("금액을 추정하지 않았습니다. 규칙: 증빙유형에 「영수증」이 없으면 판독 불가로 표시한다.")
    return out


# ── 2. 신청서생성 [자동] → 신청서초안.csv ──────────────────────────────
COLS_신청 = ["청구번호", "사번", "성명", "청구금액", "진단코드", "중증후보", "상태"]


def 신청서생성(read):
    seen, rows = set(), []
    for r in read:
        상태 = "중복" if r["청구번호"] in seen else r["상태"]
        seen.add(r["청구번호"])
        rows.append({k: r.get(k, "") for k in COLS_신청} | {"상태": 상태})
    step("신청서생성", f"신청서초안 {len(rows)}행 (판독불가 건도 버리지 않고 상태로 남김)")
    TR.step("2. 신청서생성", "자동",
            f"신청서초안 **{len(rows)}행**을 만들었습니다. 판독불가 건도 버리지 않고 상태 칸에 남겼습니다.")
    TR.file("out/신청서초안.csv", len(rows))
    write("신청서초안.csv", rows, COLS_신청)
    return rows


# ── 3. 지급기준대조 [증강] ── 갈림길 ───────────────────────────────────
def 기준항목(claim, rules):
    """진단코드·병원명으로 기준항목 하나를 고른다. 못 고르면 None (→ 예외심사)."""
    if claim["진단코드"].startswith("C"):
        return next(r for r in rules if r["기준항목"] == "중증질환")
    if claim["진단코드"].startswith("K0"):
        return next(r for r in rules if r["기준항목"] == "치과보철")
    if claim["진단코드"].startswith("H5"):
        return next(r for r in rules if r["기준항목"] == "시력교정")
    if claim["진단코드"][:1] in "JMIK":
        return next(r for r in rules if r["기준항목"] == "일반진료")
    return None


def 지급기준대조(신청, claims, rules):
    by_no = {c["청구번호"]: c for c in claims}
    지급, 보완, 예외 = [], [], []
    for r in 신청:
        c = by_no[r["청구번호"]]
        if r["상태"] in ("판독불가", "중복"):
            보완.append({**c, "사유": "필수 증빙(영수증) 누락 — 금액 판정을 하지 않음"})
            continue
        rule = 기준항목(c, rules)
        if rule is None:
            예외.append({**c, "예외사유": "기준항목 특정 불가",
                        "심사근거": f"진단코드 {c['진단코드']} — 지급기준표에 해당 항목 없음"})
            continue
        금액, 한도 = int(c["청구금액"]), int(rule["연간한도"])
        부담률 = float(rule["자기부담률"])
        지급액 = int(금액 * (1 - 부담률))
        if 부담률 >= 1.0:
            예외.append({**c, "예외사유": rule["기준항목"],
                        "심사근거": f"{rule['비고']} (자기부담률 100%)"})
        elif c["수진자관계"] not in rule["적용대상"].split("/"):
            예외.append({**c, "예외사유": rule["기준항목"],
                        "심사근거": f"수진자관계 '{c['수진자관계']}'는 적용대상({rule['적용대상']}) 아님"})
        elif 금액 > 한도:
            예외.append({**c, "예외사유": rule["기준항목"],
                        "심사근거": f"청구 {금액:,}원 > 연간한도 {한도:,}원"})
        elif 지급액 > 한도 * 0.8:
            예외.append({**c, "예외사유": rule["기준항목"],
                        "심사근거": f"지급액 {지급액:,}원이 한도의 80%({int(한도*0.8):,}원) 초과"})
        else:
            지급.append({**c, "기준항목": rule["기준항목"],
                        "자기부담률": rule["자기부담률"], "지급액": 지급액})
    step("지급기준대조", f"◆ 갈림길 — 자동지급 {len(지급)}건 / 보완요청 {len(보완)}건 / 예외심사 {len(예외)}건")
    TR.fork("3. 지급기준대조", "증강",
            [("기준 충족", "자동지급상신", len(지급)),
             ("증빙 미비", "보완요청작성", len(보완)),
             ("모호 · 한도 초과", "예외심사요청", len(예외))],
            note="지급기준표.csv와 대조해 **세 갈래로 갈랐습니다.**")
    TR.warn("판단이 서지 않는 건은 자동지급 쪽으로 기울이지 않고 예외심사로 보냅니다. "
            "규칙: 기준항목을 하나로 정할 수 없으면 자동지급상신으로 보내지 않는다.")
    return 지급, 보완, 예외


# ── 4. 자동지급상신 [자동] → 지급대장.csv ──────────────────────────────
COLS_지급 = ["청구번호", "사번", "성명", "청구금액", "자기부담률", "지급액", "기준항목", "상태"]


def 자동지급상신(지급, 예외):
    rows = []
    for r in 지급:
        if r["지급액"] <= 0:                      # SKILL.md의 예외 규칙
            예외.append({**r, "예외사유": r["기준항목"], "심사근거": "지급액 0원"})
            continue
        rows.append({k: r.get(k, "") for k in COLS_지급} | {"상태": "승인대기"})
    step("자동지급상신", f"{len(rows)}건 상신 · 상태는 전부 '승인대기' (지급 실행 아님)")
    TR.step("4. 자동지급상신", "자동",
            f"{len(rows)}건을 지급대장에 올렸습니다. 상태는 전부 **승인대기**입니다 — "
            f"지급이 실행된 것이 아닙니다.")
    TR.table("지급대장", rows,
             ["청구번호", "성명", "기준항목", "청구금액", "지급액", "상태"])
    TR.file("out/지급대장.csv", len(rows))
    write("지급대장.csv", rows, COLS_지급)
    return rows


# ── 5. 보완요청작성 [증강] ── 갈래의 끝, 발송하지 않음 ─────────────────
def 보완요청작성(보완):
    lines = ["# 보완 요청 안내문 (초안)", "",
             "> 담당자 확인 전입니다. **신청자에게 발송하지 않았습니다.**", ""]
    for r in 보완:
        lines += [f"## {r['청구번호']} · {r['성명']}({r['사번']})",
                  f"- 진료일: {r['진료일']} · {r['병원명']} · 청구 {int(r['청구금액']):,}원",
                  f"- 빠진 것: {r['사유']}",
                  f"- 재제출 기한: 접수일 +14일", ""]
    OUT.mkdir(exist_ok=True)
    (OUT / "보완요청안내문.md").write_text("\n".join(lines), encoding="utf-8")
    step("보완요청작성", f"{len(보완)}건 안내문 초안 — 발송 안 함 (사람 확인 대기)")
    print("  → out/보완요청안내문.md")
    TR.halt("5. 보완요청작성", "증강",
            f"{len(보완)}건에 대해 안내문 초안을 만들었습니다. 재제출 기한은 접수일 +14일입니다.",
            checklist=[f"{r['청구번호']} {r['성명']} — {r['사유']}" for r in 보완])
    TR.warn("**발송하지 않았습니다.** 이 갈래의 끝이고, 담당자가 확인할 때까지 멈춥니다.")
    TR.file("out/보완요청안내문.md")
    return 보완


# ── 6. 예외심사요청 [증강] → 예외심사대장.csv ──────────────────────────
COLS_예외 = ["청구번호", "사번", "성명", "청구금액", "예외사유", "심사근거", "상태"]


def 예외심사요청(예외):
    rows = [{k: r.get(k, "") for k in COLS_예외} | {"상태": "심사대기"} for r in 예외]
    step("예외심사요청", f"{len(rows)}건 심사 요청 · 지급 여부를 추천하지 않음")
    TR.step("6. 예외심사요청", "증강",
            f"{len(rows)}건을 심사 대기로 올렸습니다. **지급 여부를 추천하지 않았습니다** — "
            f"판단은 심사자가 합니다.")
    TR.table("예외심사대장", rows, ["청구번호", "성명", "예외사유", "심사근거"])
    TR.file("out/예외심사대장.csv", len(rows))
    write("예외심사대장.csv", rows, COLS_예외)
    return rows


# ── 7. 지급승인 [사람고유] ── 여기서 멈춘다 ────────────────────────────
def 지급승인(지급행, 예외행):
    lines = ["# 승인 대기 목록", "",
             "> ⛔ 여기서 멈춥니다. **에이전트는 아무것도 승인하지 않았습니다.**",
             "> 복리후생 팀장이 확인하고 승인해야 지급이 진행됩니다.", "",
             f"## 자동지급 상신 {len(지급행)}건", ""]
    for r in 지급행:
        lines.append(f"- {r['청구번호']} {r['성명']} · {r['기준항목']} · "
                     f"지급액 **{int(r['지급액']):,}원** (청구 {int(r['청구금액']):,}원)")
    lines += ["", f"## 예외심사 대기 {len(예외행)}건", ""]
    for r in 예외행:
        lines.append(f"- {r['청구번호']} {r['성명']} · {r['예외사유']} — {r['심사근거']}")
    lines += ["", "---", "", "이 팩에는 지급 실행 코드가 없습니다."]
    OUT.mkdir(exist_ok=True)
    (OUT / "승인대기목록.md").write_text("\n".join(lines), encoding="utf-8")
    step("지급승인", "⛔ 사람고유 — 승인 대기 목록만 만들고 멈춤")
    print("  → out/승인대기목록.md")
    합계 = sum(int(r["지급액"]) for r in 지급행)
    TR.halt("7. 지급승인", "사람고유",
            f"**여기서 멈췄습니다.** 에이전트는 아무것도 승인하지 않았습니다. "
            f"자동지급 상신 {len(지급행)}건(합계 {합계:,}원)과 예외심사 대기 {len(예외행)}건이 "
            f"복리후생 팀장 확인을 기다립니다.",
            actions=[f"{len(지급행)}건 승인", f"예외 {len(예외행)}건 검토", "전체 반려"])
    TR.file("out/승인대기목록.md")


def main():
    global TR
    print("의료비 청구 건 판독·지급 판정 에이전트\n")
    TR = Trace("의료비 판독 AI",
               source="SKI AX 과제 · Talent AX실 · HR AI",
               lv4="의료비 지원 운영", lv5="의료비 청구 건 판독·지급 판정")
    claims, rules = load("청구접수대장.csv"), load("지급기준표.csv")
    print(f"입력: 청구접수대장.csv {len(claims)}건 · 지급기준표.csv {len(rules)}개 기준\n")
    TR.input("청구접수대장", len(claims), "2026년 7~8월 접수분")
    TR.input("지급기준표", len(rules))

    read = 증빙서류판독(claims)
    신청 = 신청서생성(read)
    지급, 보완, 예외 = 지급기준대조(신청, claims, rules)

    print("\n  ├─ 경로 A ─────────────")
    지급행 = 자동지급상신(지급, 예외)
    print("  ├─ 경로 B ─────────────")
    보완요청작성(보완)
    print("  ├─ 경로 C ─────────────")
    예외행 = 예외심사요청(예외)
    print("  └─ 합류 ───────────────")
    지급승인(지급행, 예외행)

    TR.done(f"경로 A(자동지급) {len(지급행)}건 · 경로 B(보완) {len(보완)}건 · "
            f"경로 C(예외심사) {len(예외행)}건 = 총 {len(claims)}건 · 사람 확인 없이 나간 것 없음")
    TR.save(OUT)
    print("  → out/trace.json (실행 기록 — 목업 화면이 이것을 읽습니다)")

    print(f"\n경로 A(자동지급) {len(지급행)}건 · 경로 B(보완) {len(보완)}건 · "
          f"경로 C(예외심사) {len(예외행)}건 = 총 {len(claims)}건")
    print("사람 확인 없이 나간 것: 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
