# -*- coding: utf-8 -*-
"""予選の組み合わせ表を作る。
16名（本田プロ＋P1〜P15 → 1〜4卓／ゆうこママ＋P16〜P30 → 5〜8卓）を4半荘、
・同じ相手とは2度当たらない（GF(4) のアフィン平面の平行類を4つ使う）
・4半荘で 東南西北 を1回ずつ
・卓はできるだけ違う卓を回る（全員が4卓とも違うのは数学的に不可能なので最善を取る）
乱数は固定（seed=20261024）なので、何度作っても同じ表になる。
出力: score/schedule.js（ページ用）と .work/schedule.md（MD貼り付け用）"""
import itertools, json, random
from pathlib import Path

random.seed(20261024)
repo = Path(__file__).resolve().parents[1]

# GF(4): 0,1,2(=a),3(=a+1)。加算はXOR、乗算は表
MUL = [[0, 0, 0, 0], [0, 1, 2, 3], [0, 2, 3, 1], [0, 3, 1, 2]]
CLASSES = [0, 1, 2, 3, "v"]     # 傾き0..3 と 垂直線。ここから4つ選ぶ
USE = None                      # 実際に使う4つ（探索で決める）
def line_of(m, x, y):          # 平行類 m で、点(x,y)が乗る直線の番号 b
    c = USE[m]
    return x if c == "v" else (y ^ MUL[c][x])

players = [(x, y) for x in range(4) for y in range(4)]   # 16点

# 卓割り当て: table[m][b] = 卓番号(0..3)。各選手が4半荘で4つの卓を1回ずつ
perms = list(itertools.permutations(range(4)))
def find_tables():
    """各選手が4半荘で回る卓の種類数が、最も多くなる割り当てを選ぶ（全員4卓は不可能なので最善を取る）"""
    global USE
    cand = list(itertools.product(perms, repeat=4))
    random.shuffle(cand)
    best, best_key = None, None
    for use in itertools.combinations(CLASSES, 4):
        USE = list(use)
        for tabs in cand:
            counts = sorted(len({tabs[m][line_of(m, x, y)] for m in range(4)}) for (x, y) in players)
            key = (counts[0], sum(counts))
            if best_key is None or key > best_key:
                best, best_key = (list(use), tabs), key
    USE = best[0]
    print("卓の種類数（最少, 合計）:", best_key)
    return best[1]
tables = find_tables()
print("classes:", USE)

# 席割り当て: 各半荘・各直線で4人に 0..3（東南西北）を割り、各選手が4半荘で4席を1回ずつ
def find_seats():
    seat = {}  # (m, player) -> seat
    blocks = []
    for m in range(4):
        for b in range(4):
            blocks.append((m, [p for p in players if line_of(m, p[0], p[1]) == b]))
    def rec(i):
        if i == len(blocks):
            return True
        m, mem = blocks[i]
        ps = perms[:]
        random.shuffle(ps)
        for perm in ps:
            ok = True
            for p, s in zip(mem, perm):
                if any(seat.get((k, p)) == s for k in range(4) if k != m):
                    ok = False; break
            if not ok:
                continue
            for p, s in zip(mem, perm):
                seat[(m, p)] = s
            if rec(i + 1):
                return True
            for p in mem:
                del seat[(m, p)]
        return False
    if not rec(0):
        raise SystemExit("席割り当てが見つからない")
    return seat
seats = find_seats()

# 選手番号 → 名前（点(x,y) を 0..15 に並べ、0 が固定ゲスト）
order = players[:]
random.shuffle(order)
def names_for(group):
    guest = "本田プロ" if group == 0 else "ゆうこママ"
    base = 0 if group == 0 else 15
    m = {order[0]: guest}
    for i, p in enumerate(order[1:], 1):
        m[p] = f"P{base + i}"
    return m

WINDS = ["東", "南", "西", "北"]
schedule = {}   # round -> list of {table, seats:[東,南,西,北]}
for r in range(4):
    rows = []
    for group in (0, 1):
        nm = names_for(group)
        for b in range(4):
            mem = [p for p in players if line_of(r, p[0], p[1]) == b]
            by_seat = sorted(mem, key=lambda p: seats[(r, p)])
            rows.append({"table": tables[r][b] + 1 + group * 4, "seats": [nm[p] for p in by_seat]})
    rows.sort(key=lambda d: d["table"])
    schedule[str(r + 1)] = rows

# 検証
pairs = {}
for r, rows in schedule.items():
    for row in rows:
        for a, b in itertools.combinations(row["seats"], 2):
            pairs.setdefault(frozenset((a, b)), []).append(r)
dup = [k for k, v in pairs.items() if len(v) > 1]
assert not dup, dup
seen_seat, seen_table = {}, {}
for r, rows in schedule.items():
    for row in rows:
        for i, nm in enumerate(row["seats"]):
            seen_seat.setdefault(nm, set()).add(i)
            seen_table.setdefault(nm, set()).add(row["table"])
assert all(len(v) == 4 for v in seen_seat.values())
print("卓の種類数の分布:", sorted(len(v) for v in seen_table.values()))

(repo / "score" / "schedule.js").write_text(
    "// 予選の組み合わせ表（tools/make_schedule.py が生成。手で直さない）\n"
    "window.HALU_SCHEDULE = " + json.dumps(schedule, ensure_ascii=False) + ";\n", encoding="utf-8")

# MD 表
md = []
for r in range(1, 5):
    md.append(f"### 予選{r}半荘目\n")
    md.append("| 卓 | 東（起家） | 南 | 西 | 北 |")
    md.append("|---|---|---|---|---|")
    for row in schedule[str(r)]:
        md.append(f"| {row['table']}卓 | " + " | ".join(row["seats"]) + " |")
    md.append("")
# 選手別
md.append("### 選手別（卓・席）\n")
md.append("| 選手 | 1半荘目 | 2半荘目 | 3半荘目 | 4半荘目 |")
md.append("|---|---|---|---|---|")
allnames = ["本田プロ"] + [f"P{i}" for i in range(1, 16)] + ["ゆうこママ"] + [f"P{i}" for i in range(16, 31)]
for nm in allnames:
    cells = []
    for r in range(1, 5):
        for row in schedule[str(r)]:
            if nm in row["seats"]:
                cells.append(f"{row['table']}卓 {WINDS[row['seats'].index(nm)]}")
    md.append(f"| {nm} | " + " | ".join(cells) + " |")
md.append("")
work = repo / ".work"; work.mkdir(exist_ok=True)
(work / "schedule.md").write_text("\n".join(md), encoding="utf-8")
print("OK schedule.js / .work/schedule.md")
