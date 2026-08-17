#!/usr/bin/env bash
# 상류 코치 산출물 → 스킬 → 게이트 → 하네스 전 구간 테스트
#
# 검증하는 것: 세션 3(ATF)·4(와이어프레임)의 실제 출력 규격이 세션 6 통합 파이프라인을
# 통과하는가. 상류에 없는 정보는 RED로 정확히 걸리고, 팀이 채우면 GREEN→PASS가 되는가.
set -u
cd "$(dirname "$0")/.."
PACK="${1:-/tmp/upstream-e2e-pack}"
rm -rf "$PACK"

echo "═══ 1. 상류 산출물 → 스킬 변환 ═══"
python3 harness/adapt_upstream.py examples/upstream/wireframe \
        examples/upstream/atf/ATF보고서_전황업데이트.html "$PACK" || exit 1

echo
echo "═══ 2. 계약 게이트 (상류 그대로 = 정보 부족이므로 RED가 정답) ═══"
python3 harness/check_contract.py "$PACK" >/dev/null 2>&1
code=$?
if [ $code -eq 2 ]; then
  echo "✅ RED (예상대로) — 상류에 체인 정보가 없어 팀 결정이 필요함"
else
  echo "❌ RED가 나와야 하는데 종료 코드 $code — 게이트가 정보 부족을 놓쳤다"
  exit 1
fi

echo
echo "═══ 3. 세션 6 확정 반영 (계약·기획서·스킬 정렬) ═══"
python3 harness/fixtures_session6.py "$PACK" || exit 1

echo
echo "═══ 4. 게이트 → 하네스 (여기서 전체 통과해야 함) ═══"
python3 harness/check_contract.py "$PACK" --run-harness
final=$?
echo
if [ $final -eq 0 ]; then
  echo "✅ 전 구간 통과 — 상류 규격이 통합 파이프라인과 호환됨"
else
  echo "❌ 실패 (종료 코드 $final)"
fi
exit $final
