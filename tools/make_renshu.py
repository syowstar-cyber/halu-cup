# -*- coding: utf-8 -*-
"""点数報告ページ（score/index.html）から、点数入力の練習ページ（renshu/index.html）を作る（2026-10-10〜）。
練習ページは受け口（API）へ送らず、点数はそのブラウザの localStorage（halu-renshu:*）だけに置く。
名前は出さず P番号で表示し、卓は練習用の仮の組み合わせ（本番の対戦表とは関係ない）。
score/index.html を直したら、これを実行して作り直す。置換元が見つからないときは何も書かずに止まる。
使い方: python tools/make_renshu.py"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
repo = Path(__file__).resolve().parents[1]
SRC = repo / "score" / "index.html"
DST = repo / "renshu" / "index.html"

BANNER = """  <div class="hint renshu"><b>練習用のページです。ここで送った点数は、本番の集計に入りません。</b>
    <ol>
      <li>半荘と卓を選ぶ</li>
      <li>3人分の点棒を百点単位で入れる（25,300点なら 253）</li>
      <li>4人目は自動で入るので、確かめて送信する</li>
      <li>下の集計に出るのを見る。取り消しも試せます</li>
    </ol>
    <div class="small">点数はこのスマホの中だけに残ります。名前は出さず、P番号で表示します。卓の組み合わせは練習用の仮のもので、本番の対戦表とは関係ありません。</div>
  </div>"""

HEAD_JS = """// 練習用（tools/make_renshu.py が score/index.html から生成。手で直さない）。受け口（API）へは送らない
const API = '';
// 点数はこのブラウザの localStorage だけに置く（本番ページのキー halu:* とは別）
const STORE = 'halu-renshu:data';
// 練習用の仮の卓。本番の対戦表とは関係ない（毎半荘同じ顔ぶれで、起家だけ1つずつ回す）
const SCHED = (() => {
  const P = i => 'P' + i;
  const g = [[P(1), P(2), P(3), '本田プロ']];
  for (let i = 4; i <= 15; i += 4) g.push([P(i), P(i + 1), P(i + 2), P(i + 3)]);
  g.push([P(16), P(17), P(18), 'ゆうこママ']);
  for (let i = 19; i <= 30; i += 4) g.push([P(i), P(i + 1), P(i + 2), P(i + 3)]);
  const s = {};
  for (let r = 1; r <= 4; r++) s[r] = g.map((m, t) => ({ table: t + 1, seats: m.slice(r - 1).concat(m.slice(0, r - 1)) }));
  return s;
})();"""

POST_JS = """// 練習用の受け口: 本番の受け口と同じ検査をして、このブラウザの中だけに記録する
function readStore() { try { const d = JSON.parse(localStorage.getItem(STORE) || 'null'); if (d && d.players) return d; } catch (e) {} return { players: {}, updated: '', roster: {} }; }
function writeStore(d) { try { localStorage.setItem(STORE, JSON.stringify(d)); } catch (e) {} }
let LOCAL = readStore();
async function post(body) {
  if (!PLAYERS.includes(body.player)) return { ok: false, error: 'player' };
  if (!['1', '2', '3', '4', 'S', 'F'].includes(body.round)) return { ok: false, error: 'round' };
  const p = LOCAL.players[body.player] = LOCAL.players[body.player] || {};
  if (body.action === 'clear') delete p[body.round];
  else if (!Number.isInteger(body.score) || body.score < -200000 || body.score > 99900) return { ok: false, error: 'score' };
  else p[body.round] = body.score;
  LOCAL.updated = new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' });
  writeStore(LOCAL);
  return { ok: true, data: JSON.parse(JSON.stringify(LOCAL)) };
}"""

LOAD_JS = """function load() { LOCAL = readStore(); render(JSON.parse(JSON.stringify(LOCAL))); }
document.getElementById('reset').addEventListener('click', () => {
  if (!confirm('練習で入れた点数をぜんぶ消しますか？')) return;
  LOCAL = { players: {}, updated: '', roster: {} }; writeStore(LOCAL);
  EDITING = false; load(); say('qmsg', '練習の点数をぜんぶ消しました', true);
});"""

# (置換元, 置換先, 件数)
REPS = [
    ('<meta name="theme-color" content="#7a1a1a">', '<meta name="theme-color" content="#1f5a48">', 1),
    ("<title>Halu杯 点数報告</title>", "<title>Halu杯 点数入力の練習</title>", 1),
    ("--accent:#7a1a1a;", "--accent:#1f5a48;", 1),
    (".hint{background:var(--soft);border:1px solid var(--line);border-radius:8px;padding:10px 12px;font-size:.95rem}\n",
     ".hint{background:var(--soft);border:1px solid var(--line);border-radius:8px;padding:10px 12px;font-size:.95rem}\n"
     ".renshu{border:2px solid var(--accent);background:#eef6f2}\n.renshu ol{margin:6px 0 4px;padding-left:1.4em}\n", 1),
    ("<h1>🀄 Halu杯 点数報告</h1>", "<h1>🀄 Halu杯 点数入力の練習</h1>", 1),
    ('<div class="sub">半荘が終わったら、卓の代表が4人分の点棒を送ってください。ポイントは自動計算です。</div>',
     '<div class="sub">点数報告ページと同じ入力を、本番の前に試せるページです。</div>', 1),
    ('<a href="../score/" aria-current="page">点数報告</a>', '<a href="../score/">点数報告（本番）</a>', 2),
    ('  <div id="setup" class="hint" hidden>点数報告の受け口（API）がまだ設定されていません。</div>', BANNER, 1),
    ("<h2>点数の報告（卓ごと・予選／準決勝／決勝）</h2>", "<h2>点数の報告（練習・予選／準決勝／決勝）</h2>", 1),
    ('id="qsend">この卓の4人分を送信する</button>', 'id="qsend">この卓の4人分を送信する（練習）</button>', 1),
    ("<h2>集計（予選は4半荘の合計ポイント）</h2>", "<h2>集計（練習・予選は4半荘の合計ポイント）</h2>", 1),
    ('<button class="ghost" type="button" id="reload">最新に更新</button>',
     '<button class="ghost" type="button" id="reset">練習の点数をぜんぶ消す</button>', 1),
    ("<summary>組み合わせ表（予選）</summary>", "<summary>組み合わせ表（練習用の仮の卓）</summary>", 1),
    ('<script src="config.js"></script>\n<script src="schedule.js"></script>\n', "", 1),
    ("const API = (window.HALU_API || '').trim();\nconst SCHED = window.HALU_SCHEDULE || {};", HEAD_JS, 1),
    ("async function post(body) {\n  const r = await fetch(API, { method: 'POST', body: JSON.stringify(body) });\n  return r.json();\n}", POST_JS, 1),
    ("  if (!API) { say('qmsg', 'APIが未設定です', false); return; }\n", "", 1),
    ("人分を記録しました', true);", "人分を記録しました（練習）', true);", 1),
    ("async function load() {\n  if (!API) { document.getElementById('setup').hidden = false; return; }\n"
     "  try { const r = await fetch(API + '?t=' + Date.now(), { cache: 'no-store' }); const j = await r.json(); if (j.ok) render(j.data); }\n"
     "  catch (e) { document.getElementById('updated').textContent = '読み込みに失敗しました（通信）'; }\n}\n"
     "document.getElementById('reload').addEventListener('click', load);", LOAD_JS, 1),
    ("setInterval(load, 60000);\n", "", 1),
    ("'halu:table'", "'halu-renshu:table'", 2),
    ("'halu:bdplayer'", "'halu-renshu:bdplayer'", 2),
    # 練習ページだけ: 上限は 999（99,900点）。1000以上は入れられない（2530 のような打ち間違いを止める。2026-10-10 主催の指示・本番は 9999＝999,900点まで）
    ('min="-2000" max="9999"', 'min="-2000" max="999"', 1),
    ("u >= -2000 && u <= 9999)", "u >= -2000 && u <= 999)", 1),
    ("u < -2000 || u > 9999;", "u < -2000 || u > 999;", 1),
    ("const BAD_UNIT = '百点単位の整数で入れてください（25,300点なら 253）';",
     "const BAD_UNIT = '百点単位の整数で入れてください（25,300点なら 253。上限は 999＝99,900点）';", 1),
    ("00は打ちません（25,300点 → 253）。3人入れると4人目は自動で入ります。",
     "00は打ちません（25,300点 → 253）。上限は 999（99,900点）です。3人入れると4人目は自動で入ります。", 1),
]

# 練習ページに残ってはいけないもの（本番の受け口へ届く道・本番の保存キー）
FORBIDDEN = ["fetch(", 'src="config.js"', 'src="schedule.js"', "HALU_API", "HALU_SCHEDULE", "'halu:"]


def main():
    text = SRC.read_text(encoding="utf-8")
    for old, new, n in REPS:
        got = text.count(old)
        if got != n:
            raise SystemExit(f"STOP score/index.html の置換元が {got} 件（{n} 件のはず）: {old[:50]!r}\n"
                             "score/index.html が変わったので、tools/make_renshu.py の置換元を直す")
        text = text.replace(old, new)
    left = [f for f in FORBIDDEN if f in text]
    if left:
        raise SystemExit(f"STOP 練習ページに残ってはいけないものがある: {left}")
    DST.parent.mkdir(exist_ok=True)
    DST.write_text(text, encoding="utf-8", newline="")
    print("OK", DST.relative_to(repo).as_posix(), len(text.encode("utf-8")))


if __name__ == "__main__":
    main()
