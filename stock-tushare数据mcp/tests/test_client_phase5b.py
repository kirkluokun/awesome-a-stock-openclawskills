"""
Phase 5b 新增接口的单元测试

覆盖：债券扩展（cb_issue, cb_rate, cb_call, cb_share, cb_price_chg, repo_daily）,
      指数深化（index_basic, index_weight, index_weekly, index_monthly, sw_daily）,
      A股行情扩展（weekly, monthly, stk_limit）,
      财务补充（fina_audit, fina_mainbz, disclosure_date）
"""

import pandas as pd
import pytest

from tushare_mcp import client
from tests.conftest import make_df


# ==================== 债券扩展 ====================


class TestCbIssue:
    def test_query(self, mock_pro_api):
        mock_pro_api.cb_issue.return_value = make_df({
            "ts_code": ["113050.SH"],
            "ann_date": ["20200115"],
            "issue_size": [8000000000.0],
        })
        df = client.cb_issue(ts_code="113050.SH")
        assert df.iloc[0]["issue_size"] == 8000000000.0


class TestCbRate:
    def test_query(self, mock_pro_api):
        mock_pro_api.cb_rate.return_value = make_df({
            "ts_code": ["113050.SH"],
            "coupon_rate": [0.4],
        })
        df = client.cb_rate(ts_code="113050.SH")
        assert df.iloc[0]["coupon_rate"] == 0.4
        mock_pro_api.cb_rate.assert_called_once_with(ts_code="113050.SH")


class TestCbCall:
    def test_query(self, mock_pro_api):
        mock_pro_api.cb_call.return_value = make_df({
            "ts_code": ["113050.SH"],
            "call_type": ["赎回"],
            "ann_date": ["20260115"],
        })
        df = client.cb_call(ts_code="113050.SH")
        assert df.iloc[0]["call_type"] == "赎回"


class TestCbShare:
    def test_query(self, mock_pro_api):
        mock_pro_api.cb_share.return_value = make_df({
            "ts_code": ["113050.SH"],
            "convert_val": [500000000.0],
            "convert_ratio": [6.25],
        })
        df = client.cb_share(ts_code="113050.SH", ann_date="2026-01-15")
        assert df.iloc[0]["convert_ratio"] == 6.25
        mock_pro_api.cb_share.assert_called_once_with(
            ts_code="113050.SH", ann_date="20260115",
        )


class TestCbPriceChg:
    def test_query(self, mock_pro_api):
        mock_pro_api.cb_price_chg.return_value = make_df({
            "ts_code": ["113050.SH"],
            "convertprice_bef": [15.5],
            "convertprice_aft": [14.8],
        })
        df = client.cb_price_chg(ts_code="113050.SH")
        assert df.iloc[0]["convertprice_aft"] == 14.8
        mock_pro_api.cb_price_chg.assert_called_once_with(ts_code="113050.SH")


class TestRepoDaily:
    def test_query(self, mock_pro_api):
        mock_pro_api.repo_daily.return_value = make_df({
            "ts_code": ["204001.SH"],
            "trade_date": ["20260226"],
            "close": [1.85],
        })
        df = client.repo_daily(ts_code="204001.SH", trade_date="2026-02-26")
        assert df.iloc[0]["close"] == 1.85
        mock_pro_api.repo_daily.assert_called_once_with(
            ts_code="204001.SH", trade_date="20260226",
        )


# ==================== 指数深化 ====================


class TestIndexBasic:
    def test_query(self, mock_pro_api):
        mock_pro_api.index_basic.return_value = make_df({
            "ts_code": ["000300.SH"],
            "name": ["沪深300"],
            "market": ["CSI"],
        })
        df = client.index_basic(market="CSI")
        assert df.iloc[0]["name"] == "沪深300"


class TestIndexWeight:
    def test_query(self, mock_pro_api):
        mock_pro_api.index_weight.return_value = make_df({
            "index_code": ["000300.SH"],
            "con_code": ["600519.SH"],
            "weight": [5.2],
        })
        df = client.index_weight(index_code="000300.SH", trade_date="2026-02-26")
        assert df.iloc[0]["weight"] == 5.2
        mock_pro_api.index_weight.assert_called_once_with(
            index_code="000300.SH", trade_date="20260226",
        )


