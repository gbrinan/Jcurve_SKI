# Sourcing Operations Lab package manifest

## Package

| 항목 | 값 |
|---|---|
| 이름 | `Sourcing Operations Lab` |
| 형태 | `team agent` |
| 목적 | 가상 공급업체 견적을 보존·정규화하고 정책 편차와 검토 브리프를 사람의 구매 판단 앞까지 생성 |
| 현재 상태 | 합성 fixture로 로컬 실행 가능, 운영 연결은 차단 |

## Generated agent and skills

- 에이전트 정의: [AGENTS.md](AGENTS.md)
- 실행 계획 정본: [agent-plan.md](agent-plan.md)
- 계약 정본: [CONTRACT.md](CONTRACT.md)

| 스킬 | 소유자 | 입력 → 출력 | 다음 단계 |
|---|---|---|---|
| [quote-intake-normalizer](skills/depth/quote-intake-normalizer/SKILL.md) | `sourcing-analyst` | `quote_bundle → normalized_quotes` | `quote-variance-analyzer` |
| [quote-variance-analyzer](skills/depth/quote-variance-analyzer/SKILL.md) | `sourcing-analyst` | `normalized_quotes → variance_flags` | 구매담당자 검토 후 `sourcing-review-brief` |
| [sourcing-review-brief](skills/breadth/sourcing-review-brief/SKILL.md) | `buyer` | `variance_flags → sourcing_review_brief` | `buyer-confirmation-hold` |

## Run now

패키지 루트에서 다음을 실행한다.

```powershell
node run.mjs
```

- 입력: `data/input/incoming-quotes.csv`와 `data/reference/l4-policy-fixture.json`
- 생성: `data/output/normalized-quotes.csv`, `comparison-table.csv`, `sourcing-review-brief.md`, `trace.json`
- 가상 기대 결과: 입력 3행 보존, 정상 1건, 사람 검토 2건, 사람 정지점 2개, 외부 행동 0건
- 첫 사람 정지: `buyer-variance-review-hold`. 구매담당자가 예외와 근거를 확인하기 전에는 브리프 단계로 진행하지 않는다.

실행 전에 화면으로 확인하려면 [agent-mockup.html](agent-mockup.html)을 연다. 발표용 요약은 [agent-plan-deck.html](agent-plan-deck.html), 검증 근거는 [validation-report.md](validation-report.md)에서 확인한다.

## Safety and production blockers

- 공급업체 선택, 연락, 구매주문 전송, ERP 반영은 실행하지 않는다.
- 운영 `sourcing-policy.csv` 스키마·환율 소스·connector가 승인되지 않아 production activation은 차단한다.
- 실제 사용 전 합성 입력을 승인된 비식별 입력으로 교체하고 사람 정지점을 다시 확인한다.
