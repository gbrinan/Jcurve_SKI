#!/usr/bin/env python3
"""팩 스킬 내보내기 — 팩의 Lv6 명세를 Claude Code가 부를 수 있는 스킬로 만든다.

사용:
    python3 check/export_skills.py <팩 경로>                → <팩>/export/skills/
    python3 check/export_skills.py <팩> --install           → ~/.claude/skills/ 에 바로 설치
    python3 check/export_skills.py <팩> --dest <폴더>

무엇이 나오는가:
    · Lv6 스킬 하나당 폴더 하나 — `/평가정합성검증` 처럼 개별 호출 가능
    · 팀 에이전트 스킬 하나 — `/연간성과평가운영` 을 부르면 Claude가 CONTRACT.md의
      순서대로 스킬들을 이어 실행하고, 갈림길은 when 조건으로 판단하고,
      **사람고유 지점에서 멈춰 확인을 요청한다.**

무엇을 지어내지 않는가:
    description·판단기준·정지 규칙은 전부 팩에 이미 있는 문장에서 조립한다.
    (미정)인 것은 (미정)이라고 말하는 스킬이 된다 — 스킬이 되면서 그럴듯해지지 않는다.

왜 이렇게 되는가:
    팩 스킬의 판단기준은 한국어 문장이라 파이썬은 계산하지 못한다(orchestrate.py의 경계).
    그러나 **Claude는 그 문장을 읽고 판단할 수 있다.** 그래서 내보낸 스킬의 본문은
    원래 명세 그대로이고, frontmatter만 Claude Code 형식으로 입힌다.
"""
import re
import shutil
import sys
from pathlib import Path


def parse_skill(p):
    text = p.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None, ""
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def load_skills(pack):
    out = {}
    for p in sorted(pack.glob("skills/*/*/[sS][kK][iI][lL][lL].md")):
        meta, body = parse_skill(p)
        if meta and "name" in meta:
            out[meta["name"]] = (meta, body)
    return out


def slug(s):
    """스킬 폴더 이름 — 한글은 그대로, 공백·슬래시만 정리한다."""
    s = re.sub(r"[\s/·.]+", "-", s.strip())
    return re.sub(r"-{2,}", "-", s).strip("-")


def rule_of(body):
    m = re.search(r"^## 판단기준.*?\n(.*?)(?=\n##|\Z)", body, re.S | re.M)
    if not m:
        return ""
    for line in m.group(1).splitlines():
        s = line.strip().lstrip("-").strip()
        if s and not s.startswith("("):
            return s
    return ""


def plan_facts(pack):
    f = pack / "agent-plan.md"
    txt = f.read_text(encoding="utf-8") if f.is_file() else ""
    g = lambda pat: (re.search(pat, txt, re.M) or [None, ""])[1].strip()
    one = ""
    m = re.search(r"^- 한 문장:\s*(.+(?:\n  +\S.*)*)$", txt, re.M)
    if m:
        one = re.sub(r"\s*\n\s+", " ", m.group(1)).strip()
    title = (re.search(r"^#\s+(.+)$", txt, re.M) or [None, pack.name])[1].strip()
    title = re.sub(r"\s*\([^)]*\)\s*$", "", title)
    title = re.sub(r"\s*팀?\s*기획서\s*$", "", title).strip() or pack.name
    return {"title": title, "one": one,
            "lv4": g(r"^- Lv4:\s*(.+)$"), "lv5": g(r"^- Lv5:\s*(.+)$")}


def nexts_of(meta):
    v = meta.get("next", "")
    if not v or v == "null":
        return []
    return [x.strip() for x in re.split(r"[|,]", v) if x.strip() and x.strip() != "null"]


def esc(s):
    return s.replace('"', "'")


