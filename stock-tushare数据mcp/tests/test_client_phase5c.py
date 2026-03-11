"""
Phase 5c 新增接口的单元测试

覆盖：公告研究（anns, stk_managers, broker_recommend）,
      股票信息扩展（namechange, suspend_d, new_share）,
      同花顺板块（ths_index, ths_daily, ths_member）,
      大宗交易与股东（block_trade, stk_holdertrade, ccass_hold）
"""

import pandas as pd
import pytest

from tushare_mcp import client
from tests.conftest import make_df


# ==================== 公告与研究 ====================


class TestAnns:
    def test_query(self, mock_pro_api):
        mock_pro_api.anns_d.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "ann_date": ["20260226"],
            "title": ["2025年年度报告"],
        })
        df = client.anns(ts_code="000001.SZ", ann_date="2026-02-26")
        assert df.iloc[0]["title"] == "2025年年度报告"
        mock_pro_api.anns_d.assert_called_once_with(
            ts_code="000001.SZ", ann_date="20260226",
        )


class TestStkManagers:
    def test_query(self, mock_pro_api):
        mock_pro_api.stk_managers.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "ann_date": ["20260301"],
            "name": ["张三"],
            "title": ["董事长"],
        })
        df = client.stk_managers(ts_code="000001.SZ")
        assert df.iloc[0]["name"] == "张三"


class TestBrokerRecommend:
    def test_query(self, mock_pro_api):
        mock_pro_api.broker_recommend.return_value = make_df({
            "month": ["202602"],
            "broker": ["中信证券"],
            "ts_code": ["600519.SH"],
            "name": ["贵州茅台"],
        })
        df = client.broker_recommend(month="202602")
        assert df.iloc[0]["broker"] == "中信证券"
        mock_pro_api.broker_recommend.assert_called_once_with(
            month="202602",
        )


# ==================== 股票信息扩展 ====================


class TestNamechange:
    def test_query(self, mock_pro_api):
        mock_pro_api.namechange.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "name": ["平安银行"],
            "start_date": ["20120621"],
            "ann_date": ["20120614"],
        })
        df = client.namechange(ts_code="000001.SZ")
        assert df.iloc[0]["name"] == "平安银行"


class TestSuspendD:
    def test_query(self, mock_pro_api):
        mock_pro_api.suspend_d.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "trade_date": ["20260226"],
            "suspend_type": ["S"],
            "suspend_timing": ["全天"],
        })
        df = client.suspend_d(ts_code="000001.SZ", trade_date="2026-02-26")
        assert df.iloc[0]["suspend_type"] == "S"
        mock_pro_api.suspend_d.assert_called_once_with(
            ts_code="000001.SZ", trade_date="20260226",
        )


class TestNewShare:
    def test_query(self, mock_pro_api):
        mock_pro_api.new_share.return_value = make_df({
            "ts_code": ["301234.SZ"],
            "name": ["新股测试"],
            "ipo_date": ["20260301"],
            "issue_date": ["20260225"],
            "price": [25.5],
        })
        df = client.new_share(start_date="2026-02-01", end_date="2026-02-28")
        assert df.iloc[0]["price"] == 25.5
        mock_pro_api.new_share.assert_called_once_with(
            start_date="20260201", end_date="20260228",
        )


# ==================== 同花顺板块 ====================


class TestThsIndex:
    def test_query(self, mock_pro_api):
        mock_pro_api.ths_index.return_value = make_df({
            "ts_code": ["885338.TI"],
            "name": ["半导体"],
            "type": ["N"],
            "exchange": ["A"],
        })
        df = client.ths_index(exchange="A", type="N")
        assert df.iloc[0]["name"] == "半导体"
        mock_pro_api.ths_index.assert_called_once_with(
            exchange="A", type="N",
        )


class TestThsDaily:
    def test_query(self, mock_pro_api):
        mock_pro_api.ths_daily.return_value = make_df({
            "ts_code": ["885338.TI"],
            "trade_date": ["20260226"],
            "close": [1580.5],
            "pct_change": [2.35],
        })
        df = client.ths_daily(ts_code="885338.TI", trade_date="2026-02-26")
        assert df.iloc[0]["close"] == 1580.5
        mock_pro_api.ths_daily.assert_called_once_with(
            ts_code="885338.TI", trade_date="20260226",
        )


class TestThsMember:
    def test_query(self, mock_pro_api):
        mock_pro_api.ths_member.return_value = make_df({
            "ts_code": ["885338.TI"],
            "con_code": ["002049.SZ"],
            "name": ["紫光国微"],
        })
        df = client.ths_member(ts_code="885338.TI")
        assert df.iloc[0]["con_code"] == "002049.SZ"
        mock_pro_api.ths_member.assert_called_once_with(
            ts_code="885338.TI",
        )


# ==================== 大宗交易与股东 ====================


class TestBlockTrade:
    def test_query(self, mock_pro_api):
        mock_pro_api.block_trade.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "trade_date": ["20260226"],
            "price": [15.2],
            "vol": [1000000.0],
            "amount": [15200000.0],
        })
        df = client.block_trade(ts_code="000001.SZ", trade_date="2026-02-26")
        assert df.iloc[0]["amount"] == 15200000.0
        mock_pro_api.block_trade.assert_called_once_with(
            ts_code="000001.SZ", trade_date="20260226",
        )


class TestStkHoldertrade:
    def test_query(self, mock_pro_api):
        mock_pro_api.stk_holdertrade.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "ann_date": ["20260226"],
            "holder_name": ["张三"],
            "trade_type": ["IN"],
            "vol": [500000.0],
        })
        df = client.stk_holdertrade(
            ts_code="000001.SZ", trade_type="IN", holder_type="G",
        )
        assert df.iloc[0]["trade_type"] == "IN"
        mock_pro_api.stk_holdertrade.assert_called_once_with(
            ts_code="000001.SZ", trade_type="IN", holder_type="G",
        )


class TestCcassHold:
    def test_query(self, mock_pro_api):
        mock_pro_api.ccass_hold_detail.return_value = make_df({
            "ts_code": ["605009.SH"],
            "hk_code": ["95009"],
            "trade_date": ["20260226"],
            "shareholding": [10000000.0],
            "ratio": [5.25],
        })
        df = client.ccass_hold(
            ts_code="605009.SH", trade_date="2026-02-26",
        )
        assert df.iloc[0]["ratio"] == 5.25
        mock_pro_api.ccass_hold_detail.assert_called_once_with(
            ts_code="605009.SH", trade_date="20260226",
        )
