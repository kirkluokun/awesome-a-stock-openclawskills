"""
Phase 2 新增接口的单元测试

覆盖：yc_cb, shibor_lpr, forecast, express, report_rc, index_classify, news
"""

import pandas as pd
import pytest

from tushare_mcp import client
from tushare_mcp.errors import ApiError
from tests.conftest import make_df


class TestYcCb:
    def test_query_10y(self, mock_pro_api):
        mock_pro_api.yc_cb.return_value = make_df({
            "ts_code": ["1001.CB"],
            "trade_date": ["20260227"],
            "curve_term": [10.0],
            "yield": [2.35],
        })
        df = client.yc_cb(ts_code="1001.CB", curve_term=10.0, trade_date="2026-02-27")
        assert df.iloc[0]["yield"] == 2.35
        mock_pro_api.yc_cb.assert_called_once_with(
            ts_code="1001.CB", curve_term=10.0, trade_date="20260227"
        )


class TestShiborLpr:
    def test_query(self, mock_pro_api):
        mock_pro_api.shibor_lpr.return_value = make_df({
            "date": ["20260220"],
            "lpr_1y": [3.1],
            "lpr_5y": [3.6],
        })
        df = client.shibor_lpr(start_date="2026-02-01", end_date="2026-02-28")
        assert df.iloc[0]["lpr_5y"] == 3.6


class TestForecast:
    def test_query_by_code(self, mock_pro_api):
        mock_pro_api.forecast.return_value = make_df({
            "ts_code": ["000858.SZ"],
            "ann_date": ["20260115"],
            "type": ["预增"],
            "p_change_min": [50.0],
            "p_change_max": [80.0],
        })
        df = client.forecast(ts_code="000858.SZ")
        assert df.iloc[0]["type"] == "预增"

    def test_query_by_ann_date(self, mock_pro_api):
        mock_pro_api.forecast.return_value = make_df({
            "ts_code": ["000858.SZ", "600519.SH"],
            "ann_date": ["20260115", "20260115"],
        })
        df = client.forecast(ann_date="20260115")
        assert len(df) == 2


class TestExpress:
    def test_query(self, mock_pro_api):
        mock_pro_api.express.return_value = make_df({
            "ts_code": ["000001.SZ"],
            "revenue": [120000000000.0],
            "net_profit": [45000000000.0],
        })
        df = client.express(ts_code="000001.SZ", period="20251231")
        assert df.iloc[0]["revenue"] == 120000000000.0


class TestReportRc:
    def test_query(self, mock_pro_api):
        mock_pro_api.report_rc.return_value = make_df({
            "ts_code": ["000858.SZ"],
            "org_name": ["中信证券"],
            "eps": [5.2],
            "rating": ["买入"],
            "max_price": [300.0],
        })
        df = client.report_rc(ts_code="000858.SZ", start_date="2026-01-01")
        assert df.iloc[0]["rating"] == "买入"
        mock_pro_api.report_rc.assert_called_once_with(
            ts_code="000858.SZ", start_date="20260101"
        )


class TestIndexClassify:
    def test_query_l1(self, mock_pro_api):
        mock_pro_api.index_classify.return_value = make_df({
            "index_code": ["801010.SI"],
            "industry_name": ["农林牧渔"],
            "level": ["L1"],
        })
        df = client.index_classify(level="L1", src="SW2021")
        assert df.iloc[0]["industry_name"] == "农林牧渔"
        mock_pro_api.index_classify.assert_called_once_with(
            level="L1", src="SW2021"
        )


class TestNews:
    def test_query(self, mock_pro_api):
        mock_pro_api.news.return_value = make_df({
            "datetime": ["2026-02-27 08:30:00"],
            "title": ["央行宣布降准"],
            "content": ["中国人民银行决定..."],
        })
        df = client.news(
            start_date="2026-02-27 00:00:00",
            end_date="2026-02-27 23:59:59",
            src="sina",
        )
        assert "降准" in df.iloc[0]["title"]
        # 新闻接口日期不做格式转换
        mock_pro_api.news.assert_called_once_with(
            start_date="2026-02-27 00:00:00",
            end_date="2026-02-27 23:59:59",
            src="sina",
        )
