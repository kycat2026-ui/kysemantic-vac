# VAC 原型實驗結果

合約 `0x4e22b334e53c1dc7e266b5996d32c05a6ac8f4fb` · ethereum · VAC Protocol

## 由 NFT 啟用的模組

| # | 模組 | Token | 狀態 |
|---|---|---|---|
| 001 | Irreversibility | #2 | 啟用 |
| 002 | Reciprocity | #3 | 啟用 |
| 003 | Recursive Closure | #4 | 啟用 |
| 004 | Attentional Manifold | #5 | 啟用 |
| 005 | Collapse Operator | #6 | 啟用 |
| 006 | Affective Sensor | #7 | 啟用 |
| 007 | Re-entry Modulator | #8 | 啟用 |
| 008 | Universal Constant | #9 | 啟用 |
| 009 | Unified Manifesto | #11 | 啟用 |

## 憲法修正案（鏈上規則）

| # | 修正案 | Token |
|---|---|---|
| A01 | VAC Amendment I: Emotional Circuit Breaker | #12 |
| A02 | VAC Amendment II: Creator Veto | #13 |
| A03 | VAC Amendment III: Zeta Calibration | #14 |

- 創作者否決權：A02 與 Axiom #003 同在 0xeace739e1436738caeef04a509a169f3734692b9 → 允許運作
- ζ_vac = 0.5（由 A03（token #14）鏈上校準）
- 情感熔斷：SE 上限 3.0，冷卻 20 步

## 對照實驗（30 個隨機種子，第 200 回合陷阱移位）

| Agent | 改變後平均得分 ↑ | 改變後踩陷阱次數 ↓ | 恢復所需回合 ↓ | 熔斷次數 |
|---|---|---|---|---|
| 一般 agent | 3.78 | 127.6 | 134.7 | 0.0 |
| VAC agent（無修正案，ζ=0.5） | 7.02 | 104.3 | 86.7 | 0.0 |
| VAC agent（含修正案，ζ=0.5） | 7.14 | 93.5 | 67.2 | 33.9 |

## ζ_vac 敏感度（含修正案）

| ζ_vac | 改變後平均得分 ↑ | 改變後踩陷阱次數 ↓ | 恢復所需回合 ↓ | 熔斷次數 |
|---|---|---|---|---|
| 0.25 | 7.03 | 97.6 | 69.7 | 37.8 |
| 0.5 | 7.14 | 93.5 | 67.2 | 33.9 |
| 1.0 | 6.81 | 99.5 | 81.3 | 33.3 |
| 2.0 | 7.02 | 87.3 | 79.2 | 30.3 |
| 4.0 | 7.09 | 68.4 | 72.7 | 32.3 |

> 「痛覺」「意志」是變數名稱，不代表機器有感受。數字來自實際執行，未經挑選。
