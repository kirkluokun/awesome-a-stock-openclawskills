"""
Phase 5d-3 新增接口的单元测试

覆盖：东财板块（dc_index, dc_member, dc_hot）,
      通达信板块（tdx_index, tdx_daily, tdx_member）,
      涨跌停（limit_list_d, limit_cpt_list）,
      ETF补充（etf_share_size, etf_index）,
      筹码分析（cyq_chips, cyq_perf）,
      游资（hm_list, hm_detail）,
      期货补充（fut_settle, fut_holding, fut_wm）,
      分钟行情（stk_mins, hk_mins, etf_mins, opt_mins, rt_min）
"""

import pandas as pd
import pytest

from tushare_mcp import client
from tests.conftest import make_df


# ==================== 东财板块 ====================


class TestDcIndex:
    def test_query(self, mock_pro_api):
        mock_pro_api.dc_index.return_value = make_df({
            "ts_code": ["DC0001"],
            "name": ["半导体"],
            "trade_date": ["20260227"],
            "close": [1200.5],
        })
        df = client.dc_index(ts_code="DC0001", trade_date="2026-02-27")
        assert df.iloc[0]["name"] == "半导体"
        mock_pro_api.dc_index.assert_called_once_with(
            ts_code="DC0001", trade_date="20260227",
        )


class TestDcMember:
    def test_query(self, mock_pro_api):
        mock_pro_api.dc_member.return_value = make_df({
            "ts_code": ["DC0001"],
            "con_code": ["000001.SZ"],
            "name": ["平安银行"],
        })
        df = client.dc_member(ts_code="DC0001", trade_date="2026-02-27")
        assert df.iloc[0]["con_code"] == "000001.SZ"
        mock_pro_api.dc_member.assert_called_once_with(
            ts_code="DC0001", trade_date="20260227",
        )


class TestDcHot:
    def test_query(self, mock_pro_api):
        mock_pro_api.dc_hot.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "trade_date": ["20260227"],
            "hot_type": ["人气榜"],
            "rank": [1],
        })
        df = client.dc_hot(trade_date="2026-02-27", hot_type="人气榜")
        assert df.iloc[0]["rank"] == 1
        mock_pro_api.dc_hot.assert_called_once_with(
            trade_date="20260227", hot_type="人气榜",
        )


# ==================== 通达信板块 ====================


class TestTdxIndex:
    def test_query(self, mock_pro_api):
        mock_pro_api.tdx_index.return_value = make_df({
            "ts_code": ["880001"],
            "trade_date": ["20260227"],
            "close": [5600.0],
        })
        df = client.tdx_index(ts_code="880001", trade_date="2026-02-27")
        assert df.iloc[0]["close"] == 5600.0
        mock_pro_api.tdx_index.assert_called_once_with(
            ts_code="880001", trade_date="20260227",
        )


class TestTdxDaily:
    def test_query(self, mock_pro_api):
        mock_pro_api.tdx_daily.return_value = make_df({
            "ts_code": ["880001"],
            "trade_date": ["20260227"],
            "close": [5600.0],
            "pct_chg": [1.2],
        })
        df = client.tdx_daily(ts_code="880001", trade_date="2026-02-27")
        assert df.iloc[0]["pct_chg"] == 1.2
        mock_pro_api.tdx_daily.assert_called_once_with(
            ts_code="880001", trade_date="20260227",
        )


class TestTdxMember:
    def test_query(self, mock_pro_api):
        mock_pro_api.tdx_member.return_value = make_df({
            "ts_code": ["880001"],
            "con_code": ["600036.SH"],
            "name": ["招商银行"],
        })
        df = client.tdx_member(ts_code="880001", trade_date="2026-02-27")
        assert df.iloc[0]["name"] == "招商银行"
        mock_pro_api.tdx_member.assert_called_once_with(
            ts_code="880001", trade_date="20260227",
        )


# ==================== 涨跌停 ====================


class TestLimitListD:
    def test_query(self, mock_pro_api):
        mock_pro_api.limit_list_d.return_value = make_df({
            "trade_date": ["20260227"],
            "ts_code": ["000001.SZ"],
            "name": ["平安银行"],
            "limit_type": ["U"],
        })
        df = client.limit_list_d(trade_date="2026-02-27", limit_type="U")
        assert df.iloc[0]["limit_type"] == "U"
        mock_pro_api.limit_list_d.assert_called_once_with(
            trade_date="20260227", limit_type="U",
        )


