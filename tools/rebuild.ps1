# 正典(fp/events/第20回_四麻Halu杯.md)から index.html を作り直す。
# 使い方: powershell -File tools\rebuild.ps1 [最終更新日 YYYY-MM-DD]
$ErrorActionPreference = "Stop"
$tools = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo  = Split-Path -Parent $tools
$updated = if ($args.Count -ge 1) { $args[0] } else { (Get-Date).ToString("yyyy-MM-dd") }
python (Join-Path $tools "build.py")
python (Join-Path $tools "assemble.py") $updated
Remove-Item (Join-Path $repo ".work\body.html") -ErrorAction SilentlyContinue
python (Join-Path $tools "build_sanka.py") $updated
Write-Output "OK index.html 更新 ($updated)"
