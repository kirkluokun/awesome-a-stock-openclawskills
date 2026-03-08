# 05 — 组合与因子分析 (Portfolio & Factor Analysis)

从单资产分析到多资产组合维度。涵盖组合优化、因子分解和绩效评估。

---

## 方法一览

| 方法                 | 函数                                            | 输出                  |
| -------------------- | ----------------------------------------------- | --------------------- |
| 均值-方差(Markowitz) | `optimize_portfolio(df, method='markowitz')`    | 有效前沿 + 权重       |
| 最大夏普             | `optimize_portfolio(df, method='max_sharpe')`   | 最优风险收益比        |
| 最小方差             | `optimize_portfolio(df, method='min_variance')` | 最低风险组合          |
| 风险平价             | `optimize_portfolio(df, method='risk_parity')`  | 等风险贡献权重        |
| PCA 因子             | `pca_factors(df)`                               | 主成分 + 载荷         |
| 绩效指标             | `performance_metrics(returns)`                  | Sharpe/Sortino/Calmar |

---

## 组合优化

```python
from analysis_toolkit import optimize_portfolio

# 准备多资产日收益率
returns_df = pd.DataFrame({
    'AAPL': aapl_returns,
    'GLD': gold_returns,
    'TLT': bond_returns,
    'BTC': btc_returns,
})

# 最大夏普比率组合
result = optimize_portfolio(returns_df, method='max_sharpe', risk_free=0.04)
print(f"最优权重: {result['weights']}")
print(f"预期年化: {result['expected_return']:.2%}")
print(f"年化波动: {result['volatility']:.2%}")
print(f"夏普比率: {result['sharpe']:.2f}")

# 风险平价组合
rp = optimize_portfolio(returns_df, method='risk_parity')
print(f"风险平价权重: {rp['weights']}")
```

### 有效前沿可视化
```python
import matplotlib.pyplot as plt

result = optimize_portfolio(returns_df, method='markowitz', n_portfolios=10000)
plt.figure(figsize=(10, 6))
plt.scatter(result['frontier_volatilities'], result['frontier_returns'],
            c=result['frontier_sharpes'], cmap='viridis', alpha=0.5, s=5)
plt.colorbar(label='Sharpe Ratio')
plt.xlabel('年化波动率')
plt.ylabel('年化收益率')
plt.title('有效前沿')
```

### 方法选择
| 方法            | 优点             | 缺点           | 适用             |
| --------------- | ---------------- | -------------- | ---------------- |
| Max Sharpe      | 最优风险收益比   | 对估计误差敏感 | 预期收益可靠时   |
| Min Variance    | 不需要收益率估计 | 可能过度集中   | 不确定收益方向时 |
| **Risk Parity** | 分散化好，稳健   | 不考虑预期收益 | **默认推荐**     |

---

## PCA 因子分析

从多只股票中提取公共驱动因子：

```python
from analysis_toolkit import pca_factors

# 用一组股票的收益率
result = pca_factors(returns_df, n_components=3)

# 解释方差比
print(f"前3个因子解释了 {result['cumulative_ratio'][-1]:.1%} 的方差")
print(f"PC1: {result['explained_ratio'][0]:.1%}")
print(f"PC2: {result['explained_ratio'][1]:.1%}")
print(f"PC3: {result['explained_ratio'][2]:.1%}")

# 因子载荷（哪些股票对哪个因子暴露大）
print("因子载荷:")
print(result['loadings'])
```

### 解读
- **PC1** 通常代表市场因子（所有股票同涨同跌）
- **PC2** 可能代表板块因子（行业分化）
- **PC3** 可能代表风格因子（大小盘、价值成长）

---

## 绩效指标

```python
from analysis_toolkit import performance_metrics

metrics = performance_metrics(strategy_returns, risk_free=0.04/252,
                              benchmark=index_returns)

print(f"年化收益: {metrics['annual_return']:.2%}")
print(f"年化波动: {metrics['annual_volatility']:.2%}")
print(f"Sharpe:   {metrics['sharpe_ratio']:.2f}")
print(f"Sortino:  {metrics['sortino_ratio']:.2f}")
print(f"Calmar:   {metrics['calmar_ratio']:.2f}")
print(f"最大回撤: {metrics['max_drawdown']:.2%}")
print(f"胜率:     {metrics['win_rate']:.1%}")
print(f"偏度:     {metrics['skewness']:.2f}")
print(f"峰度:     {metrics['kurtosis']:.2f}")

if 'information_ratio' in metrics:
    print(f"信息比率: {metrics['information_ratio']:.2f}")
    print(f"跟踪误差: {metrics['tracking_error']:.2%}")
```

### 指标解读快查
| 指标          | 好的标准 | 含义                 |
| ------------- | -------- | -------------------- |
| Sharpe > 1    | 优秀     | 每单位风险的超额收益 |
| Sortino > 1.5 | 优秀     | 只考虑下行风险       |
| Calmar > 1    | 良好     | 收益 / 最大回撤      |
| MDD < 20%     | 可接受   | 历史最大亏损         |
| 偏度 > 0      | 好       | 正向非对称           |
| 峰度 < 3      | 好       | 尾部风险小           |

---

## 典型分析组合

### "优化我的组合"
```
1. 计算各资产绩效指标 → 了解各自风险收益
2. 相关矩阵 → 确认分散化效果
3. 组合优化 → 生成有效前沿
4. 比较 Max Sharpe vs Risk Parity → 推荐方案
```

### "我的持仓暴露了什么风险？"
```
1. PCA 因子分析 → 提取主驱动因子
2. 因子载荷矩阵 → 每只股票的因子暴露
3. 协方差分解 → 系统性 vs 特异性风险占比
```
