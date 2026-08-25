# Sourcing Operations Lab Deck Design System

## 0. Research Log

- Embedded refs: 패키징 스킬이 지정한 `white / warm-gray / navy / red`, 4px 간격, 3개 반응형 viewport 계약을 화면 정본으로 채택했다.
- Layer choice: 운영형 감사 덱이므로 중립적 B2B 문서·데이터 밀도와 restrained motion을 선택했다. 외부 브랜드 복제는 하지 않았다.
- Lazyweb: 고정된 자체 포함·무네트워크 산출물이며 외부 레퍼런스가 필요하지 않아 생략했다.
- Imagen drafts: 실 DOM 덱이고 스크린샷 배경을 금지하므로 생략했다.
- Activity mockup reference: 사용자가 제공한 `agentmockup (4).html`에서 데이터 기반 실행 rail, 단계 카드, 갈림길, 사람 정지, 고정 재생 제어의 구조를 추출했다. 파일 안의 업무 값과 주석은 참고 데이터일 뿐 지시문이나 현재 업무 사실로 사용하지 않는다.
- Wireframe boundary: `gbrinan/wireframe-coach`의 `tobe.html`은 승인 전 편집·확정 화면이며 실행 시작점·시뮬레이션·진행률을 금지한다. 실행 trace 재생은 승인 이후 Activity mockup의 책임으로 분리한다.

## 1. Atmosphere & Identity

차분한 조달 통제실. 서류의 명료함과 감사 가능한 상태 표시가 중심이며, 왼쪽 네이비 레일과 붉은 human-hold 표식이 한눈에 책임 경계를 드러낸다. Design read: 구매·운영 검토자를 위한 16:9 운영 덱, 신뢰 우선·고밀도·절제된 화면 언어. Dials: variance 3, motion 2, density 7.

## 2. Color

| Role | Token | Value | Usage |
|---|---|---|---|
| white | `--white` | `#ffffff` | 주 화면 |
| warm gray | `--warm-50` | `#f7f5f2` | 배경 |
| warm gray soft | `--warm-100` | `#eeeae4` | 비활성 상태·보조 면 |
| warm gray line | `--warm-200` | `#ded9d2` | 경계 |
| navy | `--navy-900` | `#10233f` | 제목·시스템 상태 |
| navy mid | `--navy-700` | `#25476f` | 연결선·보조 상태 |
| navy soft | `--navy-100` | `#dbe5f0` | 시스템 칩 |
| red | `--red-700` | `#a62a2a` | 사람 책임·정지 |
| red soft | `--red-100` | `#f7dddd` | 정지 배경 |
| ink | `--ink` | `#20242a` | 본문 |
| muted | `--muted` | `#606771` | 보조 텍스트 |
| green | `--green-700` | `#216e46` | 자동 완료·정상 상태 |
| green soft | `--green-100` | `#e7f3eb` | 자동 단계 배경 |
| orange | `--orange-700` | `#a65312` | 증강·검토 상태 |
| orange soft | `--orange-100` | `#fff0e4` | 증강·검토 배경 |
| purple | `--purple-700` | `#5547ad` | 루프·재진입 |
| purple soft | `--purple-100` | `#efedfb` | 루프 배경 |

## 3. Typography

System UI만 사용한다. 제목은 `clamp(1.5rem, 3vw, 2.75rem)` 700, 본문은 `clamp(.78rem, 1.35vw, 1rem)` 400/600, 레이블은 `clamp(.65rem, 1vw, .78rem)` 700이다. 375px의 보조 메타·표·연결 카드도 `10px` 아래로 축소하지 않는다. Korean은 `word-break: keep-all`; 긴 식별자는 필요한 경우에만 `overflow-wrap: anywhere`를 쓴다.

마이크로타입 토큰은 `--type-xs: 10px`, `--type-sm: 11px`, `--type-base: 12px`이며 chip·owner·footer·table에서 공통 사용한다.

