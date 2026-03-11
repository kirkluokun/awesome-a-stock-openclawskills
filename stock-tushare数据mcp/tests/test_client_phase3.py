"""
Phase 3 新增接口的单元测试

覆盖：margin, margin_detail, top_list, top_inst, stk_holdernumber,
      top10_holders, top10_floatholders, dividend, repurchase, share_float,
      pledge_stat, pledge_detail, stk_surv, moneyflow, moneyflow_hsgt,
      hsgt_top10, ggt_top10, kpl_concept, kpl_concept_cons, shibor
"""

import pandas as pd
import pytest

from tushare_mcp import client
from tests.conftest import make_df


# ==================== 融资融券 ====================


class TestMargin:
    def test_query_by_date(self, mock_pro_api):
        mock_pro_api.margin.return_value = make_df({
            "trade_date": ["20260226"],
            "exchange_id": ["SSE"],
            "rzye": [800000000000.0],
            "rqye": [50000000000.0],
        })
        df = client.margin(trade_date="2026-02-26")
        assert df.iloc[0]["exchange_id"] == "SSE"
        mock_pro_api.margin.assert_called_once_with(trade_date="20260226")


class TestMarginDetail:
    def test_query_by_code(self, mock_pro_api):
        mock_pro_api.margin_detail.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "trade_date": ["20260226"],
            "rzye": [5000000000.0],
            "rzmre": [100000000.0],
        })
        df = client.margin_detail(ts_code="000001.SZ", trade_date="2026-02-26")
        assert df.iloc[0]["ts_code"] == "000001.SZ"
        mock_pro_api.margin_detail.assert_called_once_with(
            ts_code="000001.SZ", trade_date="20260226"
        )


# ==================== 龙虎榜 ====================


class TestTopList:
    def test_query(self, mock_pro_api):
        mock_pro_api.top_list.return_value = make_df({
            "trade_date": ["20260226"],
            "ts_code": ["000858.SZ"],
            "name": ["五粮液"],
            "net_amount": [50000000.0],
            "reason": ["日涨幅偏离值达7%"],
        })
        df = client.top_list(trade_date="2026-02-26")
        assert df.iloc[0]["name"] == "五粮液"
        mock_pro_api.top_list.assert_called_once_with(trade_date="20260226")


class TestTopInst:
    def test_query(self, mock_pro_api):
        mock_pro_api.top_inst.return_value = make_df({
            "trade_date": ["20260226"],
            "ts_code": ["000858.SZ"],
            "exalter": ["机构专用"],
            "buy": [30000000.0],
            "sell": [0.0],
        })
        df = client.top_inst(trade_date="2026-02-26", ts_code="000858.SZ")
        assert df.iloc[0]["exalter"] == "机构专用"


# ==================== 股东数据 ====================


class TestStkHolderNumber:
    def test_query(self, mock_pro_api):
        mock_pro_api.stk_holdernumber.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "ann_date": ["20260115"],
            "holder_num": [580000],
        })
        df = client.stk_holdernumber(ts_code="000001.SZ")
        assert df.iloc[0]["holder_num"] == 580000


class TestTop10Holders:
    def test_query(self, mock_pro_api):
        mock_pro_api.top10_holders.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "holder_name": ["香港中央结算(代理人)有限公司"],
            "hold_amount": [10000000000.0],
            "hold_ratio": [15.5],
        })
        df = client.top10_holders(ts_code="000001.SZ", period="2025-12-31")
        assert df.iloc[0]["hold_ratio"] == 15.5
        mock_pro_api.top10_holders.assert_called_once_with(
            ts_code="000001.SZ", period="20251231"
        )


class TestTop10FloatHolders:
    def test_query(self, mock_pro_api):
        mock_pro_api.top10_floatholders.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "holder_name": ["深圳市投资控股有限公司"],
            "hold_amount": [5000000000.0],
        })
        df = client.top10_floatholders(ts_code="000001.SZ")
        assert df.iloc[0]["hold_amount"] == 5000000000.0


# ==================== 公司行为 ====================


class TestDividend:
    def test_query(self, mock_pro_api):
        mock_pro_api.dividend.return_value = make_df({
            "ts_code": ["000858.SZ"],
            "end_date": ["20251231"],
            "cash_div": [2.5],
            "stk_div": [0.0],
            "ex_date": ["20260615"],
        })
        df = client.dividend(ts_code="000858.SZ")
        assert df.iloc[0]["cash_div"] == 2.5


class TestRepurchase:
    def test_query(self, mock_pro_api):
        mock_pro_api.repurchase.return_value = make_df({
            "ts_code": ["600519.SH"],
            "ann_date": ["20260115"],
            "amount": [5000000000.0],
        })
        df = client.repurchase(start_date="2026-01-01", end_date="2026-02-28")
        assert df.iloc[0]["amount"] == 5000000000.0
        mock_pro_api.repurchase.assert_called_once_with(
            start_date="20260101", end_date="20260228"
        )


