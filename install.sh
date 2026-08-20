#!/usr/bin/env bash
# Activity Coach_SKI — 오프라인 설치 (macOS / Linux / WSL)
#
#   bash install.sh              ~/.claude/skills/ 에 설치 (모든 프로젝트에서 사용)
#   bash install.sh --project    ./.claude/skills/ 에 설치 (이 폴더에서만 사용)
#
# 인터넷·git·pip 모두 필요 없습니다. 파일 복사만 합니다.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS=("activity-coach" "slide-pack")

if [ "${1:-}" = "--project" ]; then
  DEST="$PWD/.claude/skills"; SCOPE="이 폴더"
else
  DEST="$HOME/.claude/skills";  SCOPE="모든 프로젝트"
fi

echo "Activity Coach_SKI 설치"
echo "  대상: $DEST  ($SCOPE 에서 사용)"
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ python3 가 없습니다. Python 3.8 이상을 먼저 설치하십시오."
  echo "   (외부 패키지는 필요 없습니다 — 표준 라이브러리만 씁니다)"
  exit 1
fi
echo "✅ $(python3 -V)"

mkdir -p "$DEST"
for s in "${SKILLS[@]}"; do
  src="$HERE/.claude/skills/$s"
  dst="$DEST/$s"
  [ -d "$src" ] || { echo "❌ 원본 없음: $src"; exit 1; }
  [ -d "$dst" ] && { echo "  기존 $s 제거"; rm -rf "$dst"; }
  mkdir -p "$dst"
  cp "$src/SKILL.md" "$dst/"
  echo "  · $s"
done

# 스킬이 실제로 실행할 것들을 함께 넣는다 — 스킬 폴더 하나로 자기완결이 되게.
cp -R "$HERE/check"   "$DEST/activity-coach/"
cp -R "$HERE/assets"  "$DEST/activity-coach/"
cp -R "$HERE/assets"  "$DEST/slide-pack/"
cp    "$HERE/DESIGN.md" "$DEST/slide-pack/"
mkdir -p "$DEST/activity-coach/examples"
cp -R "$HERE/examples/sample" "$DEST/activity-coach/examples/"

echo
echo "동작 확인"
if python3 "$DEST/activity-coach/check/run_check.py" \
     "$DEST/activity-coach/examples/sample/quarterly-close-agent" >/dev/null 2>&1; then
  echo "  ✅ 통합 점검기 정상 (재무 샘플 팩 통과)"
else
  echo "  ❌ 통합 점검기가 샘플 팩을 통과시키지 못했습니다. 복사가 덜 된 것 같습니다."
  exit 1
fi

cat <<EOF

설치 완료.

Claude Code를 새로 열고 이렇게 부르십시오:

  /activity-coach              팀 스킬들을 하나의 에이전트로 묶기
  /slide-pack agent-plan.md    문서를 발표용 슬라이드로

바로 해볼 것 (샘플 팩 실행):

  cd $DEST/activity-coach/examples/sample/quarterly-close-agent
  python3 run.py

지우려면: rm -rf $DEST/activity-coach $DEST/slide-pack
EOF