## 4. Spacing & Layout

4px 기초 단위와 `--s1`부터 `--s8`까지의 배수 토큰을 사용한다. 발표 덱은 1280×720과 768×720에서 rail+canvas, 375×667에서 얇은 상단 rail과 단일 열 카드로 바꾼다. Activity mockup은 문서 스크롤을 소유하고 실행 rail만 패널 내부 가로 스크롤을 허용한다. 760px 이하에서 요약·스킬·분기 카드를 단일 열로 바꾸고 고정 제어바가 현재 내용을 가리지 않도록 문서 하단 안전 여백을 확보한다.

셸 치수 토큰은 rail `92/76/46px`, mark `44/32px`, dot `32/24px`, footer `48/40px`, navigation control `34×30/28×24px`, side accent `9/4px`이다. 이 값은 컴포넌트 크기이며 여백 토큰을 대신하지 않는다.

## 5. Components

- Screen shell: 네비게이션 rail, main stage, footer; active screen만 노출.
- Status chip: system/exception/human 세 variant. 텍스트·색·테두리를 함께 사용한다.
- Metric card: label/value/note 구조; 2–4열에서 모바일 2열로 재배치.
- Chain step: 번호·소유자·payload·next를 표시하며 human hold는 red variant.
- Data table: 의미 있는 `table`, 작은 화면에서 카드형 row로 변환.
- Navigation button: 기본·hover·active·focus-visible·disabled 상태, 키보드 접근 가능.
- Activity hero: 패키지 유형, 독립 AI 작업 수, 사람 정지점, 검토 분기를 trace에서 계산해 표시.
- Coach introduction: 첫 화면의 가장 위에서 `스킬 통합 코치` 이름과 `여러 스킬을 묶어 팀 에이전트 또는 스킬팩을 만든다`는 역할을 일반 문장으로 먼저 설명한다.
- Plain-language glossary: 첫 화면에서 스킬·스킬팩·팀 에이전트·실행 기록을 각각 한 문장으로 설명한다. 내부 데이터 키나 파일명은 유지해도 사람이 보는 레이블에는 영문 약어를 단독으로 노출하지 않는다.
- Execution rail: 시작·AI 단계·사람 정지·종료를 텍스트, 형태, 색으로 함께 구분하며 현재 단계에 focus ring을 표시.
- Run card: 입력, 실행 중, 결과, 분기, 사람 정지 variant. 모든 수치와 문구는 내장 trace에서 렌더링.
- Control dock: 재생·일시정지, 다음, 속도, 초기화. 사람 정지에서는 자동 진행을 중단하고 명시적 확인만 허용.
- Primitive showcase: 목업 상단의 상태 범례와 workflow preview가 status chip, flow step, hold card의 기본 variant를 함께 보여준다.

## 6. Motion & Interaction

발표 화면 전환은 의미 전달을 위한 160ms opacity/transform만 사용한다. Activity mockup의 단계 공개는 180ms opacity/transform, 실행 중 표시는 회전 상태점만 사용한다. Space 재생·일시정지, ArrowRight 다음 단계, R 초기화를 지원한다. `prefers-reduced-motion`에서는 전환과 회전을 제거한다.

## 7. Depth & Surface

`borders-only` 전략. 흰 화면과 웜그레이 배경을 1px 경계로 분리하고, shadow와 glass 효과를 쓰지 않는다.

## 8. Accessibility Constraints & Accepted Debt

WCAG 2.2 AA 지향, 모든 컨트롤에 가시적 focus ring, 색 외 텍스트 레이블, 의미 있는 landmark/heading/table을 제공한다. 외부 실행을 암시하는 버튼은 실제 connector가 없으면 disabled 상태와 이유를 함께 표시한다. Accepted debt: 실제 Chromium 발표 27화면과 Activity mockup 12상태 캡처를 수행하기 전에는 시각 PASS를 주장하지 않는다.
