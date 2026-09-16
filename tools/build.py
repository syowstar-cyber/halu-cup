# -*- coding: utf-8 -*-
"""fp/events/第20回_四麻Halu杯.md → 幹部向けHTML断片(body.html)。
除外: 冒頭の手元資料メモ／ゲスト表の依頼ルート・出身／出典／主催マター。"""
import re, html, sys, io
from pathlib import Path

here = Path(__file__).resolve().parents[1] / ".work"; here.mkdir(exist_ok=True)
SRC = Path(__file__).resolve().parents[2] / "fp" / "events" / "第20回_四麻Halu杯.md"
src = SRC.read_text(encoding="utf-8-sig").splitlines()

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = s.replace("※要確定", '<span class="warn">※要確定</span>')
    # 「N章」をページ内リンクに。「参加者ページのN章」「参加者案内N章」は参加者ページの章へ
    s = re.sub(r"(参加者ページの|参加者案内の|参加者案内)([0-9]+)章", r'<a class="xref" href="sanka/#s\2">\1\2章</a>', s)
    s = re.sub(r"([0-9]+)章(?![^<]*</a>)", r'<a class="xref" href="#s\1">\1章</a>', s)
    return s

out = []
i = 0
# 冒頭は "## 1." まで読み飛ばす
while i < len(src) and not src[i].startswith("## 1."):
    i += 1

section = ""      # 現在の "## n" 番号
skip_owner = False
in_code = False
table = []
lst = None        # ("ul"|"ol", items)

TODO_LIST_SECTIONS = ("11", "12", "13")    # 設営・手配物・出発前チェック（箇条書きにチェック）
TODO_TABLE_SECTIONS = ("14",)              # 確認事項一覧（表の行にチェック）

def keyfn(s):
    return html.escape(re.sub(r"\W+", "", s)[:40])

# 文言を変えた項目: 新しい本文 → 以前の本文（チェック状態のキー引き継ぎ用。消さずに積む）
LEGACY_TEXT = {
    "対戦表4半荘分を全部貼り出す（精算10分で回すため、半荘ごとの発表待ちをなくす）": "卓組表4回戦分を全部貼り出す（精算10分で回すため、回戦ごとの発表待ちをなくす）",
    "　対戦表 4半荘分": "　卓組表 4回戦分",
    "　記録用紙（予選8卓×4半荘、準決勝2卓、決勝1卓）": "　記録用紙（予選8卓×4回戦、準決勝2卓、決勝1卓）",
    # 2026-09-16 主催の指示（設営・手配物の文言変更）
    "受付の設置": "受付机の設置",
    "集計係の端末で集計表を開いておく。店のテレビにミラーリングできれば映す（店-9）。店のWi-Fiにつないでよいか確認（店-8）": "集計係の端末で集計表を開いておく（大画面があれば映す）。店のWi-Fiにつながるか確認",
    "マイク・スピーカーの動作確認（店にあるかは店-6）": "マイク・スピーカーの動作確認",
    "賞品・トロフィーの配置（置き場所は店-10で確認）": "賞品の配置",
    "賞品（優勝／準優勝／第3位／役満賞／飛び賞）とトロフィー": "賞品（優勝／準優勝／第3位／役満賞／飛び賞）",
    "Haluお食事券（③の回答人数分）": "Haluお食事券（④の回答人数分）",
}

def flush_table():
    global table
    if not table:
        return
    rows = [r for r in table if not re.match(r"^\|\s*-", r)]
    todo = section in TODO_TABLE_SECTIONS
    h = ['<div class="tw"><table' + (' class="todo"' if todo else '') + '>']
    for k, r in enumerate(rows):
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        tag = "th" if k == 0 else "td"
        tds = [f"<{tag}>{inline(c)}</{tag}>" for c in cells]
        if todo and tag == "td" and len(cells) >= 2:
            key = keyfn(section + cells[0] + cells[1])
            tds[0] = f'<td><label><input type="checkbox" data-k="{key}" data-legacy=""><span>{inline(cells[0])}</span></label></td>'
        h.append("<tr>" + "".join(tds) + "</tr>")
    h.append("</table></div>")
    out.append("\n".join(h))
    table = []

