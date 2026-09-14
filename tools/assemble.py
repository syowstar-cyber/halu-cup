# -*- coding: utf-8 -*-
from pathlib import Path
import datetime, sys
here = Path(__file__).resolve().parents[1] / ".work"
repo = Path(__file__).resolve().parents[1]
tpl = (repo / "tools" / "template.html").read_text(encoding="utf-8")
cipher = (here / "cipher.json").read_text(encoding="utf-8").strip()
updated = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
html = tpl.replace("__CIPHER__", cipher).replace("__UPDATED__", updated)
out = Path(sys.argv[2]) if len(sys.argv) > 2 else repo / "index.html"
out.write_text(html, encoding="utf-8")
print("OK", out, len(html))
