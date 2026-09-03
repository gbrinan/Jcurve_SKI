# Findings & Decisions

> 기술적 발견, 중요한 결정이 있을 때마다 즉시 갱신한다.

## Requirements

- [x] paperthin의 철학과 규약(자기완결 스킬 · 사분면 · 제거 우선 · SSOT)으로 세팅한다
- [x] file-based planning(세 파일 메모리)으로 세팅한다
- [x] 범용 엔진(skillmergeagent)과의 경계를 문서에 적는다

## Research Findings

### 이 저장소의 실측 규칙 (엔진으로 옮겨 간 것)

- 게이트가 점검기보다 먼저: 이름 어긋남(`견적_비교표` vs `견적비교표`)이 단일 기록자 검사를 통과시켜 진짜 충돌을 가렸다.
- `halt_at`은 체인 중간도: 사람고유 판단이 중간에 있을 때 정지 문구가 빠져도 L4(끝점만 검사)가 통과시켰다.
- `결정됨`이 있는 `DECISIONS.md`는 덮어쓰지 않는다: 재실행이 팀의 결정을 지운 적이 있다.
- 수용된 위험 ⚠️는 실패와 구분하되 출력에서 사라지지 않는다.
- 직선·태스크 적음은 탈락이 아니라 이름 붙이기(스킬팩 / 에이전트).

### 여기 남는 회사 고유 부분

| 항목 | 위치 |
| --- | --- |
| 교육 세션 번호·50분 타임라인·이노허브(Codex) 전제 | `prompts/` |
| SK CI 디자인 토큰 | `DESIGN.md` (SSOT) · `skills/depth/slide-pack/assets/template-sk-ci.html` |
| 상류 도구 형식(ATF 보고서 HTML · `WFDATA` 와이어프레임)과 어댑터 | `examples/upstream/` · `check/adapt_upstream.py` · `check/adapt_workflow.py` |
| SK 팀장·실무자 페르소나 인터뷰 | `personas/` |

### 팩 규격 (엔진과 공유)

스킬 frontmatter `name · owner · quadrant · human · inputs · outputs · reads · writes · next`, 계약 블록 `tables · writers · chain · payloads · threshold · halt_at`. 이 규격이 두 저장소를 잇는다. 코드가 아니라.

### paperthin 냉독 결과 (2026-09-03)

컨텍스트 없는 별도 세션이 README와 CLAUDE.md만 읽고 보고한 결함: Lv5·ATF·WFDATA·이노허브·상류·팩·계약·게이트·L1~L4·자동/증강/사람고유·SSOT가 정의 없이 등장, 명령을 어디서 치는지 없음, 저장소 이름(Jcurve vs Activity Coach)·엔진 스킬 5 vs 6·`SKILL.md` vs `skill.md`·점검 도구 소재가 두 문서에서 어긋남. 모두 README 앞부분의 두 절(누가 어디서 무엇을 하나 · 용어)과 문장 통일로 고쳤다. 교육 자료는 "팀장이 첫 화면에서 멈추는 곳"이 곧 결함이라는 기준을 적용했다.

## Technical Decisions

| Decision | Rationale |
| --- | --- |
| `SKILL.md`를 `skills/depth/slide-pack/`로, `assets/`도 함께 | paperthin 레이아웃 `skills/<사분면>/<이름>/`. 스킬은 자기 자산을 품는다 |
| `DESIGN.md`는 루트에 남긴다 | 디자인 토큰의 SSOT. 슬라이드 외의 산출물도 읽을 수 있게 |
| `scripts/validate-skills.sh`는 엔진의 사본, 필수 절만 이 저장소에 맞춤 | 교안이 쓰는 절 이름을 바꾸지 않기 위해 |

## Issues Encountered

### 1. 스킬 이동 후 경로 참조

**문제**: `SKILL.md`·README·`DESIGN.md`가 `assets/template*.html`을 루트 기준으로 가리켰다.

**해결**: 세 문서의 경로를 `skills/depth/slide-pack/assets/`로 갱신.

## Resources

- 엔진: https://github.com/gbrinan/skillmergeagent
- 철학 원문: https://github.com/LilMGenius/paperthin
- 세 파일 패턴: https://github.com/ahastudio/til/blob/main/ai/file-based-planning-workflow.md
- 점검 기준: `check/통합점검-기준.md`

## Learnings

### (2026-09-03) 프로필은 엔진을 링크하지 않는다

교육 현장은 오프라인이거나 파일 접근이 제한된다. 이 저장소의 `check/`가 엔진을 import하면 현장에서 돌지 않는다. 공유하는 것은 규격(frontmatter·계약 블록)이고, 규격이 같으면 어댑터가 만든 팩을 어느 쪽 점검기도 읽는다.
