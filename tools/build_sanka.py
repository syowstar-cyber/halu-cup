# -*- coding: utf-8 -*-
"""fp/events/第20回_四麻Halu杯_参加者案内.md → sanka/index.html（暗号化なし・公開）"""
import re, html, sys, datetime
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parents[2] / "fp" / "events" / "第20回_四麻Halu杯_参加者案内.md"
src = SRC.read_text(encoding="utf-8-sig").splitlines()
updated = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s

out, table, lst = [], [], None
section = ""
i = 0
while i < len(src) and not src[i].startswith("## 1."):
    i += 1

def flush_table():
    global table
    if not table:
        return
    rows = [r for r in table if not re.match(r"^\|\s*-", r)]
    h = ['<div class="tw"><table>']
    for k, r in enumerate(rows):
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        tag = "th" if k == 0 else "td"
        h.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in cells) + "</tr>")
    h.append("</table></div>")
    out.append("\n".join(h)); table = []

def flush_list():
    global lst
    if not lst:
        return
    kind, items = lst
    out.append(f"<{kind}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{kind}>"); lst = None

while i < len(src):
    line = src[i]; i += 1
    m = re.match(r"^(#{2,3})\s+(.*)", line)
    if m:
        flush_table(); flush_list()
        level = len(m.group(1)); title = m.group(2)
        if level == 2:
            section = re.match(r"(\d+)", title).group(1)
            out.append(f'<h2 id="s{section}">{inline(title)}</h2>')
        else:
            out.append(f"<h3>{inline(title)}</h3>")
        continue
    if line.startswith("|"):
        flush_list(); table.append(line); continue
    flush_table()
    if line.strip() == "---":
        flush_list(); continue
    m = re.match(r"^- (.*)", line)
    if m:
        if lst and lst[0] != "ul": flush_list()
        if not lst: lst = ("ul", [])
        lst[1].append(m.group(1)); continue
    m = re.match(r"^\d+\. (.*)", line)
    if m:
        if lst and lst[0] != "ol": flush_list()
        if not lst: lst = ("ol", [])
        lst[1].append(m.group(1)); continue
    flush_list()
    if not line.strip():
        continue
    if line.startswith("流れ:"):
        steps = [s.strip() for s in line[3:].split("→")]
        out.append('<div class="flow">' + "<i>→</i>".join(f"<span>{inline(s)}</span>" for s in steps) + "</div>"); continue
    if line.strip() == "<!--party-->":          # 打ち上げ希望の回答フォーム（ページの JS が埋める）
        out.append('<div id="party" class="party"></div>'); continue
    out.append(f"<p>{inline(line)}</p>")
flush_table(); flush_list()

tpl = (repo / "tools" / "template_sanka.html").read_text(encoding="utf-8")
page = tpl.replace("__BODY__", "\n".join(out)).replace("__UPDATED__", updated)
dst = repo / "sanka" / "index.html"
dst.parent.mkdir(exist_ok=True)
dst.write_text(page, encoding="utf-8")
print("OK sanka/index.html", len(page))
