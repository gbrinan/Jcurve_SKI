# 계열사 AX전략 팀장에게 공유 — 팀 스킬팩

4개의 Lv6 태스크(공유대상자목록정리 → 관련회의록첨부 → 메일본문작성 → 메일발송)가
개별 조각이 아니라 **하나의 실행 단위**로 동작한다는 것을 실제로 보여주는 예시다.

```
python3 run.py
```

`data/`의 두 CSV를 읽어 `out/`에 4개 산출물을 낸다. 마지막 단계(메일 발송)는
사람고유라서 실제 발송 없이 확인 요청(`발송대기.md`)에서 멈춘다.

검증은 [`check/check_contract.py`](../../../check/check_contract.py)로:

```
python3 ../../../check/check_contract.py . --run-check
```

상세는 [agent-plan.md](agent-plan.md).
