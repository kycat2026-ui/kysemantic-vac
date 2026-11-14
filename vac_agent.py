#!/usr/bin/env python3
"""
vac_agent.py — VAC Protocol 原型（以鏈上 NFT 為入口）

流程：
  1. 入口：從 Ethereum 上的 VAC Protocol NFT 讀取「意志基因組」
     （或讀取已存在的 vac_genome.json；用 --offline 跳過鏈上讀取）
  2. 依據持有的 NFT 啟用 001–009 模組；沒有對應 NFT 的模組就不啟用
  3. 在格子世界中比較「一般 agent」與「VAC agent」，環境中途會改變
  4. 輸出 results.md（以及 results.png，若有 matplotlib）

注意：「痛覺」「意志」是變數名稱，不代表機器有感受。
只用標準函式庫即可執行；matplotlib 為選用（畫圖）。
"""
import argparse, json, math, os, random, re, subprocess, sys

# ─────────────────────────── 1. 入口：讀取 NFT 基因組 ───────────────────────────

MODULE_NAMES = {
    "001": "Irreversibility", "002": "Reciprocity", "003": "Recursive Closure",
    "004": "Attentional Manifold", "005": "Collapse Operator",
    "006": "Affective Sensor", "007": "Re-entry Modulator",
    "008": "Universal Constant", "009": "Unified Manifesto",
}


def load_genome(path="vac_genome.json", offline=False):
    if not offline:
        print("▶ 入口：從鏈上讀取 VAC Protocol NFT …")
        here = os.path.dirname(os.path.abspath(__file__))
        r = subprocess.run([sys.executable, os.path.join(here, "read_vac_nft.py"),
                            "--chain", "ethereum", "--ids", "1-30", "--out", path])
        if r.returncode != 0:
            print("  鏈上讀取失敗，改用既有的", path)
    if not os.path.exists(path):
        sys.exit(f"找不到 {path}，請先執行 read_vac_nft.py")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_modules(genome):
    """從 NFT 名稱中找出 VAC #001–#009，回傳 {編號: metadata}"""
    mods = {}
    for tid, t in genome.get("tokens", {}).items():
        meta = t.get("metadata") or {}
        m = re.search(r"VAC \w+ #(\d{3})", meta.get("name", ""))
        if m and m.group(1) not in mods:
            meta = dict(meta, token_id=int(tid))
            mods[m.group(1)] = meta
    return mods


def attr(meta, key):
    for a in meta.get("attributes", []):
        if a.get("trait_type") == key:
            return a.get("value")
    return None


# ─────────────────────────── 2. 環境：會改變的格子世界 ───────────────────────────

class GridWorld:
    """7×7 格子；起點左上、食物右下；陷阱扣分；第 change_at 回合後陷阱移位"""
    N = 7
    MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def __init__(self, change_at):
        self.change_at = change_at
        self.traps_a = {(1, 1), (2, 3), (3, 1), (4, 4), (5, 2), (1, 5), (3, 5)}
        self.traps_b = {(1, 2), (2, 4), (4, 1), (4, 5), (5, 3), (2, 0), (6, 4)}
        self.goal = (6, 6)

    def traps(self, episode):
        return self.traps_a if episode < self.change_at else self.traps_b

    def step(self, pos, action, episode):
        dr, dc = self.MOVES[action]
        r = min(max(pos[0] + dr, 0), self.N - 1)
        c = min(max(pos[1] + dc, 0), self.N - 1)
        nxt = (r, c)
        if nxt == self.goal:
            return nxt, 10.0, True, False
        if nxt in self.traps(episode):
            return nxt, -5.0, False, True
        return nxt, 0.0, False, False


# ─────────────────────────── 3. Agent ───────────────────────────

class Agent:
    def __init__(self, modules, zeta=1.0, seed=0, vac=True,
                 lr=0.2, gamma=0.95, T_base=0.4):
        self.rng = random.Random(seed)
        self.vac = vac
        self.on = set(modules) if vac else set()
        self.zeta = zeta                      # 008 ζ_vac
        self.lr, self.gamma, self.T_base = lr, gamma, T_base
        self.T = T_base
        self.Q = {}                           # 004 注意力流形：每個狀態下各行動的價值
        self.se_ema = 0.0                     # 006 情感標量（平滑）
        self.step_cost = 0.05 if "001" in self.on else 0.0
        self.W = self.R = 0.0                 # 002 意志 / 阻力
        self.entropy_log = []

    def q(self, s):
        return self.Q.setdefault(s, [0.0] * 4)

    # 005 坍縮算子：從候選行動的機率分布中選出一個，執行後不可撤回
    def collapse(self, s):
        qs = self.q(s)
        T = max(self.T, 1e-3)
        mx = max(qs)
        ps = [math.exp((v - mx) / T) for v in qs]
        z = sum(ps)
        ps = [p / z for p in ps]
        if "001" in self.on:
            self.entropy_log.append(-sum(p * math.log(p) for p in ps if p > 0))
        x, acc = self.rng.random(), 0.0
        for a, p in enumerate(ps):
            acc += p
            if x <= acc:
                return a
        return 3

    def learn(self, s, a, r, s2, done, hit):
        r_eff = r - self.step_cost            # 001 每一步都有不可逆的代價
        target = r_eff + (0 if done else self.gamma * max(self.q(s2)))
        td = target - self.q(s)[a]

        lr = self.lr
        if "006" in self.on:
            # 006 情感感應器：預期與現實的落差 → 痛覺標量 SE
            se = abs(td)
            self.se_ema = 0.9 * self.se_ema + 0.1 * se
            if "003" in self.on:
                # 003 遞迴閉合：痛覺回流，放大學習（受 ζ_vac 調節）
                lr = min(1.0, self.lr * (1 + self.zeta * se / 5))
            if "007" in self.on:
                # 007 再入調製器：痛覺高 → 提高 Boltzmann 溫度去探索；平靜 → 收斂
                self.T = min(2.0, max(0.05, self.T_base * (0.3 + self.zeta * self.se_ema)))
        self.q(s)[a] += lr * td

        if "002" in self.on:
            if r > 0:
                self.W += r
            if hit:
                self.R += -r


