"""
DataStore 单元测试

测试 SQLite 存储引擎的核心功能：
- 保存 DataFrame 到数据库
- 查询索引
- 动态建表和加列
- 空 DataFrame 不保存
"""

import json
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from tushare_mcp.storage import DataStore


@pytest.fixture
def store(tmp_path):
    """创建临时数据库的 DataStore 实例"""
    db_path = tmp_path / "test.db"
    s = DataStore(str(db_path))
    yield s
    s.close()


@pytest.fixture
def sample_daily_df():
    """模拟 tushare daily 返回的 DataFrame"""
    return pd.DataFrame({
        "ts_code": ["000001.SZ", "000001.SZ", "000001.SZ"],
        "trade_date": ["20250101", "20250102", "20250103"],
        "open": [10.5, 10.6, 10.7],
        "high": [10.8, 10.9, 11.0],
        "low": [10.3, 10.4, 10.5],
        "close": [10.6, 10.7, 10.8],
        "vol": [100000.0, 120000.0, 110000.0],
        "amount": [1060000.0, 1284000.0, 1188000.0],
    })


@pytest.fixture
def sample_income_df():
    """模拟 tushare income 返回的 DataFrame"""
    return pd.DataFrame({
        "ts_code": ["600000.SH"],
        "ann_date": ["20250401"],
        "f_ann_date": ["20250401"],
        "end_date": ["20241231"],
        "report_type": ["1"],
        "total_revenue": [500000000.0],
        "net_income": [120000000.0],
    })


class TestDataStoreSave:
    """测试保存功能"""

    def test_save_creates_index_record(self, store, sample_daily_df):
        """保存后索引表应有一条记录"""
        params = {"ts_code": "000001.SZ", "start_date": "20250101", "end_date": "20250103"}
        query_id = store.save("daily", params, sample_daily_df)

        assert query_id > 0

        # 检查索引表
        idx = store.query_index(api_name="daily")
        assert len(idx) == 1
        assert idx.iloc[0]["api_name"] == "daily"
        assert idx.iloc[0]["ts_code"] == "000001.SZ"
        assert idx.iloc[0]["row_count"] == 3
        assert idx.iloc[0]["table_name"] == "data_daily"

    def test_save_creates_data_table(self, store, sample_daily_df):
        """保存后应创建 data_daily 表并包含数据"""
        params = {"ts_code": "000001.SZ"}
        store.save("daily", params, sample_daily_df)

        # 直接查 SQLite 验证
        cursor = store._conn.execute("SELECT COUNT(*) FROM data_daily")
        count = cursor.fetchone()[0]
        assert count == 3

        # 检查 _query_id 列存在
        cursor = store._conn.execute("SELECT _query_id FROM data_daily LIMIT 1")
        row = cursor.fetchone()
        assert row[0] > 0

    def test_save_preserves_data_values(self, store, sample_daily_df):
        """保存的数据值应正确"""
        params = {"ts_code": "000001.SZ"}
        store.save("daily", params, sample_daily_df)

        cursor = store._conn.execute(
            "SELECT ts_code, close FROM data_daily ORDER BY trade_date"
        )
        rows = cursor.fetchall()
        assert rows[0] == ("000001.SZ", 10.6)
        assert rows[2] == ("000001.SZ", 10.8)

    def test_save_empty_df_returns_negative(self, store):
        """空 DataFrame 不保存，返回 -1"""
        empty_df = pd.DataFrame()
        result = store.save("daily", {}, empty_df)

        assert result == -1

        # 索引表应为空
        idx = store.query_index()
        assert len(idx) == 0

    def test_save_multiple_queries(self, store, sample_daily_df):
        """多次保存应在索引表生成多条记录"""
        store.save("daily", {"ts_code": "000001.SZ"}, sample_daily_df)
        store.save("daily", {"ts_code": "000002.SZ"}, sample_daily_df)

        idx = store.query_index(api_name="daily")
        assert len(idx) == 2

        # 数据表应有 6 行
        cursor = store._conn.execute("SELECT COUNT(*) FROM data_daily")
        assert cursor.fetchone()[0] == 6

    def test_save_stores_query_params_as_json(self, store, sample_daily_df):
        """查询参数应以 JSON 格式保存"""
        params = {"ts_code": "000001.SZ", "start_date": "20250101"}
        store.save("daily", params, sample_daily_df)

        idx = store.query_index()
        stored_params = json.loads(idx.iloc[0]["query_params"])
        assert stored_params["ts_code"] == "000001.SZ"
        assert stored_params["start_date"] == "20250101"

    def test_save_stores_columns_as_json(self, store, sample_daily_df):
        """列名应以 JSON 数组保存"""
        store.save("daily", {}, sample_daily_df)

        idx = store.query_index()
        columns = json.loads(idx.iloc[0]["columns"])
        assert "ts_code" in columns
        assert "close" in columns
        assert "vol" in columns


