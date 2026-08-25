# 스킬·에이전트 통합 코치 일반화 예시

## TL;DR

단일 `skills/activity-packaging-coach/SKILL.md`와 비식별 가상 구매 입력만으로 실행 가능한 `team agent`, trace 기반 Activity 실행 목업, 9면 발표 HTML을 생성한 독립 실행 예시다. 이전의 HR 전용 실험물 대신 이 도메인 중립 스킬을 정본으로 사용한다.

## 구성

- `input/`: 승인된 가상 구매 WFDATA, 맥락, task skill 3개
- `results/reference/team-package/`: `MANIFEST.md`에서 생성 에이전트·스킬·실행 명령을 확인하고 `node run.mjs`로 재생성하는 기준 패키지
- `results/reference/agent-mockup.html`: 설치 없이 바로 확인하는 Activity 실행 목업, Edge 12/12
- `results/reference/agent-plan-deck.html`: 기준 발표자료, Edge 27/27
- `results/luna/`: Luna 5 원본 결과, 독립 Edge 18/27
- `COMPARISON.md`: 관찰 차이, 원인, 변경 제안과 반대 관점

두 실행 모두 L0–L4와 사람 정지점은 보존했다. Luna 결과는 375·768에서 통과했지만 1280의 `body` 바깥 패딩 때문에 문서 높이가 viewport보다 14px 커졌다. 비교의 재현성을 위해 Luna HTML은 수정하지 않았다.

에이전트 설계 코치의 `tobe.html`은 선택한 LV5의 전체 작업 흐름을 확인하고 승인하는 화면이다. 팀원 개개인이 만든 스킬을 넣은 뒤, 실행 시작·기록 재생·진행률·분기 결과·사람 정지는 스킬·에이전트 통합 코치가 만든 `agent-mockup.html`에서 직접 테스트한다. `agent-plan-deck.html`은 같은 결과를 팀 발표용으로 설명한다.

실제 업무에서는 `input/`을 복사하지 말고 비식별화한 승인 WFDATA와 해당 업무의 task skill로 교체한다. 이 예시는 외부 전송, 구매 승인, 결제 또는 운영 시스템 쓰기를 수행하지 않는다.
