"""
formatter.py 单元测试
"""

import pandas as pd

from tushare_mcp.formatter import format_response


class TestFormatResponse:
    def test_json_format(self):
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        result = format_response(df, "test_api", output_format="json", limit=100)

        assert result["api"] == "test_api"
        assert result["total_rows"] == 2
        assert result["returned_rows"] == 2
        assert result["truncated"] is False
        assert len(result["data"]) == 2
        assert result["data"][0]["a"] == 1

    def test_markdown_format(self):
        df = pd.DataFrame({"col1": [1], "col2": ["val"]})
        result = format_response(df, "test_api", output_format="markdown")

        assert isinstance(result["data"], str)
        assert "col1" in result["data"]

    def test_truncation(self):
        df = pd.DataFrame({"x": range(200)})
        result = format_response(df, "test_api", limit=50)

        assert result["total_rows"] == 200
        assert result["returned_rows"] == 50
        assert result["truncated"] is True

    def test_empty_df(self):
        df = pd.DataFrame()
        result = format_response(df, "test_api")

        assert result["total_rows"] == 0
        assert result["returned_rows"] == 0
        assert result["truncated"] is False
