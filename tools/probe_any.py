"""Read any NFT (chain / contract / token) and list its contract functions"""
import json, re, sys, urllib.request
CHAIN, CONTRACT, TOKEN = "base", "0x9ec492fc7c0664a84f01ab5bb98521bb6ba947db", 1
RPC = {"base": "https://base-rpc.publicnode.com", "ethereum": "https://ethereum-rpc.publicnode.com"}[CHAIN]
GW = ["https://amaranth-added-bug-25.mypinata.cloud/ipfs/", "https://ipfs.io/ipfs/", "https://dweb.link/ipfs/"]

def rpc(method, params):
    b = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, b, {"content-type": "application/json", "user-agent": "vac"}), timeout=20))
    if "error" in r: raise RuntimeError(r["error"])
    return r["result"]
call = lambda d: rpc("eth_call", [{"to": CONTRACT, "data": d}, "latest"])
def s(h):
    b = bytes.fromhex(h[2:]); o = int.from_bytes(b[:32], "big"); n = int.from_bytes(b[o:o+32], "big")
    return b[o+32:o+32+n].decode("utf-8", "replace")
u = lambda n: format(n, "064x")

print("chain:", CHAIN, "contract:", CONTRACT, "token:", TOKEN)
for label, fn in [("name", lambda: s(call("0x06fdde03"))), ("symbol", lambda: s(call("0x95d89b41"))),
                  ("owner()", lambda: "0x" + call("0x8da5cb5b")[-40:]),
                  ("ownerOf", lambda: "0x" + call("0x6352211e" + u(TOKEN))[-40:]),
                  ("is721", lambda: int(call("0x01ffc9a780ac58cd" + "0"*56), 16)),
                  ("is1155", lambda: int(call("0x01ffc9a7d9b67a26" + "0"*56), 16))]:
    try: print(f"{label}: {fn()}")
    except Exception as e: print(f"{label}: failed ({e})")
uri = None
for sel in ("0xc87b56dd", "0x0e89341c"):
    try:
        uri = s(call(sel + u(TOKEN))); print("tokenURI/uri:", uri[:300]); break
    except Exception as e: print(sel, "failed", e)
if uri:
    try:
        if uri.startswith("data:application/json;base64,"):
            import base64; meta = json.loads(base64.b64decode(uri.split(",", 1)[1]))
        elif uri.startswith("data:"):
            import urllib.parse; meta = json.loads(urllib.parse.unquote(uri.split(",", 1)[1]))
        else:
            cid = uri.replace("ipfs://", "")
            urls = [g + cid for g in GW] if uri.startswith("ipfs://") else [uri]
            meta = None
            for x in urls:
                try: meta = json.load(urllib.request.urlopen(urllib.request.Request(x, headers={"user-agent": "vac"}), timeout=20)); break
                except Exception as e: print("  fetch failed", x[:80], e)
        if meta:
            img = meta.get("image", "")
            if isinstance(img, str) and len(img) > 200: meta["image"] = img[:200] + f"...(len {len(img)})"
            print("METADATA:", json.dumps(meta, ensure_ascii=False, indent=1)[:4000])
    except Exception as e: print("metadata parse failed", e)
code = rpc("eth_getCode", [CONTRACT, "latest"])
print("bytecode bytes:", (len(code) - 2) // 2)
sels = sorted(set(re.findall(r"63([0-9a-f]{8})", code[2:])))
for x in sels:
    name = "?"
    try:
        r = json.load(urllib.request.urlopen(urllib.request.Request(f"https://www.4byte.directory/api/v1/signatures/?hex_signature=0x{x}", headers={"user-agent": "vac"}), timeout=15))
        if r.get("results"): name = " | ".join(t["text_signature"] for t in r["results"][:2])
    except Exception: pass
    print(f"  0x{x} {name}")
