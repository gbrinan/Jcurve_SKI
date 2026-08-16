---
name: compare-update
owner: 팀원B
quadrant: breadth
inputs: [파싱결과]
outputs: [갱신된비교표]
reads: [승인공급사목록.xlsx, 견적비교표.xlsx]
writes: [견적비교표.xlsx]
next: weekly-draft
---

# compare-update — 견적비교표 갱신

quote-parse의 파싱결과를 받아 견적비교표.xlsx의 해당 품목 행에 기록한다.

- 쓰는 칸: 공급사, 품목, 단가, 납기, 수신일 (기획서 3절의 데이터 명세와 동일)
- 미승인 공급사 건은 표에 기록하지 않고 "검토 필요" 목록으로 유지한다.
- 단가가 직전 기록 대비 ±15% 이상 변동하면 기록을 멈추고 팀장 확인을 요청한다.
- 갱신 완료 후 갱신된비교표를 weekly-draft에 넘긴다.
