"""
Phase 4 新增接口的单元测试

覆盖：港股（hk_basic, hk_tradecal, hk_daily, hk_adjfactor, ggt_daily,
      hk_income, hk_balancesheet, hk_cashflow, hk_fina_indicator）,
      美股（us_basic, us_tradecal, us_daily, us_adjfactor,
      us_income, us_balancesheet, us_cashflow）,
      基金（fund_basic, fund_nav, fund_div, fund_portfolio, fund_company,
      fund_manager, fund_share, fund_adj）,
      ETF（fund_daily, etf_basic）
"""

import pandas as pd
import pytest

from tushare_mcp import client
from tests.conftest import make_df


# ==================== 港股行情 ====================


class TestHkBasic:
    def test_query(self, mock_pro_api):
        mock_pro_api.hk_basic.return_value = make_df({
            "ts_code": ["00001.HK"],
            "name": ["长和"],
            "list_status": ["L"],
        })
        df = client.hk_basic(ts_code="00001.HK")
        assert df.iloc[0]["name"] == "长和"


class TestHkTradecal:
    def test_query(self, mock_pro_api):
        mock_pro_api.hk_tradecal.return_value = make_df({
            "cal_date": ["20260226"],
            "is_open": [1],
        })
        df = client.hk_tradecal(start_date="2026-02-01", end_date="2026-02-28")
        mock_pro_api.hk_tradecal.assert_called_once_with(
            start_date="20260201", end_date="20260228"
        )


class TestHkDaily:
    def test_query(self, mock_pro_api):
        mock_pro_api.hk_daily.return_value = make_df({
            "ts_code": ["00700.HK"],
            "trade_date": ["20260226"],
            "close": [380.0],
            "vol": [15000000.0],
        })
        df = client.hk_daily(ts_code="00700.HK", trade_date="2026-02-26")
        assert df.iloc[0]["close"] == 380.0
        mock_pro_api.hk_daily.assert_called_once_with(
            ts_code="00700.HK", trade_date="20260226"
        )


class TestHkAdjfactor:
    def test_query(self, mock_pro_api):
        mock_pro_api.hk_adjfactor.return_value = make_df({
            "ts_code": ["00700.HK"],
            "trade_date": ["20260226"],
            "adj_factor": [1.25],
        })
        df = client.hk_adjfactor(ts_code="00700.HK")
        assert df.iloc[0]["adj_factor"] == 1.25


class TestGgtDaily:
    def test_query(self, mock_pro_api):
        mock_pro_api.ggt_daily.return_value = make_df({
            "trade_date": ["20260226"],
            "buy_amount": [5000000000.0],
            "sell_amount": [4000000000.0],
        })
        df = client.ggt_daily(trade_date="2026-02-26")
        mock_pro_api.ggt_daily.assert_called_once_with(trade_date="20260226")


# ==================== 港股财务 ====================


class TestHkIncome:
    def test_query(self, mock_pro_api):
        mock_pro_api.hk_income.return_value = make_df({
            "ts_code": ["00700.HK"],
            "ann_date": ["20260315"],
            "ind_name": ["营业额"],
            "ind_value": [560000000000.0],
        })
        df = client.hk_income(ts_code="00700.HK", period="2025-12-31")
        assert df.iloc[0]["ind_value"] == 560000000000.0
        mock_pro_api.hk_income.assert_called_once_with(
            ts_code="00700.HK", period="20251231"
        )


class TestHkBalancesheet:
    def test_query(self, mock_pro_api):
        mock_pro_api.hk_balancesheet.return_value = make_df({
            "ts_code": ["00700.HK"],
            "ind_name": ["总资产"],
            "ind_value": [1500000000000.0],
        })
        df = client.hk_balancesheet(ts_code="00700.HK")
        assert df.iloc[0]["ind_name"] == "总资产"


class TestHkCashflow:
    def test_query(self, mock_pro_api):
        mock_pro_api.hk_cashflow.return_value = make_df({
            "ts_code": ["00700.HK"],
            "ind_name": ["经营活动产生的现金流量净额"],
            "ind_value": [200000000000.0],
        })
        df = client.hk_cashflow(ts_code="00700.HK")
        assert df.iloc[0]["ind_value"] == 200000000000.0


class TestHkFinaIndicator:
    def test_query(self, mock_pro_api):
        mock_pro_api.hk_fina_indicator.return_value = make_df({
            "ts_code": ["00700.HK"],
            "period": ["20251231"],
            "roe": [22.5],
        })
        df = client.hk_fina_indicator(ts_code="00700.HK", period="20251231")
        assert df.iloc[0]["roe"] == 22.5


# ==================== 美股行情 ====================


class TestUsBasic:
    def test_query(self, mock_pro_api):
        mock_pro_api.us_basic.return_value = make_df({
            "ts_code": ["AAPL"],
            "name": ["Apple Inc"],
            "classify": ["EQ"],
        })
        df = client.us_basic(ts_code="AAPL")
        assert df.iloc[0]["name"] == "Apple Inc"


class TestUsTradecal:
    def test_query(self, mock_pro_api):
        mock_pro_api.us_tradecal.return_value = make_df({
            "cal_date": ["20260226"],
            "is_open": [1],
        })
        df = client.us_tradecal(start_date="2026-02-01", end_date="2026-02-28")
        mock_pro_api.us_tradecal.assert_called_once_with(
            start_date="20260201", end_date="20260228"
        )


class TestUsDaily:
    def test_query(self, mock_pro_api):
        mock_pro_api.us_daily.return_value = make_df({
            "ts_code": ["AAPL"],
            "trade_date": ["20260226"],
            "close": [185.5],
            "vol": [50000000.0],
        })
        df = client.us_daily(ts_code="AAPL", trade_date="2026-02-26")
        assert df.iloc[0]["close"] == 185.5


