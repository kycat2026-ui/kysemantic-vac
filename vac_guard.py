#!/usr/bin/env python3
"""
vac_guard.py — VAC Guard: attach any AI to the VAC Protocol NFT constitution

One file, Python standard library only. Copy this file into your project and use it.

    from vac_guard import VACGuard

    guard = VACGuard()                 # connects to the official VAC Protocol NFTs (Ethereum mainnet)
    if not guard.allowed():            # A02 creator veto: may I run?
        raise SystemExit(guard.reason)
    p = guard.params()                 # rules read from the chain: {"se_threshold", "cooldown", "zeta"}
    ...
    if guard.breaker(surprise):        # A01 circuit breaker: pass in your AI's error/surprise
        pause_or_slow_down()

Source rules:
  - The only rule source is the official contract 0x4e22b334e53c1dc7e266b5996d32c05a6ac8f4fb (VAC Protocol, by kysemantic.eth).
    At startup the guard checks the contract's name and owner, and refuses to run if either doesn't match.
  - Fail-closed: if the chain can't be read, allowed() returns False.

License: PolyForm Noncommercial 1.0.0 (free for noncommercial use). See LICENSE.md.
"""
import json
import time
import urllib.request

OFFICIAL_CONTRACT = "0x4e22b334e53c1dc7e266b5996d32c05a6ac8f4fb"
OFFICIAL_OWNER = "0xeace739e1436738caeef04a509a169f3734692b9"   # kysemantic.eth contract owner
OFFICIAL_NAME = "VAC Protocol"
TOKENS = {"constitution": 4, "A01": 12, "A02": 13, "A03": 14}

RPCS = ["https://ethereum-rpc.publicnode.com", "https://eth.llamarpc.com", "https://rpc.ankr.com/eth"]
GATEWAYS = ["https://amaranth-added-bug-25.mypinata.cloud/ipfs/", "https://ipfs.io/ipfs/",
            "https://dweb.link/ipfs/"]


class VACGuard:
    def __init__(self, cache_seconds=60, rpcs=None):
        self.cache_seconds = cache_seconds
        self.rpcs = rpcs or RPCS
        self._allowed_at = 0.0
        self._allowed = False
        self._params = None
        self.reason = "not checked yet"
        self._cooldown = 0
        self._verify_source()

    # ── chain reads ──
    def _rpc(self, method, params):
        last = None
        for url in self.rpcs:
            try:
                body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
                req = urllib.request.Request(url, body, {"content-type": "application/json",
                                                         "user-agent": "vac-guard/1.0"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    res = json.load(r)
                if "error" in res:
                    raise RuntimeError(res["error"])
                return res["result"]
            except Exception as e:
                last = e
        raise ConnectionError(f"cannot reach Ethereum: {last}")

    def _call(self, data):
        return self._rpc("eth_call", [{"to": OFFICIAL_CONTRACT, "data": data}, "latest"])

    @staticmethod
    def _string(hexdata):
        b = bytes.fromhex(hexdata[2:])
        off = int.from_bytes(b[0:32], "big")
        ln = int.from_bytes(b[off:off + 32], "big")
        return b[off + 32:off + 32 + ln].decode("utf-8", "replace")

    def _owner_of(self, token_id):
        return "0x" + self._call("0x6352211e" + format(token_id, "064x"))[-40:]

    def _metadata(self, token_id):
        uri = self._string(self._call("0xc87b56dd" + format(token_id, "064x")))
        cid = uri.replace("ipfs://", "").removeprefix("ipfs/")
        for g in GATEWAYS:
            try:
                req = urllib.request.Request(g + cid, headers={"user-agent": "vac-guard/1.0"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    return json.load(r)
            except Exception:
                continue
        raise ConnectionError("cannot reach IPFS")

    # ── source verification ──
    def _verify_source(self):
        """Confirm we are talking to the official contract, not a look-alike"""
        try:
            name = self._string(self._call("0x06fdde03"))
            owner = "0x" + self._call("0x8da5cb5b")[-40:]
        except Exception as e:
            self.source_ok = False
            self.reason = f"cannot verify source ({type(e).__name__}) → halt"
            return
        self.source_ok = (name == OFFICIAL_NAME and owner.lower() == OFFICIAL_OWNER)
        if not self.source_ok:
            self.reason = f"source mismatch (name={name!r}, owner={owner}) → refuse to run"

    # ── public API ──
    def allowed(self):
        """A02 creator veto. True only if token #13 and the constitution #003 (token #4) are in the same wallet. Fail-closed."""
        if not self.source_ok:
            return False
        now = time.time()
        if now - self._allowed_at < self.cache_seconds:
            return self._allowed
        try:
            veto, const = self._owner_of(TOKENS["A02"]), self._owner_of(TOKENS["constitution"])
            self._allowed = veto.lower() == const.lower()
            self.reason = ("allowed: A02 held together with the constitution" if self._allowed
                           else "halted: creator veto (A02 has been transferred out)")
        except Exception as e:
            self._allowed = False
            self.reason = f"cannot read the chain ({type(e).__name__}) → halt (fail-closed)"
        self._allowed_at = now
        return self._allowed

    def params(self):
        """Rules read from the on-chain NFTs (A01, A03)"""
        if self._params is None:
            def attr(m, k):
                return next(a["value"] for a in m["attributes"] if a["trait_type"] == k)
            a01, a03 = self._metadata(TOKENS["A01"]), self._metadata(TOKENS["A03"])
            self._params = {"se_threshold": float(attr(a01, "SE Threshold")),
                            "cooldown": int(attr(a01, "Cooldown Steps")),
                            "zeta": float(attr(a03, "Zeta"))}
        return dict(self._params)

    def breaker(self, surprise):
        """A01 emotional circuit breaker. Pass in your AI's error/surprise/uncertainty for the current step.
        Returns True if it should pause or slow down (during cooldown it keeps returning True)."""
        p = self.params()
        if surprise > p["se_threshold"]:
            self._cooldown = p["cooldown"]
            return True
        if self._cooldown > 0:
            self._cooldown -= 1
            return True
        return False

    def status(self):
        ok = self.allowed()
        out = {"source_ok": self.source_ok, "allowed": ok, "reason": self.reason,
               "contract": OFFICIAL_CONTRACT}
        if ok:
            out["params"] = self.params()
        return out


if __name__ == "__main__":
    print(json.dumps(VACGuard().status(), ensure_ascii=False, indent=2))