class TestDynamicSchema:
    """测试动态建表和加列"""

    def test_different_apis_create_different_tables(self, store, sample_daily_df, sample_income_df):
        """不同 API 应创建不同的数据表"""
        store.save("daily", {}, sample_daily_df)
        store.save("income", {}, sample_income_df)

        # 检查两张表都存在
        cursor = store._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'data_%'"
        )
        tables = {row[0] for row in cursor.fetchall()}
        assert "data_daily" in tables
        assert "data_income" in tables

    def test_new_column_auto_added(self, store):
        """新列应自动 ALTER TABLE ADD"""
        # 第一次保存：2 列
        df1 = pd.DataFrame({"ts_code": ["000001.SZ"], "close": [10.5]})
        store.save("test_api", {}, df1)

        # 第二次保存：多了一列 vol
        df2 = pd.DataFrame({"ts_code": ["000001.SZ"], "close": [10.6], "vol": [50000.0]})
        store.save("test_api", {}, df2)

        # vol 列应存在
        cols = store._get_table_columns("data_test_api")
        assert "vol" in cols

        # 数据应完整
        cursor = store._conn.execute("SELECT COUNT(*) FROM data_test_api")
        assert cursor.fetchone()[0] == 2

    def test_dtype_mapping(self, store):
        """pandas 类型应正确映射到 SQLite 类型"""
        df = pd.DataFrame({
            "name": ["test"],           # object → TEXT
            "price": [10.5],            # float64 → REAL
            "count": [100],             # int64 → INTEGER
        })
        store.save("dtype_test", {}, df)

        # 检查列类型
        cursor = store._conn.execute('PRAGMA table_info("data_dtype_test")')
        col_types = {row[1]: row[2] for row in cursor.fetchall()}
        assert col_types["name"] == "TEXT"
        assert col_types["price"] == "REAL"
        assert col_types["count"] == "INTEGER"


class TestQueryIndex:
    """测试索引查询"""

    def test_query_by_api_name(self, store, sample_daily_df, sample_income_df):
        """按 api_name 筛选"""
        store.save("daily", {"ts_code": "000001.SZ"}, sample_daily_df)
        store.save("income", {"ts_code": "600000.SH"}, sample_income_df)

        result = store.query_index(api_name="daily")
        assert len(result) == 1
        assert result.iloc[0]["api_name"] == "daily"

    def test_query_by_ts_code(self, store, sample_daily_df):
        """按 ts_code 筛选"""
        store.save("daily", {"ts_code": "000001.SZ"}, sample_daily_df)
        store.save("daily", {"ts_code": "000002.SZ"}, sample_daily_df)

        result = store.query_index(ts_code="000001.SZ")
        assert len(result) == 1

    def test_query_limit(self, store, sample_daily_df):
        """limit 参数限制返回行数"""
        for i in range(5):
            store.save("daily", {"ts_code": f"00000{i}.SZ"}, sample_daily_df)

        result = store.query_index(limit=3)
        assert len(result) == 3

    def test_query_empty_result(self, store):
        """无匹配记录返回空 DataFrame"""
        result = store.query_index(api_name="nonexistent")
        assert len(result) == 0

    def test_query_order_by_saved_at_desc(self, store, sample_daily_df):
        """结果应按 saved_at 倒序"""
        store.save("daily", {"ts_code": "000001.SZ"}, sample_daily_df)
        store.save("daily", {"ts_code": "000002.SZ"}, sample_daily_df)

        result = store.query_index()
        # 后保存的排前面
        assert result.iloc[0]["ts_code"] == "000002.SZ"
        assert result.iloc[1]["ts_code"] == "000001.SZ"


