# -*- coding: utf-8 -*-
"""encrypt.ps1 の Python 版（標準ライブラリだけ・追加インストール不要）。
.work/body.html を PBKDF2(SHA-256, 200000) → AES-256-CBC + HMAC-SHA256 で暗号化し .work/cipher.json へ。
出力形式は encrypt.ps1 と同じ（ページ側の復号 JS はそのまま）。
Bash から PowerShell スクリプトは実行ポリシーで動かないので、こちらを使う。
使い方: python tools/encrypt.py            … 暗号化
        python tools/encrypt.py --verify   … いまの cipher.json を復号して中身を検算（書かない）"""
import base64, hashlib, hmac, json, os, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

work = Path(__file__).resolve().parents[1] / ".work"
ITER = 200000

# ---- AES（純Python・FIPS-197）----
def _gen_sbox():
    sbox = [0] * 256; p = q = 1
    while True:
        p = p ^ ((p << 1) & 0xFF) ^ (0x1B if p & 0x80 else 0)      # p *= 3
        q ^= q << 1; q ^= q << 2; q ^= q << 4; q &= 0xFF          # q /= 3
        if q & 0x80: q ^= 0x09
        x = q ^ (q << 1) ^ (q << 2) ^ (q << 3) ^ (q << 4)
        sbox[p] = (x ^ (x >> 8) ^ 0x63) & 0xFF
        if p == 1: break
    sbox[0] = 0x63
    return sbox
SBOX = _gen_sbox()
INV_SBOX = [0] * 256
for _i, _v in enumerate(SBOX): INV_SBOX[_v] = _i

def _xt(a): return ((a << 1) ^ 0x1B) & 0xFF if a & 0x80 else a << 1
def _mul(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        a = _xt(a); b >>= 1
    return r

def _expand(key):
    nk, nr = 8, 14
    w = [list(key[4*i:4*i+4]) for i in range(nk)]
    rcon = 1
    for i in range(nk, 4 * (nr + 1)):
        t = w[i-1][:]
        if i % nk == 0:
            t = t[1:] + t[:1]
            t = [SBOX[b] for b in t]
            t[0] ^= rcon; rcon = _xt(rcon)
        elif i % nk == 4:
            t = [SBOX[b] for b in t]
        w.append([w[i-nk][j] ^ t[j] for j in range(4)])
    return [sum(w[4*r:4*r+4], []) for r in range(nr + 1)]   # round keys（16バイトずつ）

def _add(s, k): return [a ^ b for a, b in zip(s, k)]
def _shift(s):     return [s[r + 4 * ((c + r) % 4)] for c in range(4) for r in range(4)]
def _inv_shift(s): return [s[r + 4 * ((c - r) % 4)] for c in range(4) for r in range(4)]
def _mix(s, m):
    out = []
    for c in range(4):
        a = s[4*c:4*c+4]
        for r in range(4):
            out.append(_mul(a[0], m[(0 - r) % 4]) ^ _mul(a[1], m[(1 - r) % 4]) ^ _mul(a[2], m[(2 - r) % 4]) ^ _mul(a[3], m[(3 - r) % 4]))
    return out
def _enc_block(b, rk):
    s = _add(list(b), rk[0])
    for r in range(1, 14):
        s = _add(_mix(_shift([SBOX[x] for x in s]), (2, 3, 1, 1)), rk[r])
    return bytes(_add(_shift([SBOX[x] for x in s]), rk[14]))
def _dec_block(b, rk):
    s = _add(list(b), rk[14])
    for r in range(13, 0, -1):
        s = _mix(_add([INV_SBOX[x] for x in _inv_shift(s)], rk[r]), (14, 11, 13, 9))
    return bytes(_add([INV_SBOX[x] for x in _inv_shift(s)], rk[0]))

def aes_cbc_encrypt(key, iv, data):
    pad = 16 - len(data) % 16
    data = data + bytes([pad]) * pad
    rk = _expand(key); prev = iv; out = bytearray()
    for i in range(0, len(data), 16):
        blk = bytes(a ^ b for a, b in zip(data[i:i+16], prev))
        prev = _enc_block(blk, rk); out += prev
    return bytes(out)
def aes_cbc_decrypt(key, iv, data):
    rk = _expand(key); prev = iv; out = bytearray()
    for i in range(0, len(data), 16):
        out += bytes(a ^ b for a, b in zip(_dec_block(data[i:i+16], rk), prev)); prev = data[i:i+16]
    pad = out[-1]
    if not 1 <= pad <= 16 or out[-pad:] != bytes([pad]) * pad: raise ValueError("padding")
    return bytes(out[:-pad])

def keys(pw, salt):
    k = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, ITER, 64)
    return k[:32], k[32:]

def encrypt(plain, pw):
    salt, iv = os.urandom(16), os.urandom(16)
    ak, mk = keys(pw, salt)
    ct = aes_cbc_encrypt(ak, iv, plain)
    mac = hmac.new(mk, iv + ct, hashlib.sha256).digest()
    b64 = lambda x: base64.b64encode(x).decode()
    return {"salt": b64(salt), "iv": b64(iv), "ct": b64(ct), "mac": b64(mac), "iter": ITER}

def decrypt(obj, pw):
    d = lambda k: base64.b64decode(obj[k])
    salt, iv, ct, mac = d("salt"), d("iv"), d("ct"), d("mac")
    ak, mk = keys(pw, salt)
    if not hmac.compare_digest(hmac.new(mk, iv + ct, hashlib.sha256).digest(), mac): raise ValueError("MAC mismatch")
    return aes_cbc_decrypt(ak, iv, ct)

if __name__ == "__main__":
    pw = (work / "pw.txt").read_text(encoding="utf-8").strip()
    if "--verify" in sys.argv:
        obj = json.loads((work / "cipher.json").read_text(encoding="utf-8"))
        plain = decrypt(obj, pw)
        print("VERIFY OK", len(plain), "bytes,", "head:", plain[:40].decode("utf-8", "replace").replace("\n", " "))
        sys.exit(0)
    plain = (work / "body.html").read_bytes()
    obj = encrypt(plain, pw)
    assert decrypt(obj, pw) == plain, "roundtrip failed"
    (work / "cipher.json").write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("OK", len(base64.b64decode(obj["ct"])))
