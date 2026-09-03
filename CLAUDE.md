# Jcurve_SKI (Activity Coach_SKI)

팀원들이 각자 만든 스킬을 하나의 팀 에이전트로 묶고, 잘 묶였는지 판정하고, 결과를 발표 자료로 만드는 도구 모음의 **SK이노베이션 프로필**이다. 회사에 묶이지 않는 범용 엔진은 [skillmergeagent](https://github.com/gbrinan/skillmergeagent)이고, 이 저장소는 그 엔진을 한 회사의 교육 흐름(세션 3 핏 코치 → 4 와이어프레임 코치 → 6·7 통합·패키징)에 맞춘 인스턴스다. 이 문서는 에이전트와 기여자가 따르는 규약이다. 사람이 읽는 정문은 [README](./README.md)다.

## 철학 (paperthin)

- **자료를 믿고, 저자를 믿지 않는다.** 인터뷰는 파일에서 아는 것을 확인표로 통째 확인하고, 없는 것만 묻는다. 없는 값은 `(없음)`·`(미정)`이다. 지어내지 않는다.
- **제거 우선.** 두 스킬이 같은 일을 하면 하나로. 아무도 답 못 하는 항목은 뺀다. 의견이 갈리면 빼는 쪽이 기본값. 슬라이드는 문서를 옮기지 않고 발표에 필요한 것만 남긴다.
- **하나의 진실, 한 곳에.** 기획서 `agent-plan.md`가 팀 에이전트 정보의 원본, `CONTRACT.md`가 이름의 원본, `DESIGN.md`가 슬라이드 디자인 토큰의 원본이다. 슬라이드 HTML은 요약본이라 원문이 바뀌면 다시 만든다.
- **절제.** 점검 항목을 늘리기 전에 그 항목이 실패를 실제로 잡은 적이 있는지 묻는다. 고칠 것이 없는 한 판은 아무것도 바꾸지 않는다.
- **자기 확인 금지.** 기계 판정이 통과해도 실제 실행과 오류 주입 없이 "동작 확인"이라고 적지 않는다.

## 엔진과 프로필의 경계

| 여기(프로필)에 두는 것 | 엔진(skillmergeagent)에 두는 것 |
| --- | --- |
| 교육 세션 번호·타임라인, 이노허브/Codex 전제 | 스킬 6개(intake · askflow · skillmerge · weave · mergechk · planfiles) |
| SK CI 디자인 토큰(`DESIGN.md`), slide-pack 테마 | 팩 규격 서식(`templates/`), 점검 기준 |
| 상류 도구 형식(ATF HTML, `WFDATA` 와이어프레임)과 어댑터(`check/adapt_*.py`) | 유사도 감사(`similarity.py`) |
| 페르소나 인터뷰, 교안용 예시 팩 | 범용 예시(before/after) |

`check/`의 게이트·점검기·readchk는 엔진에 일반화된 사본이 있다. **팩 규격**(스킬 frontmatter `name·owner·quadrant·human·inputs·outputs·reads·writes·next`, 계약 블록 `tables·writers·chain·payloads·threshold·halt_at`)은 두 저장소가 같게 유지한다. 규격을 바꾸면 양쪽을 같이 바꾼다. 코드는 링크로 공유하지 않는다. 어느 쪽도 혼자 설치돼 돌아야 한다.

## 레이아웃

```text
skills/<사분면>/<이름>/SKILL.md     ← 이 저장소가 제공하는 스킬 (지금은 depth/slide-pack 하나)
check/                              ← 점검기 · 게이트 · readchk · 상류 어댑터 · E2E
prompts/                            ← 인터뷰 프롬프트 v1·v2 (팀장이 붙여넣는 것)
examples/sample/<팀>/               ← 팩 규격의 실제 예시 (스킬은 skills/<사분면>/<이름>/skill.md)
planning/                           ← 이 저장소 자신의 tasks · findings · progress
```

스킬은 자기완결이다. `slide-pack`은 자기 `assets/`를 품고, 디자인 토큰만 저장소 루트의 `DESIGN.md`를 읽는다. 스킬이 늘면 사분면(depth 한 번에 끝남 · breadth 여러 파일을 가로지름 · coil 주기마다 돎) 아래 폴더를 만들고 `plugin.json`과 README 색인에 등록한다.

## 파일 기반 계획

세션을 시작하면 `planning/tasks.md` → `findings.md` → `progress.md`를 먼저 읽는다. 발견은 `findings.md`에 즉시, 단계 전환·결정·오류는 `tasks.md`에, 세션 기록과 테스트 결과는 `progress.md`에. 세션을 끝낼 때 `progress.md`의 5문항 답을 갱신한다. 서식은 엔진의 `templates/`와 같다.

## 출하 전 확인

1. `bash scripts/validate-skills.sh` — 스킬 이름=폴더, plugin.json 등록, README 링크, 필수 절.
2. `python3 check/run_check.py --self` — README 구조도가 실재하는 최상위 폴더를 전부 안내한다.
3. 예시 팩 세 개가 `check_contract.py --run-check`를 통과하고, `bash check/test_upstream_e2e.sh`가 전 구간 통과한다.
4. `DESIGN.md`의 토큰 표를 바꿨으면 `skills/depth/slide-pack/assets/template-sk-ci.html`의 `:root`에도 반영했다.
5. `planning/`에 이번 세션의 발견·결정·오류가 들어갔다.

커밋 메시지는 인수인계용으로: 제목 한 줄, 빈 줄, 실제로 달라진 것마다 `-` 한 줄.
