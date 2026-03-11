"""
Phase 5d-1 新增接口的单元测试

覆盖：上市公司基本信息(stock_company)、沪深港通股票列表(stock_hsgt)、
      ST股票列表(stock_st)、AH股比价(stk_ah_comparison)、
      国际主要指数(index_global)、大盘指数每日指标(index_dailybasic)、
      沪深市场每日交易统计(daily_info)、期货合约列表(fut_basic)、
      管理层薪酬和持股(stk_rewards)、申万行业成分(index_member_all)、
      中信行业指数日行情(ci_daily)、中信行业成分(ci_index_member)、
      全球财经事件(eco_cal)、新闻联播文字稿(cctv_news)
"""

import pandas as pd
import pytest

from tushare_mcp import client
from tests.conftest import make_df


# ==================== 股票信息 ====================


class TestStockCompany:
    def test_query(self, mock_pro_api):
        mock_pro_api.stock_company.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "chairman": ["谢永林"],
            "manager": ["冀光恒"],
            "reg_capital": [194.05],
        })
        df = client.stock_company(ts_code="000001.SZ")
        assert df.iloc[0]["chairman"] == "谢永林"
        mock_pro_api.stock_company.assert_called_once_with(
            ts_code="000001.SZ",
        )


class TestStockHsgt:
    def test_query(self, mock_pro_api):
        mock_pro_api.stock_hsgt.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "name": ["平安银行"],
            "trade_date": ["20260226"],
        })
        df = client.stock_hsgt(type="HK_SZ", trade_date="2026-02-26")
        assert df.iloc[0]["name"] == "平安银行"
        mock_pro_api.stock_hsgt.assert_called_once_with(
            type="HK_SZ", trade_date="20260226",
        )


class TestStockSt:
    def test_query(self, mock_pro_api):
        mock_pro_api.stock_st.return_value = make_df({
            "ts_code": ["000023.SZ"],
            "name": ["*ST深天"],
            "trade_date": ["20260226"],
        })
        df = client.stock_st(trade_date="2026-02-26")
        assert df.iloc[0]["name"] == "*ST深天"
        mock_pro_api.stock_st.assert_called_once_with(
            trade_date="20260226",
        )


class TestStkAhComparison:
    def test_query(self, mock_pro_api):
        mock_pro_api.stk_ah_comparison.return_value = make_df({
            "ts_code": ["601318.SH"],
            "hk_code": ["02318.HK"],
            "trade_date": ["20260226"],
            "ah_ratio": [1.25],
        })
        df = client.stk_ah_comparison(
            ts_code="601318.SH", trade_date="2026-02-26",
        )
        assert df.iloc[0]["ah_ratio"] == 1.25
        mock_pro_api.stk_ah_comparison.assert_called_once_with(
            ts_code="601318.SH", trade_date="20260226",
        )


# ==================== 指数与市场 ====================


class TestIndexGlobal:
    def test_query(self, mock_pro_api):
        mock_pro_api.index_global.return_value = make_df({
            "ts_code": ["SPX"],
            "trade_date": ["20260226"],
            "close": [5800.0],
            "pct_chg": [0.85],
        })
        df = client.index_global(ts_code="SPX", trade_date="2026-02-26")
        assert df.iloc[0]["close"] == 5800.0
        mock_pro_api.index_global.assert_called_once_with(
            ts_code="SPX", trade_date="20260226",
        )


class TestIndexDailybasic:
    def test_query(self, mock_pro_api):
        mock_pro_api.index_dailybasic.return_value = make_df({
            "ts_code": ["000300.SH"],
            "trade_date": ["20260226"],
            "pe": [13.5],
            "turnover_rate": [0.85],
        })
        df = client.index_dailybasic(
            ts_code="000300.SH", trade_date="2026-02-26",
        )
        assert df.iloc[0]["pe"] == 13.5
        mock_pro_api.index_dailybasic.assert_called_once_with(
            ts_code="000300.SH", trade_date="20260226",
        )


