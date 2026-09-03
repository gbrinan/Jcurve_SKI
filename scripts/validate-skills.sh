#!/usr/bin/env bash
# 스킬 카탈로그 검증 — CLAUDE.md의 규약대로 출하 가능한가. skillmergeagent의 것을 이 저장소 절 이름에 맞춘 사본.
set -uo pipefail
cd "$(dirname "$0")/.."

fail=0
err() { echo "::error::$*"; fail=1; }

python3 -c "import json; json.load(open('.claude-plugin/plugin.json', encoding='utf-8'))" 2>/dev/null \
  || err "plugin.json is not valid JSON"

required_sections=("변환 절차" "산출물 이름 규칙")
desc_max=800

while IFS= read -r f; do
  d=$(dirname "$f"); name=$(awk -F': *' '/^name:/{gsub(/\r$/, "", $2); print $2; exit}' "$f")
  grep -q '^description:' "$f"                       || err "$f: missing 'description'"
  [ -n "$name" ]                                     || err "$f: missing 'name'"
  [ "$name" = "$(basename "$d")" ]                   || err "$f: name '$name' != directory '$(basename "$d")'"
  grep -qF "\"./$d\"" .claude-plugin/plugin.json     || err "$d: not registered in plugin.json"
  grep -qF "$d/SKILL.md" README.md                   || err "$d: not listed in README.md"
  grep -q '\.\./' "$f"                               && err "$f: deep cross-file ref ('../') — compose by naming, not relative links"
  desc_len=$(awk '/^description:/{sub(/^description: */,""); gsub(/^"|"$/,""); print length; exit}' "$f")
  [ -n "$desc_len" ] && [ "$desc_len" -le "$desc_max" ] \
    || err "$f: description length ${desc_len:-0} > $desc_max chars"
  for sec in "${required_sections[@]}"; do
    grep -qE "^## +${sec}\$" "$f" || err "$f: missing required section '## ${sec}'"
  done
done < <(find skills -name SKILL.md)

while IFS= read -r p; do
  [ -f "$p/SKILL.md" ] || err "plugin.json: '$p' has no SKILL.md"
done < <(grep -oE '\./skills/[A-Za-z0-9/_-]+' .claude-plugin/plugin.json)

if [ "$fail" -eq 0 ]; then
  echo "✓ skill catalog valid ($(find skills -name SKILL.md | wc -l | tr -d ' ') skills)"
else
  echo "✗ catalog validation failed"; exit 1
fi
