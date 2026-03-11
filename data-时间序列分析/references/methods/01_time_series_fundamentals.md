# 01 — 时间序列基础 (Time Series Fundamentals)

在对任何金融序列进行分析之前，必须先理解其统计特性。本文档涵盖平稳性检验、序列分解、自相关分析、结构断裂检测和长记忆性判断。

---

## 方法一览

| 方法            | 函数                                     | 用途                                   |
| --------------- | ---------------------------------------- | -------------------------------------- |
| ADF 检验        | `test_stationarity(s, methods=['adf'])`  | 单位根检验，判断序列是否平稳           |
| KPSS 检验       | `test_stationarity(s, methods=['kpss'])` | ADF 的互补检验（原假设相反）           |
| Phillips-Perron | `test_stationarity(s, methods=['pp'])`   | 对异方差更稳健的单位根检验             |
| STL 分解        | `decompose_series(s, model='stl')`       | 趋势 + 季节性 + 残差                   |
| 经典分解        | `decompose_series(s, model='additive')`  | 加法/乘法分解                          |
| ACF / PACF      | `acf_pacf(s, nlags=40)`                  | 自相关分析，确定模型阶数               |
| 变点检测        | `detect_changepoints(s, method='pelt')`  | 检测趋势突变时间点                     |
| Hurst 指数      | `hurst_exponent(s)`                      | 趋势性(>0.5)/随机(=0.5)/均值回复(<0.5) |

所有函数均在 `scripts/analysis_toolkit.py` 中。

---

## 平稳性检验

### 为什么重要？
大多数统计分析方法（ARIMA、VAR、协整等）**要求序列平稳或差分后平稳**。对非平稳序列直接建模会产生伪回归。

### 推荐流程
```python
from analysis_toolkit import test_stationarity

# 1. 检验原始价格序列
results = test_stationarity(price_series, methods=['adf', 'kpss'])
print(results['adf']['interpretation'])
print(results['kpss']['interpretation'])

# 2. 如果不平稳，检验一阶差分（日收益率）
returns = price_series.pct_change().dropna()
results_diff = test_stationarity(returns, methods=['adf', 'kpss'])

# 3. ADF 和 KPSS 结论比较
# ADF说平稳 + KPSS说平稳 → 确认平稳
# ADF说不平稳 + KPSS说不平稳 → 确认不平稳
# 冲突 → 需进一步检验（差分阶数可能不够或存在结构断裂）
```

### 解读经验
- **金融价格序列**几乎总是非平稳的（ADF p > 0.05）
- **收益率序列**通常平稳（ADF p < 0.05）
- **商品价格**可能存在单位根，也可能是带趋势的平稳过程

---

## 序列分解

将价格/成交量分解为三个成分：

- **趋势 (Trend)**：长期方向
- **季节性 (Seasonal)**：固定周期的重复模式
- **残差 (Residual)**：去除趋势和季节性后的波动

```python
from analysis_toolkit import decompose_series

# STL 分解（推荐，更灵活）
result = decompose_series(price_series, period=252, model='stl')

# 获取各成分
trend = result.trend
seasonal = result.seasonal
residual = result.resid

# 可视化
import matplotlib.pyplot as plt
fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)
price_series.plot(ax=axes[0], title='原始序列')
trend.plot(ax=axes[1], title='趋势')
seasonal.plot(ax=axes[2], title='季节性')
residual.plot(ax=axes[3], title='残差')
plt.tight_layout()
```

### period 选择指南
| 数据频率 | 推荐 period | 场景                 |
| -------- | ----------- | -------------------- |
| 日线     | 252         | 年度季节性（交易日） |
| 日线     | 21          | 月度周期             |
| 周线     | 52          | 年度季节性           |
| 月线     | 12          | 年度季节性           |

---

## Hurst 指数

判断序列的长记忆特性，对策略选择有直接指导意义：

```python
from analysis_toolkit import hurst_exponent

H = hurst_exponent(price_series)

if H > 0.6:
    print(f"H = {H:.3f} → 趋势性强，适合趋势跟踪策略")
elif H < 0.4:
    print(f"H = {H:.3f} → 均值回复，适合均值回归策略")
else:
    print(f"H = {H:.3f} → 接近随机游走")
```

---

## 变点检测

找到价格趋势发生质变的时间点：

```python
from analysis_toolkit import detect_changepoints

breakpoints = detect_changepoints(price_series, method='pelt')

# 将索引位置映射到日期
dates = price_series.dropna().index
bp_dates = [dates[bp] for bp in breakpoints if bp < len(dates)]
print("结构断裂时间点:", bp_dates)
```

### 三种方法对比
| 方法     | 特点                   | 适用场景             |
| -------- | ---------------------- | -------------------- |
| PELT     | 自动确定断点数，速度快 | **首选**，大多数场景 |
| Binseg   | 需指定断点数，二分搜索 | 已知大约有几个转折点 |
| BottomUp | 自底向上合并，保守     | 需要更稳定的结果     |

---

## 典型分析组合

### "铜价有没有趋势？"
```
1. ADF 检验 → 是否单位根
2. Hurst 指数 → 是否趋势性/均值回复
3. STL 分解 → 提取趋势成分看方向
```

### "COVID 后市场结构是否变了？"
```
1. 变点检测 → 找到 2020年初的结构断裂
2. 分段比较均值/方差
3. 分段 Hurst 指数对比
```

### "确定 ARIMA 模型的阶数"
```
1. ADF 确认差分阶数 d
2. ACF/PACF 确认 p 和 q
3. 拟合后检查残差白噪声
```
