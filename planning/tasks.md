# Project: Jcurve_SKI

## Goal

SK이노베이션 AI 에이전트 제작 교육(세션 6·7)에서, 팀원들이 각자 만든 Lv.6 스킬을 팀 Lv.5 에이전트로 묶고 · 검증하고 · 발표하는 도구 모음. 범용 엔진(skillmergeagent)의 첫 인스턴스로서 회사 고유 부분만 여기 둔다.

## Current Phase

✅ Phase 3: paperthin 규약 · 파일 기반 계획으로 세팅

## Phases

### Phase 1: 교육용 도구 완성 ✅ (이전 세션들)

- [x] 인터뷰 프롬프트 v1·v2
- [x] 계약 게이트 · 통합 점검기 · readchk · 상류 어댑터 · E2E
- [x] slide-pack (다크 / SK CI 테마)

### Phase 2: 엔진 분리 ✅

- [x] 회사에 묶이지 않는 부분을 skillmergeagent로 일반화 (스킬 6개 · 서식 · 점검기 · 유사도 감사)
- [x] 여기에는 프로필(세션·이노허브·SK CI·상류 어댑터·페르소나)만 남긴다고 결정

### Phase 3: 세팅 ✅

- [x] `SKILL.md`·`assets/`를 `skills/depth/slide-pack/`로 이동 (자기완결)
- [x] `CLAUDE.md` · `.claude-plugin/plugin.json` · `scripts/validate-skills.sh` · CI
- [x] `planning/` 세 파일
- [x] README를 지도·색인·엔진 관계가 보이도록 다시 씀

### Phase 4: 실측 ⏸️

- [ ] `examples/sample/report-wording-pack`에 `data/`가 없어 L1이 실패한다 (README는 통과 예시라고 설명). `data/`를 채우거나 README 설명을 고친다

- [ ] 세션 6에서 엔진의 `intake` → `askflow`를 실제 팀 폴더에 돌려보고 v2 프롬프트와 비교
- [ ] 슬라이드 생성 후 검증 체크리스트 5항목 실측

## Key Questions

1. 세션 6 진행에 v2 프롬프트를 계속 쓸 것인가, 엔진의 `askflow`로 대체할 것인가? → 실측 후 결정.
2. 상류 어댑터(ATF·WFDATA)가 다른 교육 기수에도 그대로 맞는가?

## Decisions Made

| Decision | Rationale |
| --- | --- |
| 엔진과 프로필을 두 저장소로 | 회사 고유 명사가 엔진에 섞이면 다른 팀이 못 쓴다 |
| `check/`는 그대로 둔다 | 상류 어댑터와 E2E가 이 저장소의 실측 자산. 엔진에는 일반화 사본. 규격만 같게 유지 |
| `slide-pack`은 `depth/` | 문서 하나를 받아 덱 하나를 내고 끝난다 |
| validate 필수 절은 이 스킬의 절 이름(변환 절차 · 산출물 이름 규칙) | 절 이름을 영어로 바꾸면 교안과 어긋난다. 절제 |

## Errors Encountered

| Error | Attempt | Resolution |
| --- | --- | --- |
| `run_check.py --self`가 `skills/`·`scripts/`·`planning/`을 구조도에서 못 찾음 | 1 | README 구조도 갱신 |
| report-wording-pack L1 `data/ 존재` 실패 | 1 | 이 브랜치 이전부터의 상태. CI에서 제외, Phase 4 항목으로 남김 |

## Notes

- 진행할 때마다 Phase 상태를 갱신한다.
- 중요한 결정 전에 이 파일을 다시 읽는다.
