# -*- coding: utf-8 -*-
import secrets
from pathlib import Path
# 数字6桁（ユーザー指定 2026-09-15）
pw = "".join(secrets.choice("0123456789") for _ in range(6))
(Path(__file__).resolve().parents[1] / ".work" / "pw.txt").write_text(pw, encoding="ascii")
print("OK")