class TestLimitCptList:
    def test_query(self, mock_pro_api):
        mock_pro_api.limit_cpt_list.return_value = make_df({
            "trade_date": ["20260227"],
            "ts_code": ["000001.SZ"],
            "days": [3],
        })
        df = client.limit_cpt_list(trade_date="2026-02-27")
        assert df.iloc[0]["days"] == 3
        mock_pro_api.limit_cpt_list.assert_called_once_with(
            trade_date="20260227",
        )


# ==================== ETF 补充 ====================


class TestEtfShareSize:
    def test_query(self, mock_pro_api):
        mock_pro_api.etf_share_size.return_value = make_df({
            "ts_code": ["510300.SH"],
            "trade_date": ["20260227"],
            "fd_share": [1500000.0],
            "nav": [4.5],
        })
        df = client.etf_share_size(ts_code="510300.SH", trade_date="2026-02-27")
        assert df.iloc[0]["fd_share"] == 1500000.0
        mock_pro_api.etf_share_size.assert_called_once_with(
            ts_code="510300.SH", trade_date="20260227",
        )


class TestEtfIndex:
    def test_query(self, mock_pro_api):
        mock_pro_api.etf_index.return_value = make_df({
            "ts_code": ["510300.SH"],
            "index_code": ["000300.SH"],
            "index_name": ["沪深300"],
        })
        df = client.etf_index(ts_code="510300.SH")
        assert df.iloc[0]["index_name"] == "沪深300"
        mock_pro_api.etf_index.assert_called_once_with(
            ts_code="510300.SH",
        )


# ==================== 筹码分析 ====================


class TestCyqChips:
    def test_query(self, mock_pro_api):
        mock_pro_api.cyq_chips.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "trade_date": ["20260227"],
            "his_low": [10.5],
            "his_high": [15.2],
        })
        df = client.cyq_chips(ts_code="000001.SZ", trade_date="2026-02-27")
        assert df.iloc[0]["his_low"] == 10.5
        mock_pro_api.cyq_chips.assert_called_once_with(
            ts_code="000001.SZ", trade_date="20260227",
        )


class TestCyqPerf:
    def test_query(self, mock_pro_api):
        mock_pro_api.cyq_perf.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "trade_date": ["20260227"],
            "chip_perf": [0.85],
        })
        df = client.cyq_perf(ts_code="000001.SZ", trade_date="2026-02-27")
        assert df.iloc[0]["chip_perf"] == 0.85
        mock_pro_api.cyq_perf.assert_called_once_with(
            ts_code="000001.SZ", trade_date="20260227",
        )


# ==================== 游资 ====================


class TestHmList:
    def test_query(self, mock_pro_api):
        mock_pro_api.hm_list.return_value = make_df({
            "hm_name": ["赵老哥"],
            "hm_code": ["HM001"],
        })
        df = client.hm_list(name="赵老哥")
        assert df.iloc[0]["hm_name"] == "赵老哥"
        mock_pro_api.hm_list.assert_called_once_with(
            name="赵老哥",
        )


class TestHmDetail:
    def test_query(self, mock_pro_api):
        mock_pro_api.hm_detail.return_value = make_df({
            "trade_date": ["20260227"],
            "ts_code": ["000001.SZ"],
            "hm_name": ["赵老哥"],
            "buy_amount": [50000000.0],
        })
        df = client.hm_detail(trade_date="2026-02-27", hm_name="赵老哥")
        assert df.iloc[0]["buy_amount"] == 50000000.0
        mock_pro_api.hm_detail.assert_called_once_with(
            trade_date="20260227", hm_name="赵老哥",
        )


# ==================== 期货补充 ====================


class TestFutSettle:
    def test_query(self, mock_pro_api):
        mock_pro_api.fut_settle.return_value = make_df({
            "ts_code": ["IF2603.CFX"],
            "trade_date": ["20260227"],
            "settle": [5800.0],
        })
        df = client.fut_settle(trade_date="2026-02-27", ts_code="IF2603.CFX")
        assert df.iloc[0]["settle"] == 5800.0
        mock_pro_api.fut_settle.assert_called_once_with(
            trade_date="20260227", ts_code="IF2603.CFX",
        )


