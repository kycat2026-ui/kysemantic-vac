"""檢查 VAC Protocol 合約有哪些函式（比對 bytecode 中的函式選擇器），並讀取擁有者資訊。"""
import json, re, sys, urllib.request
sys.path.insert(0, ".")
from read_vac_nft import rpc, RPCS, CONTRACT, decode_string

URL = RPCS["ethereum"]
SIGS = {
    "safeMint(address,string)": "d204c45e", "safeMint(address)": "40d097c3",
    "safeMint(address,uint256)": "a1448194", "safeMint(address,uint256,string)": "cd279c7c",
    "mint(address,string)": "d0def521", "mint(address)": "6a627842",
    "mint(address,uint256)": "40c10f19", "mint(string)": "d85d3d27",
    "mintNFT(address,string)": "eacabe14", "mintTo(address,string)": "0ba5b2da",
    "setTokenURI(uint256,string)": "162094c4", "setBaseURI(string)": "55f804b3",
    "owner()": "8da5cb5b", "transferOwnership(address)": "f2fde38b",
    "totalSupply()": "18160ddd", "burn(uint256)": "42966c68",
    "pause()": "8456cb59", "renounceOwnership()": "715018a6",
}
code = rpc(URL, "eth_getCode", [CONTRACT, "latest"])
print("bytecode bytes:", (len(code) - 2) // 2)
for sig, sel in SIGS.items():
    print(("✅ " if sel in code else "   ") + sig)

def call(data):
    return rpc(URL, "eth_call", [{"to": CONTRACT, "data": data}, "latest"])
try:
    print("owner():", "0x" + call("0x8da5cb5b")[-40:])
except Exception as e:
    print("owner() 失敗", e)
for tid in (1, 4):
    try:
        print(f"ownerOf({tid}):", "0x" + call("0x6352211e" + format(tid, "064x"))[-40:])
    except Exception as e:
        print(f"ownerOf({tid}) 失敗", e)
try:
    print("totalSupply():", int(call("0x18160ddd"), 16))
except Exception:
    pass

# 嘗試抓 Etherscan 頁面上的原始碼
try:
    req = urllib.request.Request("https://etherscan.io/address/" + CONTRACT + "#code",
                                 headers={"user-agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    m = re.search(r"<pre[^>]*id=['\"]editor['\"][^>]*>(.*?)</pre>", html, re.S)
    if m:
        import html as H
        open("contract_source.sol", "w").write(H.unescape(m.group(1)))
        print("已取得原始碼 → contract_source.sol")
    else:
        print("Etherscan 頁面中找不到原始碼區塊")
except Exception as e:
    print("Etherscan 抓取失敗:", e)

# 列出 bytecode 中所有函式選擇器，並查詢 4byte.directory 取得名稱
sels = sorted(set(re.findall(r"63([0-9a-f]{8})", code[2:])))
print(f"\n找到 {len(sels)} 個選擇器：")
for s in sels:
    name = "?"
    try:
        u = f"https://www.4byte.directory/api/v1/signatures/?hex_signature=0x{s}"
        r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"user-agent": "vac"}), timeout=15))
        if r.get("results"):
            name = " | ".join(x["text_signature"] for x in r["results"][:3])
    except Exception as e:
        name = f"(查詢失敗 {e})"
    print(f"  0x{s}  {name}")