def export_task_skill(name, meta, body, facts, dest):
    """Lv6 스킬 하나 → 호출 가능한 스킬 하나. 본문은 원래 명세 그대로."""
    human = meta.get("human", "(미정)")
    rule = rule_of(body)
    ins = meta.get("inputs", "[]").strip("[]")
    outs = meta.get("outputs", "[]").strip("[]")

    # description은 팩에 이미 있는 문장으로만 조립한다.
    desc = (f"{facts['lv5'] or facts['title']} 팀 에이전트의 Lv6 태스크. "
            + (f"{rule} " if rule else "판단기준은 아직 (미정)이다. ")
            + f"입력: {ins or '(미정)'} → 출력: {outs or '(미정)'}. "
            + ("사람고유 태스크 — 목록·근거만 만들고 사람 확인을 기다린다. "
               if human == "사람고유" else "")
            + f"'{name}' 또는 '{name} 해줘'라고 하면 이 스킬을 쓴다.")

    guard = []
    if human == "사람고유":
        guard = ["", "## ⛔ 이 스킬이 하지 않는 것",
                 "이 태스크는 **사람고유**다. 판단·승인·발송을 대신하지 않는다.",
                 "자료를 정리해 사람 앞에 놓고 **멈춘다.** 사용자가 결정을 말하기 전에는",
                 "다음 단계로 진행하지 않는다.", ""]

    fm = ["---",
          f"name: {slug(name)}",
          'version: "1.0.0"',
          f'description: "{esc(desc)}"',
          "allowed-tools: Read, Write, Glob, Grep",
          "user-invocable: true",
          "# ── 아래는 팩 원본 메타데이터 (점검기·목업이 쓰는 값 그대로) ──"]
    for k in ("owner", "quadrant", "human", "skillability", "source_id",
              "inputs", "outputs", "reads", "writes", "next",
              "when", "loop_to", "loop_exit"):
        if meta.get(k):
            fm.append(f"{k}: {meta[k]}")
    fm.append("---")

    d = dest / slug(name)
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(
        "\n".join(fm) + "\n\n" + "\n".join(guard) + body.strip() + "\n", encoding="utf-8")
    return slug(name)


