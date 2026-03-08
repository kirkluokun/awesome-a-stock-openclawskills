"""
SQLite 数据存储引擎

将 MCP 获取的 tushare 数据持久化到本地 SQLite，
建立索引方便未来数据回溯和历史查询。

两层表结构：
- data_index: 元数据索引表（每次查询一条记录）
- data_{api_name}: 每个 API 一张数据表（动态建表）
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)


# pandas dtype → SQLite 类型映射
_DTYPE_MAP = {
    "int64": "INTEGER",
    "Int64": "INTEGER",
    "float64": "REAL",
    "Float64": "REAL",
    "object": "TEXT",
    "bool": "INTEGER",
    "datetime64[ns]": "TEXT",
}


class DataStore:
    """
    SQLite 数据存储

    每次 API 调用的结果自动保存：
    1. 在 data_index 写一条索引记录
    2. 在 data_{api_name} 表写入数据行
    """

    def __init__(self, db_path: str) -> None:
        """
        初始化存储引擎

        Args:
            db_path: SQLite 数据库文件路径
        """
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        # 启用 WAL 模式，提高并发读写性能
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._ensure_index_table()

    def _ensure_index_table(self) -> None:
        """创建索引表（如果不存在）"""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS data_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_name TEXT NOT NULL,
                query_params TEXT,
                ts_code TEXT,
                trade_date TEXT,
                start_date TEXT,
                end_date TEXT,
                row_count INTEGER,
                columns TEXT,
                table_name TEXT,
                saved_at TEXT DEFAULT (datetime('now','localtime'))
            );
            CREATE INDEX IF NOT EXISTS idx_index_api_name ON data_index(api_name);
            CREATE INDEX IF NOT EXISTS idx_index_ts_code ON data_index(ts_code);
            CREATE INDEX IF NOT EXISTS idx_index_saved_at ON data_index(saved_at);
        """)
        self._conn.commit()

    def save(self, api_name: str, params: dict[str, Any], df: pd.DataFrame) -> int:
        """
        保存 API 返回的 DataFrame

        Args:
            api_name: 接口名称（如 "daily"、"income"）
            params: 原始查询参数（过滤 None 后的）
            df: tushare 返回的 DataFrame

        Returns:
            索引记录 id
        """
        if df.empty:
            return -1

        table_name = f"data_{api_name}"

        # 确保数据表存在且列齐全
        self._ensure_data_table(table_name, df)

        # 写索引记录
        query_id = self._insert_index(api_name, params, df, table_name)

        # 写数据行
        self._insert_data(table_name, query_id, df)

        return query_id

    def query_index(
        self,
        api_name: Optional[str] = None,
        ts_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
    ) -> pd.DataFrame:
        """
        查询索引表

        Args:
            api_name: 按接口名筛选
            ts_code: 按股票代码筛选
            start_date: 保存时间起始（YYYY-MM-DD）
            end_date: 保存时间截止（YYYY-MM-DD）
            limit: 返回行数上限

        Returns:
            索引记录 DataFrame
        """
        conditions = []
        values: list[Any] = []

        if api_name:
            conditions.append("api_name = ?")
            values.append(api_name)
        if ts_code:
            conditions.append("ts_code = ?")
            values.append(ts_code)
        if start_date:
            conditions.append("saved_at >= ?")
            values.append(start_date)
        if end_date:
            conditions.append("saved_at <= ?")
            values.append(end_date + " 23:59:59")

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM data_index WHERE {where} ORDER BY saved_at DESC LIMIT ?"
        values.append(limit)

        return pd.read_sql_query(sql, self._conn, params=values)

    def read_data(
        self,
        query_id: Optional[int] = None,
        api_name: Optional[str] = None,
        ts_code: Optional[str] = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        从本地数据库读取历史数据（不调用 API）

        三种查询模式：
        1. 按 query_id 精确读取某次查询的数据
        2. 按 api_name 读取某类数据（如所有 daily 数据）
        3. 按 api_name + ts_code 读取特定标的数据

        Args:
            query_id: 索引记录 id（精确匹配某次查询）
            api_name: 接口名称（如 daily, income）
            ts_code: 股票/标的代码（需配合 api_name 使用）
            limit: 最大返回行数

        Returns:
            数据 DataFrame
        """
        # 按 query_id 精确查询
        if query_id is not None:
            # 先从索引表找到 table_name
            cursor = self._conn.execute(
                "SELECT table_name FROM data_index WHERE id = ?", (query_id,)
            )
            row = cursor.fetchone()
            if row is None:
                return pd.DataFrame()
            table_name = row[0]
            sql = f'SELECT * FROM "{table_name}" WHERE _query_id = ? LIMIT ?'
            return pd.read_sql_query(sql, self._conn, params=[query_id, limit])

        # 按 api_name + 可选 ts_code 查询
        if api_name is None:
            return pd.DataFrame()

        table_name = f"data_{api_name}"

        # 检查表是否存在
        cursor = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        if cursor.fetchone() is None:
            return pd.DataFrame()

        conditions = []
        values: list[Any] = []

        if ts_code:
            conditions.append('"ts_code" = ?')
            values.append(ts_code)

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f'SELECT * FROM "{table_name}" WHERE {where} ORDER BY rowid DESC LIMIT ?'
        values.append(limit)

        return pd.read_sql_query(sql, self._conn, params=values)

    def close(self) -> None:
        """关闭数据库连接"""
        self._conn.close()

    # ==================== 内部方法 ====================

    def _insert_index(
        self,
        api_name: str,
        params: dict[str, Any],
        df: pd.DataFrame,
        table_name: str,
    ) -> int:
        """写索引记录，返回自增 id"""
        # 从参数中提取常用字段方便查询
        ts_code = params.get("ts_code")
        trade_date = params.get("trade_date")
        start_date = params.get("start_date")
        end_date = params.get("end_date")
        columns = list(df.columns)

        cursor = self._conn.execute(
            """INSERT INTO data_index
               (api_name, query_params, ts_code, trade_date, start_date, end_date,
                row_count, columns, table_name)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                api_name,
                json.dumps(params, ensure_ascii=False, default=str),
                ts_code,
                trade_date,
                start_date,
                end_date,
                len(df),
                json.dumps(columns, ensure_ascii=False),
                table_name,
            ),
        )
        self._conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def _ensure_data_table(self, table_name: str, df: pd.DataFrame) -> None:
        """
        确保数据表存在，列齐全

        如果表不存在则创建；如果有新列则 ALTER TABLE ADD COLUMN。
        """
        # 检查表是否存在
        cursor = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        if cursor.fetchone() is None:
            # 建新表
            self._create_data_table(table_name, df)
            return

        # 表已存在，检查是否需要加列
        existing_cols = self._get_table_columns(table_name)
        for col in df.columns:
            if col not in existing_cols:
                sqlite_type = self._map_dtype(df[col].dtype)
                self._conn.execute(
                    f'ALTER TABLE "{table_name}" ADD COLUMN "{col}" {sqlite_type}'
                )
                logger.info("表 %s 新增列: %s %s", table_name, col, sqlite_type)
        self._conn.commit()

    def _create_data_table(self, table_name: str, df: pd.DataFrame) -> None:
        """从 DataFrame 创建数据表"""
        col_defs = ['"_query_id" INTEGER']
        for col in df.columns:
            sqlite_type = self._map_dtype(df[col].dtype)
            col_defs.append(f'"{col}" {sqlite_type}')

        sql = f'CREATE TABLE "{table_name}" ({", ".join(col_defs)})'
        self._conn.execute(sql)
        # 为 _query_id 建索引，方便按查询批次检索
        self._conn.execute(
            f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_qid" ON "{table_name}"("_query_id")'
        )
        self._conn.commit()
        logger.info("创建数据表: %s (%d 列)", table_name, len(df.columns))

    def _insert_data(self, table_name: str, query_id: int, df: pd.DataFrame) -> None:
        """批量插入数据行"""
        # 构造 INSERT 语句
        cols = ["_query_id"] + list(df.columns)
        placeholders = ", ".join(["?"] * len(cols))
        col_names = ", ".join(f'"{c}"' for c in cols)
        sql = f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})'

        # 准备数据：NaN → None
        rows = []
        for _, row in df.iterrows():
            values = [query_id]
            for col in df.columns:
                val = row[col]
                # pandas NaN/NaT → None（SQLite NULL）
                if pd.isna(val):
                    values.append(None)
                else:
                    values.append(val)
            rows.append(values)

        self._conn.executemany(sql, rows)
        self._conn.commit()

    def _get_table_columns(self, table_name: str) -> set[str]:
        """获取已有表的列名集合"""
        cursor = self._conn.execute(f'PRAGMA table_info("{table_name}")')
        return {row[1] for row in cursor.fetchall()}

    @staticmethod
    def _map_dtype(dtype: Any) -> str:
        """pandas dtype → SQLite 类型"""
        dtype_str = str(dtype)
        return _DTYPE_MAP.get(dtype_str, "TEXT")
