#!/usr/bin/env python3
"""에이전트 실행 화면 목업 생성기 — 손으로 쓰던 것을 실행 결과에서 만든다.

사용: python3 check/make_mockup.py <팩 경로>   → <팩>/agent-mockup.html

읽는 것:
  · <팩>/out/trace.json   — run.py가 남긴 실행 기록. 화면의 **모든 숫자가 여기서 온다.**
  · <팩>/skills/*/*/SKILL.md — 진행 레일에 쓸 순서·Human 여부·루프백
  · DESIGN.md             — 색 토큰. 목업이 팔레트를 따로 갖지 않게 한다 (SSOT)

trace.json이 없으면 만들지 않는다. 실행하지 않은 화면은 지어낸 화면이다.
"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trace import load as load_trace   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# DESIGN.md에 없지만 목업에만 필요한 것 — 없으면 여기 기본값을 쓴다.
FALLBACK = {"loop": "#5B4FCF", "warn": "#B26A00"}
HUMAN_CLS = {"자동": "auto", "증강": "aug", "사람고유": "human"}


def e(s):
    return html.escape(str(s), quote=True)


def rich(s):
    """기록에 적힌 **굵게**·`코드`를 화면에서도 굵게·코드로. 그 밖의 태그는 막는다."""
    s = e(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def money(s):
    """표의 정수 칸에 천 단위 쉼표. 화면에서만 — 원본 파일은 그대로 둔다."""
    if re.fullmatch(r"-?\d{4,}", s):
        return f"{int(s):,}"
    return s


def tokens():
    """DESIGN.md의 토큰 표에서 색을 읽는다 — 목업이 팔레트를 복제하지 않도록."""
    md = ROOT / "DESIGN.md"
    t = {}
    if md.is_file():
        for name, val in re.findall(r"`--([a-z-]+)`\s*\|\s*`(#[0-9A-Fa-f]{3,8})`",
                                    md.read_text(encoding="utf-8")):
            t[name] = val
    for k, v in FALLBACK.items():
        t.setdefault(k, v)
    return t


def skills(pack):
    out = {}
    for p in sorted(pack.glob("skills/*/*/[sS][kK][iI][lL][lL].md")):
        m = re.match(r"^---\n(.*?)\n---", p.read_text(encoding="utf-8"), re.S)
        if not m:
            continue
        meta = {}
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        if "name" in meta:
            out[meta["name"]] = meta
    return out


def rail(sk, tr):
    """상단 진행 레일 — 흐름 순서대로. 갈림길·사람고유·루프백을 색으로 구분."""
    nexts = {n: [x.strip() for x in re.split(r"[|,]", m.get("next", "")) if x.strip()
                 and x.strip() != "null"] for n, m in sk.items()}
    # 위상 정렬. 깊이 우선으로 걸으면 갈래가 만나는 지점이 형제 갈래보다 앞에 와서
    # 레일이 실제 순서와 어긋난다 (실측). 들어오는 화살표가 다 처리된 뒤에 놓는다.
    indeg = {n: 0 for n in sk}
    for v in nexts.values():
        for x in v:
            if x in indeg:
                indeg[x] += 1
    queue = [n for n in sk if indeg[n] == 0]
    order = []
    while queue:
        n = queue.pop(0)
        order.append(n)
        for m_ in nexts.get(n, []):
            if m_ in indeg:
                indeg[m_] -= 1
                if indeg[m_] == 0:
                    queue.append(m_)
    for n in sk:          # 순환에 갇힌 것도 빠뜨리지 않는다
        if n not in order:
            order.append(n)

    cycles = {l["from"]: l.get("cycles") for l in tr.get("loops", [])}
    out = []
    for i, n in enumerate(order):
        cls, extra = "done", ""
        if len(nexts.get(n, [])) > 1:
            cls, extra = "fork", "◆ "
        if sk[n].get("loop_to"):
            cls, extra = "loop", "↩ "
        if sk[n].get("human") == "사람고유" and not sk[n].get("loop_to"):
            cls, extra = "halt", "⛔ "
        c = cycles.get(n)
        times = ""
        for l in tr.get("loops", []):
            if l["to"] == n and l.get("cycles"):
                times = f" ×{l['cycles']}"
        out.append(f'<span class="n {cls}">{extra}{e(n)}{times}</span>')
        if i < len(order) - 1:
            out.append('<span class="arrow">›</span>')
    return "\n  ".join(out)


def table_html(t):
    head = "".join(f"<th>{e(c)}</th>" for c in t["cols"])
    body = []
    for r in t["rows"]:
        cls = f' class="{r["mark"]}"' if r.get("mark") else ""
        tds = "".join(
            f'<td class="num">{e(money(c))}</td>' if re.fullmatch(r"-?[\d,]+", c)
            else f"<td>{e(c)}</td>"
            for c in r["cells"])
        body.append(f"<tr{cls}>{tds}</tr>")
    return (f'<div class="scroll"><table><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def step_html(s, sk):
    if s["kind"] == "loopback":
        return (f'<div class="loopback">↩ {e(s["to"])}로 되돌아감'
                f'{" &nbsp;·&nbsp; 탈출 조건: " + e(s["exit"]) if s.get("exit") else ""}</div>')

    hc = HUMAN_CLS.get(s.get("human"), "")
    tags = [f'<span class="tag {hc}">{e(s["human"])}</span>'] if s.get("human") else []
    if s["kind"] == "fork":
        tags.append('<span class="tag fork">◆ 갈림길</span>')
    if s["kind"] == "halt":
        tags.append('<span class="tag human">멈춤</span>')
    if s.get("cycle"):
        tags.insert(0, f'<span class="cycle">{s["cycle"]}회차</span>')

    body = [f"<p>{rich(s['note'])}</p>"] if s.get("note") else []
    for w in s.get("warns", []):
        body.append(f'<div class="warn">⚠️ {rich(w)}</div>')

    if s["kind"] == "fork":
        cards = []
        for b in s["branches"]:
            # 어느 갈래로 갔는지는 taken이 말한다 — 건수 0을 "안 갔다"로 읽지 않는다.
            taken = ' taken' if b.get("to") == s.get("taken") else ""
            cnt = (f'<div class="cnt">{b["count"]}<span>건</span></div>'
                   if b.get("count") is not None else '<div class="cnt none">—</div>')
            cards.append(f'<div class="br{taken}"><div class="cond">{e(b["cond"])}</div>'
                         f'<div class="to">→ {e(b["to"])}</div>{cnt}</div>')
        body.append(f'<div class="branches">{"".join(cards)}</div>')

    for t in s.get("tables", []):
        body.append(table_html(t))

    if s["kind"] == "halt":
        if s.get("checklist"):
            items = "".join(f"<li>☐ {rich(c)}</li>" for c in s["checklist"])
            body.append(f'<ul class="chk">{items}</ul>')
        if s.get("actions"):
            btns = "".join(
                "<button{}>{}</button>".format(' class="primary"' if i == 0 else "", e(a))
                for i, a in enumerate(s["actions"]))
            body.append(f'<div class="actions">{btns}</div>')
            body.append('<p class="disabled-note">※ 목업입니다. 이 팩에는 실행 코드가 없습니다 — '
                        '버튼은 동작하지 않습니다.</p>')

    for f in s.get("files", []):
        cnt = f' <b>{f["count"]}건</b>' if f.get("count") is not None else ""
        body.append(f'<div class="files"><span class="file">→ {e(f["path"])}{cnt}</span></div>')

    cls = {"fork": " fork-card", "halt": " halt"}.get(s["kind"], "")
    return (f'<div class="card{cls}"><header><b>{e(s["skill"])}</b>{"".join(tags)}</header>'
            f'<div class="body">{"".join(body)}</div></div>')


def css(tk):
    root = " ".join(f"--{k}:{v};" for k, v in tk.items())
    return f"""
  :root {{ {root} }}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:var(--bg-soft);color:var(--text);
       font:15px/1.6 -apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif}}
  .app{{max-width:1120px;margin:0 auto;background:var(--bg);min-height:100vh;
       border-left:1px solid var(--line);border-right:1px solid var(--line)}}
  .top{{display:flex;align-items:center;gap:12px;padding:14px 22px;
       border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:5}}
  .mark{{width:30px;height:30px;border-radius:8px;background:var(--brand);color:#fff;
        display:grid;place-items:center;font-size:14px;font-weight:700;flex:none}}
  .top h1{{font-size:15px;letter-spacing:-.01em}}
  .top .sub{{font-size:12px;color:var(--muted)}}
  .pill{{margin-left:auto;font-size:11px;border:1px solid var(--line);border-radius:999px;
        padding:3px 10px;color:var(--muted)}}
  .rail{{display:flex;gap:6px;padding:14px 22px;overflow-x:auto;align-items:center;
        border-bottom:1px solid var(--line);background:var(--bg-soft)}}
  .rail .n{{flex:none;font-size:12px;padding:5px 11px;border-radius:999px;white-space:nowrap;
           border:1px solid var(--line);background:var(--bg);color:var(--muted)}}
  .rail .n.done{{border-color:var(--ok);color:var(--ok)}}
  .rail .n.fork{{border-color:var(--brand-sub);color:var(--brand-sub);font-weight:600}}
  .rail .n.halt{{border-color:var(--brand);color:var(--brand);font-weight:600}}
  .rail .n.loop{{border-color:var(--loop);color:var(--loop);font-weight:600}}
  .rail .arrow{{flex:none;color:var(--line);font-size:12px}}
  main{{padding:20px 22px 60px}}
  .log{{display:flex;flex-direction:column;gap:14px}}
  .card{{border:1px solid var(--line);border-radius:10px;overflow:hidden}}
  .card>header{{display:flex;align-items:center;gap:9px;padding:10px 14px;font-size:13px;
                background:var(--bg-soft);border-bottom:1px solid var(--line)}}
  .card.fork-card{{border-color:var(--brand-sub)}}
  .card.halt{{border-color:var(--brand)}}
  .card.halt>header{{background:#FDF2F4;border-color:var(--brand);color:var(--brand)}}
  .tag{{font-size:11px;padding:1px 7px;border-radius:999px;border:1px solid var(--line);
       color:var(--muted)}}
  .tag.auto{{border-color:var(--ok);color:var(--ok)}}
  .tag.aug{{border-color:var(--brand-sub);color:var(--brand-sub)}}
  .tag.human{{border-color:var(--brand);color:var(--brand)}}
  .tag.fork{{border-color:var(--brand-sub);color:var(--brand-sub)}}
  .cycle{{font-size:11px;border:1px solid var(--loop);color:var(--loop);border-radius:999px;
         padding:1px 8px;font-weight:600}}
  .body{{padding:13px 14px;font-size:14px}}
  .body p+p{{margin-top:6px}}
  .files{{margin-top:9px;display:flex;gap:6px;flex-wrap:wrap}}
  .file{{font-size:12px;border:1px solid var(--line);border-radius:6px;padding:3px 9px;
        color:var(--muted)}}
  .file b{{color:var(--text);font-weight:600}}
  .warn{{background:#FFF6F0;border:1px solid var(--brand-sub);border-radius:8px;
        padding:10px 12px;font-size:13px;margin-top:10px}}
  .branches{{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));
            gap:10px;margin-top:11px}}
  .br{{border:1px solid var(--line);border-radius:8px;padding:11px 12px}}
  .br.taken{{border-color:var(--brand-sub);background:#FFF9F5}}
  .br .cond{{font-size:11px;color:var(--brand-sub);font-weight:600;margin-bottom:3px}}
  .br .to{{font-size:13px;font-weight:600}}
  .br .cnt{{font-size:22px;font-weight:700;letter-spacing:-.02em;margin-top:5px}}
  .br .cnt.none{{color:var(--muted);font-weight:400}}
  .br .cnt span{{font-size:12px;font-weight:400;color:var(--muted);margin-left:3px}}
  .loopback{{text-align:center;font-size:12px;color:var(--loop);padding:7px;font-weight:600;
            border:1px dashed var(--loop);border-radius:8px;background:#F8F7FE}}
  .scroll{{overflow-x:auto;margin-top:10px}}
  table{{width:100%;border-collapse:collapse;font-size:13px;min-width:520px}}
  th{{text-align:left;font-size:11px;color:var(--muted);font-weight:600;padding:6px 9px;
     border-bottom:1px solid var(--line);white-space:nowrap}}
  td{{padding:6px 9px;border-bottom:1px solid var(--line);white-space:nowrap}}
  td.num{{text-align:right;font-variant-numeric:tabular-nums}}
  tr.diff td{{background:#FFF6F0}}
  tr.na td{{color:var(--muted)}}
  tbody tr:last-child td{{border-bottom:none}}
  .chk{{list-style:none;margin-top:10px;font-size:13px}}
  .chk li{{padding:5px 0;border-bottom:1px solid var(--line)}}
  .chk li:last-child{{border-bottom:none}}
  .actions{{display:flex;gap:8px;margin-top:13px;flex-wrap:wrap}}
  button{{font:inherit;font-size:13px;padding:8px 16px;border-radius:7px;cursor:not-allowed;
         border:1px solid var(--line);background:var(--bg);color:var(--muted)}}
  button.primary{{background:var(--brand);border-color:var(--brand);color:#fff}}
  .disabled-note{{font-size:12px;color:var(--muted);margin-top:7px}}
  .foot{{margin-top:26px;padding-top:16px;border-top:1px solid var(--line);
        font-size:12px;color:var(--muted);line-height:1.8}}
  .foot code{{background:var(--bg-soft);border:1px solid var(--line);border-radius:4px;
             padding:1px 5px}}
"""


def main(pack_dir):
    pack = Path(pack_dir)
    tr = load_trace(pack)
    if tr is None:
        print(f"❌ {pack}/out/trace.json 이 없습니다.")
        print("   먼저 run.py를 돌리십시오 — 실행하지 않은 화면은 지어낸 화면입니다.")
        return 2

    sk = skills(pack)
    kind = []
    if any(len(re.split(r"[|,]", m.get("next", ""))) > 1 for m in sk.values()
           if m.get("next") and m.get("next") != "null"):
        kind.append("갈림길")
    if tr.get("loops"):
        kind.append("루프백")
    verdict = f"팀 에이전트 · {'+'.join(kind)}" if kind else "팀 스킬팩"

    ins = " · ".join(f"{e(i['name'])} <b>{i['count']}건</b>" for i in tr["inputs"])
    input_card = (
        f'<div class="card"><header><b>입력</b>'
        f'<span class="tag">{e(tr["inputs"][0].get("note", "")) if tr["inputs"] else ""}</span>'
        f'</header><div class="body"><p>{ins}</p></div></div>') if tr["inputs"] else ""

    steps = "\n\n  ".join(step_html(s, sk) for s in tr["steps"])
    loops = " · ".join(f"{e(l['from'])} ↩ {e(l['to'])}"
                       + (f" ({l['cycles']}회차)" if l.get("cycles") else "")
                       for l in tr.get("loops", []))

    doc = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(tr['title'])} — 실행 화면</title>
<!-- 이 파일은 check/make_mockup.py 가 out/trace.json 에서 생성했습니다.
     손으로 고치지 마십시오 — run.py를 다시 돌리고 이 스크립트를 다시 실행하십시오.
     색 토큰의 SSOT는 DESIGN.md 입니다. -->
<style>{css(tokens())}</style>
</head>
<body>
<div class="app">

<div class="top">
  <div class="mark">{e(tr['title'][:1])}</div>
  <div>
    <h1>{e(tr['title'])}</h1>
    <div class="sub">{e(tr['source'])}{' · Lv5 「' + e(tr['lv5']) + '」' if tr.get('lv5') else ''}</div>
  </div>
  <span class="pill">{e(verdict)}</span>
</div>

<div class="rail">
  {rail(sk, tr)}
</div>

<main>
<div class="log">

  {input_card}

  {steps}

</div>

<div class="foot">
  {e(tr.get('summary', ''))}<br>
  {'루프백: ' + loops + '<br>' if loops else ''}
  이 화면은 <code>python3 run.py</code>의 실제 실행 결과입니다 —
  숫자·표는 <code>out/trace.json</code>에서 그대로 가져왔습니다.
  데이터를 고치고 다시 돌리면 이 화면도 다시 만들어야 합니다:
  <code>python3 check/make_mockup.py {e(pack.name)}</code><br>
  {e(tr['source'])} · 데이터는 실습용 가상 값입니다.
</div>
</main>
</div>
</body>
</html>
"""
    out = pack / "agent-mockup.html"
    out.write_text(doc, encoding="utf-8")
    print(f"목업 생성: {out}")
    print(f"  단계 {len([s for s in tr['steps'] if s['kind'] != 'loopback'])}개 · "
          f"표 {sum(len(s.get('tables', [])) for s in tr['steps'])}개 · "
          f"루프백 {len(tr.get('loops', []))}곳 · 판정 {verdict}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
