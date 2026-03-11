# 06 — 状态识别与结构分析 (Regime & Structure)

识别市场所处的状态、发现隐藏周期、多尺度分解价格结构。

---

## 方法一览

| 方法         | 函数                            | 用途               |
| ------------ | ------------------------------- | ------------------ |
| HMM 状态识别 | `detect_regimes(r, n_states=3)` | 自动划分牛/熊/震荡 |
| 变点检测     | `detect_changepoints(s)`        | 趋势突变时间点     |
| 谱分析 (FFT) | `spectral_analysis(s)`          | 发现隐藏周期       |
| 小波分解     | `wavelet_decompose(s)`          | 多尺度时频分析     |
| Hurst 指数   | `hurst_exponent(s)`             | 趋势/随机/均值回复 |

---

## HMM 市场状态识别

```python
from analysis_toolkit import detect_regimes

returns = price_series.pct_change().dropna()

# 三状态模型
result = detect_regimes(returns, n_states=3)
print(f"当前市场状态: {result['current_state']}")
print(f"各状态均值: {result['state_means']}")

# 可视化
import matplotlib.pyplot as plt
fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

# 价格 + 状态着色
colors = {0: 'red', 1: 'yellow', 2: 'green'}
state_series = result['state_series']
for state, color in colors.items():
    mask = state_series == state
    axes[0].fill_between(mask.index, price_series.loc[mask.index].min(),
                         price_series.loc[mask.index].max(),
                         where=mask, alpha=0.3, color=color,
                         label=result['labels'].get(state))
price_series.plot(ax=axes[0], color='black', linewidth=0.8)
axes[0].legend()
axes[0].set_title('价格 + 市场状态')

# 状态序列
state_series.plot(ax=axes[1], title='状态序列')
```

### 状态数选择
| n_states | 含义             | 适用                       |
| -------- | ---------------- | -------------------------- |
| 2        | 牛市 / 熊市      | 趋势策略的开关             |
| **3**    | 牛 / 震荡 / 熊   | **默认推荐**               |
| 4        | 加入"高波动"状态 | 需要区分平稳震荡和剧烈震荡 |

---

## 谱分析 (FFT)

发现价格中的隐藏周期成分：

```python
from analysis_toolkit import spectral_analysis

result = spectral_analysis(price_series)
print(result['interpretation'])

# 功率谱可视化
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(1/result['frequencies'][1:], result['power'][1:])
ax.set_xlabel('周期 (天)')
ax.set_ylabel('功率')
ax.set_title('功率谱密度')
ax.set_xlim(2, 300)

# 标注主导周期
for p in result['dominant_periods'][:3]:
    ax.axvline(x=p, color='r', linestyle='--', alpha=0.5)
    ax.text(p, ax.get_ylim()[1]*0.9, f'{p:.0f}天', ha='center')
```

---

## 小波分解

同时在时域和频域上分析信号——比 FFT 更适合分析**非平稳**的金融序列：

```python
from analysis_toolkit import wavelet_decompose

result = wavelet_decompose(price_series, wavelet='db4', level=5)

# 每层对应不同的时间尺度
for info in result['levels_info']:
    print(f"{info['level']}: 周期≈{info.get('period', 'N/A')}, 能量={info['energy']:.1f}")

# 可视化各层
import pywt
coeffs = result['coeffs']
fig, axes = plt.subplots(len(coeffs), 1, figsize=(14, 3*len(coeffs)))
for i, (c, ax) in enumerate(zip(coeffs, axes)):
    ax.plot(c)
    ax.set_title(result['levels_info'][i]['level'])
plt.tight_layout()
```

### 小波选择
| 小波    | 特点                     |
| ------- | ------------------------ |
| **db4** | 默认推荐，平衡时频分辨率 |
| haar    | 最简单，检测突变         |
| sym8    | 对称，减少相位失真       |

---

## 典型分析组合

### "现在 A 股处于什么状态？"
```
1. HMM 3状态 → 当前是牛/熊/震荡
2. 转移概率矩阵 → 下一个状态最可能是什么
3. 各状态的历史持续时间统计
```

### "螺纹钢有没有 40 天周期？"
```
1. FFT 谱分析 → 主导周期是多少
2. 小波分解 → 该周期成分的能量变化
3. 与已知基本面周期对比（产能周期/补库周期）
```

### "这轮下跌是趋势反转还是震荡回调？"
```
1. HMM → 是否切换到了熊市状态
2. 变点检测 → 是否检测到结构断裂
3. Hurst 指数(近期) → 近期是趋势性还是均值回复
```
