"""财务指标查询功能"""

import json
import sys
from pathlib import Path
from typing import Optional, List, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.fina_indicator._shared.db import connect


def get_fina_indicator(ts_code: str, end_date: str = None) -> Optional[Dict]:
    conn = connect()
    try:
        if end_date:
            sql = "SELECT * FROM fina_indicator WHERE ts_code = ? AND end_date = ? ORDER BY ann_date DESC LIMIT 1"
            cur = conn.execute(sql, (ts_code, end_date))
        else:
            sql = "SELECT * FROM fina_indicator WHERE ts_code = ? ORDER BY end_date DESC, ann_date DESC LIMIT 1"
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


def get_fina_indicator_history(ts_code: str, start_date: str = None, end_date: str = None, limit: int = None) -> List[Dict]:
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
        sql = f"SELECT * FROM fina_indicator WHERE {' AND '.join(conditions)} ORDER BY end_date DESC, ann_date DESC"
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
    record = get_fina_indicator(ts_code, end_date)
    if not record:
        return None
    value = record.get(field_name)
    if value is not None:
        return float(value)
    return None
