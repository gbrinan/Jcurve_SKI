---
name: quote-parse
owner: 팀원A
quadrant: depth
inputs: [견적메일]
outputs: [파싱결과]
reads: [승인공급사목록.xlsx]
writes: []
next: compare-update
---

# quote-parse — 견적 메일 파싱

지정된 폴더의 견적 메일(PDF 첨부 포함)에서 공급사·품목·단가·납기·수신일을 추출한다.

- 승인공급사목록.xlsx의 공급사와 대조하여 미승인 공급사 건은 "검토 필요"로 표시한다.
- 어떤 표에도 직접 기록하지 않는다. 추출 결과(파싱결과)를 compare-update에 넘긴다.
- 추출 실패(형식 인식 불가) 건은 건너뛰지 말고 실패 목록으로 보고한다.
