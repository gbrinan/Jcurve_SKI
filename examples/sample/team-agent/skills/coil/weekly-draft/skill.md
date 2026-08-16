---
name: weekly-draft
owner: 팀장
quadrant: coil
inputs: [갱신된비교표]
outputs: [품의초안, 검토필요목록]
reads: [견적비교표.xlsx]
writes: []
next: retry-request
---

# weekly-draft — 주간 발주 품의 초안

갱신된 견적비교표를 근거로 발주 품의 초안(md)을 작성한다. 매주 월요일 주기로 돈다.

- 품목별 최저가·납기를 비교표에서 인용하고, 출처 행을 명시한다.
- 초안은 발송하지 않는다. 품의초안과 검토필요목록(미승인·파싱 실패 건)을 retry-request로 넘긴다.
- 팀장 확인 요청은 체인 마지막의 confirm-brief가 담당한다.