class TestIndexWeekly:
    def test_query(self, mock_pro_api):
        mock_pro_api.index_weekly.return_value = make_df({
            "ts_code": ["000300.SH"],
            "trade_date": ["20260227"],
            "close": [4500.0],
        })
        df = client.index_weekly(ts_code="000300.SH")
        assert df.iloc[0]["close"] == 4500.0


class TestIndexMonthly:
    def test_query(self, mock_pro_api):
        mock_pro_api.index_monthly.return_value = make_df({
            "ts_code": ["000300.SH"],
            "trade_date": ["20260228"],
            "close": [4520.0],
        })
        df = client.index_monthly(ts_code="000300.SH")
        assert df.iloc[0]["close"] == 4520.0


class TestSwDaily:
    def test_query(self, mock_pro_api):
        mock_pro_api.sw_daily.return_value = make_df({
            "ts_code": ["801010.SI"],
            "trade_date": ["20260226"],
            "close": [3500.0],
            "pe": [25.0],
            "pb": [3.2],
        })
        df = client.sw_daily(ts_code="801010.SI", trade_date="2026-02-26")
        assert df.iloc[0]["pe"] == 25.0
        mock_pro_api.sw_daily.assert_called_once_with(
            ts_code="801010.SI", trade_date="20260226",
        )


# ==================== A股行情扩展 ====================


class TestWeekly:
    def test_query(self, mock_pro_api):
        mock_pro_api.weekly.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "trade_date": ["20260227"],
            "close": [15.5],
            "vol": [500000.0],
        })
        df = client.weekly(ts_code="000001.SZ", trade_date="2026-02-27")
        assert df.iloc[0]["close"] == 15.5
        mock_pro_api.weekly.assert_called_once_with(
            ts_code="000001.SZ", trade_date="20260227",
        )


class TestMonthly:
    def test_query(self, mock_pro_api):
        mock_pro_api.monthly.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "trade_date": ["20260228"],
            "close": [15.8],
        })
        df = client.monthly(ts_code="000001.SZ")
        assert df.iloc[0]["close"] == 15.8


class TestStkLimit:
    def test_query(self, mock_pro_api):
        mock_pro_api.stk_limit.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "trade_date": ["20260226"],
            "up_limit": [17.05],
            "down_limit": [13.95],
        })
        df = client.stk_limit(ts_code="000001.SZ", trade_date="2026-02-26")
        assert df.iloc[0]["up_limit"] == 17.05
        mock_pro_api.stk_limit.assert_called_once_with(
            ts_code="000001.SZ", trade_date="20260226",
        )


# ==================== 财务补充 ====================


class TestFinaAudit:
    def test_query(self, mock_pro_api):
        mock_pro_api.fina_audit.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "ann_date": ["20260401"],
            "audit_result": ["标准无保留意见"],
        })
        df = client.fina_audit(ts_code="000001.SZ")
        assert df.iloc[0]["audit_result"] == "标准无保留意见"


class TestFinaMainbz:
    def test_query(self, mock_pro_api):
        mock_pro_api.fina_mainbz.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "bz_item": ["利息净收入"],
            "bz_sales": [150000000000.0],
        })
        df = client.fina_mainbz(ts_code="000001.SZ", period="2025-12-31")
        assert df.iloc[0]["bz_item"] == "利息净收入"
        mock_pro_api.fina_mainbz.assert_called_once_with(
            ts_code="000001.SZ", period="20251231",
        )


class TestDisclosureDate:
    def test_query(self, mock_pro_api):
        mock_pro_api.disclosure_date.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "end_date": ["20251231"],
            "pre_date": ["20260328"],
            "actual_date": ["20260328"],
        })
        df = client.disclosure_date(ts_code="000001.SZ", end_date="2025-12-31")
        assert df.iloc[0]["pre_date"] == "20260328"
        mock_pro_api.disclosure_date.assert_called_once_with(
            ts_code="000001.SZ", end_date="20251231",
        )
