---
name: quote-intake-normalizer
owner: sourcing-analyst
inputs: quote_bundle
outputs: normalized_quotes
reads: incoming-quotes.csv
writes: normalized-quotes.csv
next: quote-variance-analyzer
---

# Quote Intake Normalizer

## Trigger

확인된 가상 견적 번들이 주간 또는 수시로 도착하면 시작한다.

## Inputs

`incoming-quotes.csv`의 `quote_id, supplier_code, item_code, unit_price, lead_days, currency` 전체 행.

## Procedure

1. 파일 존재를 확인하고 없으면 `missing-input-hold`에서 중단한다.
2. 모든 가상 견적 행을 읽고 source evidence를 보존한다.
3. 지원 통화만 KRW로 변환하고 필수 필드를 결정론적으로 정규화한다.
4. 각 입력 `quote_id`를 `normalized-quotes.csv`에 정확히 한 번 쓴다.

## Decision rules

지원되는 통화와 유효한 값만 정규화한다. 누락 가격을 추론하지 않는다.

## Exceptions

파싱 실패는 삭제하지 않고 `parse_status=review`로 남긴다. 입력 파일 누락은 실행을 중단한다.

## Output

`normalized_quotes` payload와 `normalized-quotes.csv`의 `quote_id, supplier_code, item_code, unit_price_krw, lead_days, parse_status`.

## Completion conditions

모든 입력 quote ID가 출력에 정확히 한 번 나타나고 source evidence와 실패 상태가 보존된다.

## Prohibited actions

공급업체 연락, 견적 선택, 누락 가격 추론, 실패 행 삭제, 입력 파일 수정.

## Visual delivery

사람에게 제시할 때 정상 행은 `SYSTEM`, 실패 행은 `EXCEPTION / REVIEW` 텍스트·테두리·색으로 함께 구분하고, 삭제된 행이 없음을 건수로 표시한다.
