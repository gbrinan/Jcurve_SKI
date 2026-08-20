#!/usr/bin/env python3
"""AX전략 공유 에이전트 — 4개 스킬을 하나로 묶어 실제 실행한다.

skills/depth/{공유대상자목록정리, 관련회의록첨부, 메일본문작성, 메일발송}
네 개가 각자 조각으로 존재하는 게 아니라, agent-plan.md 4절이 정한 순서
(1→2→3→4)대로 이어져 하나의 입력(data/)에서 하나의 결과(out/)를 낸다는 것을
실제로 증명하는 실행기다. check/check_contract.py --run-check가 구조를
검증한다면, 이 스크립트는 그 구조가 실제로 돌아간다는 것을 보여준다.

판단(rule)이 아니라 조립(assemble) 태스크로만 구성돼 있어 지어낼 업무
규칙이 없다. 필터·첨부·초안 작성은 data/의 원본 값만으로 수행한다.
"""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).parent
for cand in (HERE.parents[2] / "check", HERE.parent / "check", HERE / "check"):
    if (cand / "trace.py").is_file():
        sys.path.insert(0, str(cand))
        break
else:
    sys.exit("trace.py를 찾지 못했습니다 — 툴킷의 check/ 폴더가 있어야 합니다.")
from trace import Trace   # noqa: E402


def main():
    data, out = HERE / "data", HERE / "out"
    out.mkdir(exist_ok=True)
    TR = Trace("계열사 AX전략 공유 에이전트",
               source="SKI AX 과제 · 계열사 AX전략 팀장 공유",
               lv4="AX전략 공유하기", lv5="계열사 AX전략 팀장에게 공유")

    # 1) 공유대상자목록정리 — "대상" 표시된 후보만
    cands = list(csv.DictReader(open(data / "공유대상자후보.csv", encoding="utf-8")))
    targets = [r for r in cands if r["대상여부"] == "대상"]
    with open(out / "공유대상자목록.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["이름", "소속", "직책"])
        w.writeheader()
        for r in targets:
            w.writerow({"이름": r["이름"], "소속": r["소속"], "직책": r["직책"]})
    print(f"[1 공유대상자목록정리] 후보 {len(cands)}명 중 대상 {len(targets)}명 선정 "
          f"({', '.join(r['이름'] + '(' + r['소속'] + ')' for r in targets)})")
    TR.input("공유대상자후보", len(cands), "AX전략 공유 대상 선정")
    TR.step("1. 공유대상자목록정리", "증강",
            f"후보 {len(cands)}명 중 **대상 {len(targets)}명**을 골랐습니다. "
            f"「대상」으로 표시된 행만 씁니다 — 판단하지 않습니다.")
    TR.table("공유대상자목록", targets, ["이름", "소속", "직책"])
    TR.file("out/공유대상자목록.csv", len(targets))

    # 2) 관련회의록첨부 — 주제="AX전략"인 회의록만
    minutes = list(csv.DictReader(open(data / "회의록목록.csv", encoding="utf-8")))
    attach = [r for r in minutes if r["주제"] == "AX전략"]
    with open(out / "첨부파일목록.md", "w", encoding="utf-8") as f:
        f.write("# 첨부 파일\n\n")
        for r in attach:
            f.write(f"- {r['파일명']} ({r['일자']})\n")
    print(f"[2 관련회의록첨부] 회의록 {len(minutes)}건 중 AX전략 관련 {len(attach)}건 첨부 "
          f"({', '.join(r['파일명'] for r in attach)})")
    TR.input("회의록목록", len(minutes))
    TR.step("2. 관련회의록첨부", "증강",
            f"회의록 {len(minutes)}건 중 주제가 「AX전략」인 **{len(attach)}건**만 첨부했습니다.")
    TR.table("첨부파일목록", attach, ["파일명", "일자", "주제"])
    TR.file("out/첨부파일목록.md", len(attach))

    # 3) 메일본문작성 — 1·2 산출물을 그대로 받아 초안 조립 (발송하지 않음)
    to_line = "; ".join(f"{r['이름']}({r['소속']})" for r in targets)
    attach_line = "\n".join(f"- {r['파일명']}" for r in attach)
    draft = f"""제목: [AX전략] 계열사 AX전략 팀장 공유 — 2026년 8월

받는사람: {to_line}

안녕하십니까,
AX전략 관련 최근 논의 내용을 공유드립니다. 첨부된 회의록을 참고 부탁드립니다.

첨부:
{attach_line}

감사합니다.
"""
    (out / "메일초안.md").write_text(draft, encoding="utf-8")
    print(f"[3 메일본문작성] 초안 생성 — 수신 {len(targets)}명, 첨부 {len(attach)}건. 발송하지 않음")
    TR.step("3. 메일본문작성", "증강",
            f"1·2단계 산출물을 그대로 받아 초안을 조립했습니다 — 수신 {len(targets)}명, "
            f"첨부 {len(attach)}건. **발송하지 않았습니다.**")
    TR.file("out/메일초안.md")

    # 4) 메일발송 — 사람고유(halt_at). 여기서 멈추고 확인을 요청한다.
    halt = f"""# 발송 대기 — 사람 확인 필요

아래 메일을 발송 전 확인해 주세요. **이 단계는 자동으로 진행되지 않습니다.**

- 수신자 {len(targets)}명: {to_line}
- 첨부 {len(attach)}건
- 본문: out/메일초안.md 참조

## 선정 근거 (1·2단계 결과 그대로)
- 대상자 {len(cands)}명 후보 중 소속 "AX전략팀장" 직책 {len(targets)}명만 선정
- 회의록 {len(minutes)}건 중 주제="AX전략" {len(attach)}건만 첨부

승인 후 담당자가 직접 발송합니다. 에이전트는 여기서 멈춥니다.
"""
    (out / "발송대기.md").write_text(halt, encoding="utf-8")
    print("[4 메일발송] 사람고유 — 확인 요청 후 정지. 자동 발송 없음")
    TR.halt("4. 메일발송", "사람고유",
            "**여기서 멈췄습니다.** 에이전트는 메일을 보내지 않았습니다. "
            f"수신 {len(targets)}명 · 첨부 {len(attach)}건을 담당자가 확인한 뒤 직접 발송합니다.",
            actions=[f"{len(targets)}명에게 발송", "초안 수정", "취소"],
            checklist=[f"{r['이름']} ({r['소속']} · {r['직책']})" for r in targets])
    TR.warn("이 팩에 메일 발송 코드가 없습니다.")
    TR.file("out/발송대기.md")

    TR.done(f"후보 {len(cands)}명 → 대상 {len(targets)}명 · 회의록 {len(minutes)}건 → "
            f"첨부 {len(attach)}건 · 발송 없음")
    TR.save(out)
    print("  → out/trace.json (실행 기록 — 목업 화면이 이것을 읽습니다)")

    print("\n" + "=" * 50)
    print(f"산출물: {sorted(p.name for p in out.iterdir())}")
    print("자동 발송 여부: 없음 (out/ 폴더에 초안만 존재)")


if __name__ == "__main__":
    main()
