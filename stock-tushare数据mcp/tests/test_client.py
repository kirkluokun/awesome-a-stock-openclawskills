"""
client.py 单元测试

通过 mock tushare pro_api 验证所有 10 个接口。
"""

import pandas as pd
import pytest

from tushare_mcp import client
from tushare_mcp.errors import ApiError, TokenError
from tests.conftest import make_df


class TestFormatDate:
    """日期格式化测试"""

    def test_dash_format(self):
        assert client._format_date("2024-01-15") == "20240115"

    def test_plain_format(self):
        assert client._format_date("20240115") == "20240115"

    def test_none(self):
        assert client._format_date(None) is None


class TestStockBasic:
    def test_query_by_ts_code(self, mock_pro_api):
        mock_pro_api.stock_basic.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "name": ["平安银行"],
            "industry": ["银行"],
        })
        df = client.stock_basic(ts_code="000001.SZ")
        assert len(df) == 1
        assert df.iloc[0]["name"] == "平安银行"
        mock_pro_api.stock_basic.assert_called_once_with(ts_code="000001.SZ")

    def test_query_by_market(self, mock_pro_api):
        mock_pro_api.stock_basic.return_value = make_df({
            "ts_code": ["000001.SZ", "000002.SZ"],
            "name": ["平安银行", "万科A"],
        })
        df = client.stock_basic(market="主板")
        assert len(df) == 2
        mock_pro_api.stock_basic.assert_called_once_with(market="主板")


class TestTradeCalendar:
    def test_query_with_dates(self, mock_pro_api):
        mock_pro_api.trade_cal.return_value = make_df({
            "exchange": ["SSE"],
            "cal_date": ["20240102"],
            "is_open": [1],
        })
        df = client.trade_cal(start_date="2024-01-01", end_date="2024-01-05")
        assert len(df) == 1
        # 验证日期被格式化
        mock_pro_api.trade_cal.assert_called_once_with(
            start_date="20240101", end_date="20240105"
        )


class TestDaily:
    def test_query_by_code_and_dates(self, mock_pro_api):
        mock_pro_api.daily.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "trade_date": ["20240115"],
            "close": [10.5],
            "vol": [100000.0],
        })
        df = client.daily(ts_code="000001.SZ", start_date="2024-01-01", end_date="2024-01-31")
        assert len(df) == 1
        assert df.iloc[0]["close"] == 10.5

    def test_query_by_trade_date(self, mock_pro_api):
        mock_pro_api.daily.return_value = make_df({
            "ts_code": ["000001.SZ", "000002.SZ"],
            "trade_date": ["20240115", "20240115"],
            "close": [10.5, 8.2],
        })
        df = client.daily(trade_date="2024-01-15")
        assert len(df) == 2


class TestDailyBasic:
    def test_query(self, mock_pro_api):
        mock_pro_api.daily_basic.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "pe": [8.5],
            "pb": [0.7],
            "total_mv": [300000.0],
        })
        df = client.daily_basic(ts_code="000001.SZ", trade_date="20240115")
        assert df.iloc[0]["pe"] == 8.5


class TestAdjFactor:
    def test_query(self, mock_pro_api):
        mock_pro_api.adj_factor.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "trade_date": ["20240115"],
            "adj_factor": [120.5],
        })
        df = client.adj_factor(ts_code="000001.SZ", start_date="2024-01-01")
        assert df.iloc[0]["adj_factor"] == 120.5


class TestIncome:
    def test_query(self, mock_pro_api):
        mock_pro_api.income.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "end_date": ["20231231"],
            "revenue": [500000.0],
            "n_income": [100000.0],
        })
        df = client.income(ts_code="000001.SZ", period="20231231")
        assert df.iloc[0]["revenue"] == 500000.0


class TestBalancesheet:
    def test_query(self, mock_pro_api):
        mock_pro_api.balancesheet.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "total_assets": [1000000.0],
            "total_liab": [800000.0],
        })
        df = client.balancesheet(ts_code="000001.SZ", period="20231231")
        assert df.iloc[0]["total_assets"] == 1000000.0


class TestCashflow:
    def test_query(self, mock_pro_api):
        mock_pro_api.cashflow.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "n_cashflow_act": [50000.0],
        })
        df = client.cashflow(ts_code="000001.SZ", period="20231231")
        assert df.iloc[0]["n_cashflow_act"] == 50000.0


class TestFinaIndicator:
    def test_query(self, mock_pro_api):
        mock_pro_api.fina_indicator.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "roe": [12.5],
            "grossprofit_margin": [35.2],
        })
        df = client.fina_indicator(ts_code="000001.SZ", period="20231231")
        assert df.iloc[0]["roe"] == 12.5


class TestIndexDaily:
    def test_query(self, mock_pro_api):
        mock_pro_api.index_daily.return_value = make_df({
            "ts_code": ["000300.SH"],
            "trade_date": ["20240115"],
            "close": [3500.0],
        })
        df = client.index_daily(ts_code="000300.SH", start_date="2024-01-01")
        assert df.iloc[0]["close"] == 3500.0


class TestErrorHandling:
    def test_token_missing(self, monkeypatch):
        """TUSHARE_TOKEN 未设置时应抛出 TokenError"""
        monkeypatch.delenv("TUSHARE_TOKEN", raising=False)
        # 重置单例
        client._pro_api = None
        with pytest.raises(TokenError):
            client.stock_basic()

    def test_api_error_wrapped(self, mock_pro_api):
        """tushare 抛出的异常应被包装为 ApiError"""
        mock_pro_api.daily.side_effect = Exception("抱歉，您每分钟最多访问该接口200次")
        with pytest.raises(ApiError, match="daily"):
            client.daily(ts_code="000001.SZ")

    def test_none_return_gives_empty_df(self, mock_pro_api):
        """tushare 返回 None 时应得到空 DataFrame"""
        mock_pro_api.stock_basic.return_value = None
        df = client.stock_basic()
        assert isinstance(df, pd.DataFrame)
        assert df.empty
