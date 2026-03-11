"""
Phase 5a 新增接口的单元测试

覆盖：期货（fut_mapping, fut_daily, fut_wsr, ft_limit, fut_weekly_detail）,
      外汇（fx_obasic, fx_daily）,
      宏观（cn_gdp, cn_pmi）,
      期权（opt_basic, opt_daily）,
      可转债（cb_basic, cb_daily）
"""

import pandas as pd
import pytest

from tushare_mcp import client
from tests.conftest import make_df


# ==================== 期货 ====================


class TestFutMapping:
    def test_query(self, mock_pro_api):
        mock_pro_api.fut_mapping.return_value = make_df({
            "ts_code": ["CU2603.SHF"],
            "trade_date": ["20260226"],
            "mapping_ts_code": ["CU2604.SHF"],
        })
        df = client.fut_mapping(ts_code="CU2603.SHF", trade_date="2026-02-26")
        assert df.iloc[0]["mapping_ts_code"] == "CU2604.SHF"
        mock_pro_api.fut_mapping.assert_called_once_with(
            ts_code="CU2603.SHF", trade_date="20260226",
        )


class TestFutDaily:
    def test_query(self, mock_pro_api):
        # 南华期货指数走 index_daily 接口
        mock_pro_api.index_daily.return_value = make_df({
            "ts_code": ["NHCI.NH"],
            "trade_date": ["20260226"],
            "close": [1500.0],
        })
        df = client.fut_daily(ts_code="NHCI.NH", trade_date="2026-02-26")
        assert df.iloc[0]["close"] == 1500.0
        mock_pro_api.index_daily.assert_called_with(
            ts_code="NHCI.NH", trade_date="20260226",
        )


class TestFutWsr:
    def test_query(self, mock_pro_api):
        mock_pro_api.fut_wsr.return_value = make_df({
            "trade_date": ["20260226"],
            "symbol": ["CU"],
            "vol": [50000.0],
        })
        df = client.fut_wsr(trade_date="2026-02-26", symbol="CU")
        mock_pro_api.fut_wsr.assert_called_once_with(
            trade_date="20260226", symbol="CU",
        )


class TestFtLimit:
    def test_query(self, mock_pro_api):
        mock_pro_api.ft_limit.return_value = make_df({
            "ts_code": ["CU2603.SHF"],
            "trade_date": ["20260226"],
            "up_limit": [70000.0],
            "down_limit": [60000.0],
        })
        df = client.ft_limit(ts_code="CU2603.SHF", trade_date="2026-02-26")
        assert df.iloc[0]["up_limit"] == 70000.0
        mock_pro_api.ft_limit.assert_called_once_with(
            ts_code="CU2603.SHF", trade_date="20260226",
        )


class TestFutWeeklyDetail:
    def test_query(self, mock_pro_api):
        mock_pro_api.fut_weekly_detail.return_value = make_df({
            "exchange": ["SHFE"],
            "prd": ["铜"],
            "vol": [1000000.0],
            "week": ["202609"],
        })
        df = client.fut_weekly_detail(week="202609", exchange="SHFE")
        assert df.iloc[0]["prd"] == "铜"
        mock_pro_api.fut_weekly_detail.assert_called_once_with(
            week="202609", exchange="SHFE",
        )


# ==================== 外汇 ====================


class TestFxObasic:
    def test_query(self, mock_pro_api):
        mock_pro_api.fx_obasic.return_value = make_df({
            "ts_code": ["USDCNH.FXCM"],
            "name": ["美元/离岸人民币"],
            "classify": ["FX"],
        })
        df = client.fx_obasic(classify="FX")
        assert df.iloc[0]["ts_code"] == "USDCNH.FXCM"


class TestFxDaily:
    def test_query(self, mock_pro_api):
        mock_pro_api.fx_daily.return_value = make_df({
            "ts_code": ["USDCNH.FXCM"],
            "trade_date": ["20260226"],
            "bid_close": [7.25],
            "ask_close": [7.26],
        })
        df = client.fx_daily(ts_code="USDCNH.FXCM", trade_date="2026-02-26")
        assert df.iloc[0]["bid_close"] == 7.25
        mock_pro_api.fx_daily.assert_called_once_with(
            ts_code="USDCNH.FXCM", trade_date="20260226",
        )


# ==================== 宏观经济 ====================


class TestCnGdp:
    def test_query(self, mock_pro_api):
        mock_pro_api.cn_gdp.return_value = make_df({
            "quarter": ["2025Q4"],
            "gdp": [320000.0],
            "gdp_yoy": [5.2],
        })
        df = client.cn_gdp(q="2025Q4")
        assert df.iloc[0]["gdp_yoy"] == 5.2
        mock_pro_api.cn_gdp.assert_called_once_with(q="2025Q4")


class TestCnPmi:
    def test_query(self, mock_pro_api):
        mock_pro_api.cn_pmi.return_value = make_df({
            "month": ["202601"],
            "pmi010000": [50.5],
        })
        df = client.cn_pmi(m="202601")
        assert df.iloc[0]["pmi010000"] == 50.5
        mock_pro_api.cn_pmi.assert_called_once_with(m="202601")


# ==================== 期权 ====================


class TestOptBasic:
    def test_query(self, mock_pro_api):
        mock_pro_api.opt_basic.return_value = make_df({
            "ts_code": ["10007976.SH"],
            "name": ["50ETF购3月3000"],
            "exchange": ["SSE"],
            "call_put": ["C"],
        })
        df = client.opt_basic(exchange="SSE", call_put="C")
        assert df.iloc[0]["call_put"] == "C"


class TestOptDaily:
    def test_query(self, mock_pro_api):
        mock_pro_api.opt_daily.return_value = make_df({
            "ts_code": ["10007976.SH"],
            "trade_date": ["20260226"],
            "close": [0.15],
            "vol": [50000.0],
        })
        df = client.opt_daily(ts_code="10007976.SH", trade_date="2026-02-26")
        assert df.iloc[0]["close"] == 0.15
        mock_pro_api.opt_daily.assert_called_once_with(
            ts_code="10007976.SH", trade_date="20260226",
        )


# ==================== 可转债 ====================


class TestCbBasic:
    def test_query(self, mock_pro_api):
        mock_pro_api.cb_basic.return_value = make_df({
            "ts_code": ["113050.SH"],
            "bond_short_name": ["南银转债"],
            "stk_code": ["601009.SH"],
        })
        df = client.cb_basic(ts_code="113050.SH")
        assert df.iloc[0]["bond_short_name"] == "南银转债"


class TestCbDaily:
    def test_query(self, mock_pro_api):
        mock_pro_api.cb_daily.return_value = make_df({
            "ts_code": ["113050.SH"],
            "trade_date": ["20260226"],
            "close": [115.5],
            "vol": [100000.0],
        })
        df = client.cb_daily(ts_code="113050.SH", trade_date="2026-02-26")
        assert df.iloc[0]["close"] == 115.5
        mock_pro_api.cb_daily.assert_called_once_with(
            ts_code="113050.SH", trade_date="20260226",
        )
