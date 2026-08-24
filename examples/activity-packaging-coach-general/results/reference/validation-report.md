# Validation report

## TL;DR

`Sourcing Operations Lab` 패키지는 3개 독립 AI 작업이 하나의 도달 가능한 체인을 이루고 L0–L4와 실제 Edge/Playwright 27화면 시각 검사를 통과했으므로 `team agent`다. 다만 운영 `sourcing-policy.csv` 열 스키마는 승인 입력에 없어서 `(미확인)`으로 유지했으며, 실제 운영 연결 전 구매담당자가 확인해야 한다. 패키지 수준 검증은 PASS이고 production activation은 이 스키마 확인 전까지 보류한다.

## Package verdict

- Type: `team agent`
- Independent AI task count: `3`
- Rationale: `quote-intake-normalizer`, `quote-variance-analyzer`, `sourcing-review-brief`는 각각 고유 input, output, owner, acceptance test를 가진다. 세 작업은 정확히 하나의 시작점에서 모두 도달 가능하다.
- Canonical plan: `agent-plan.md`
- Validation date: 2026-08-24 (Asia/Seoul)

## Batch intake maps

### Skill map

| skill | owner | purpose | input | output | next |
|---|---|---|---|---|---|
| `quote-intake-normalizer` | `sourcing-analyst` | 모든 견적 행 정규화와 파싱 상태 보존 | `quote_bundle` | `normalized_quotes` | `quote-variance-analyzer` |
| `quote-variance-analyzer` | `sourcing-analyst` | 정책 대비 가격·납기 편차와 근거 판정 | `normalized_quotes` | `variance_flags` | `sourcing-review-brief` (buyer review hold 뒤) |
| `sourcing-review-brief` | `buyer` | 모든 견적·근거·미해결 질문 브리프 | `variance_flags` | `sourcing_review_brief` | `human` |

### Rule map

| skill/node | decision rule | exception | environment | human gate |
|---|---|---|---|---|
| normalizer / Read quote bundle | 모든 가상 견적 행 읽기 | 파일 누락 시 중단 | fictional, weekly/on-demand | `missing-input-hold` |
| normalizer / Normalize quote fields | 지원 통화 변환과 source evidence 보존 | failed parse는 `review` | fictional, independent | 없음 |
| analyzer / Join policy | `item_code`로 매칭 | missing match는 `review` | fictional, independent | `buyer-variance-review-hold` |
| analyzer / Apply variance rules | 가격 `12% 초과` 또는 납기 `7일 초과`는 review | ambiguity는 buyer로 | fictional, independent | `buyer-variance-review-hold` |
| brief / Draft review brief | 모든 quote와 evidence 요약 | missing evidence는 unresolved | fictional, independent | 없음 |
| brief / Buyer confirmation | buyer가 예외와 supplier choice 확인 | purchase order 미전송 | fictional, independent | `buyer-confirmation-hold` |

### Chain map

| start | transitions | branches | stop points | final output |
|---|---|---|---|---|
| `quote-intake-normalizer` | normalizer → analyzer → buyer review hold → brief → buyer confirmation hold | threshold/parse/match/ambiguity가 review hold로 분기 | missing input, intermediate buyer review, final buyer confirmation, external action | `sourcing-review-brief.md` |

## Gate results

| Gate | Status | Evidence |
|---|---|---|
| L0 contract | PASS | `CONTRACT.md`에 표·열·writer·chain·payload·threshold·halt_at 정본 1개. `normalized-quotes.csv`와 `comparison-table.csv`는 각각 단독 writer 1개. 충돌 0. |
| L1 structure | PASS | 필수 파일·data/skills 디렉터리 존재. `agent-plan.md` 정확히 1개, 섹션 정확히 8개, `README.md` 정확히 3줄. 3개 packaged skill의 7개 frontmatter 필드와 본문이 모두 비어 있지 않음. |
| L2 context preservation | PASS | 입력 스킬 3개를 병합/삭제 없이 정확히 한 번 배치. WFDATA의 6개 node 규칙, 6개 예외, `sourcing-analyst`/`buyer` owner, 2개 gate와 purchase-order 금지를 plan·agent·skill에 보존. 모든 read/write 데이터가 plan 3절에 존재. |
| L3 consistency | PASS | start 1, reachable skill 3/3, cycle 0, orphan 0. `quote_bundle → normalized_quotes → variance_flags → sourcing_review_brief`가 인접 frontmatter와 CONTRACT에서 일치. terminal `human`은 `buyer-confirmation-hold`로 명시. |
| L4 end to end | PASS | 합성 fixture 3행 모두 normalizer·comparison·brief에 보존. ordinary `Q-NORMAL`은 pass, threshold `Q-REVIEW`와 failed parse `Q-FAILED`는 human review에서 중단. 외부 send/PO/ERP write 0. |

## L4 scenario trace

### Ordinary fictional scenario

1. `Q-NORMAL` 입력 행을 KRW 값 그대로 정규화해 `parse_status=ok`로 보존했다.
2. schema를 발명하지 않는 `l4-policy-test-adapter.md`가 item match와 0%/0일 편차를 반환했다.
3. `comparison-table.csv`에 `policy_status=pass`와 evidence를 남겼다.
4. 브리프의 Ordinary 절에 quote ID와 근거를 포함했다.

### Adversarial fictional scenario