class TestNaNHandling:
    """测试 NaN/None 处理"""

    def test_nan_saved_as_null(self, store):
        """pandas NaN 应存为 SQLite NULL"""
        df = pd.DataFrame({
            "ts_code": ["000001.SZ", "000002.SZ"],
            "value": [10.5, float("nan")],
        })
        store.save("nan_test", {}, df)

        cursor = store._conn.execute(
            "SELECT value FROM data_nan_test WHERE ts_code = '000002.SZ'"
        )
        assert cursor.fetchone()[0] is None


class TestReadData:
    """测试从本地 DB 读取数据"""

    def test_read_by_query_id(self, store, sample_daily_df):
        """按 query_id 精确读取某次查询的数据"""
        query_id = store.save("daily", {"ts_code": "000001.SZ"}, sample_daily_df)

        result = store.read_data(query_id=query_id)
        assert len(result) == 3
        assert "ts_code" in result.columns
        assert "close" in result.columns

    def test_read_by_query_id_not_found(self, store):
        """query_id 不存在返回空 DataFrame"""
        result = store.read_data(query_id=99999)
        assert len(result) == 0

    def test_read_by_api_name(self, store, sample_daily_df):
        """按 api_name 读取数据"""
        store.save("daily", {"ts_code": "000001.SZ"}, sample_daily_df)
        store.save("daily", {"ts_code": "000002.SZ"}, sample_daily_df)

        result = store.read_data(api_name="daily")
        assert len(result) == 6  # 两次各 3 行

    def test_read_by_api_name_and_ts_code(self, store, sample_daily_df):
        """按 api_name + ts_code 读取特定标的"""
        store.save("daily", {"ts_code": "000001.SZ"}, sample_daily_df)

        # 造一个不同 ts_code 的数据
        df2 = sample_daily_df.copy()
        df2["ts_code"] = "000002.SZ"
        store.save("daily", {"ts_code": "000002.SZ"}, df2)

        result = store.read_data(api_name="daily", ts_code="000001.SZ")
        assert len(result) == 3
        assert all(result["ts_code"] == "000001.SZ")

    def test_read_nonexistent_api(self, store):
        """读取不存在的 api_name 返回空"""
        result = store.read_data(api_name="nonexistent")
        assert len(result) == 0

    def test_read_no_params_returns_empty(self, store):
        """不传任何参数返回空"""
        result = store.read_data()
        assert len(result) == 0

    def test_read_respects_limit(self, store, sample_daily_df):
        """limit 参数限制返回行数"""
        store.save("daily", {"ts_code": "000001.SZ"}, sample_daily_df)

        result = store.read_data(api_name="daily", limit=2)
        assert len(result) == 2

    def test_read_data_values_match_saved(self, store, sample_daily_df):
        """读取的数据值应与保存时一致"""
        query_id = store.save("daily", {"ts_code": "000001.SZ"}, sample_daily_df)

        result = store.read_data(query_id=query_id)
        # 按 trade_date 排序后对比
        result = result.sort_values("trade_date").reset_index(drop=True)
        assert result.iloc[0]["close"] == 10.6
        assert result.iloc[2]["close"] == 10.8
