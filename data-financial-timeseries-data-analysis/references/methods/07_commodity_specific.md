# 07 — 商品特有分析 (Commodity-Specific)

商品市场有独特的分析维度。本文档覆盖季节性、价差、期限结构等商品特有的分析方法。

---

## 方法一览

| 方法       | 函数/方式                              | 用途                     |
| ---------- | -------------------------------------- | ------------------------ |
| 季节性分析 | `seasonal_analysis(s, freq='monthly')` | 月度/周度涨跌规律        |
| 价差分析   | `spread_analysis(a, b)`                | 跨品种/跨期价差          |
| 期限结构   | 手动构建（见下方）                     | Contango / Backwardation |
| 裂解价差   | 手动构建（见下方）                     | 炼化利润                 |
| 压榨价差   | 手动构建（见下方）                     | 油脂加工利润             |

### 数据获取

| 资产                  | 数据源      | 方式                   |
| --------------------- | ----------- | ---------------------- |
| CBOT 大豆/玉米/小麦   | yfinance    | `ZS=F`, `ZC=F`, `ZW=F` |
| NYMEX 原油/天然气     | yfinance    | `CL=F`, `NG=F`         |
| COMEX 黄金/白银/铜    | yfinance    | `GC=F`, `SI=F`, `HG=F` |
| 国内期货（铜/螺纹钢） | tushare MCP | `tushare_fut_daily`    |
| 国内期货持仓          | tushare MCP | `tushare_fut_holding`  |
| 仓单数据              | tushare MCP | `tushare_fut_wsr`      |

---

## 季节性分析

```python
from analysis_toolkit import seasonal_analysis

# 月度季节性
result = seasonal_analysis(natgas_prices, freq='monthly')
print(f"历史上最强月份: {result['best_period']}")
print(f"历史上最弱月份: {result['worst_period']}")
print(result['stats'])

# 可视化
import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
result['stats']['mean'].plot(kind='bar', ax=axes[0], title='月均收益率',
                              color=['g' if x > 0 else 'r' for x in result['stats']['mean']])
result['win_rate'].plot(kind='bar', ax=axes[1], title='月度上涨概率')
axes[1].axhline(y=0.5, color='gray', linestyle='--')
```

### 经典商品季节性规律（供参考，非绝对）
| 商品   | 通常强势期   | 通常弱势期 | 驱动因素        |
| ------ | ------------ | ---------- | --------------- |
| 天然气 | 10月-2月     | 4月-6月    | 冬季取暖需求    |
| 原油   | 2月-5月      | 9月-11月   | 驾驶季+炼厂检修 |
| 大豆   | 6月-7月      | 9月-10月   | 北半球种植→收获 |
| 黄金   | 1月, 8月-9月 | 3月-4月    | 印度婚季+避险   |
| 铜     | 1月-4月      | 7月-8月    | 开工季+淡季     |

> ⚠️ 季节性是历史统计规律，不是确定性信号。需结合当期基本面。

---

## 价差分析

```python
from analysis_toolkit import spread_analysis

# 金银比
result = spread_analysis(gold_prices, silver_prices, names=['黄金', '白银'])
print(result['interpretation'])

# Z-Score 可视化
fig, axes = plt.subplots(2, 1, figsize=(14, 8))
result['spread'].plot(ax=axes[0], title='价差序列')
result['z_score'].plot(ax=axes[1], title='Z-Score')
axes[1].axhline(y=2, color='r', linestyle='--')
axes[1].axhline(y=-2, color='g', linestyle='--')
axes[1].axhline(y=0, color='gray', linestyle='--')
axes[1].fill_between(result['z_score'].index, -2, 2, alpha=0.1, color='gray')
```

---

## 裂解价差 (Crack Spread)

原油 → 汽油 + 取暖油的炼化利润：

```python
from data_fetcher import fetch

oil = fetch('CL=F', period='2y')['Close']
gasoline = fetch('RB=F', period='2y')['Close']
heating_oil = fetch('HO=F', period='2y')['Close']

# 3:2:1 裂解价差（3桶原油 → 2桶汽油 + 1桶取暖油）
# 注意单位：原油$/桶，成品油$/加仑，1桶=42加仑
crack_spread = (2 * gasoline * 42 + 1 * heating_oil * 42 - 3 * oil) / 3

crack_spread.plot(title='3:2:1 裂解价差', figsize=(12, 5))
plt.ylabel('$/桶')
plt.axhline(y=crack_spread.mean(), color='gray', linestyle='--', label=f'均值 ${crack_spread.mean():.1f}')
plt.legend()
```

---

## 压榨价差 (Crush Spread)

大豆 → 豆粕 + 豆油的加工利润：

```python
soybean = fetch('ZS=F', period='2y')['Close']     # 美分/蒲式耳
meal = fetch('ZM=F', period='2y')['Close']          # $/短吨
oil = fetch('ZL=F', period='2y')['Close']           # 美分/磅

# 大豆压榨毛利 (Board Crush)
# 1蒲式耳大豆 ≈ 产出 44磅豆粕 + 11磅豆油
crush_margin = (meal / 2000 * 44 + oil * 11 / 100 - soybean / 100)

crush_margin.plot(title='大豆压榨价差', figsize=(12, 5))
plt.ylabel('$/蒲式耳')
```

---

## 期限结构 (Term Structure)

用 yfinance 获取不同月份的期货合约来判断 Contango（远月>近月）或 Backwardation（近月>远月）：

```python
from data_fetcher import fetch

# 原油不同月份合约（示例）
contracts = {
    '近月': 'CL=F',
    '次月': 'CLG25.NYM',  # 具体合约代码需查询
}

# 国内期货用 tushare MCP
# ToolSearch("+tushare 期货")
# tushare_fut_basic → 获取合约列表
# tushare_fut_daily → 获取各合约价格
# tushare_fut_mapping → 主力合约映射
```

### Contango vs Backwardation
| 状态              | 特征        | 含义                                 |
| ----------------- | ----------- | ------------------------------------ |
| **Contango**      | 远月 > 近月 | 供应充足，持有成本为正，做多展期亏损 |
| **Backwardation** | 近月 > 远月 | 供应紧张，便利收益高，做多展期盈利   |

---

## 典型分析组合

### "天然气每年什么时候涨？"
```
1. 季节性分析(monthly) → 月度涨跌统计
2. 5年/10年叠加图 → 可视化历史模式
3. STL 分解 → 提取季节成分
```

### "炼化利润趋势如何？"
```
1. 裂解价差计算 → 当前利润水平
2. 价差 Z-Score → vs 历史均值
3. 趋势分析 → 利润是否在扩大/收缩
4. 季节性 → 夏季驾驶季利润是否符合规律
```

### "铜价和螺纹钢有套利机会吗？"
```
1. 协整检验 → 长期均衡关系
2. 价差分析 + Z-Score → 当前偏离程度
3. 季节性 → 价差本身有没有季节规律
```
