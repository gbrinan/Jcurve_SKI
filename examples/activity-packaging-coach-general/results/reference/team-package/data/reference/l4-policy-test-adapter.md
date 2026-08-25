# L4 policy test adapter

이 파일은 운영 `sourcing-policy.csv` 스키마를 정의하지 않는다. 승인 입력에 정책 열이 없으므로 L4 제어 흐름만 검증하는 합성 어댑터다.

- `Q-NORMAL`: item match 성공, 가격 편차 `0%`, 납기 편차 `0일`.
- `Q-REVIEW`: item match 성공, 가격 편차 `12.01%`, 납기 편차 `8일`.
- `Q-FAILED`: upstream `parse_status=review`; 정책 계산을 시도하지 않고 human review.

이 값은 테스트 픽스처일 뿐 운영 기준값·정책 열·공급업체 결과가 아니다.
