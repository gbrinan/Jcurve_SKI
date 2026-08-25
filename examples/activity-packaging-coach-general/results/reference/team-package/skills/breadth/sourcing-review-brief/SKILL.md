---
name: sourcing-review-brief
owner: buyer
inputs: variance_flags
outputs: sourcing_review_brief
reads: comparison-table.csv
writes: (none)
next: human
---

# Sourcing Review Brief

## Trigger

`variance_flags`가 완성되고 필요한 중간 구매담당자 검토가 해제되면 시작한다.

## Inputs

`comparison-table.csv`의 모든 견적, 상태, 근거와 해결되지 않은 질문.

## Procedure

1. ordinary, flagged, unresolved 행을 구분하되 모두 포함한다.
2. 견적별 근거와 남은 질문을 요약한다.
3. 구매담당자의 다음 행동을 명시한 `sourcing-review-brief.md`를 렌더링한다.
4. `buyer-confirmation-hold`에서 중단한다.

## Decision rules

모든 quote ID를 한 번 이상 명시하고, 검토 대상의 evidence와 구매담당자 다음 행동을 함께 제시한다.

## Exceptions

근거 누락은 해결된 것으로 표시하지 않고 unresolved로 남긴다. 구매담당자 확인이 없으면 최종 선택 단계로 진행하지 않는다.

## Output

`sourcing_review_brief` payload와 사람 검토용 `sourcing-review-brief.md`. 데이터 표 writeback은 없다.

## Completion conditions

브리프가 모든 quote ID, 근거, 미해결 질문, 구매담당자의 다음 행동을 포함하고 최종 human hold에 도달한다.

## Prohibited actions

공급업체 선택, 구매 승인, 구매주문 전송, ERP 쓰기, 미해결 근거 은폐.

## Visual delivery

브리프는 정상·예외·사람 책임을 제목, 상태 텍스트, 테두리, 색으로 동시에 구분하고 최종 `HUMAN / HOLD`와 금지된 외부 행동을 눈에 띄게 표시한다.
