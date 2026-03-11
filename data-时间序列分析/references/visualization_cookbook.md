# 可视化菜谱 (Visualization Cookbook)

常见金融图表的代码模板。所有模板共享中文字体设置。

---

## 全局设置

```python
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np

# 中文字体
plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti TC', 'SimHei', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False

# 配色方案
COLORS = {
    'bull': '#FF4444',
    'bear': '#44AA44',
    'neutral': '#AAAAAA',
    'primary': '#2196F3',
    'secondary': '#FF9800',
    'accent': '#9C27B0',
}
```

---

## K 线图（mplfinance）

```python
import mplfinance as mpf

mc = mpf.make_marketcolors(up='r', down='g', edge='inherit', wick='inherit', volume='in')
style = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', gridcolor='#e6e6e6')

add_plots = [
    mpf.make_addplot(df['MA5'], color='#FF6B6B', width=0.8),
    mpf.make_addplot(df['MA20'], color='#4ECDC4', width=0.8),
    mpf.make_addplot(df['MA60'], color='#45B7D1', width=0.8),
]

fig, axes = mpf.plot(df[['Open','High','Low','Close','Volume']], type='candle',
                      style=style, volume=True, addplot=add_plots,
                      title=f'\n{symbol} K线图', figsize=(14, 8), returnfig=True)
fig.savefig('kline.png', dpi=150, bbox_inches='tight')
```

---

## 热力图（相关矩阵）

```python
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='RdBu_r', center=0,
            fmt='.2f', square=True, linewidths=0.5, ax=ax,
            vmin=-1, vmax=1)
ax.set_title('资产相关性矩阵', fontsize=14)
```

---

## 技术指标四合一面板

```python
fig, axes = plt.subplots(4, 1, figsize=(14, 12), height_ratios=[3,1,1,1], sharex=True)

# 价格 + 布林带
axes[0].plot(df.index, df['Close'], 'k-', lw=1, label='收盘价')
axes[0].fill_between(df.index, df['BOLL_UPPER'], df['BOLL_LOWER'], alpha=0.1, color='blue')
axes[0].legend(loc='upper left', fontsize=8)

# MACD
colors = ['#FF4444' if v >= 0 else '#44AA44' for v in df['MACD_HIST']]
axes[1].bar(df.index, df['MACD_HIST'], color=colors, width=0.8, alpha=0.6)
axes[1].plot(df.index, df['MACD_DIF'], 'b-', lw=0.8)
axes[1].plot(df.index, df['MACD_DEA'], 'r--', lw=0.8)

# RSI
axes[2].plot(df.index, df['RSI14'], color='purple', lw=1)
axes[2].axhline(y=70, color='red', linestyle='--', lw=0.5)
axes[2].axhline(y=30, color='green', linestyle='--', lw=0.5)
axes[2].set_ylim(0, 100)

# KDJ
axes[3].plot(df.index, df['KDJ_K'], 'b-', lw=0.8, label='K')
axes[3].plot(df.index, df['KDJ_D'], color='orange', lw=0.8, label='D')
axes[3].plot(df.index, df['KDJ_J'], color='purple', lw=0.8, label='J')
axes[3].legend(fontsize=8)

plt.tight_layout()
```

---

## 多股归一化对比

```python
fig, ax = plt.subplots(figsize=(12, 6))
for col in df_returns.columns:
    cumret = (1 + df_returns[col]).cumprod() - 1
    ax.plot(cumret.index, cumret * 100, lw=1.5, label=col)
ax.axhline(y=0, color='gray', lw=0.5, linestyle='--')
ax.set_ylabel('累计收益率 (%)')
ax.set_title('资产收益率对比')
ax.legend()
ax.grid(True, alpha=0.3)
```

---

## 波动率锥

```python
fig, ax = plt.subplots(figsize=(10, 6))
cone_df = volatility_cone_data  # DataFrame from volatility_cone()
windows = cone_df.columns

for pct in ['min', '25%', '50%', '75%', 'max']:
    ax.plot(range(len(windows)), cone_df.loc[pct], '--', alpha=0.5, label=pct)
ax.plot(range(len(windows)), cone_df.loc['current'], 'ro-', lw=2, ms=8, label='当前')
ax.set_xticks(range(len(windows)))
ax.set_xticklabels(windows)
ax.set_ylabel('年化波动率')
ax.set_title('波动率锥')
ax.legend()
```

---

## 有效前沿散点图

```python
fig, ax = plt.subplots(figsize=(10, 6))
scatter = ax.scatter(vols, rets, c=sharpes, cmap='viridis', alpha=0.5, s=5)
plt.colorbar(scatter, label='Sharpe Ratio')
ax.scatter(opt_vol, opt_ret, marker='*', s=300, c='red', label='最优组合')
ax.set_xlabel('年化波动率')
ax.set_ylabel('年化收益率')
ax.set_title('有效前沿')
ax.legend()
```

---

## 网络图

```python
import networkx as nx

fig, ax = plt.subplots(figsize=(12, 10))
pos = nx.spring_layout(G, k=2, seed=42)
sizes = [centrality[n] * 3000 + 300 for n in G.nodes()]
nx.draw(G, pos, ax=ax, with_labels=True, node_size=sizes,
        node_color='lightblue', font_size=9, font_weight='bold',
        edge_color='gray', width=1.5)
ax.set_title('资产网络结构')
```

---

## 季节性柱状图

```python
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
colors = ['#44AA44' if x > 0 else '#FF4444' for x in monthly_means]
axes[0].bar(range(12), monthly_means, color=colors)
axes[0].set_xticks(range(12))
axes[0].set_xticklabels(['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'])
axes[0].set_title('月均收益率')
axes[0].axhline(y=0, color='gray', lw=0.5)

axes[1].bar(range(12), win_rates, color='#2196F3')
axes[1].axhline(y=0.5, color='gray', linestyle='--')
axes[1].set_title('月度上涨概率')
```

---

## 保存规范

- 分辨率：`dpi=150`（报告用）或 `dpi=300`（出版级）
- 格式：`.png`（通用）或 `.svg`（矢量）
- 裁切：始终使用 `bbox_inches='tight'`
- 命名：`{symbol}_{chart_type}_{date}.png`