class TestUsAdjfactor:
    def test_query(self, mock_pro_api):
        mock_pro_api.us_adjfactor.return_value = make_df({
            "ts_code": ["AAPL"],
            "trade_date": ["20260226"],
            "adj_factor": [1.0],
        })
        df = client.us_adjfactor(ts_code="AAPL")
        assert df.iloc[0]["adj_factor"] == 1.0


# ==================== 美股财务 ====================


class TestUsIncome:
    def test_query(self, mock_pro_api):
        mock_pro_api.us_income.return_value = make_df({
            "ts_code": ["AAPL"],
            "period": ["20251231"],
            "ind_name": ["Total Revenue"],
            "ind_value": [400000000000.0],
        })
        df = client.us_income(ts_code="AAPL", period="2025-12-31")
        mock_pro_api.us_income.assert_called_once_with(
            ts_code="AAPL", period="20251231"
        )


class TestUsBalancesheet:
    def test_query(self, mock_pro_api):
        mock_pro_api.us_balancesheet.return_value = make_df({
            "ts_code": ["AAPL"],
            "ind_name": ["Total Assets"],
            "ind_value": [350000000000.0],
        })
        df = client.us_balancesheet(ts_code="AAPL")
        assert df.iloc[0]["ind_name"] == "Total Assets"


class TestUsCashflow:
    def test_query(self, mock_pro_api):
        mock_pro_api.us_cashflow.return_value = make_df({
            "ts_code": ["AAPL"],
            "ind_name": ["Operating Cash Flow"],
            "ind_value": [120000000000.0],
        })
        df = client.us_cashflow(ts_code="AAPL")
        assert df.iloc[0]["ind_value"] == 120000000000.0


# ==================== 基金 ====================


class TestFundBasic:
    def test_query(self, mock_pro_api):
        mock_pro_api.fund_basic.return_value = make_df({
            "ts_code": ["510300.SH"],
            "name": ["沪深300ETF"],
            "market": ["E"],
        })
        df = client.fund_basic(market="E")
        assert df.iloc[0]["name"] == "沪深300ETF"


class TestFundNav:
    def test_query(self, mock_pro_api):
        mock_pro_api.fund_nav.return_value = make_df({
            "ts_code": ["510300.SH"],
            "nav_date": ["20260226"],
            "unit_nav": [4.25],
            "accum_nav": [4.25],
        })
        df = client.fund_nav(ts_code="510300.SH")
        assert df.iloc[0]["unit_nav"] == 4.25


class TestFundDiv:
    def test_query(self, mock_pro_api):
        mock_pro_api.fund_div.return_value = make_df({
            "ts_code": ["510300.SH"],
            "ann_date": ["20260115"],
            "ex_date": ["20260120"],
        })
        df = client.fund_div(ts_code="510300.SH")
        assert df.iloc[0]["ts_code"] == "510300.SH"


class TestFundPortfolio:
    def test_query(self, mock_pro_api):
        mock_pro_api.fund_portfolio.return_value = make_df({
            "ts_code": ["510300.SH"],
            "symbol": ["600519.SH"],
            "mkv": [5000000000.0],
        })
        df = client.fund_portfolio(ts_code="510300.SH")
        assert df.iloc[0]["symbol"] == "600519.SH"


class TestFundCompany:
    def test_query(self, mock_pro_api):
        mock_pro_api.fund_company.return_value = make_df({
            "name": ["华夏基金"],
            "short_name": ["华夏"],
        })
        df = client.fund_company()
        assert df.iloc[0]["name"] == "华夏基金"


class TestFundManager:
    def test_query(self, mock_pro_api):
        mock_pro_api.fund_manager.return_value = make_df({
            "ts_code": ["510300.SH"],
            "name": ["张三"],
        })
        df = client.fund_manager(ts_code="510300.SH")
        assert df.iloc[0]["name"] == "张三"


class TestFundShare:
    def test_query(self, mock_pro_api):
        mock_pro_api.fund_share.return_value = make_df({
            "ts_code": ["510300.SH"],
            "trade_date": ["20260226"],
            "fd_share": [50000000000.0],
        })
        df = client.fund_share(ts_code="510300.SH", trade_date="2026-02-26")
        mock_pro_api.fund_share.assert_called_once_with(
            ts_code="510300.SH", trade_date="20260226"
        )


class TestFundAdj:
    def test_query(self, mock_pro_api):
        mock_pro_api.fund_adj.return_value = make_df({
            "ts_code": ["510300.SH"],
            "trade_date": ["20260226"],
            "adj_factor": [1.05],
        })
        df = client.fund_adj(ts_code="510300.SH")
        assert df.iloc[0]["adj_factor"] == 1.05


# ==================== ETF ====================


class TestFundDaily:
    def test_query(self, mock_pro_api):
        mock_pro_api.fund_daily.return_value = make_df({
            "ts_code": ["510300.SH"],
            "trade_date": ["20260226"],
            "close": [4.25],
            "vol": [500000000.0],
        })
        df = client.fund_daily(ts_code="510300.SH", trade_date="2026-02-26")
        assert df.iloc[0]["close"] == 4.25
        mock_pro_api.fund_daily.assert_called_once_with(
            ts_code="510300.SH", trade_date="20260226"
        )


class TestEtfBasic:
    def test_query(self, mock_pro_api):
        mock_pro_api.etf_basic.return_value = make_df({
            "ts_code": ["510300.SH"],
            "name": ["沪深300ETF"],
            "index_code": ["000300.SH"],
        })
        df = client.etf_basic(ts_code="510300.SH")
        assert df.iloc[0]["index_code"] == "000300.SH"