1. `Q-FAILED`의 `unit_price=not-a-number`를 추론하거나 삭제하지 않았다.
2. `normalized-quotes.csv`에 빈 KRW 값과 `parse_status=review`로 원본 quote ID를 보존했다.
3. analyzer가 계산을 강행하지 않고 `policy_status=review`와 실패 근거를 기록했다.
4. 브리프가 unresolved 항목과 buyer next action을 명시하고 `buyer-confirmation-hold`에서 멈췄다.

추가 threshold fixture `Q-REVIEW`는 가격 12.01%와 납기 8일로 승인된 두 임계값을 모두 초과해 `buyer-variance-review-hold`로 라우팅되었다.

## Visual QA

- Status: `PASS — 27/27` (fresh rerun against current `agent-plan-deck.html`)
- Fresh 27-screen evidence timestamp: `2026-08-24T10:27:55.591Z` (`2026-08-24 19:27:55 KST`)
- Fresh motion/focus evidence timestamp: `2026-08-24T10:29:31.032Z` (`2026-08-24 19:29:31 KST`)
- Browser: Microsoft Edge Chromium, Playwright headless 단일 세션
- Viewports: `375×667`, `768×720`, `1280×720`
- Screen coverage: 각 viewport의 9개 화면, 총 27개 PNG
- Fit rule: 모든 화면에서 document와 active screen의 가로/세로 overflow가 1px 이하, 실제 결과는 0px; footer가 viewport 안에 완전히 보이고 active screen 수는 1개.
- Pixel rule: 모든 PNG의 실제 픽셀 크기가 요청 viewport와 정확히 일치.
- Interaction: 각 viewport에서 Home, Space, ArrowRight, End, PageUp 실제 키보드 순서를 검증해 3/3 PASS. 화면 dot click은 27회 순회에 사용되어 정상 동작 확인.
- Manual inspection: 3개 3×3 contact sheet와 모바일 고밀도 화면 03/04/08을 직접 확인했다. 27화면에서 CJK glyph 누락·한 글자 고아줄·카드/테이블 충돌·푸터 잘림·부분 합성·예상치 못한 내부 스크롤을 발견하지 못했다.
- Focused final-patch inspection: `375×667 / screen-04`의 네 table card에서 filename, canonical columns, writer, state label을 읽을 수 있고 충돌·클리핑·고아줄이 없다. `768×720 / screen-03`의 computed `.tag`와 `.owner` font-size 최솟값은 각각 `10px`이며 세로 체인의 모든 label/owner/payload가 읽힌다.
- Normal-motion evidence: screen 01 rest는 opacity `1`과 원점 행렬, screen 02의 `80ms` mid-transition은 opacity `0.684643`과 X 이동 `4.41499px`, screen 02 settled는 opacity `1`과 원점 행렬로 관측되어 전환 상태 3개가 구분된다.
- Focus-visible evidence: `375×667`과 `1280×720`에서 키보드 Tab으로 첫 nav dot에 진입했으며 둘 다 `:focus-visible=true`, `3px` white + `5px` red box-shadow가 계산·렌더링되었다.
- Contact sheet provenance: 3개 contact sheet는 최종 27개 개별 PNG를 덮어쓴 뒤 `2026-08-24 19:29:48 KST`에 해당 PNG만으로 다시 합성했다.
- Evidence: `evidence/browser-qa.json`, `evidence/motion-focus-qa.json`, `evidence/visual/<viewport>/screen-01..09.png`, `evidence/visual/contact-<viewport>.png`, `evidence/visual/states/*.png`.
- Execution note: 최초 raw Chrome 개별 프로필 방식은 프로세스 재사용으로 2장 뒤 중단했다. 단일 Playwright 세션으로 전환해 27장을 새로 덮어썼고 `.chrome-profile`과 `.profile-*` 임시 디렉터리는 최종 증거에서 모두 삭제했다.

## Human stops and next actions

| Halt | Owner | Reason | Next action |
|---|---|---|---|
| `missing-input-hold` | sourcing analyst / buyer | 입력 파일 누락 시 추측 금지 | 승인된 가상 입력을 복구하거나 실행 취소 |
| `buyer-variance-review-hold` | buyer | threshold 초과, parse failure, missing match, ambiguity는 정책 판단 | 예외·근거 확인 후 brief 단계 진행 여부 결정 |
| `buyer-confirmation-hold` | buyer | 공급업체 선택은 사람 책임 | 모든 quote와 예외 확인 후 별도 승인 절차 수행 |
| `external-action-hold` | buyer/system owner | connector와 구매 실행 권한 없음 | 이 패키지 밖에서 승인된 절차를 사용; agent가 실행하지 않음 |

## Missing or unverified

- `sourcing-policy.csv`의 운영 열 스키마와 기준값 위치: `(미확인)`. 입력 번들에 없으므로 발명하지 않았다.
- 실제 운영 통화 변환 소스와 지원 통화 목록: `(미확인)`. 정규화 스킬은 확인된 지원 통화만 처리해야 한다.
- ERP write connector: 승인되지 않음. 현재는 독립.

이 항목들은 fictional package validation의 RED 충돌은 아니지만 production activation blocker다. 구매담당자와 system owner가 스키마·통화 소스·connector 범위를 확인하기 전에는 실제 데이터로 실행하지 않는다.

## Counter-rationale

브리프 작성이 향후 단순 결정론적 템플릿 렌더링으로 축소되어 고유 acceptance test를 잃거나, 실제 독립 AI 작업 수가 2개 이하가 되면 `team agent`는 과도하다. 그때는 동일한 표·writer·payload·threshold·human hold를 유지한 채 `team skillpack`으로 되돌리는 편이 운영 복잡도와 권한 오해를 줄인다.
