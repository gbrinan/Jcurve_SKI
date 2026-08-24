# Activity Packaging Coach 일반화 예시

## TL;DR

단일 `skills/activity-packaging-coach/SKILL.md`와 비식별 가상 구매 입력만으로 완전한 `team agent` 패키지와 9면 HTML을 생성한 독립 실행 예시다. 이전의 HR 전용 실험물 대신 이 도메인 중립 스킬을 정본으로 사용한다.

## 구성

- `input/`: 승인된 가상 구매 WFDATA, 맥락, task skill 3개
- `results/reference/`: 기준 독립 에이전트 결과, 실제 Edge 27/27
- `results/luna/`: Luna 5 원본 결과, 독립 Edge 18/27
- `COMPARISON.md`: 관찰 차이, 원인, 변경 제안과 반대 관점

두 실행 모두 L0–L4와 사람 정지점은 보존했다. Luna 결과는 375·768에서 통과했지만 1280의 `body` 바깥 패딩 때문에 문서 높이가 viewport보다 14px 커졌다. 비교의 재현성을 위해 Luna HTML은 수정하지 않았다.

실제 업무에서는 `input/`을 복사하지 말고 비식별화한 승인 WFDATA와 해당 업무의 task skill로 교체한다. 이 예시는 외부 전송, 구매 승인, 결제 또는 운영 시스템 쓰기를 수행하지 않는다.
