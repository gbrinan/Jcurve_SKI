---
name: quote-variance-analyzer
owner: sourcing-analyst
inputs: normalized_quotes
outputs: variance_flags
reads: normalized-quotes.csv, sourcing-policy.csv
writes: comparison-table.csv
next: sourcing-review-brief
---

# Quote Variance Analyzer

## Trigger

`normalized_quotes`가 완성되고 승인된 `sourcing-policy.csv`를 읽을 수 있을 때 시작한다.

## Inputs

`normalized-quotes.csv` 전체 행과 읽기 전용 `sourcing-policy.csv`.

## Procedure

1. 정규화 견적과 정책을 `item_code`로 매칭한다.
2. 모든 견적의 가격 편차와 납기 편차를 계산한다.
3. 규칙·예외·근거를 `comparison-table.csv`에 기록한다.
4. 검토 조건이 하나라도 있으면 `buyer-variance-review-hold`에서 중단하고 구매담당자 확인을 요청한다.

## Decision rules

가격 편차가 `12% 초과`이거나 납기 편차가 `7일 초과`이면 human review다. 파싱 실패와 정책 매칭 누락도 human review다.

## Exceptions

정책 매칭이 없으면 review. 모호성은 구매담당자에게 라우팅한다. 정책 스키마·근거가 없으면 추측하지 않고 미해결로 남긴다.

## Output

`variance_flags` payload와 `comparison-table.csv`의 `quote_id, price_variance_pct, lead_variance_days, policy_status, evidence`.

## Completion conditions

모든 정규화 견적에 policy status가 있고 모든 flag에 evidence가 있으며, 검토 대상은 구매담당자 hold에 도달한다.

## Prohibited actions

공급업체 승인·선택, 정책 수정, 임계값 변경, 근거 없는 통과, 구매담당자 hold 우회.

## Visual delivery

각 행에 `SYSTEM / PASS`, `EXCEPTION / REVIEW`, `HUMAN / HOLD` 상태를 텍스트·테두리·색으로 함께 표시하고 임계값과 근거를 인접 배치한다.
