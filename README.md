# halu-cup

麻雀大会「Halu杯」の幹部向けページ。`index.html` の本文はパスワードで暗号化してあり（PBKDF2 + AES-256-CBC + HMAC-SHA256）、ブラウザ内で復号して表示する。
平文の正典は fp リポの `events/` 配下。更新はそちらを直してから再生成する。
