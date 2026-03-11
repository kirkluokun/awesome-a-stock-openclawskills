"""
Phase 5d-2 新增接口的单元测试

覆盖：利率（hibor, libor, us_tycr, us_trycr, us_tltr, us_trltr, us_tbr）,
      宏观（cn_m, sf_month）, 黄金（sge_basic, sge_daily）,
      民间借贷利率（gz_index, wz_index）
"""

import pandas as pd
import pytest

from tushare_mcp import client
from tests.conftest import make_df


# ==================== 国际利率 ====================


class TestHibor:
    def test_query(self, mock_pro_api):
        mock_pro_api.hibor.return_value = make_df({
            "date": ["20260226"],
            "on": [4.5],
            "1w": [4.6],
            "1m": [4.7],
        })
        df = client.hibor(date="2026-02-26")
        assert df.iloc[0]["on"] == 4.5
        mock_pro_api.hibor.assert_called_once_with(
            date="20260226",
        )


class TestLibor:
    def test_query(self, mock_pro_api):
        mock_pro_api.libor.return_value = make_df({
            "date": ["20260226"],
            "curr_type": ["USD"],
            "on": [5.3],
            "1m": [5.4],
        })
        df = client.libor(date="2026-02-26", curr_type="USD")
        assert df.iloc[0]["on"] == 5.3
        mock_pro_api.libor.assert_called_once_with(
            date="20260226", curr_type="USD",
        )


class TestUsTycr:
    def test_query(self, mock_pro_api):
        mock_pro_api.us_tycr.return_value = make_df({
            "date": ["20260226"],
            "m1": [5.2],
            "y1": [4.8],
            "y10": [4.3],
        })
        df = client.us_tycr(date="2026-02-26")
        assert df.iloc[0]["y10"] == 4.3
        mock_pro_api.us_tycr.assert_called_once_with(
            date="20260226",
        )


class TestUsTrycr:
    def test_query(self, mock_pro_api):
        mock_pro_api.us_trycr.return_value = make_df({
            "date": ["20260226"],
            "y5": [1.8],
            "y10": [2.0],
        })
        df = client.us_trycr(date="2026-02-26")
        assert df.iloc[0]["y10"] == 2.0
        mock_pro_api.us_trycr.assert_called_once_with(
            date="20260226",
        )


class TestUsTltr:
    def test_query(self, mock_pro_api):
        mock_pro_api.us_tltr.return_value = make_df({
            "date": ["20260226"],
            "ltrate": [4.5],
        })
        df = client.us_tltr(date="2026-02-26")
        assert df.iloc[0]["ltrate"] == 4.5
        mock_pro_api.us_tltr.assert_called_once_with(
            date="20260226",
        )


class TestUsTrltr:
    def test_query(self, mock_pro_api):
        mock_pro_api.us_trltr.return_value = make_df({
            "date": ["20260226"],
            "ltavg": [4.2],
        })
        df = client.us_trltr(date="2026-02-26")
        assert df.iloc[0]["ltavg"] == 4.2
        mock_pro_api.us_trltr.assert_called_once_with(
            date="20260226",
        )


class TestUsTbr:
    def test_query(self, mock_pro_api):
        mock_pro_api.us_tbr.return_value = make_df({
            "date": ["20260226"],
            "w4_bd": [5.1],
            "w52_ce": [4.9],
        })
        df = client.us_tbr(date="2026-02-26")
        assert df.iloc[0]["w4_bd"] == 5.1
        mock_pro_api.us_tbr.assert_called_once_with(
            date="20260226",
        )


# ==================== 宏观经济 ====================


class TestCnM:
    def test_query(self, mock_pro_api):
        mock_pro_api.cn_m.return_value = make_df({
            "month": ["202601"],
            "m0": [12000000.0],
            "m1": [68000000.0],
            "m2": [300000000.0],
        })
        df = client.cn_m(m="202601")
        assert df.iloc[0]["m2"] == 300000000.0
        mock_pro_api.cn_m.assert_called_once_with(
            m="202601",
        )


class TestSfMonth:
    def test_query(self, mock_pro_api):
        mock_pro_api.sf_month.return_value = make_df({
            "month": ["202601"],
            "rmbloans": [2500000.0],
            "aggregate_financing": [5000000.0],
        })
        df = client.sf_month(m="202601")
        assert df.iloc[0]["aggregate_financing"] == 5000000.0
        mock_pro_api.sf_month.assert_called_once_with(
            m="202601",
        )


# ==================== 黄金 ====================


class TestSgeBasic:
    def test_query(self, mock_pro_api):
        mock_pro_api.sge_basic.return_value = make_df({
            "ts_code": ["Au99.99"],
            "name": ["黄金9999"],
            "unit": ["克/手"],
        })
        df = client.sge_basic(ts_code="Au99.99")
        assert df.iloc[0]["name"] == "黄金9999"
        mock_pro_api.sge_basic.assert_called_once_with(
            ts_code="Au99.99",
        )


class TestSgeDaily:
    def test_query(self, mock_pro_api):
        mock_pro_api.sge_daily.return_value = make_df({
            "ts_code": ["Au99.99"],
            "trade_date": ["20260226"],
            "close": [680.5],
            "vol": [15000.0],
        })
        df = client.sge_daily(ts_code="Au99.99", trade_date="2026-02-26")
        assert df.iloc[0]["close"] == 680.5
        mock_pro_api.sge_daily.assert_called_once_with(
            ts_code="Au99.99", trade_date="20260226",
        )


# ==================== 民间借贷利率 ====================


class TestGzIndex:
    def test_query(self, mock_pro_api):
        mock_pro_api.gz_index.return_value = make_df({
            "date": ["20260226"],
            "rate": [15.5],
        })
        df = client.gz_index(date="2026-02-26")
        assert df.iloc[0]["rate"] == 15.5
        mock_pro_api.gz_index.assert_called_once_with(
            date="20260226",
        )


class TestWzIndex:
    def test_query(self, mock_pro_api):
        mock_pro_api.wz_index.return_value = make_df({
            "date": ["20260226"],
            "rate": [16.2],
        })
        df = client.wz_index(date="2026-02-26")
        assert df.iloc[0]["rate"] == 16.2
        mock_pro_api.wz_index.assert_called_once_with(
            date="20260226",
        )
