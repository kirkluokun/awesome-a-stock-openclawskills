# 03 — 跨资产关系分析 (Cross-Asset Relationships)

分析不同资产之间的统计关系。从简单的相关性到复杂的非线性因果。

---

## 方法一览

| 方法         | 函数                                | 输出            | 复杂度 |
| ------------ | ----------------------------------- | --------------- | ------ |
| 相关矩阵     | `correlation_matrix(df)`            | N×N 矩阵        | ⭐      |
| 滚动相关     | `rolling_correlation(a, b, window)` | 时间序列        | ⭐      |
| 协整检验     | `test_cointegration(a, b)`          | 是否协整 + 价差 | ⭐⭐     |
| Granger 因果 | `granger_causality(a, b)`           | 方向性预测因果  | ⭐⭐     |
| 交叉相关     | `cross_correlation(a, b)`           | 最优 lag        | ⭐⭐     |
| 互信息       | `mutual_information(a, b)`          | 非线性相关度量  | ⭐⭐⭐    |

---

## 相关性分析

```python
from analysis_toolkit import correlation_matrix, rolling_correlation

# 静态相关矩阵
corr = correlation_matrix(returns_df, method='spearman')

# 可视化热力图
import seaborn as sns
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr, annot=True, cmap='RdBu_r', center=0, fmt='.2f', ax=ax)
ax.set_title('资产相关性矩阵')

# 滚动相关（动态追踪）
rolling_corr = rolling_correlation(gold_returns, usd_returns, window=60)
rolling_corr.plot(title='黄金 vs 美元 60日滚动相关')
plt.axhline(y=0, color='gray', linestyle='--')
```

### Pearson vs Spearman vs Kendall
| 方法         | 测量               | 适用                           |
| ------------ | ------------------ | ------------------------------ |
| Pearson      | 线性关系           | 正态分布数据                   |
| **Spearman** | 秩相关（单调关系） | **金融数据首选**，对异常值稳健 |
| Kendall      | 排序一致性         | 小样本、离散数据               |

---

## 协整分析

两个资产虽然分别非平稳，但它们的线性组合是平稳的 → **长期均衡关系**。

```python
from analysis_toolkit import test_cointegration

result = test_cointegration(gold_series, silver_series, method='engle-granger')
print(result['interpretation'])
print(f"对冲比率: {result['hedge_ratio']:.4f}")

# 价差序列
spread = result['spread']
z_score = (spread - spread.mean()) / spread.std()

# 配对交易信号
fig, axes = plt.subplots(2, 1, figsize=(14, 8))
spread.plot(ax=axes[0], title='价差序列')
z_score.plot(ax=axes[1], title='Z-Score')
axes[1].axhline(y=2, color='r', linestyle='--', label='卖出阈值')
axes[1].axhline(y=-2, color='g', linestyle='--', label='买入阈值')
axes[1].axhline(y=0, color='gray', linestyle='--')
axes[1].legend()
```

### 配对交易逻辑
1. 找到协整的资产对
2. 计算价差序列和 Z-Score
3. Z > +2 → 做空价差（空A多B）
4. Z < -2 → 做多价差（多A空B）
5. Z 回归 0 → 平仓

---

## Granger 因果

检验 A 的历史信息是否有助于预测 B（不是真正的因果，是"预测性因果"）。

```python
from analysis_toolkit import granger_causality

# 铜价是否"Granger 因果"于有色板块？
result = granger_causality(copper_returns, nonferrous_returns, max_lag=10)
for lag, info in result.items():
    if info['is_causal']:
        print(f"Lag {lag}: F={info['f_stat']:.2f}, p={info['p_value']:.4f} ✅ 显著")
```

### 注意
- Granger 因果是**线性的**，非线性关系用 Transfer Entropy
- 需要平稳序列（先差分）
- 双向检验：A→B 和 B→A 都要做

---

## 交叉相关（领先-滞后）

找两个序列之间的最优时间差：

```python
from analysis_toolkit import cross_correlation

result = cross_correlation(copper_returns, stock_returns, max_lag=20)
print(f"最优滞后: {result['optimal_lag']}天, 相关系数: {result['max_corr']:.3f}")

# 正 lag = A 领先 B，负 lag = B 领先 A
```

---

## 互信息

捕捉非线性相关性（相关系数只能捕捉线性关系）：

```python
from analysis_toolkit import mutual_information

mi = mutual_information(series_a, series_b, n_bins=20)
print(f"互信息: {mi:.4f}")
# MI = 0 → 独立
# MI 越大 → 依赖性越强（包括非线性）
```

---

## 典型分析组合

### "黄金和美元的关系"
```
1. Spearman 相关矩阵 → 看整体方向（通常负相关）
2. 滚动相关(60天) → 负相关是否一直稳定
3. 协整检验 → 是否存在长期均衡
4. Granger 因果 → 谁领先谁
```

### "该不该做铜铝配对交易？"
```
1. 协整检验 → 是否长期均衡
2. 价差 Z-Score → 当前偏离程度
3. 滚动相关 → 相关性是否稳定
4. Hurst 指数(价差) → 价差是否均值回复
```

### "BTC 和纳指的联动"
```
1. 滚动相关(30天/90天) → 联动是否加强
2. Granger 因果 → 谁影响谁
3. 交叉相关 → 谁领先几天
4. 互信息 → 是否有非线性联动
```
