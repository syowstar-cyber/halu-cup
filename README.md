# halu-cup

麻雀大会「Halu杯」の幹部向けページ。`index.html` の本文はパスワードで暗号化してあり（PBKDF2 + AES-256-CBC + HMAC-SHA256）、ブラウザ内で復号して表示する。
平文の正典は fp リポの `events/` 配下。更新はそちらを直してから再生成する。

## 更新のしかた

1. fp リポの `events/第20回_四麻Halu杯.md` を直す。
2. `powershell -File tools\rebuild.ps1` を実行（パスワードは `.work/pw.txt` を使い回す）。
3. `git commit` → `git push`。GitHub Pages が数十秒で反映する。

`.work/` は git 対象外（平文とパスワードを置く場所）。`index.html` には暗号文しか入らない。