class TestDailyInfo:
    def test_query(self, mock_pro_api):
        mock_pro_api.daily_info.return_value = make_df({
            "trade_date": ["20260226"],
            "exchange": ["SH"],
            "up_count": [1200],
            "down_count": [800],
        })
        df = client.daily_info(trade_date="2026-02-26", exchange="SH")
        assert df.iloc[0]["up_count"] == 1200
        mock_pro_api.daily_info.assert_called_once_with(
            trade_date="20260226", exchange="SH",
        )


# ==================== 期货 ====================


class TestFutBasic:
    def test_query(self, mock_pro_api):
        mock_pro_api.fut_basic.return_value = make_df({
            "ts_code": ["IF2603.CFX"],
            "symbol": ["IF2603"],
            "exchange": ["CFFEX"],
            "name": ["沪深300指数期货2603"],
        })
        df = client.fut_basic(exchange="CFFEX")
        assert df.iloc[0]["exchange"] == "CFFEX"
        mock_pro_api.fut_basic.assert_called_once_with(
            exchange="CFFEX",
        )


# ==================== 公司行为 ====================


class TestStkRewards:
    def test_query(self, mock_pro_api):
        mock_pro_api.stk_rewards.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "ann_date": ["20260401"],
            "name": ["谢永林"],
            "title": ["董事长"],
            "reward": [5000000.0],
        })
        df = client.stk_rewards(ts_code="000001.SZ", end_date="2025-12-31")
        assert df.iloc[0]["reward"] == 5000000.0
        mock_pro_api.stk_rewards.assert_called_once_with(
            ts_code="000001.SZ", end_date="20251231",
        )


# ==================== 行业分类 ====================


class TestIndexMemberAll:
    def test_query(self, mock_pro_api):
        mock_pro_api.index_member_all.return_value = make_df({
            "l1_code": ["801010"],
            "l1_name": ["农林牧渔"],
            "ts_code": ["000998.SZ"],
            "name": ["隆平高科"],
        })
        df = client.index_member_all(l1_code="801010")
        assert df.iloc[0]["l1_name"] == "农林牧渔"
        mock_pro_api.index_member_all.assert_called_once_with(
            l1_code="801010",
        )


class TestCiDaily:
    def test_query(self, mock_pro_api):
        mock_pro_api.ci_daily.return_value = make_df({
            "ts_code": ["CI005001.WI"],
            "trade_date": ["20260226"],
            "close": [8500.0],
            "pct_change": [1.2],
        })
        df = client.ci_daily(ts_code="CI005001.WI", trade_date="2026-02-26")
        assert df.iloc[0]["close"] == 8500.0
        mock_pro_api.ci_daily.assert_called_once_with(
            ts_code="CI005001.WI", trade_date="20260226",
        )


class TestCiIndexMember:
    def test_query(self, mock_pro_api):
        mock_pro_api.ci_index_member.return_value = make_df({
            "l1_code": ["CI005001"],
            "ts_code": ["600036.SH"],
            "name": ["招商银行"],
            "is_new": ["Y"],
        })
        df = client.ci_index_member(l1_code="CI005001", is_new="Y")
        assert df.iloc[0]["name"] == "招商银行"
        mock_pro_api.ci_index_member.assert_called_once_with(
            l1_code="CI005001", is_new="Y",
        )


# ==================== 宏观/新闻 ====================


class TestEcoCal:
    def test_query(self, mock_pro_api):
        mock_pro_api.eco_cal.return_value = make_df({
            "date": ["20260226"],
            "country": ["美国"],
            "event": ["GDP"],
            "value": ["3.2%"],
        })
        df = client.eco_cal(date="2026-02-26", country="美国")
        assert df.iloc[0]["event"] == "GDP"
        mock_pro_api.eco_cal.assert_called_once_with(
            date="20260226", country="美国",
        )


class TestCctvNews:
    def test_query(self, mock_pro_api):
        mock_pro_api.cctv_news.return_value = make_df({
            "date": ["20260226"],
            "title": ["习近平出席会议"],
            "content": ["今天的新闻联播..."],
        })
        df = client.cctv_news(date="2026-02-26")
        assert df.iloc[0]["title"] == "习近平出席会议"
        mock_pro_api.cctv_news.assert_called_once_with(
            date="20260226",
        )
