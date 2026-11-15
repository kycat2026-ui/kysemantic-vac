"""Wallet attention check (Blockscout public API, no key). Output goes only to a private artifact."""
import json, urllib.request, collections
W = "0xeace739e1436738caeef04a509a169f3734692b9"
CHAINS = {"ethereum": "https://eth.blockscout.com/api/v2", "base": "https://base.blockscout.com/api/v2"}

def get(url):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"user-agent": "vac-attention"}), timeout=30))
    except Exception as e:
        return {"error": str(e)}

def pages(url, maxp=10):
    items, nxt = [], None
    for _ in range(maxp):
        u = url + ("" if nxt is None else ("&" if "?" in url else "?") + "&".join(f"{k}={v}" for k, v in nxt.items()))
        d = get(u)
        if "items" not in d: break
        items += d["items"]; nxt = d.get("next_page_params")
        if not nxt: break
    return items

for chain, api in CHAINS.items():
    print(f"\n######## {chain}")
    info = get(f"{api}/addresses/{W}")
    print("ENS:", info.get("ens_domain_name"), "| tx count:", (get(f"{api}/addresses/{W}/counters") or {}).get("transactions_count"))
    tt = pages(f"{api}/addresses/{W}/token-transfers", 15)
    inc = [t for t in tt if (t.get("to") or {}).get("hash", "").lower() == W and (t.get("from") or {}).get("hash", "").lower() != W]
    print(f"token transfers: {len(tt)} total, {len(inc)} incoming from others")
    for t in inc[:40]:
        tok = t.get("token") or {}
        f = (t.get("from") or {}).get("hash")
        print(f"  IN  {t.get('timestamp','')[:10]} {tok.get('type')} {str(tok.get('name'))[:40]!r} ({tok.get('address_hash','')[:10]}) from {f} method={t.get('method')}")
    txs = pages(f"{api}/addresses/{W}/transactions", 10)
    others = [x for x in txs if (x.get("from") or {}).get("hash", "").lower() != W]
    print(f"transactions: {len(txs)} seen, {len(others)} initiated by other addresses")
    for x in others[:20]:
        print(f"  TX  {x.get('timestamp','')[:10]} from {(x.get('from') or {}).get('hash')} method={x.get('method')} value={x.get('value')}")
    outs = collections.Counter()
    for t in tt:
        if (t.get("from") or {}).get("hash", "").lower() == W and (t.get("to") or {}).get("hash", "").lower() != W:
            outs[((t.get("token") or {}).get("name"), (t.get("to") or {}).get("hash"))] += 1
    print("outgoing token transfers to others:", dict(list(outs.items())[:15]))
    # Collections minted by the user: other holders of tokens / transfers involving others
    nfts = pages(f"{api}/addresses/{W}/nft/collections?type=ERC-721,ERC-1155", 5)
    for c in nfts:
        tok = c.get("token") or {}
        addr = tok.get("address_hash")
        hold = get(f"{api}/tokens/{addr}/counters")
        print(f"  HOLD {tok.get('type')} {str(tok.get('name'))[:40]!r} {addr} amount={c.get('amount')} holders={hold.get('token_holders_count')} transfers={hold.get('transfers_count')}")
