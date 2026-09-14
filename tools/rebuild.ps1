# 正典(fp/events/第20回_四麻Halu杯.md)から index.html を作り直す。
# パスワードは .work/pw.txt を使い回す（無ければ genpw.py で生成）。
# 使い方: powershell -File tools\rebuild.ps1 [最終更新日 YYYY-MM-DD]
$ErrorActionPreference = "Stop"
$tools = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo  = Split-Path -Parent $tools
$updated = if ($args.Count -ge 1) { $args[0] } else { (Get-Date).ToString("yyyy-MM-dd") }
python (Join-Path $tools "build.py")
if (-not (Test-Path (Join-Path $repo ".work\pw.txt"))) { python (Join-Path $tools "genpw.py") }
& (Join-Path $tools "encrypt.ps1")
python (Join-Path $tools "assemble.py") $updated
Remove-Item (Join-Path $repo ".work\body.html") -ErrorAction SilentlyContinue
$hit = Select-String -Path (Join-Path $repo "index.html") -Pattern "本田|由子" -Quiet
if ($hit) { Write-Output "NG 平文が残っています"; exit 1 }
Write-Output "OK index.html 更新 ($updated)"