class TestShareFloat:
    def test_query(self, mock_pro_api):
        mock_pro_api.share_float.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "float_date": ["20260301"],
            "float_share": [50000000.0],
            "float_ratio": [2.5],
        })
        df = client.share_float(ts_code="000001.SZ")
        assert df.iloc[0]["float_ratio"] == 2.5


class TestPledgeStat:
    def test_query(self, mock_pro_api):
        mock_pro_api.pledge_stat.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "pledge_count": [15],
            "pledge_ratio": [8.5],
        })
        df = client.pledge_stat(ts_code="000001.SZ")
        assert df.iloc[0]["pledge_count"] == 15


class TestPledgeDetail:
    def test_query(self, mock_pro_api):
        mock_pro_api.pledge_detail.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "holder_name": ["某某股东"],
            "pledge_amount": [100000000.0],
        })
        df = client.pledge_detail(ts_code="000001.SZ")
        assert df.iloc[0]["holder_name"] == "某某股东"


class TestStkSurv:
    def test_query(self, mock_pro_api):
        mock_pro_api.stk_surv.return_value = make_df({
            "ts_code": ["000858.SZ"],
            "surv_date": ["20260220"],
            "rece_org": ["中信证券"],
        })
        df = client.stk_surv(ts_code="000858.SZ", start_date="2026-02-01")
        assert df.iloc[0]["rece_org"] == "中信证券"
        mock_pro_api.stk_surv.assert_called_once_with(
            ts_code="000858.SZ", start_date="20260201"
        )


# ==================== 资金流向 ====================


class TestMoneyflow:
    def test_query(self, mock_pro_api):
        mock_pro_api.moneyflow.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "trade_date": ["20260226"],
            "buy_sm_amount": [500000.0],
            "net_mf_amount": [-200000.0],
        })
        df = client.moneyflow(ts_code="000001.SZ", trade_date="2026-02-26")
        assert df.iloc[0]["net_mf_amount"] == -200000.0
        mock_pro_api.moneyflow.assert_called_once_with(
            ts_code="000001.SZ", trade_date="20260226"
        )


class TestMoneyflowHsgt:
    def test_query(self, mock_pro_api):
        mock_pro_api.moneyflow_hsgt.return_value = make_df({
            "trade_date": ["20260226"],
            "hgt": [5000000000.0],
            "sgt": [3000000000.0],
        })
        df = client.moneyflow_hsgt(trade_date="2026-02-26")
        assert df.iloc[0]["hgt"] == 5000000000.0


class TestHsgtTop10:
    def test_query(self, mock_pro_api):
        mock_pro_api.hsgt_top10.return_value = make_df({
            "trade_date": ["20260226"],
            "ts_code": ["600519.SH"],
            "name": ["贵州茅台"],
            "amount": [1000000000.0],
        })
        df = client.hsgt_top10(trade_date="2026-02-26", market_type="1")
        assert df.iloc[0]["name"] == "贵州茅台"


class TestGgtTop10:
    def test_query(self, mock_pro_api):
        mock_pro_api.ggt_top10.return_value = make_df({
            "trade_date": ["20260226"],
            "ts_code": ["00700.HK"],
            "name": ["腾讯控股"],
            "amount": [2000000000.0],
        })
        df = client.ggt_top10(trade_date="2026-02-26")
        assert df.iloc[0]["name"] == "腾讯控股"


# ==================== 概念板块 ====================


class TestKplConcept:
    def test_query(self, mock_pro_api):
        mock_pro_api.kpl_concept.return_value = make_df({
            "trade_date": ["20260226"],
            "ts_code": ["000001.KP"],
            "name": ["人工智能"],
            "z_t_num": [5],
        })
        df = client.kpl_concept(trade_date="2026-02-26")
        assert df.iloc[0]["name"] == "人工智能"
        mock_pro_api.kpl_concept.assert_called_once_with(trade_date="20260226")


class TestKplConceptCons:
    def test_query(self, mock_pro_api):
        mock_pro_api.kpl_concept_cons.return_value = make_df({
            "ts_code": ["000001.KP"],
            "con_code": ["000001.SZ"],
            "con_name": ["平安银行"],
        })
        df = client.kpl_concept_cons(ts_code="000001.KP")
        assert df.iloc[0]["con_name"] == "平安银行"


# ==================== Shibor ====================


class TestShibor:
    def test_query(self, mock_pro_api):
        mock_pro_api.shibor.return_value = make_df({
            "date": ["20260226"],
            "on": [1.5],
            "1w": [1.8],
            "1m": [2.0],
            "3m": [2.2],
            "1y": [2.5],
        })
        df = client.shibor(start_date="2026-02-01", end_date="2026-02-28")
        assert df.iloc[0]["1y"] == 2.5
        mock_pro_api.shibor.assert_called_once_with(
            start_date="20260201", end_date="20260228"
        )
