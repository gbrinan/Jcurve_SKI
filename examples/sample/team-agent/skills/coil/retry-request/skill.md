---
name: retry-request
owner: 팀원A
quadrant: coil
inputs: [품의초안, 검토필요목록]
outputs: [재요청초안]
reads: [승인공급사목록.xlsx]
writes: []
next: confirm-brief
---

# retry-request — 예외 건 후속 조치·재요청 초안

weekly-draft가 넘긴 검토필요목록(미승인 공급사·파싱 실패 건)을 건별 후속 조치로 바꾼다.

- 미승인 공급사: 승인공급사목록.xlsx와 대조해 빠진 등록 서류 항목을 명시한 재요청 메일 초안 생성
- 파싱 실패 건: 원본 파일명·실패 사유를 적은 재발송 요청 초안 생성
- 공급사 이름·항목은 원본 데이터에서만 치환한다 (수기 복붙 오타 방지 — 인터뷰 발견 2)
- 메일은 발송하지 않는다. 재요청초안과 품의초안을 confirm-brief로 넘긴다.