def flush_list():
    global lst
    if not lst:
        return
    kind, items = lst
    todo = section in TODO_LIST_SECTIONS
    h = [f'<{kind}{" class=todo" if todo else ""}>']
    for it in items:
        if todo and kind == "ul":
            key = keyfn(it)
            legacy = keyfn(LEGACY_TEXT[it]) if it in LEGACY_TEXT else ""
            h.append(f'<li><label><input type="checkbox" data-k="{key}" data-legacy="{legacy}"><span>{inline(it)}</span></label></li>')
        else:
            h.append(f"<li>{inline(it)}</li>")
    h.append(f"</{kind}>")
    out.append("\n".join(h))
    lst = None

while i < len(src):
    line = src[i]
    i += 1
    if in_code:
        if line.startswith("```"):
            in_code = False
            out.append("</pre>")
        else:
            out.append(html.escape(line, quote=False))
        continue
    if line.startswith("```"):
        flush_table(); flush_list()
        in_code = True
        out.append('<pre class="box">')
        continue
    m = re.match(r"^(#{2,3})\s+(.*)", line)
    if m:
        flush_table(); flush_list()
        level = len(m.group(1))
        title = m.group(2)
        if level == 2:
            section = re.match(r"(\d+)", title).group(1) if re.match(r"\d", title) else ""
            skip_owner = False
        if level == 3 and title.startswith("主催マター"):
            skip_owner = True
            continue
        if skip_owner:
            continue
        out.append(f"<h{level} id=\"s{section}\">{inline(title)}</h{level}>" if level == 2
                   else f"<h{level}>{inline(title)}</h{level}>")
        continue
    if skip_owner:
        continue
    if line.startswith("出典:"):
        while i < len(src) and src[i].strip() and not src[i].startswith("---"):
            i += 1
        continue
    if line.startswith("|"):
        flush_list()
        if re.match(r"^\|\s*(依頼ルート|出身)\s*\|", line):
            continue
        table.append(line)
        continue
    flush_table()
    if line.strip() == "---":
        flush_list()
        continue
    m = re.match(r"^- (.*)", line)
    if m:
        if lst and lst[0] != "ul":
            flush_list()
        if not lst:
            lst = ("ul", [])
        lst[1].append(m.group(1))
        continue
    m = re.match(r"^\d+\. (.*)", line)
    if m:
        if lst and lst[0] != "ol":
            flush_list()
        if not lst:
            lst = ("ol", [])
        lst[1].append(m.group(1))
        continue
    m = re.match(r"^  - (.*)", line)
    if m and lst:
        lst[1].append("　" + m.group(1))
        continue
    flush_list()
    if not line.strip():
        continue
    if line.startswith("流れ:"):
        steps = [s.strip() for s in line[3:].split("→")]
        out.append('<div class="flow">' + "<i>→</i>".join(f"<span>{inline(s)}</span>" for s in steps) + "</div>")
        continue
    if line.strip() == "<!--party-->":          # 打ち上げ希望の回答（ページの JS が埋める）
        out.append('<div id="party" class="party"></div>')
        continue
    out.append(f"<p>{inline(line)}</p>")

flush_table(); flush_list()
lead = "<p class=\"lead\">主催: トミーさん・ゆうこママ。変更の経緯は末尾の「16. 変更履歴」にまとめています。</p>\n"
body = lead + "\n".join(out)
# 15章のLINE用テキストは折りたたみに
body = re.sub(r'<h3>(参加者向け|運営・幹部向け)</h3>\n<pre class="box">(.*?)</pre>',
              r'<details><summary>\1（タップで開く／長押しでコピー）</summary><pre class="box">\2</pre></details>',
              body, flags=re.S)
(here / "body.html").write_text(body, encoding="utf-8")
print("OK", len(body))
