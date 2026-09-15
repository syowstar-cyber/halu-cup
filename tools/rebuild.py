# -*- coding: utf-8 -*-
"""rebuild.ps1 の Python 版（Bash / 実行ポリシーが Restricted の端末でも動く）。
正典(fp/events/第20回_四麻Halu杯.md)から index.html を、参加者案内MDから sanka/index.html を作り直す。
パスワードは .work/pw.txt を使い回す（無ければ genpw.py で生成）。
使い方: python tools/rebuild.py [最終更新日 YYYY-MM-DD]"""
import datetime, re, subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

tools = Path(__file__).resolve().parent
repo = tools.parent
work = repo / ".work"
updated = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

def run(*args):
    subprocess.run([sys.executable, *args], check=True)

run(tools / "build.py")
if not (work / "pw.txt").exists():
    run(tools / "genpw.py")
run(tools / "encrypt.py")
run(tools / "assemble.py", updated)
(work / "body.html").unlink(missing_ok=True)
if re.search(r"本田|由子", (repo / "index.html").read_text(encoding="utf-8")):
    print("NG 平文が残っています"); sys.exit(1)
run(tools / "build_sanka.py", updated)
print(f"OK index.html 更新 ({updated})")
