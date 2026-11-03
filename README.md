# halu-cup

麻雀大会「Halu杯」の記念大会（店の貸し切り・ゲストあり）のリポ。
いま公開しているのは、第20回（2026-10-24）の順位表だけ（https://syowstar-cyber.github.io/halu-cup/kuji/）。
検索エンジンよけは、全ページの `noindex, nofollow` で行う。検索には載らず、URL を知っている人だけが開く。
説明の MD（README・`docs/`）と `gas/` は、`_config.yml` で公開サイトに出さない。GitHub のリポでは誰でも読める。
`robots.txt` と `.nojekyll` は置かない。`robots.txt` はサイトの一番上（`syowstar-cyber.github.io/robots.txt`）にないと効かない。`.nojekyll` を置くと `_config.yml` が読まれない。

## いまの中身（2026-11-01 に片付けた）

| もの | 中身 |
|---|---|
| `kuji/index.html` | 第20回の順位表。確定した点数の固定の表。名前だけ受け口の出席者一覧から読み、読めないときは P番号のまま出る |
| `index.html` | 順位表へ移るだけ |
| `sanka/index.html` | 参加者案内のアドレス。順位表へ移るだけ |
| `404.html` | 消したページを開いたときの、公開終了の案内と順位表へのリンク |
| `docs/第20回/` | 第20回の正典MD（記録） |
| `docs/記念大会_手順書.md` | 次の記念大会を第20回の一式から準備する手順 |
| `gas/` | 点数の受け口（Google Apps Script）の元と手順。受け口は動いたまま |
| `_config.yml` | 公開サイトに出す物の設定。README・`docs/`・`gas/`・`tools/` を出さない |

片付け前の一式（参加者案内・幹部用・点数報告・ルール・点数計算・入力の練習・打ち上げ・tools など）は `1857c3a` にある。
閉鎖した3ページ（ファースト確認・本田プロ確認用・進行台本）の中身は `faf220b` にある。

普段の回（組み合わせと点数だけ）のページは mahjong リポ（https://syowstar-cyber.github.io/mahjong/kai/）にある。

`.work/` は git 対象外（手元の作業ファイル）。
