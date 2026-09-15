# halu-cup

麻雀大会「Halu杯」の幹部向けページ。`index.html` の本文はパスワードで暗号化してあり（PBKDF2 + AES-256-CBC + HMAC-SHA256）、ブラウザ内で復号して表示する。
平文の正典は fp リポの `events/` 配下。更新はそちらを直してから再生成する。

## 更新のしかた

1. fp リポの `events/第20回_四麻Halu杯.md` を直す。
2. `powershell -File tools\rebuild.ps1` を実行（パスワードは `.work/pw.txt` を使い回す）。
3. `git commit` → `git push`。GitHub Pages が数十秒で反映する。

`.work/` は git 対象外（平文とパスワードを置く場所）。`index.html` には暗号文しか入らない。

## 参加者用ページ

`sanka/index.html` は暗号化なしの公開ページ。正典は fp リポの `events/第20回_四麻Halu杯_参加者案内.md`。
`tools/rebuild.ps1` が幹部用と一緒に作り直す（`tools/build_sanka.py`）。金銭の記述は載せない。

## 点数報告（score/）

`score/index.html` は点数の送信と集計の画面。データは Google Apps Script のウェブアプリ（`gas/Code.gs`）が
Google ドライブの `halu-cup-scores.json` 1つに保存する。配置手順は `gas/README.md`。
API の URL は `score/config.js` に書く。報告キーはスクリプト プロパティ側にあり、リポには置かない。
