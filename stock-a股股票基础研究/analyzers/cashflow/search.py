"""现金流量表查询功能"""

import json
import sys
from pathlib import Path
from typing import Optional, List, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.cashflow._shared.db import connect


def get_cashflow(ts_code: str, end_date: str = None) -> Optional[Dict]:
    conn = connect()
    try:
        if end_date:
            sql = "SELECT * FROM cashflow WHERE ts_code = ? AND end_date = ? ORDER BY ann_date DESC LIMIT 1"
            cur = conn.execute(sql, (ts_code, end_date))
        else:
            sql = "SELECT * FROM cashflow WHERE ts_code = ? ORDER BY end_date DESC, ann_date DESC LIMIT 1"
            cur = conn.execute(sql, (ts_code,))
        row = cur.fetchone()
        if not row:
            return None
        result = dict(row)
        if result.get("payload_json"):
            try:
                result.update(json.loads(result["payload_json"]))
            except (json.JSONDecodeError, TypeError):
                pass
        return result
    finally:
        conn.close()


def get_cashflow_history(
    ts_code: str,
    start_date: str = None,
    end_date: str = None,
    limit: int = None
) -> List[Dict]:
    conn = connect()
    try:
        conditions = ["ts_code = ?"]
        params = [ts_code]
        if start_date:
            conditions.append("end_date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("end_date <= ?")
            params.append(end_date)
        sql = f"SELECT * FROM cashflow WHERE {' AND '.join(conditions)} ORDER BY end_date DESC, ann_date DESC"
        if limit is not None:
            if not isinstance(limit, int) or limit <= 0:
                raise ValueError("limit must be a positive int")
            sql += " LIMIT ?"
            params.append(limit)
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        results = []
        for row in rows:
            result = dict(row)
            if result.get("payload_json"):
                try:
                    result.update(json.loads(result["payload_json"]))
                except (json.JSONDecodeError, TypeError):
                    pass
            results.append(result)
        return results
    finally:
        conn.close()


def get_field_value(ts_code: str, field_name: str, end_date: str = None) -> Optional[float]:
    record = get_cashflow(ts_code, end_date)
    if not record:
        return None
    value = record.get(field_name)
    if value is not None:
        return float(value)
    return None


def ensure_data(ts_code: str, end_date: str = None, years: int = 4) -> bool:
    from datetime import datetime, timedelta
    from fetchers.cashflow import fetch_and_save

    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    existing = get_cashflow_history(ts_code, end_date=end_date, limit=years * 4 + 4)
    need_years = years + 1
    start_date_dt = datetime.strptime(end_date, "%Y%m%d") - timedelta(days=need_years * 365)
    start_date = start_date_dt.strftime("%Y%m%d")
    if len(existing) < years * 4:
        print(f"数据不足（{len(existing)}条），拉取 {start_date} 至 {end_date} 的数据...")
        try:
            fetch_and_save(ts_code=ts_code, start_date=start_date, end_date=end_date)
            return True
        except Exception as e:
            print(f"拉取失败: {e}")
            return False
    return True