class TestFutHolding:
    def test_query(self, mock_pro_api):
        mock_pro_api.fut_holding.return_value = make_df({
            "trade_date": ["20260227"],
            "symbol": ["IF"],
            "broker": ["中信期货"],
            "vol": [15000],
        })
        df = client.fut_holding(trade_date="2026-02-27", symbol="IF")
        assert df.iloc[0]["broker"] == "中信期货"
        mock_pro_api.fut_holding.assert_called_once_with(
            trade_date="20260227", symbol="IF",
        )


class TestFutWm:
    def test_query(self, mock_pro_api):
        mock_pro_api.fut_weekly_monthly.return_value = make_df({
            "ts_code": ["IF2603.CFX"],
            "trade_date": ["20260227"],
            "close": [5800.0],
        })
        df = client.fut_wm(freq="W", ts_code="IF2603.CFX")
        assert df.iloc[0]["close"] == 5800.0
        mock_pro_api.fut_weekly_monthly.assert_called_once_with(
            freq="W", ts_code="IF2603.CFX",
        )


# ==================== 券商研报 ====================


class TestResearchReport:
    def test_query(self, mock_pro_api):
        mock_pro_api.research_report.return_value = make_df({
            "trade_date": ["20260121"],
            "title": ["东吴证券_2025年业绩预增点评"],
            "author": ["孙婷"],
            "inst_csname": ["东吴证券"],
            "url": ["https://example.com/report.pdf"],
        })
        df = client.research_report(
            trade_date="2026-01-21", inst_csname="东吴证券",
        )
        assert df.iloc[0]["inst_csname"] == "东吴证券"
        assert "url" in df.columns
        mock_pro_api.research_report.assert_called_once_with(
            trade_date="20260121", inst_csname="东吴证券",
        )


# ==================== 分钟行情 ====================


class TestStkMins:
    def test_query(self, mock_pro_api):
        mock_pro_api.stk_mins.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "trade_time": ["2026-02-27 09:31:00"],
            "close": [12.5],
            "vol": [5000],
        })
        df = client.stk_mins(ts_code="000001.SZ", freq="1min")
        assert df.iloc[0]["close"] == 12.5
        mock_pro_api.stk_mins.assert_called_once_with(
            ts_code="000001.SZ", freq="1min",
        )


class TestHkMins:
    def test_query(self, mock_pro_api):
        mock_pro_api.hk_mins.return_value = make_df({
            "ts_code": ["00700.HK"],
            "trade_time": ["2026-02-27 09:31:00"],
            "close": [380.0],
        })
        df = client.hk_mins(ts_code="00700.HK", freq="5min")
        assert df.iloc[0]["close"] == 380.0
        mock_pro_api.hk_mins.assert_called_once_with(
            ts_code="00700.HK", freq="5min",
        )


class TestEtfMins:
    def test_query(self, mock_pro_api):
        mock_pro_api.etf_mins.return_value = make_df({
            "ts_code": ["510300.SH"],
            "trade_time": ["2026-02-27 09:31:00"],
            "close": [4.5],
        })
        df = client.etf_mins(ts_code="510300.SH", freq="15min")
        assert df.iloc[0]["close"] == 4.5
        mock_pro_api.etf_mins.assert_called_once_with(
            ts_code="510300.SH", freq="15min",
        )


class TestOptMins:
    def test_query(self, mock_pro_api):
        mock_pro_api.opt_mins.return_value = make_df({
            "ts_code": ["10006522.SH"],
            "trade_time": ["2026-02-27 09:31:00"],
            "close": [0.125],
        })
        df = client.opt_mins(ts_code="10006522.SH", freq="30min")
        assert df.iloc[0]["close"] == 0.125
        mock_pro_api.opt_mins.assert_called_once_with(
            ts_code="10006522.SH", freq="30min",
        )


class TestRtMin:
    def test_query(self, mock_pro_api):
        mock_pro_api.rt_min.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "trade_time": ["2026-02-27 14:30:00"],
            "close": [12.8],
        })
        df = client.rt_min(ts_code="000001.SZ", freq="1min")
        assert df.iloc[0]["close"] == 12.8
        mock_pro_api.rt_min.assert_called_once_with(
            ts_code="000001.SZ", freq="1min",
        )