def export_team_skill(pack, sk, facts, dest):
    """Lv5 팀 에이전트 스킬 — Claude가 계약의 순서대로 스킬을 이어 실행한다."""
    contract = (pack / "CONTRACT.md").read_text(encoding="utf-8") \
        if (pack / "CONTRACT.md").is_file() else ""
    m = re.search(r"^chain:\s*(.+)$", contract, re.M)
    chain = m.group(1).strip() if m else "(미정)"
    m = re.search(r"^halt_at:\s*(.+)$", contract, re.M)
    halt = m.group(1).strip() if m else "(미정)"

    name = slug(facts["title"])
    humans = {n: (mt.get("human") or "").strip() for n, (mt, _) in sk.items()}
    human_only = [n for n, h in humans.items() if h == "사람고유"]
    forks = {n: (mt.get("when") or "").strip() for n, (mt, _) in sk.items()
             if len(nexts_of(mt)) > 1}
    loops = [(n, mt.get("loop_to", "").strip(), mt.get("loop_exit", "").strip())
             for n, (mt, _) in sk.items()
             if mt.get("loop_to") and mt.get("loop_to").strip() not in ("", "null")]

    desc = (f"{facts['title']} — Lv5 팀 에이전트. "
            + (f"{facts['one']} " if facts["one"] else "")
            + f"Lv6 스킬 {len(sk)}개를 계약(CONTRACT.md)의 순서대로 이어 실행한다. "
            + (f"사람 확인 지점: {', '.join(human_only)}. " if human_only else "")
            + f"'{facts['title']} 실행해줘', '팀 에이전트 돌려줘'라고 하면 이 스킬을 쓴다.")

    body = [f"# {facts['title']} — Lv5 팀 에이전트", "",
            f"> Lv4 「{facts['lv4'] or '(미정)'}」 › Lv5 「{facts['lv5'] or '(미정)'}」",
            ""]
    if facts["one"]:
        body += [facts["one"], ""]
    body += ["## 실행 규칙", "",
             "1. 아래 **체인 순서대로** 각 태스크 폴더의 SKILL.md를 읽고 그 명세대로 수행한다.",
             "   판단기준이 (미정)인 태스크는 지어내지 말고, 무엇이 미정인지 사용자에게 말한다.",
             f"2. 체인: `{chain}`", ""]
    if forks:
        body += ["3. **갈림길** — 아래 조건으로 판단해 한쪽으로 간다. 조건을 판단할 근거가",
                 "   데이터에 없으면 추측하지 말고 사용자에게 묻는다."]
        for n, w in forks.items():
            body.append(f"   - {n}: {w or '(조건 미정 — 사용자에게 묻는다)'}")
        body.append("")
    if loops:
        body += ["4. **루프백** — 되돌아가 반복한다. 탈출 조건이 찰 때까지."]
        for n, to, ex in loops:
            body.append(f"   - {n} ↩ {to} (탈출: {ex or '(미정)'})")
        body.append("")
    body += [f"5. ⛔ **정지 지점: {halt}**",
             "   여기 도달하면 산출물을 정리해 보여주고 **멈춘다.**",
             "   사용자가 확인·승인을 말하기 전에는 절대 다음으로 진행하지 않는다.",
             "   발송·승인·잠금 같은 행위는 이 스킬이 아니라 사람이 한다.", "",
             "## 태스크 스킬", ""]
    for n, (mt, bd) in sk.items():
        h = mt.get("human", "(미정)")
        body.append(f"- `{slug(n)}/` — {h}"
                    + (f" · {rule_of(bd)}" if rule_of(bd) else ""))
    body += ["", "## 산출물",
             "각 태스크의 outputs를 작업 폴더의 `out/` 아래 마크다운 표로 남긴다.",
             "무엇을 만들었고 어디서 멈췄는지를 마지막에 요약한다.", ""]

    fm = ["---", f"name: {name}", 'version: "1.0.0"',
          f'description: "{esc(desc)}"',
          "allowed-tools: Read, Write, Glob, Grep",
          "user-invocable: true", "---"]
    d = dest / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text("\n".join(fm) + "\n\n" + "\n".join(body), encoding="utf-8")

    # 팀 스킬이 참조할 데이터·계약 사본 — 스킬 폴더 하나로 자기완결이 되게.
    for extra in ("CONTRACT.md", "agent-plan.md", "AGENTS.md"):
        if (pack / extra).is_file():
            shutil.copy(pack / extra, d / extra)
    if (pack / "data").is_dir():
        shutil.copytree(pack / "data", d / "data", dirs_exist_ok=True)
    return name


def main(pack_dir, dest_dir=None, install=False):
    pack = Path(pack_dir)
    sk = load_skills(pack)
    if not sk:
        print(f"❌ {pack}: 스킬을 찾지 못했습니다")
        return 2
    facts = plan_facts(pack)

    if install:
        dest = Path.home() / ".claude" / "skills"
    else:
        dest = Path(dest_dir) if dest_dir else pack / "export" / "skills"
    dest.mkdir(parents=True, exist_ok=True)

    team = export_team_skill(pack, sk, facts, dest)
    names = [export_task_skill(n, m, b, facts, dest) for n, (m, b) in sk.items()]

    print(f"내보내기: {dest}")
    print(f"  팀 에이전트 스킬 1개: /{team}")
    print(f"  Lv6 태스크 스킬 {len(names)}개: " + " ".join(f"/{n}" for n in names))
    human_only = [n for n, (m, _) in sk.items() if m.get("human") == "사람고유"]
    if human_only:
        print(f"  ⛔ 사람고유 {len(human_only)}개({', '.join(human_only)})는 "
              f"멈추는 규칙이 본문에 박혀서 나갑니다")
    if not install:
        print(f"\n설치하려면:  cp -R {dest}/* ~/.claude/skills/")
        print("또는 처음부터:  python3 check/export_skills.py <팩> --install")
    print("Claude Code를 새로 열면 목록에 뜹니다.")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(2)
    pack, dest, install = args[0], None, False
    i = 1
    while i < len(args):
        if args[i] == "--dest" and i + 1 < len(args):
            dest = args[i + 1]; i += 2
        elif args[i] == "--install":
            install = True; i += 1
        else:
            i += 1
    sys.exit(main(pack, dest, install))
