#!/usr/bin/env python3
"""세션 6 확정 픽스처 — 팀이 인터뷰로 (미정)을 채우는 단계를 재현한다.

E2E 테스트에서만 쓴다. 실제 워크숍에서는 이 자리를 prompts/의 인터뷰가 채운다.
"""
import re
import sys
from pathlib import Path

CONTRACT = """# 전황 업데이트 팀 통합 계약 (세션 6 인터뷰로 확정)

```contract
tables:
  뉴스선별목록.xlsx: 제목, 출처, 일자, 중요도
  브리핑초안.docx: 항목, 요약문, 출처

writers:
  뉴스선별목록.xlsx: 주요뉴스선별목록생성기
  브리핑초안.docx: 브리핑초안생성기

chain: 주요뉴스선별목록생성기 -> 브리핑초안생성기 -> 브리핑검토요청서생성기

payloads: 구독메일, 뉴스목록, 브리핑초안, 검토요청서

threshold: ±15%
halt_at: 브리핑검토요청서생성기
```
"""

# 스킬별 (inputs, outputs, reads, writes, next)
SPEC = {
    "주요뉴스선별목록생성기": ("구독메일", "뉴스목록", "", "뉴스선별목록.xlsx", "브리핑초안생성기"),
    "브리핑초안생성기": ("뉴스목록", "브리핑초안", "뉴스선별목록.xlsx", "브리핑초안.docx",
                        "브리핑검토요청서생성기"),
    "브리핑검토요청서생성기": ("브리핑초안", "검토요청서", "브리핑초안.docx", "", "null"),
}

PLAN_DATA = """## 3. 데이터 명세
| 표 이름 | 칸 이름 | 원본 위치(SSOT) | 읽기/쓰기 |
|---|---|---|---|
| 뉴스선별목록.xlsx | 제목, 출처, 일자, 중요도 | 공용드라이브/정세브리핑/data | 쓰기 |
| 브리핑초안.docx | 항목, 요약문, 출처 | 공용드라이브/정세브리핑/data | 쓰기 |"""

PLAN_SCENARIO = """## 4. 대표 시나리오
- 트리거: 매일 아침, 구독메일 수신 폴더를 지정
- 입력: 구독메일 → 처리: 선별·요약 → 출력: 뉴스목록 · 브리핑초안 · 검토요청서
- 파이프라인: 주요뉴스선별목록생성기 → 브리핑초안생성기 → 브리핑검토요청서생성기

## 7. 검증·휴먼인더루프 지점
- 검토요청서 발송 전 팀장 확인 필수 — 대외 발신이므로 사람이 최종 승인
- 수치가 직전 대비 ±15% 이상 변동 시 확인 요청"""


def main(pack_dir):
    pack = Path(pack_dir)
    (pack / "CONTRACT.md").write_text(CONTRACT, encoding="utf-8")

    for p in pack.glob("skills/*/*/[sS][kK][iI][lL][lL].md"):
        t = p.read_text(encoding="utf-8")
        old = re.search(r"name: (.+)", t).group(1).strip()
        new = old.replace(" ", "")
        if new not in SPEC:
            print(f"❌ 계약에 없는 스킬: {new}")
            return 1
        i, o, r, w, nx = SPEC[new]
        t = t.replace(f"name: {old}", f"name: {new}")
        t = re.sub(r"inputs: \[.*?\]", f"inputs: [{i}]", t)
        t = re.sub(r"outputs: \[.*?\]", f"outputs: [{o}]", t)
        t = t.replace("reads: []", f"reads: [{r}]").replace("writes: []", f"writes: [{w}]")
        t = t.replace("next: (미정)", f"next: {nx}")
        p.write_text(t, encoding="utf-8")

    plan = pack / "agent-plan.md"
    t = plan.read_text(encoding="utf-8")
    t = re.sub(r"## 3\. 데이터 명세.*?\| \(미정\) \| \(미정\) \| \(미정\) \| \(미정\) \|",
               PLAN_DATA, t, flags=re.S)
    t = re.sub(r"## 4\. 대표 시나리오\n- \(미정\).*", PLAN_SCENARIO, t, flags=re.S)
    plan.write_text(t, encoding="utf-8")

    print("세션 6 확정 반영 완료 (계약 · 스킬 3개 · 기획서)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
