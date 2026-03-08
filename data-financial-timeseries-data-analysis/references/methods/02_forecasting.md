# 02 — 预测方法 (Forecasting)

本文档覆盖主流时间序列预测方法。注意：**金融市场预测固有不确定性，预测结果仅供参考**。

---

## 方法一览

| 方法         | 函数/工具                          | 适用场景           | 数据要求     |
| ------------ | ---------------------------------- | ------------------ | ------------ |
| ARIMA/SARIMA | `fit_arima()`                      | 单变量短期预测     | ≥100个观测   |
| VAR/VECM     | `fit_var()`                        | 多变量互相预测     | ≥100个观测×N |
| Prophet      | `prophet` 库直接调用               | 快速基线、假日效应 | ≥2年日线     |
| Holt-Winters | `statsmodels.ExponentialSmoothing` | 有季节性的序列     | ≥2个完整周期 |

---

## ARIMA

```python
from analysis_toolkit import fit_arima

# 自动选参 + 预测10天
result = fit_arima(price_series, forecast_steps=10)
print(f"最优阶数: {result['order']}, AIC: {result['aic']:.1f}")
print(result['forecast'])

# 手动指定阶数
result = fit_arima(price_series, order=(1,1,1), forecast_steps=5)

# SARIMA（含季节项）
result = fit_arima(price_series, order=(1,1,1),
                   seasonal_order=(1,1,1,252), forecast_steps=10)
```

### ARIMA 阶数选择指南
1. **d (差分阶数)**：ADF 检验确定。价格序列通常 d=1
2. **p (AR 阶数)**：看 PACF 在第几阶截断
3. **q (MA 阶数)**：看 ACF 在第几阶截断
4. 或者用自动搜索（函数内置 AIC 网格搜索）

---

## VAR (向量自回归)

多个序列互相预测：

```python
from analysis_toolkit import fit_var
import pandas as pd

# 准备多资产收益率
returns = pd.DataFrame({
    '原油': oil_returns,
    '航空': airline_returns,
    '美元': usd_returns,
})

result = fit_var(returns, max_lag=10, forecast_steps=5)
print(f"最优滞后阶数: {result['optimal_lag']}")
print("预测:\n", result['forecast'])
```

### VAR 适用场景
- "油价如何影响航空股？" → 油价和航空收益率的 VAR
- "美元和黄金的联动预测" → 美元指数和黄金收益率
- "铜铝联动分析" → 两个金属的收益率

---

## Prophet

```python
from prophet import Prophet

# 准备数据格式
df_prophet = price_series.reset_index()
df_prophet.columns = ['ds', 'y']

model = Prophet(
    changepoint_prior_scale=0.05,  # 趋势灵活度
    seasonality_prior_scale=10,
    yearly_seasonality=True,
    weekly_seasonality=True,
)
model.fit(df_prophet)

# 预测
future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)

# 可视化
fig = model.plot(forecast)
fig2 = model.plot_components(forecast)
```

### Prophet 适用场景
- 快速基线预测
- 有明显季节性的商品（天然气、农产品）
- 需要考虑假日效应的市场

---

## 预测验证

任何预测方法都应进行验证：

```python
from sklearn.metrics import mean_absolute_error, mean_squared_error

# 滚动窗口回测
train_size = int(len(series) * 0.8)
train, test = series[:train_size], series[train_size:]

result = fit_arima(train, forecast_steps=len(test))
forecast = result['forecast']

mae = mean_absolute_error(test, forecast[:len(test)])
rmse = mean_squared_error(test, forecast[:len(test)], squared=False)
print(f"MAE: {mae:.4f}, RMSE: {rmse:.4f}")
```

---

## ⚠️ 预测方法的局限性

1. **金融市场不是纯时间序列问题** — 受政策、情绪、突发事件影响
2. **过拟合风险** — 参数过多或自动选参可能捕捉噪声
3. **结构变化** — 模型假设数据生成过程不变，但市场 regime 会切换
4. **预测≠交易信号** — 预测方向正确不代表能盈利（还有波动率、交易成本）

**建议**：将时间序列预测作为分析的一个参考维度，而非唯一决策依据。
