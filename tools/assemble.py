# -*- coding: utf-8 -*-
"""template.html に .work/body.html（平文）と最終更新日を差し込んで index.html を作る。"""
from pathlib import Path
import datetime, sys
here = Path(__file__).resolve().parents[1] / ".work"
repo = Path(__file__).resolve().parents[1]
tpl = (repo / "tools" / "template.html").read_text(encoding="utf-8")
body = (here / "body.html").read_text(encoding="utf-8")
updated = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
html = tpl.replace("__BODY__", body).replace("__UPDATED__", updated)
out = Path(sys.argv[2]) if len(sys.argv) > 2 else repo / "index.html"
out.write_text(html, encoding="utf-8")
print("OK", out, len(html))
