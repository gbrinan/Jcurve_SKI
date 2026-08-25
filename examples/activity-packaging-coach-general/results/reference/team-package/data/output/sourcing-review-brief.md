# Fictional sourcing review brief

## Ordinary

- `Q-NORMAL`: 정책 매칭 성공, 가격 편차 0%, 납기 편차 0일, `pass`.

## Human review

- `Q-REVIEW`: 가격 편차 12.01%와 납기 편차 8일로 두 임계값을 모두 초과했다. 구매담당자가 정책 예외와 근거를 확인해야 한다.
- `Q-FAILED`: 가격 파싱 실패 행을 삭제하지 않고 보존했다. 구매담당자가 원본 값과 후속 조치를 확인해야 한다.

## Unresolved

- 운영 `sourcing-policy.csv` 열 스키마는 `(미확인)`이며 실제 연결 전에 구매담당자 확인이 필요하다.

## Buyer next action

`buyer-confirmation-hold`: 예외와 근거를 확인하고 공급업체 선택은 별도로 사람이 결정한다. 이 패키지는 구매주문을 보내거나 ERP에 쓰지 않는다.
