#!/usr/bin/env python3
"""
高阶金融分析工具集
涵盖 8 大方法域的核心函数，AI 按需调用

用法：
    from analysis_toolkit import (
        test_stationarity, decompose_series, detect_changepoints, hurst_exponent,
        test_cointegration, granger_causality, rolling_correlation, cross_correlation,
        fit_garch, calculate_var, max_drawdown, volatility_cone,
        optimize_portfolio, pca_factors, performance_metrics,
        detect_regimes, spectral_analysis, wavelet_decompose,
        seasonal_analysis, spread_analysis,
        correlation_network, build_mst,
    )
"""

import warnings
import pandas as pd
import numpy as np
from scipy import stats

warnings.filterwarnings('ignore')


# ================================================================
# 01. 时间序列基础
# ================================================================

def test_stationarity(series, methods=('adf', 'kpss')):
    """
    序列平稳性检验

    Args:
        series: pd.Series，价格或收益率序列
        methods: 检验方法列表 ('adf', 'kpss', 'pp')

    Returns:
        dict: {method: {statistic, p_value, critical_values, is_stationary, interpretation}}
    """
    from statsmodels.tsa.stattools import adfuller, kpss

    results = {}

    if 'adf' in methods:
        stat, pval, _, _, crit, _ = adfuller(series.dropna(), autolag='AIC')
        results['adf'] = {
            'statistic': stat, 'p_value': pval,
            'critical_values': crit,
            'is_stationary': pval < 0.05,
            'interpretation': f'ADF={stat:.4f}, p={pval:.4f} → {"平稳" if pval < 0.05 else "非平稳"}'
        }

    if 'kpss' in methods:
        stat, pval, _, crit = kpss(series.dropna(), regression='c', nlags='auto')
        results['kpss'] = {
            'statistic': stat, 'p_value': pval,
            'critical_values': crit,
            'is_stationary': pval > 0.05,  # KPSS 原假设是平稳
            'interpretation': f'KPSS={stat:.4f}, p={pval:.4f} → {"平稳" if pval > 0.05 else "非平稳"}'
        }

    if 'pp' in methods:
        from arch.unitroot import PhillipsPerron
        pp = PhillipsPerron(series.dropna())
        results['pp'] = {
            'statistic': pp.stat, 'p_value': pp.pvalue,
            'is_stationary': pp.pvalue < 0.05,
            'interpretation': f'PP={pp.stat:.4f}, p={pp.pvalue:.4f} → {"平稳" if pp.pvalue < 0.05 else "非平稳"}'
        }

    return results


