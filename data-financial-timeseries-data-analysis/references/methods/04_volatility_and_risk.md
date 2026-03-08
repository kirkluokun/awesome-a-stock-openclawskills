# 04 — 波动率与风险 (Volatility & Risk)

波动率是金融分析的核心维度。本文档覆盖波动率建模、风险度量和极端风险分析。

---

## 方法一览

| 方法       | 函数                                    | 用途                     |
| ---------- | --------------------------------------- | ------------------------ |
| GARCH(1,1) | `fit_garch(r, model_type='garch')`      | 标准波动率建模           |
| EGARCH     | `fit_garch(r, model_type='egarch')`     | 捕捉杠杆效应             |
| GJR-GARCH  | `fit_garch(r, model_type='gjr-garch')`  | 不对称波动率             |
| 波动率锥   | `volatility_cone(prices)`               | 当前波动率在历史中的位置 |
| VaR        | `calculate_var(r, method='historical')` | 风险价值                 |
| CVaR       | `calculate_var(r)` 返回的 cvar 字段     | 尾部风险                 |
| 最大回撤   | `max_drawdown(cum_series)`              | 峰谷最大亏损             |

---

## GARCH 波动率建模

```python
from analysis_toolkit import fit_garch

# 注意：输入必须是收益率，不是价格！
returns = price_series.pct_change().dropna()

# 标准 GARCH
result = fit_garch(returns, model_type='garch', p=1, q=1)
print(f"AIC: {result['aic']:.1f}")

# EGARCH（捕捉下跌波动>上涨波动的不对称性）
result_e = fit_garch(returns, model_type='egarch')

# 条件波动率序列
cond_vol = result['conditional_volatility']
cond_vol.plot(title='GARCH 条件波动率')

# 未来5天波动率预测
print("未来5天预测方差:", result['forecast_variance'])
```

### 模型选择
| 模型           | 特点                   | 适用                 |
| -------------- | ---------------------- | -------------------- |
| **GARCH(1,1)** | 对称，最经典           | 默认首选             |
| **EGARCH**     | 允许波动率对下跌更敏感 | 股票市场（杠杆效应） |
| **GJR-GARCH**  | 另一种不对称方式       | 和 EGARCH 对比选优   |

### 分布选择
- `dist='normal'` — 默认
- `dist='t'` — 厚尾分布，更适合金融数据
- `dist='skewt'` — 偏态 + 厚尾

---

## 波动率锥

判断当前波动率处于历史什么水平：

```python
from analysis_toolkit import volatility_cone

cone = volatility_cone(price_series)
print(cone)
#        5D     10D    21D    63D    126D   252D
# min    0.05   0.08   0.10   0.12   0.14   0.15
# 25%    0.12   0.14   0.15   0.16   0.17   0.18
# 50%    0.18   0.19   0.20   0.21   0.22   0.22
# 75%    0.28   0.27   0.26   0.25   0.25   0.24
# max    0.55   0.48   0.42   0.38   0.35   0.30
# current 0.15  0.16   0.18   0.20   0.21   0.22

# 可视化
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(10, 6))
cone.loc[['min', '25%', '50%', '75%', 'max']].T.plot(ax=ax, style='--', alpha=0.5)
cone.loc['current'].plot(ax=ax, style='ro-', linewidth=2, label='当前')
ax.set_title('波动率锥')
ax.set_ylabel('年化波动率')
ax.legend()
```

---

## VaR 与 CVaR

```python
from analysis_toolkit import calculate_var

returns = price_series.pct_change().dropna()

# 历史模拟法
var_hist = calculate_var(returns, confidence=0.95, method='historical')
print(var_hist['interpretation'])

# 参数法（假设正态分布）
var_param = calculate_var(returns, confidence=0.99, method='parametric')

# Monte Carlo
var_mc = calculate_var(returns, confidence=0.95, method='montecarlo')

# 多日 VaR（10天持有期）
var_10d = calculate_var(returns, confidence=0.95, method='historical', n_days=10)
```

### 三种方法对比
| 方法        | 优点               | 缺点                     |
| ----------- | ------------------ | ------------------------ |
| 历史模拟    | 不需分布假设       | 依赖历史样本             |
| 参数法      | 计算快，公式明确   | 假设正态分布（低估尾部） |
| Monte Carlo | 灵活，可自定义分布 | 计算量大                 |

---

## 最大回撤

```python
from analysis_toolkit import max_drawdown

prices = (1 + returns).cumprod()
dd = max_drawdown(prices)

print(f"最大回撤: {dd['max_dd']:.2%}")
print(f"顶点: {dd['peak_date']}")
print(f"谷底: {dd['trough_date']}")
print(f"恢复: {dd['recovery_date']}")

# 画回撤曲线
dd['dd_series'].plot(title='回撤曲线', figsize=(12, 4))
plt.fill_between(dd['dd_series'].index, dd['dd_series'], alpha=0.3, color='red')
```

---

## 典型分析组合

### "NVDA 波动率处于什么水平？"
```
1. 波动率锥 → 当前 vs 历史分位数
2. GARCH 模型 → 条件波动率趋势
3. GARCH 预测 → 未来5天波动率走向
```

### "原油的下行风险有多大？"
```
1. VaR(95%/99%) → 单日最大可能亏损
2. CVaR → 极端情况下的平均亏损
3. GARCH → 波动率是否在扩大
4. 最大历史回撤 → 最坏情景
```
