# analyzers/balancesheet/_shared/db.py
"""资产负债表数据库工具"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from config import DB_PATH

SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """连接数据库"""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_table(conn: sqlite3.Connection = None):
    """初始化表结构"""
    if conn is None:
        conn = connect()
        should_close = True
    else:
        should_close = False
    
    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.commit()
    finally:
        if should_close:
            conn.close()


def upsert_balancesheet(conn: sqlite3.Connection, rows: list) -> int:
    """批量插入/更新资产负债表数据
    
    Args:
        conn: 数据库连接
        rows: 数据行列表，每行包含所有字段
        
    Returns:
        插入/更新的行数
    """
    if not rows:
        return 0
    
    # 基础列（常用字段）
    base_cols = [
        'ts_code', 'ann_date', 'f_ann_date', 'end_date', 'report_type', 
        'comp_type', 'end_type', 'total_share', 'money_cap', 
        'accounts_receiv', 'inventories', 'total_cur_assets', 'fix_assets',
        'total_assets', 'st_borr', 'acct_payable', 'total_cur_liab',
        'total_liab', 'undistr_porfit', 'total_hldr_eqy_exc_min_int'
    ]
    
    # 唯一键：如果ann_date为空，使用ts_code+end_date+report_type作为唯一键
    # 这样可以确保同一报告期的数据能正确更新
    unique_cols = ['ts_code', 'end_date', 'report_type']
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 准备数据
    db_rows = []
    for row in rows:
        db_row = {}
        # 提取基础列
        for col in base_cols:
            db_row[col] = row.get(col)
        
        # 存储完整JSON
        db_row['payload_json'] = json.dumps(row, ensure_ascii=False, default=str)
        db_row['source'] = 'tushare'
        db_row['created_at'] = now
        db_row['updated_at'] = now
        
        # 处理唯一键中的NULL值
        for col in unique_cols:
            if db_row.get(col) is None:
                db_row[col] = ''
        
        # 如果ann_date为空，设置为空字符串（不影响唯一键判断）
        if db_row.get('ann_date') is None:
            db_row['ann_date'] = ''
        
        db_rows.append(db_row)
    
    # 构建SQL
    all_cols = list(db_rows[0].keys())
    placeholders = ", ".join(["?"] * len(all_cols))
    columns_sql = ", ".join(all_cols)
    conflict_sql = ", ".join(unique_cols)
    update_cols = [c for c in all_cols if c not in unique_cols + ['created_at']]
    update_sql = ", ".join([f"{c} = excluded.{c}" for c in update_cols])
    
    sql = (
        f"INSERT INTO balancesheet ({columns_sql}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT({conflict_sql}) DO UPDATE SET {update_sql}"
    )
    
    values = [[r.get(col) for col in all_cols] for r in db_rows]
    
    try:
        conn.executemany(sql, values)
        conn.commit()
        return len(db_rows)
    except Exception as e:
        conn.rollback()
        raise


if __name__ == "__main__":
    # CLI入口：初始化表
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", help="初始化表结构")
    args = parser.parse_args()
    
    if args.init:
        init_table()
        print("表结构初始化完成")
