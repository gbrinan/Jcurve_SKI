# slide-pack

기획서·프롬프트·마크다운 문서를 **팀 공유용 HTML 슬라이드 덱**으로 변환하는 스킬.
파일 하나(HTML)만 나오므로 공용 드라이브에 올리면 누구나 더블클릭으로 열 수 있습니다.

- 설계 철학: [paperthin](https://github.com/LilMGenius/paperthin) — 제거 우선, SSOT
- 디자인 시스템: [awesome-design-md](https://github.com/VoltAgent/awesome-design-md) 방식의 `DESIGN.md`

## 폴더 구성

```
slide-pack/
├── SKILL.md                            ← 스킬 정의 (변환 규칙·절차)
├── DESIGN.md                           ← SK이노베이션 CI 디자인 토큰 (SSOT)
├── README.md                           ← 이 문서
├── assets/
│   ├── template.html                   ← 기본 테마 (다크) 스켈레톤
│   └── template-sk-ci.html             ← SK CI 테마 (발표용, 라이트) 스켈레톤
└── examples/
    ├── lv5-packaging-deck.html         ← 기본 테마 예시 (교육 세션 요약)
    └── lv5-presentation-deck-sk.html   ← SK CI 테마 예시 (세션 7 발표 골격)
```

## 사용법 — 종류별

### 1) 팀 내부 공유용 (기본 다크 테마)

기획서·체크리스트·회의 결과를 팀원끼리 빠르게 훑을 때.

```
slide-pack agent-plan.md
```

또는 자연어로:

```
agent-plan.md를 slide-pack으로 슬라이드 덱 만들어줘
```

→ `agent-plan-deck.html` 생성 (원문과 같은 폴더, `assets/template.html` 사용)

### 2) 발표용 (SK CI 테마)

세션 7 팀 발표, 경영진 보고 등 외부에 보여줄 자료.

```
agent-plan.md를 slide-pack SK CI 테마로 발표용 덱 만들어줘.
DESIGN.md의 토큰만 사용하고, template-sk-ci.html 스켈레톤을 써.
```

→ `agent-plan-presentation-deck.html` 생성. 발표용 규칙이 추가 적용됩니다:
- 제목은 주제가 아니라 **주장(메시지)** 으로 — "데이터 구조" ❌ → "사람은 검증 지점에서만 개입한다" ✅
- 파트가 3개 이상이면 **섹션 구분 슬라이드**(레드 배경) 삽입
- 첫 장에 발표·데모·Q&A 역할 분담, 마지막 장에 원문(SSOT) 위치

### 3) 문서 종류별 가이드

| 입력 문서 | 추천 테마 | 슬라이드 구성 팁 |
|---|---|---|
| 에이전트 기획서(agent-plan.md) | 발표용(SK CI) | 문제→해결→데모→배운 것 4파트 |
| 인터뷰 프롬프트·교육 자료 | 기본(다크) | 섹션당 1장, 표 중심 |
| 체크리스트·테스트 결과 | 기본(다크) | 체크 항목을 불릿으로, 결과는 ✅/❌ |
| 데모 시나리오 대본 | 발표용(SK CI) | 구분 슬라이드로 "라이브 데모" 표시, 슬라이드는 최소화 |

## 테마(CI) 바꾸는 법

색·폰트의 원본은 `DESIGN.md` 하나입니다.

1. 사내 브랜드 가이드라인에서 공식 색상값을 확보
2. `DESIGN.md`의 **2. 컬러 팔레트 표만** 수정
3. `assets/template-sk-ci.html`의 `:root` 토큰을 같은 값으로 반영
4. 이후 생성되는 모든 덱에 자동 적용 — 기존 덱은 재생성

새 색·폰트를 슬라이드 HTML에 직접 추가하지 마세요 (DESIGN.md 가드레일 위반).

## 공통 규칙 (Codex 슬라이드 포맷)

- HTML 파일 1개, 외부 CDN·폰트·이미지 요청 없음 (오프라인 동작)
- ←/→ 방향키 · 스페이스 · 클릭으로 이동, 우하단 페이지 표시
- 최대 10장, 슬라이드당 메시지 1개·불릿 5개·표 6행 이하
- 마지막 슬라이드에 원문 위치 명시 — **슬라이드는 요약본, 원문이 SSOT**
