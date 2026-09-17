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
    # 「N章」をページ内リンクに（見出しの id は sN）
    s = re.sub(r"([0-9]+)章", r'<a class="xref" href="#s\1">\1章</a>', s)
    return s


# 対戦表: 本田プロがいる行（予選N半荘目）と、選手別の表でその卓に当たる席に印を付ける
PRO = "本田プロ"
PRO_TABLES = []      # 半荘ごとの本田プロの卓（"1卓" など。表の出現順）
LEGEND = '<p class="legend"><span class="pro-sw"></span> 色つき＝本田プロと同卓</p>'
legend_done = False

def pro_marks(rows_cells):
    """rows_cells: [[cell,...], ...]（先頭は見出し行）。戻り値: (行ごとのクラス, セルごとのクラス)"""
    global legend_done
    n = len(rows_cells)
    row_cls = [""] * n
    cell_cls = [[""] * len(r) for r in rows_cells]
    head = rows_cells[0] if rows_cells else []
    if head and head[0] == "卓":                      # 予選N半荘目の表
        for k in range(1, n):
            if PRO in rows_cells[k]:
                row_cls[k] = "pro"
                PRO_TABLES.append(rows_cells[k][0])
    elif PRO_TABLES and all(re.match(r"^\d+卓\s", c) for c in rows_cells[1][1:]):   # 選手別（卓・席）の表
        for k in range(1, n):
            if rows_cells[k][0] == PRO:
                continue
            for j in range(1, len(rows_cells[k])):
                if j - 1 < len(PRO_TABLES) and rows_cells[k][j].startswith(PRO_TABLES[j - 1] + " "):
                    cell_cls[k][j] = "pro"
    legend = ""
    if not legend_done and (any(row_cls) or any(any(r) for r in cell_cls)):
        legend, legend_done = LEGEND, True
    return row_cls, cell_cls, legend

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
    rows_cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    row_cls, cell_cls, legend = pro_marks(rows_cells)
    h = [legend + '<div class="tw"><table>']
    for k, cells in enumerate(rows_cells):
        tag = "th" if k == 0 else "td"
        h.append(("<tr class=pro>" if row_cls[k] else "<tr>") + "".join(f"<{tag}{' class=pro' if cell_cls[k][j] else ''}>{inline(c)}</{tag}>" for j, c in enumerate(cells)) + "</tr>")
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
    if line.strip() == "<!--roster-->":         # 出席者一覧（受け口の一覧をページの JS が埋める）
        out.append('<div id="roster" class="roster"></div>'); continue
    out.append(f"<p>{inline(line)}</p>")
flush_table(); flush_list()

tpl = (repo / "tools" / "template_sanka.html").read_text(encoding="utf-8")
page = tpl.replace("__BODY__", "\n".join(out)).replace("__UPDATED__", updated)
dst = repo / "sanka" / "index.html"
dst.parent.mkdir(exist_ok=True)
dst.write_text(page, encoding="utf-8")
print("OK sanka/index.html", len(page))
