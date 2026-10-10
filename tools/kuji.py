# -*- coding: utf-8 -*-
"""予選の対戦表をくじで決める（kuji/index.html と同じ計算。2026-10-10〜）。
種   = "HALU20|2026-10-23|N4=<ナンバーズ4の当せん番号>"（先頭の0も残して4桁）
       10月23日にナンバーズ4の抽せんがなかったときだけ "HALU20|2026-10-23|N225=<日経平均の終値>"（カンマを除いて小数2桁）
くじ値 = SHA-256(種 + "|P" + 番号) の16進64桁（P1〜P30 それぞれ）
くじ値の小さい順に 枠1〜枠30 を割り当て、型（kuji/kata.js・tools/make_schedule.py が生成）の枠を P番号に置き換える。

使い方:
  python tools/kuji.py 0482                    … 計算して表示だけ（何も書かない）
  python tools/kuji.py 0482 --write            … 本番: kuji/seed.js・score/schedule.js・.work/schedule.md を書く
  python tools/kuji.py --n225 72353.96 --write … 抽せんがなかったときの代わり（日経平均の終値）
  python tools/kuji.py --check                 … kuji/seed.js の本番の番号で計算し、score/schedule.js と一致するか確かめる"""
import hashlib, json, re, sys, unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
repo = Path(__file__).resolve().parents[1]
DATE = "2026-10-23"          # 種の日付（ページの DATE と同じ）
WINDS = ["東", "南", "西", "北"]
SEED_HEAD = "// くじの本番の番号（tools/kuji.py --write が書く。抽せんの後だけ入れる。n4 が空＝まだ、\"-\"＝抽せんがなく日経平均の終値 n225 で決めた）\n"


def norm_n4(s):
    s = unicodedata.normalize("NFKC", str(s)).replace(" ", "")
    if not re.fullmatch(r"\d{4}", s):
        raise SystemExit(f"ナンバーズ4の形が違う: {s!r}（4桁。例 0482）")
    return s


def norm_n225(s):
    s = unicodedata.normalize("NFKC", str(s)).replace(",", "").replace(" ", "").replace("円", "")
    m = re.fullmatch(r"(\d+)(?:\.(\d{1,2}))?", s)
    if not m:
        raise SystemExit(f"日経平均の終値の形が違う: {s!r}（例 72353.96）")
    return f"{int(m.group(1))}.{(m.group(2) or '').ljust(2, '0')}"


def seed_n4(n4):
    return f"HALU20|{DATE}|N4={norm_n4(n4)}"


def seed_n225(v):
    return f"HALU20|{DATE}|N225={norm_n225(v)}"


def draw(seed):
    """[(P番号, くじ値)] をくじ値の小さい順に返す。先頭が枠1"""
    vals = [(f"P{i}", hashlib.sha256(f"{seed}|P{i}".encode("ascii")).hexdigest()) for i in range(1, 31)]
    return sorted(vals, key=lambda x: (x[1], int(x[0][1:])))


def load_js(path, var):
    txt = path.read_text(encoding="utf-8")
    m = re.search(r"window\." + var + r"\s*=\s*(\{.*\})\s*;", txt, re.S)
    if not m:
        raise SystemExit(f"{path} に {var} が無い")
    return json.loads(m.group(1))


def schedule_of(kata, order):
    slot = {k + 1: p for k, (p, _) in enumerate(order)}      # 枠番号 → P番号
    return {r: [{"table": row["table"], "seats": [s if isinstance(s, str) else slot[s] for s in row["seats"]]} for row in rows]
            for r, rows in kata.items()}


def md_of(schedule, order, seed):
    md = [f"種: `{seed}`", "", "| 枠 | No. | くじ値（先頭12桁） |", "|---|---|---|"]
    md += [f"| 枠{k} | {p} | {h[:12]} |" for k, (p, h) in enumerate(order, 1)]
    md.append("")
    for r in range(1, 5):
        md += [f"### 予選{r}半荘目", "", "| 卓 | 東（起家） | 南 | 西 | 北 |", "|---|---|---|---|---|"]
        md += [f"| {row['table']}卓 | " + " | ".join(row["seats"]) + " |" for row in schedule[str(r)]]
        md.append("")
    md += ["### 選手別（卓・席）", "", "| 選手 | 1半荘目 | 2半荘目 | 3半荘目 | 4半荘目 |", "|---|---|---|---|---|"]
    honda = lambda p: next(row["table"] for row in schedule["1"] if p in row["seats"]) <= 4   # 本田プロの組（1〜4卓）
    ps = sorted([p for p, _ in order], key=lambda p: int(p[1:]))
    for nm in ["本田プロ"] + [p for p in ps if honda(p)] + ["ゆうこママ"] + [p for p in ps if not honda(p)]:
        cells = []
        for r in range(1, 5):
            for row in schedule[str(r)]:
                if nm in row["seats"]:
                    cells.append(f"{row['table']}卓 {WINDS[row['seats'].index(nm)]}")
        md.append(f"| {nm} | " + " | ".join(cells) + " |")
    return "\n".join(md) + "\n"


def main():
    argv = sys.argv[1:]
    kata = load_js(repo / "kuji" / "kata.js", "HALU_KATA")
    if "--check" in argv:
        k = load_js(repo / "kuji" / "seed.js", "HALU_KUJI")
        if not k.get("n4"):
            raise SystemExit("kuji/seed.js に本番の番号がまだ無い")
        seed = seed_n225(k["n225"]) if k["n4"] == "-" else seed_n4(k["n4"])
        now = load_js(repo / "score" / "schedule.js", "HALU_SCHEDULE")
        print("一致" if now == schedule_of(kata, draw(seed)) else "不一致（score/schedule.js を kuji.py --write で作り直す）")
        return
    n225 = None
    if "--n225" in argv:
        i = argv.index("--n225")
        if i + 1 >= len(argv):
            raise SystemExit(__doc__)
        n225 = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    args = [a for a in argv if not a.startswith("--")]
    if n225 is not None:
        if args:
            raise SystemExit("ナンバーズ4と --n225 は同時に使わない（--n225 は抽せんがなかったときだけ）")
        seed, rec = seed_n225(n225), {"n4": "-", "n225": norm_n225(n225)}
    else:
        if len(args) != 1:
            raise SystemExit(__doc__)
        seed, rec = seed_n4(args[0]), {"n4": norm_n4(args[0]), "n225": ""}
    order = draw(seed)
    sched = schedule_of(kata, order)
    print("種:", seed)
    for k, (p, h) in enumerate(order, 1):
        print(f"枠{k:>2} {p:>3} {h[:16]}")
    if "--write" in argv:
        (repo / "kuji" / "seed.js").write_text(SEED_HEAD + "window.HALU_KUJI = " + json.dumps(rec) + ";\n", encoding="utf-8")
        (repo / "score" / "schedule.js").write_text(
            "// 予選の組み合わせ表（tools/kuji.py がくじの結果から生成。手で直さない）\n"
            "window.HALU_SCHEDULE = " + json.dumps(sched, ensure_ascii=False) + ";\n", encoding="utf-8")
        work = repo / ".work"; work.mkdir(exist_ok=True)
        (work / "schedule.md").write_text(md_of(sched, order, seed), encoding="utf-8")
        print("OK kuji/seed.js / score/schedule.js / .work/schedule.md")


if __name__ == "__main__":
    main()
