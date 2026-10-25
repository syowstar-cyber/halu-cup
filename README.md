# halu-cup

麻雀大会「Halu杯」の記念大会（店の貸し切り・ゲストあり）のページ一式。`index.html` は幹部向けの平文の公開ページ（2026-09-16 にパスワードを外した）。
全ページに `noindex, nofollow` を入れ、`robots.txt` で全クローラを拒否している（検索には載らない。URL を知っている人だけが開く）。
正典は `docs/第20回/` のMD（2026-10-25 に fp リポから移した）。更新はそちらを直してから再生成する。
普段の回（組み合わせと点数だけ）のページは mahjong リポ（https://syowstar-cyber.github.io/mahjong/kai/）にある。
次の記念大会を第20回の一式から準備する手順は `docs/記念大会_手順書.md`。

## 更新のしかた

1. `docs/第20回/第20回_四麻Halu杯.md` を直す。
2. `python tools/rebuild.py` を実行。PowerShell が使える端末なら `powershell -File tools\rebuild.ps1` でも同じ。
3. `git commit` → `git push`。GitHub Pages が数十秒で反映する。

`.work/` は git 対象外（ビルドの中間ファイルを置く場所）。

## 参加者用ページ

`rule/index.html` は競技ルールをやさしく書き直したルールページ（手書き。生成しない）。本大会だけのルールを変えたら早見表・2章・3章・13章も直す。

`fu/index.html` は符計算と点数表のページ（手書き。生成しない）。

`sanka/index.html` は参加者向けの公開ページ。正典は `docs/第20回/第20回_四麻Halu杯_参加者案内.md`。
`tools/rebuild.py` が幹部用と一緒に作り直す（`tools/build_sanka.py`）。金銭の記述は載せない。

## 点数報告（score/）

`score/index.html` は点数の送信と集計の画面。データは Google Apps Script のウェブアプリ（`gas/Code.gs`）が
スクリプト プロパティ（ドライブ不使用）に JSON として保存する。配置手順は `gas/README.md`。
API の URL は `score/config.js` に書く。送信にキーは要らない（2026-09-16 撤去）。

## 早川麻雀研究会（hayakawa/）

2026-10-25 に mahjong リポ（https://syowstar-cyber.github.io/mahjong/hayakawa/）へ移した。
ここの `hayakawa/` に残るのは、前の URL を開いた人を新しいページへ送る案内（4ページ）だけ。