def decompose_series(series, period=None, model='additive'):
    """
    时间序列分解：趋势 + 季节性 + 残差

    Args:
        series: pd.Series（需有 DatetimeIndex）
        period: 季节周期（None 则自动检测）
        model: 'additive' 或 'multiplicative' 或 'stl'

    Returns:
        decomposition 对象，含 .trend, .seasonal, .resid
    """
    from statsmodels.tsa.seasonal import seasonal_decompose, STL

    s = series.dropna()
    if period is None:
        period = min(len(s) // 3, 252)  # 默认年周期或1/3序列长度

    if model == 'stl':
        return STL(s, period=period).fit()
    else:
        return seasonal_decompose(s, model=model, period=period)


def hurst_exponent(series, max_lag=100):
    """
    Hurst 指数 (R/S分析)
    H > 0.5: 趋势性 | H = 0.5: 随机游走 | H < 0.5: 均值回复

    Returns:
        float: Hurst 指数
    """
    s = np.array(series.dropna())
    lags = range(2, min(max_lag, len(s) // 2))
    rs_values = []

    for lag in lags:
        subseries = [s[i:i + lag] for i in range(0, len(s) - lag, lag)]
        rs_list = []
        for sub in subseries:
            if len(sub) < 2:
                continue
            mean = sub.mean()
            devs = sub - mean
            cumdev = np.cumsum(devs)
            R = cumdev.max() - cumdev.min()
            S = sub.std(ddof=1)
            if S > 0:
                rs_list.append(R / S)
        if rs_list:
            rs_values.append((lag, np.mean(rs_list)))

    if len(rs_values) < 2:
        return 0.5

    log_lags = np.log([v[0] for v in rs_values])
    log_rs = np.log([v[1] for v in rs_values])
    H, _ = np.polyfit(log_lags, log_rs, 1)
    return H


def detect_changepoints(series, method='pelt', penalty='bic', n_bkps=None):
    """
    变点检测：找到序列中统计特性发生突变的时间点

    Args:
        series: pd.Series
        method: 'pelt' / 'binseg' / 'bottomup'
        penalty: PELT 惩罚项 ('bic', 'mbic', 'l2')
        n_bkps: Binseg/BottomUp 时指定断点数

    Returns:
        list: 断点索引位置
    """
    import ruptures as rpt

    signal = series.dropna().values
    algo_map = {
        'pelt': rpt.Pelt(model='rbf').fit(signal),
        'binseg': rpt.Binseg(model='rbf').fit(signal),
        'bottomup': rpt.BottomUp(model='rbf').fit(signal),
    }
    algo = algo_map[method]
    if method == 'pelt':
        return algo.predict(pen=np.log(len(signal)) * signal.var())
    else:
        return algo.predict(n_bkps=n_bkps or 5)


def acf_pacf(series, nlags=40):
    """
    计算 ACF 和 PACF

    Returns:
        dict: {acf: array, pacf: array, nlags: int}
    """
    from statsmodels.tsa.stattools import acf, pacf
    s = series.dropna()
    return {
        'acf': acf(s, nlags=nlags),
        'pacf': pacf(s, nlags=nlags, method='ywm'),
        'nlags': nlags
    }


# ================================================================
# 02. 预测
# ================================================================

def fit_arima(series, order=None, seasonal_order=None, forecast_steps=10):
    """
    ARIMA/SARIMA 拟合与预测

    Args:
        series: pd.Series
        order: (p,d,q)，None 则自动选择
        seasonal_order: (P,D,Q,s)
        forecast_steps: 预测步数

    Returns:
        dict: {model, fitted, forecast, aic, bic, summary}
    """
    from statsmodels.tsa.arima.model import ARIMA

    s = series.dropna()
    if order is None:
        # 简单自动选参：用 AIC 挑选
        best_aic = np.inf
        best_order = (1, 1, 1)
        for p in range(4):
            for d in range(2):
                for q in range(4):
                    try:
                        m = ARIMA(s, order=(p, d, q)).fit()
                        if m.aic < best_aic:
                            best_aic, best_order = m.aic, (p, d, q)
                    except Exception:
                        continue
        order = best_order

    model = ARIMA(s, order=order, seasonal_order=seasonal_order).fit()
    forecast = model.forecast(steps=forecast_steps)

    return {
        'model': model,
        'order': order,
        'fitted': model.fittedvalues,
        'forecast': forecast,
        'aic': model.aic,
        'bic': model.bic,
    }


def fit_var(df_returns, max_lag=10, forecast_steps=10):
    """
    VAR 向量自回归模型

    Args:
        df_returns: DataFrame，每列为一个资产的收益率
        max_lag: 最大滞后阶数
        forecast_steps: 预测步数

    Returns:
        dict: {model, optimal_lag, forecast, granger_results}
    """
    from statsmodels.tsa.api import VAR

    data = df_returns.dropna()
    model = VAR(data)
    lag_order = model.select_order(maxlags=max_lag)
    optimal_lag = lag_order.aic
    fitted = model.fit(optimal_lag)
    forecast = fitted.forecast(data.values[-optimal_lag:], steps=forecast_steps)
    forecast_df = pd.DataFrame(forecast, columns=data.columns)

    return {
        'model': fitted,
        'optimal_lag': optimal_lag,
        'forecast': forecast_df,
        'lag_selection': lag_order.summary(),
    }


# ================================================================
# 03. 跨资产关系
# ================================================================

def correlation_matrix(df, method='pearson'):
    """
    相关性矩阵

    Args:
        df: DataFrame，每列一个资产的收益率或价格
        method: 'pearson' / 'spearman' / 'kendall'
    """
    return df.corr(method=method)


def rolling_correlation(series_a, series_b, window=60):
    """
    滚动相关系数

    Returns:
        pd.Series: 滚动相关系数时间序列
    """
    return series_a.rolling(window).corr(series_b)


def test_cointegration(series_a, series_b, method='engle-granger'):
    """
    协整检验

    Args:
        method: 'engle-granger' 或 'johansen'

    Returns:
        dict: {is_cointegrated, statistic, p_value, spread, hedge_ratio}
    """
    if method == 'engle-granger':
        from statsmodels.tsa.stattools import coint
        from statsmodels.regression.linear_model import OLS
        from statsmodels.tools import add_constant
        # 先对齐索引，避免长度不一致
        aligned = pd.concat([series_a, series_b], axis=1).dropna()
        sa = aligned.iloc[:, 0]
        sb = aligned.iloc[:, 1]
        stat, pval, crit = coint(sa, sb)
        # OLS 求对冲比
        X = add_constant(sb.values)
        model = OLS(sa.values, X).fit()
        hedge_ratio = model.params[1]
        spread = sa - hedge_ratio * sb

        return {
            'is_cointegrated': pval < 0.05,
            'statistic': stat,
            'p_value': pval,
            'critical_values': crit,
            'hedge_ratio': hedge_ratio,
            'spread': spread,
            'interpretation': f'协整检验: stat={stat:.4f}, p={pval:.4f} → {"协整" if pval < 0.05 else "不协整"}'
        }
    elif method == 'johansen':
        from statsmodels.tsa.vector_ar.vecm import coint_johansen
        data = pd.concat([series_a, series_b], axis=1).dropna()
        result = coint_johansen(data, det_order=0, k_ar_diff=1)
        return {
            'trace_stat': result.trace_stat,
            'trace_crit': result.trace_stat_crit_vals,
            'eigen_stat': result.max_eig_stat,
            'eigen_crit': result.max_eig_stat_crit_vals,
            'evec': result.evec,
        }


def granger_causality(series_a, series_b, max_lag=10):
    """
    Granger 因果检验

    Returns:
        dict: {lag: {f_stat, p_value, is_causal}}
    """
    from statsmodels.tsa.stattools import grangercausalitytests

    data = pd.concat([series_a, series_b], axis=1).dropna()
    results = grangercausalitytests(data, maxlag=max_lag, verbose=False)

    output = {}
    for lag, res in results.items():
        f_stat = res[0]['ssr_ftest'][0]
        p_val = res[0]['ssr_ftest'][1]
        output[lag] = {
            'f_stat': f_stat,
            'p_value': p_val,
            'is_causal': p_val < 0.05,
        }
    return output


def cross_correlation(series_a, series_b, max_lag=20):
    """
    交叉相关分析：找最优领先-滞后关系

    Returns:
        dict: {lags: array, correlations: array, optimal_lag: int, max_corr: float}
    """
    a = (series_a - series_a.mean()) / series_a.std()
    b = (series_b - series_b.mean()) / series_b.std()
    a, b = a.dropna(), b.dropna()
    idx = a.index.intersection(b.index)
    a, b = a.loc[idx].values, b.loc[idx].values

    lags = range(-max_lag, max_lag + 1)
    corrs = []
    for lag in lags:
        if lag >= 0:
            corrs.append(np.corrcoef(a[lag:], b[:len(a) - lag])[0, 1] if lag < len(a) else 0)
        else:
            corrs.append(np.corrcoef(a[:len(a) + lag], b[-lag:])[0, 1] if -lag < len(a) else 0)

    corrs = np.array(corrs)
    opt_idx = np.argmax(np.abs(corrs))
    return {
        'lags': np.array(list(lags)),
        'correlations': corrs,
        'optimal_lag': list(lags)[opt_idx],
        'max_corr': corrs[opt_idx],
    }


def mutual_information(series_a, series_b, n_bins=20):
    """
    互信息：非线性相关性度量

    Returns:
        float: 互信息值
    """
    from sklearn.metrics import mutual_info_score
    a = pd.cut(series_a.dropna(), bins=n_bins, labels=False)
    b = pd.cut(series_b.dropna(), bins=n_bins, labels=False)
    idx = a.dropna().index.intersection(b.dropna().index)
    return mutual_info_score(a.loc[idx], b.loc[idx])


# ================================================================
# 04. 波动率与风险
# ================================================================

def fit_garch(series, model_type='garch', p=1, q=1, dist='normal'):
    """
    GARCH 家族波动率建模

    Args:
        series: 收益率序列（不是价格！）
        model_type: 'garch' / 'egarch' / 'gjr-garch'
        dist: 'normal' / 't' / 'skewt'

    Returns:
        dict: {model, conditional_volatility, forecast, params, summary}
    """
    from arch import arch_model

    vol_map = {'garch': 'Garch', 'egarch': 'EGARCH', 'gjr-garch': 'GARCH'}
    o = 1 if model_type == 'gjr-garch' else 0

    # 收益率 ×100 提升数值稳定性，输出时 /100 和 /10000 还原
    am = arch_model(series.dropna() * 100, vol=vol_map.get(model_type, 'Garch'),
                    p=p, o=o, q=q, dist=dist)
    res = am.fit(disp='off')
    forecast = res.forecast(horizon=5)

    return {
        'model': res,
        'conditional_volatility': res.conditional_volatility / 100,
        'forecast_variance': forecast.variance.iloc[-1] / 10000,
        'params': res.params,
        'aic': res.aic,
        'bic': res.bic,
    }


def calculate_var(returns, confidence=0.95, method='historical', n_days=1):
    """
    VaR 风险价值

    Args:
        returns: 收益率序列
        confidence: 置信水平
        method: 'historical' / 'parametric' / 'montecarlo'
        n_days: 持有天数

    Returns:
        dict: {var, cvar, method, confidence}
    """
    r = returns.dropna()
    alpha = 1 - confidence
    valid_methods = ('historical', 'parametric', 'montecarlo')
    if method not in valid_methods:
        raise ValueError(f"method 必须为 {valid_methods}，得到: '{method}'")

    if method == 'historical':
        var = np.percentile(r, alpha * 100)
        cvar = r[r <= var].mean()
    elif method == 'parametric':
        mu, sigma = r.mean(), r.std()
        z = stats.norm.ppf(alpha)
        var = mu + z * sigma
        cvar = mu - sigma * stats.norm.pdf(z) / alpha
    else:  # montecarlo
        mu, sigma = r.mean(), r.std()
        rng = np.random.default_rng(seed=42)  # 固定种子保证可复现
        simulated = rng.normal(mu, sigma, 100000)
        var = np.percentile(simulated, alpha * 100)
        cvar = simulated[simulated <= var].mean()

    # 多日调整
    var *= np.sqrt(n_days)
    cvar *= np.sqrt(n_days)

    return {
        'var': var,
        'cvar': cvar,
        'method': method,
        'confidence': confidence,
        'n_days': n_days,
        'interpretation': f'{confidence:.0%} VaR = {var:.4f} ({var*100:.2f}%), CVaR = {cvar:.4f}'
    }


def max_drawdown(series):
    """
    最大回撤

    Returns:
        dict: {max_dd, peak_date, trough_date, recovery_date, dd_series}
    """
    cummax = series.cummax()
    drawdown = (series - cummax) / cummax
    max_dd = drawdown.min()
    trough_idx = drawdown.idxmin()
    peak_idx = series.loc[:trough_idx].idxmax()
    recovery = series.loc[trough_idx:][series.loc[trough_idx:] >= series.loc[peak_idx]]
    recovery_idx = recovery.index[0] if len(recovery) > 0 else None

    return {
        'max_dd': max_dd,
        'peak_date': peak_idx,
        'trough_date': trough_idx,
        'recovery_date': recovery_idx,
        'dd_series': drawdown,
    }


def volatility_cone(series, windows=(5, 10, 21, 63, 126, 252)):
    """
    波动率锥：各窗口的波动率分位数分布

    Returns:
        DataFrame: columns=windows, index=[min, 25%, 50%, 75%, max, current]
    """
    returns = series.pct_change().dropna()
    result = {}
    for w in windows:
        rolling_vol = returns.rolling(w).std() * np.sqrt(252)
        rv = rolling_vol.dropna()
        if len(rv) == 0:
            result[f'{w}D'] = {
                'min': np.nan, '25%': np.nan,
                '50%': np.nan, '75%': np.nan,
                'max': np.nan, 'current': np.nan,
            }
        else:
            result[f'{w}D'] = {
                'min': rv.min(), '25%': rv.quantile(0.25),
                '50%': rv.median(), '75%': rv.quantile(0.75),
                'max': rv.max(), 'current': rv.iloc[-1],
            }
    return pd.DataFrame(result)


# ================================================================
# 05. 组合与因子
# ================================================================

def optimize_portfolio(returns_df, method='markowitz', risk_free=0.03, n_portfolios=5000):
    """
    组合优化

    Args:
        returns_df: DataFrame，每列为一个资产的日收益率
        method: 'markowitz' / 'risk_parity' / 'max_sharpe' / 'min_variance'
        risk_free: 无风险利率（年化）

    Returns:
        dict: {weights, expected_return, volatility, sharpe, efficient_frontier}
    """
    mu = returns_df.mean() * 252
    cov = returns_df.cov() * 252
    n = len(returns_df.columns)

    if method in ('markowitz', 'max_sharpe', 'min_variance'):
        # Monte Carlo 模拟有效前沿
        results = np.zeros((3, n_portfolios))
        weights_record = []
        for i in range(n_portfolios):
            w = np.random.random(n)
            w /= w.sum()
            ret = np.dot(w, mu)
            vol = np.sqrt(np.dot(w, np.dot(cov, w)))
            sharpe = (ret - risk_free) / vol
            results[0, i] = ret
            results[1, i] = vol
            results[2, i] = sharpe
            weights_record.append(w)

        if method == 'max_sharpe':
            idx = results[2].argmax()
        else:
            idx = results[1].argmin()

        best_weights = weights_record[idx]
        return {
            'weights': dict(zip(returns_df.columns, best_weights)),
            'expected_return': results[0, idx],
            'volatility': results[1, idx],
            'sharpe': results[2, idx],
            'frontier_returns': results[0],
            'frontier_volatilities': results[1],
            'frontier_sharpes': results[2],
        }

    elif method == 'risk_parity':
        from scipy.optimize import minimize

        def risk_contrib(w):
            vol = np.sqrt(w @ cov @ w)
            mrc = cov @ w / vol
            rc = w * mrc
            target = vol / n
            return np.sum((rc - target) ** 2)

        w0 = np.ones(n) / n
        bounds = [(0.01, 1.0)] * n
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        result = minimize(risk_contrib, w0, method='SLSQP', bounds=bounds, constraints=constraints)
        w = result.x
        ret = np.dot(w, mu)
        vol = np.sqrt(np.dot(w, np.dot(cov, w)))

        return {
            'weights': dict(zip(returns_df.columns, w)),
            'expected_return': ret,
            'volatility': vol,
            'sharpe': (ret - risk_free) / vol,
        }


def pca_factors(returns_df, n_components=3):
    """
    PCA 因子提取

    Returns:
        dict: {components, explained_variance, explained_ratio, loadings}
    """
    from sklearn.decomposition import PCA

    pca = PCA(n_components=n_components)
    factors = pca.fit_transform(returns_df.dropna())

    return {
        'factors': pd.DataFrame(factors, index=returns_df.dropna().index,
                                columns=[f'PC{i+1}' for i in range(n_components)]),
        'explained_variance': pca.explained_variance_,
        'explained_ratio': pca.explained_variance_ratio_,
        'cumulative_ratio': np.cumsum(pca.explained_variance_ratio_),
        'loadings': pd.DataFrame(pca.components_.T, index=returns_df.columns,
                                 columns=[f'PC{i+1}' for i in range(n_components)]),
    }


def performance_metrics(returns, risk_free=0.03/252, benchmark=None):
    """
    绩效指标计算

    Returns:
        dict: {annual_return, annual_vol, sharpe, sortino, calmar, max_dd, ...}
    """
    r = returns.dropna()
    ann_ret = r.mean() * 252
    ann_vol = r.std() * np.sqrt(252)
    sharpe = (ann_ret - risk_free * 252) / ann_vol if ann_vol > 0 else 0

    downside = r[r < 0].std() * np.sqrt(252)
    sortino = (ann_ret - risk_free * 252) / downside if downside > 0 else 0

    cum_ret = (1 + r).cumprod()
    dd = max_drawdown(cum_ret)
    calmar = ann_ret / abs(dd['max_dd']) if dd['max_dd'] != 0 else 0

    result = {
        'annual_return': ann_ret,
        'annual_volatility': ann_vol,
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
        'calmar_ratio': calmar,
        'max_drawdown': dd['max_dd'],
        'skewness': r.skew(),
        'kurtosis': r.kurtosis(),
        'win_rate': (r > 0).mean(),
    }

    if benchmark is not None:
        b = benchmark.dropna()
        idx = r.index.intersection(b.index)
        excess = r.loc[idx] - b.loc[idx]
        tracking_error = excess.std() * np.sqrt(252)
        info_ratio = excess.mean() * 252 / tracking_error if tracking_error > 0 else 0
        result['tracking_error'] = tracking_error
        result['information_ratio'] = info_ratio

    return result


# ================================================================
# 06. 状态识别与结构分析
# ================================================================

def detect_regimes(series, n_states=3):
    """
    HMM 隐马尔可夫模型 — 市场状态识别

    Args:
        series: 收益率序列
        n_states: 状态数（通常 2=牛熊 或 3=牛/熊/震荡）

    Returns:
        dict: {states, state_means, state_vars, transition_matrix, state_series}
    """
    from hmmlearn.hmm import GaussianHMM

    r = series.dropna().values.reshape(-1, 1)
    model = GaussianHMM(n_components=n_states, covariance_type='full',
                        n_iter=200, random_state=42)
    model.fit(r)
    states = model.predict(r)

    # 按均值排序状态（低→高 = 熊→牛）
    means = model.means_.flatten()
    order = np.argsort(means)
    state_map = {old: new for new, old in enumerate(order)}
    states_sorted = np.array([state_map[s] for s in states])

    labels = {0: '熊市', 1: '震荡', 2: '牛市'} if n_states == 3 else {0: '熊市', 1: '牛市'}

    return {
        'states': states_sorted,
        'state_series': pd.Series(states_sorted, index=series.dropna().index),
        'state_means': means[order],
        'state_vars': model.covars_.flatten()[order],
        'transition_matrix': model.transmat_,
        'labels': labels,
        'current_state': labels.get(states_sorted[-1], f'State {states_sorted[-1]}'),
    }


def spectral_analysis(series, sampling_rate=1):
    """
    谱分析 (FFT) — 发现隐藏周期

    Returns:
        dict: {frequencies, power, dominant_periods}
    """
    s = series.dropna().values
    s = s - s.mean()  # 去均值
    n = len(s)
    fft_vals = np.fft.rfft(s)
    power = np.abs(fft_vals) ** 2
    freqs = np.fft.rfftfreq(n, d=1.0/sampling_rate)

    # 找主导周期（排除 DC 分量）
    power_no_dc = power[1:]
    freqs_no_dc = freqs[1:]
    top_indices = np.argsort(power_no_dc)[-5:][::-1]
    dominant_periods = [1.0/freqs_no_dc[i] for i in top_indices if freqs_no_dc[i] > 0]

    return {
        'frequencies': freqs,
        'power': power,
        'dominant_periods': dominant_periods,
        'interpretation': f'主导周期: {", ".join([f"{p:.0f}天" for p in dominant_periods[:3]])}'
    }


def wavelet_decompose(series, wavelet='db4', level=4):
    """
    小波分解 — 多尺度分析

    Returns:
        dict: {coeffs, levels_info}
    """
    import pywt
    s = series.dropna().values
    coeffs = pywt.wavedec(s, wavelet, level=level)
    levels_info = []
    for i, c in enumerate(coeffs):
        if i == 0:
            levels_info.append({'level': 'Approximation', 'length': len(c), 'energy': np.sum(c**2)})
        else:
            period = 2 ** i
            levels_info.append({'level': f'Detail {i}', 'period': f'~{period}天', 'length': len(c), 'energy': np.sum(c**2)})
    return {'coeffs': coeffs, 'levels_info': levels_info}


# ================================================================
# 07. 商品特有分析
# ================================================================

def seasonal_analysis(series, freq='monthly'):
    """
    季节性分析

    Args:
        series: 价格序列（需至少2年数据）
        freq: 'monthly' / 'weekly' / 'daily'

    Returns:
        dict: {seasonal_pattern, best_month, worst_month, monthly_stats}
    """
    valid_freqs = ('monthly', 'weekly', 'daily')
    if freq not in valid_freqs:
        raise ValueError(f"freq 必须为 {valid_freqs}，得到: '{freq}'")

    r = series.pct_change().dropna()

    if freq == 'monthly':
        grouped = r.groupby(r.index.month)
        stats_df = grouped.agg(['mean', 'std', 'median', 'count'])
        stats_df.columns = ['mean', 'std', 'median', 'count']
        month_names = {1:'1月', 2:'2月', 3:'3月', 4:'4月', 5:'5月', 6:'6月',
                      7:'7月', 8:'8月', 9:'9月', 10:'10月', 11:'11月', 12:'12月'}
        stats_df.index = [month_names.get(m, str(m)) for m in stats_df.index]
    elif freq == 'weekly':
        grouped = r.groupby(r.index.dayofweek)
        stats_df = grouped.agg(['mean', 'std', 'median', 'count'])
        stats_df.columns = ['mean', 'std', 'median', 'count']
        day_names = {0:'周一', 1:'周二', 2:'周三', 3:'周四', 4:'周五'}
        stats_df.index = [day_names.get(d, str(d)) for d in stats_df.index]
    elif freq == 'daily':
        grouped = r.groupby(r.index.day)
        stats_df = grouped.agg(['mean', 'std', 'median', 'count'])
        stats_df.columns = ['mean', 'std', 'median', 'count']
        stats_df.index = [f'{d}日' for d in stats_df.index]

    best = stats_df['mean'].idxmax()
    worst = stats_df['mean'].idxmin()

    return {
        'stats': stats_df,
        'best_period': best,
        'worst_period': worst,
        'win_rate': grouped.apply(lambda x: (x > 0).mean()),
    }


def spread_analysis(series_a, series_b, names=None):
    """
    价差分析

    Returns:
        dict: {spread, z_score, mean, std, current_z, signal}
    """
    spread = series_a - series_b
    spread_clean = spread.dropna()
    mu = spread_clean.mean()
    sigma = spread_clean.std()
    z = (spread_clean - mu) / sigma

    current_z = z.iloc[-1]
    if current_z > 2:
        signal = '价差偏高，可能回归（空A多B）'
    elif current_z < -2:
        signal = '价差偏低，可能回归（多A空B）'
    else:
        signal = '价差在正常范围内'

    label_a = names[0] if names else 'A'
    label_b = names[1] if names else 'B'

    return {
        'spread': spread_clean,
        'z_score': z,
        'mean': mu,
        'std': sigma,
        'current_z': current_z,
        'signal': signal,
        'interpretation': f'{label_a} - {label_b} 价差: Z={current_z:.2f} → {signal}'
    }


# ================================================================
# 08. 网络与信息论
# ================================================================

def correlation_network(returns_df, threshold=0.5):
    """
    构建相关性网络

    Returns:
        dict: {graph, adjacency_matrix, node_centrality}
    """
    import networkx as nx

    corr = returns_df.corr()
    G = nx.Graph()

    for col in corr.columns:
        G.add_node(col)

    for i, col_a in enumerate(corr.columns):
        for j, col_b in enumerate(corr.columns):
            if i < j and abs(corr.iloc[i, j]) >= threshold:
                G.add_edge(col_a, col_b, weight=corr.iloc[i, j])

    centrality = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G)

    return {
        'graph': G,
        'adjacency': corr,
        'degree_centrality': centrality,
        'betweenness_centrality': betweenness,
        'hub': max(centrality, key=centrality.get) if centrality else None,
    }


def build_mst(returns_df):
    """
    最小生成树 (MST) — 提取最核心的资产关系

    Returns:
        dict: {mst_graph, distance_matrix, edges}
    """
    import networkx as nx

    corr = returns_df.corr()
    # 相关距离: d = sqrt(2(1-rho))
    dist = np.sqrt(2 * (1 - corr))

    G_full = nx.Graph()
    for i, a in enumerate(corr.columns):
        for j, b in enumerate(corr.columns):
            if i < j:
                G_full.add_edge(a, b, weight=dist.iloc[i, j])

    mst = nx.minimum_spanning_tree(G_full)

    return {
        'mst_graph': mst,
        'distance_matrix': dist,
        'edges': list(mst.edges(data=True)),
        'n_nodes': mst.number_of_nodes(),
        'n_edges': mst.number_of_edges(),
    }


def community_detection(returns_df):
    """
    社区检测 — 自动发现资产聚类

    Returns:
        dict: {communities, n_communities, modularity}
    """
    import networkx as nx
    from networkx.algorithms.community import greedy_modularity_communities

    corr = returns_df.corr()
    G = nx.Graph()
    for i, a in enumerate(corr.columns):
        for j, b in enumerate(corr.columns):
            if i < j and corr.iloc[i, j] > 0:
                G.add_edge(a, b, weight=corr.iloc[i, j])

    communities = list(greedy_modularity_communities(G))
    modularity = nx.community.modularity(G, communities)

    return {
        'communities': [list(c) for c in communities],
        'n_communities': len(communities),
        'modularity': modularity,
    }
