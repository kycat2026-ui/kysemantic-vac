#!/usr/bin/env python3
"""
read_vac_nft.py — 從鏈上讀取 VAC Protocol NFT 的 metadata（唯讀，不需私鑰、不花 gas）

用法：
    python3 read_vac_nft.py                 # 自動偵測鏈，讀取 token 1~9
    python3 read_vac_nft.py --chain base    # 指定鏈
    python3 read_vac_nft.py --ids 0-10      # 指定 token 範圍
只用 Python 標準函式庫，不需安裝任何套件。
"""
import argparse, json, urllib.request

CONTRACT = "0x4e22b334e53c1dc7e266b5996d32c05a6ac8f4fb"

RPCS = {
    "ethereum": "https://ethereum-rpc.publicnode.com",
    "base":     "https://base-rpc.publicnode.com",
    "polygon":  "https://polygon-bor-rpc.publicnode.com",
    "arbitrum": "https://arbitrum-one-rpc.publicnode.com",
    "optimism": "https://optimism-rpc.publicnode.com",
}
IPFS_GATEWAY = "https://ipfs.io/ipfs/"

SEL_NAME      = "0x06fdde03"  # name()
SEL_SYMBOL    = "0x95d89b41"  # symbol()
SEL_TOKENURI  = "0xc87b56dd"  # tokenURI(uint256)  ERC-721
SEL_URI       = "0x0e89341c"  # uri(uint256)       ERC-1155
SEL_IFACE     = "0x01ffc9a7"  # supportsInterface(bytes4)
IFACE_721, IFACE_1155 = "80ac58cd", "d9b67a26"


def rpc(url, method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, body, {"content-type": "application/json",
                                             "user-agent": "vac-reader/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        res = json.load(r)
    if "error" in res:
        raise RuntimeError(res["error"])
    return res["result"]


def call(url, data):
    return rpc(url, "eth_call", [{"to": CONTRACT, "data": data}, "latest"])


def u256(n):
    return format(n, "064x")


def decode_string(hexdata):
    """ABI 解碼單一 string 回傳值"""
    b = bytes.fromhex(hexdata[2:])
    if len(b) < 64:
        return ""
    off = int.from_bytes(b[0:32], "big")
    ln = int.from_bytes(b[off:off + 32], "big")
    return b[off + 32:off + 32 + ln].decode("utf-8", "replace")


def detect_chain():
    for name, url in RPCS.items():
        try:
            if rpc(url, "eth_getCode", [CONTRACT, "latest"]) not in ("0x", "0x0"):
                return name, url
        except Exception as e:
            print(f"  ({name} 查詢失敗: {e})")
    return None, None


def standard(url):
    for iface, label in ((IFACE_721, "ERC-721"), (IFACE_1155, "ERC-1155")):
        try:
            r = call(url, SEL_IFACE + iface.ljust(64, "0"))
            if int(r, 16) == 1:
                return label
        except Exception:
            pass
    return "未知"


def to_http(uri):
    if uri.startswith("ipfs://"):
        return IPFS_GATEWAY + uri[len("ipfs://"):].removeprefix("ipfs/")
    return uri


def fetch_json(uri):
    if uri.startswith("data:application/json;base64,"):
        import base64
        return json.loads(base64.b64decode(uri.split(",", 1)[1]))
    if uri.startswith("data:application/json"):
        import urllib.parse
        return json.loads(urllib.parse.unquote(uri.split(",", 1)[1]))
    req = urllib.request.Request(to_http(uri), headers={"user-agent": "vac-reader/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def token_uri(url, std, tid):
    sel = SEL_URI if std == "ERC-1155" else SEL_TOKENURI
    uri = decode_string(call(url, sel + u256(tid)))
    if std == "ERC-1155" and "{id}" in uri:
        uri = uri.replace("{id}", format(tid, "064x"))
    return uri


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chain", choices=RPCS.keys())
    ap.add_argument("--ids", default="1-9", help="例如 1-9 或 0,3,8")
    ap.add_argument("--out", default="vac_genome.json")
    a = ap.parse_args()

    if "-" in a.ids:
        s, e = map(int, a.ids.split("-")); ids = range(s, e + 1)
    else:
        ids = [int(x) for x in a.ids.split(",")]

    if a.chain:
        chain, url = a.chain, RPCS[a.chain]
    else:
        print("偵測合約所在的鏈…")
        chain, url = detect_chain()
        if not chain:
            print("五條鏈上都找不到這個合約，請用 --chain 指定，或確認地址。"); return

    std = standard(url)
    name = symbol = "?"
    try: name = decode_string(call(url, SEL_NAME))
    except Exception: pass
    try: symbol = decode_string(call(url, SEL_SYMBOL))
    except Exception: pass
    print(f"\n鏈: {chain} | 標準: {std} | 名稱: {name} ({symbol})\n")

    genome = {"contract": CONTRACT, "chain": chain, "standard": std,
              "name": name, "tokens": {}}
    for tid in ids:
        try:
            uri = token_uri(url, std, tid)
            if not uri:
                continue
            meta = fetch_json(uri)
            genome["tokens"][str(tid)] = {"tokenURI": uri, "metadata": meta}
            print(f"#{tid}: {meta.get('name')}")
            for at in meta.get("attributes", []):
                print(f"     - {at.get('trait_type')}: {at.get('value')}")
        except Exception as e:
            print(f"#{tid}: 讀取失敗（{type(e).__name__}）")

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(genome, f, ensure_ascii=False, indent=2)
    print(f"\n已存成 {a.out}，之後原型程式會從這份檔案載入「意志基因組」。")


if __name__ == "__main__":
    main()
