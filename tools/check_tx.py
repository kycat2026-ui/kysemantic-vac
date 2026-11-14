"""查詢交易狀態與 token #12～#14 是否已鑄造"""
import sys
sys.path.insert(0, ".")
from read_vac_nft import rpc, RPCS, CONTRACT, call, u256, decode_string
URL = RPCS["ethereum"]
TX = "0xb3269815cdb46a199c552118a35e888cae3b8f0dad48fa4dd5e1f94dd6a8620a"
tx = rpc(URL, "eth_getTransactionByHash", [TX])
print("交易:", "找不到" if tx is None else ("等待中（pending）" if tx.get("blockNumber") is None else f"已上鏈 block {int(tx['blockNumber'],16)}"))
rc = rpc(URL, "eth_getTransactionReceipt", [TX])
if rc:
    print("結果:", "成功" if rc.get("status") == "0x1" else "失敗")
for t in (12, 13, 14, 15):
    try:
        uri = decode_string(call(URL, "0xc87b56dd" + u256(t)))
        owner = "0x" + call(URL, "0x6352211e" + u256(t))[-40:]
        print(f"#{t}: {uri}  owner={owner}")
    except Exception:
        print(f"#{t}: 尚未鑄造")
