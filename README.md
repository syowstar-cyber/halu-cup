# halu-cup

麻雀大会「Halu杯」の幹部向けページ。`index.html` は平文の公開ページ（2026-09-16 にパスワードを外した）。
全ページに `noindex, nofollow` を入れ、`robots.txt` で全クローラを拒否している（検索には載らない。URL を知っている人だけが開く）。
正典は fp リポの `events/` 配下。更新はそちらを直してから再生成する。

## 更新のしかた

1. fp リポの `events/第20回_四麻Halu杯.md` を直す。
2. `python tools/rebuild.py` を実行。PowerShell が使える端末なら `powershell -File tools\rebuild.ps1` でも同じ。
3. `git commit` → `git push`。GitHub Pages が数十秒で反映する。

`.work/` は git 対象外（ビルドの中間ファイルを置く場所）。

## 参加者用ページ

`rule/index.html` は Mリーグ公式ルールをやさしく書き直したルールページ（手書き。生成しない）。本大会だけのルールを変えたら早見表と2章も直す。

`sanka/index.html` は参加者向けの公開ページ。正典は fp リポの `events/第20回_四麻Halu杯_参加者案内.md`。
`tools/rebuild.py` が幹部用と一緒に作り直す（`tools/build_sanka.py`）。金銭の記述は載せない。

## 点数報告（score/）

`score/index.html` は点数の送信と集計の画面。データは Google Apps Script のウェブアプリ（`gas/Code.gs`）が
スクリプト プロパティ（ドライブ不使用）に JSON として保存する。配置手順は `gas/README.md`。
API の URL は `score/config.js` に書く。送信にキーは要らない（2026-09-16 撤去）。