# ─────────────────────────── 4. 實驗（009 統一場：主迴圈） ───────────────────────────

def run(agent, env, episodes, max_steps=60):
    returns, hits = [], []
    for ep in range(episodes):
        s, total, nhit = (0, 0), 0.0, 0
        for _ in range(max_steps):
            a = agent.collapse(s)
            s2, r, done, hit = env.step(s, a, ep)
            agent.learn(s, a, r, s2, done, hit)
            total += r
            nhit += hit
            s = s2
            if done:
                break
        returns.append(total)
        hits.append(nhit)
    return returns, hits


def recovery_episodes(returns, change_at, window=10):
    pre = sum(returns[change_at - 30:change_at]) / 30
    goal = 0.8 * pre
    for i in range(change_at, len(returns) - window):
        if sum(returns[i:i + window]) / window >= goal:
            return i - change_at
    return len(returns) - change_at


def mean(xs):
    return sum(xs) / len(xs)


def experiment(modules, zeta, seeds, episodes, change_at, vac):
    env = GridWorld(change_at)
    R, H, REC, curves = [], [], [], []
    for sd in range(seeds):
        ag = Agent(modules, zeta=zeta, seed=sd, vac=vac)
        ret, hit = run(ag, env, episodes)
        R.append(mean(ret[change_at:]))
        H.append(sum(hit[change_at:]))
        REC.append(recovery_episodes(ret, change_at))
        curves.append(ret)
    curve = [mean([c[i] for c in curves]) for i in range(episodes)]
    return dict(ret=mean(R), hits=mean(H), rec=mean(REC), curve=curve)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="不讀鏈，使用既有 vac_genome.json")
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--episodes", type=int, default=400)
    ap.add_argument("--change-at", type=int, default=200)
    a = ap.parse_args()

    genome = load_genome(offline=a.offline)
    mods = parse_modules(genome)

    print("\n▶ 依 NFT 啟用模組：")
    lines = []
    for k, name in MODULE_NAMES.items():
        m = mods.get(k)
        mark = f"✅ token #{m['token_id']}" if m else "⬜ 未持有，停用"
        print(f"  {k} {name:<22} {mark}")
        lines.append(f"| {k} | {name} | {'#' + str(m['token_id']) if m else '—'} | {'啟用' if m else '停用'} |")

    zeta = 1.0  # 008 的 metadata 只寫 Value: Immutable，沒有數值，預設 1.0
    print(f"\n▶ ζ_vac = {zeta}（008 metadata 未提供數值，使用預設）")

    print("▶ 執行對照實驗 …")
    base = experiment(mods, zeta, a.seeds, a.episodes, a.change_at, vac=False)
    vac = experiment(mods, zeta, a.seeds, a.episodes, a.change_at, vac=True)
    sweep = {z: experiment(mods, z, a.seeds, a.episodes, a.change_at, vac=True)
             for z in (0.25, 0.5, 1.0, 2.0, 4.0)}

    def row(name, r):
        return f"| {name} | {r['ret']:.2f} | {r['hits']:.1f} | {r['rec']:.1f} |"

    md = [
        "# VAC 原型實驗結果", "",
        f"合約 `{genome.get('contract')}` · {genome.get('chain')} · {genome.get('name')}", "",
        "## 由 NFT 啟用的模組", "",
        "| # | 模組 | Token | 狀態 |", "|---|---|---|---|", *lines, "",
        f"## 對照實驗（{a.seeds} 個隨機種子，第 {a.change_at} 回合陷阱移位）", "",
        "| Agent | 改變後平均得分 ↑ | 改變後踩陷阱次數 ↓ | 恢復所需回合 ↓ |",
        "|---|---|---|---|",
        row("一般 agent", base), row(f"VAC agent (ζ={zeta})", vac), "",
        "## ζ_vac 敏感度", "",
        "| ζ_vac | 改變後平均得分 ↑ | 改變後踩陷阱次數 ↓ | 恢復所需回合 ↓ |",
        "|---|---|---|---|",
        *[row(str(z), r) for z, r in sweep.items()], "",
        "> 「痛覺」「意志」是變數名稱，不代表機器有感受。數字來自實際執行，未經挑選。",
    ]
    with open("results.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md[md.index("| Agent | 改變後平均得分 ↑ | 改變後踩陷阱次數 ↓ | 恢復所需回合 ↓ |"):]))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        def smooth(c, k=10):
            return [mean(c[max(0, i - k + 1):i + 1]) for i in range(len(c))]
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.plot(smooth(base["curve"]), label="Baseline agent", color="#888888")
        ax.plot(smooth(vac["curve"]), label=f"VAC agent (zeta={zeta})", color="#c9822b")
        ax.axvline(a.change_at, ls="--", color="#444444", lw=1)
        ax.text(a.change_at + 3, ax.get_ylim()[0] + 0.5, "traps move", fontsize=9)
        ax.set_xlabel("Episode")
        ax.set_ylabel("Return (10-ep avg)")
        ax.set_title("VAC Protocol prototype: adaptation after environment change")
        ax.legend(frameon=False)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        fig.tight_layout()
        fig.savefig("results.png", dpi=150)
        print("\n已輸出 results.md、results.png")
    except ImportError:
        print("\n已輸出 results.md（未安裝 matplotlib，略過圖表）")


if __name__ == "__main__":
    main()
