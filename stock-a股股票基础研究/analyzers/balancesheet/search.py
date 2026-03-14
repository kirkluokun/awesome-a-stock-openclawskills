# analyzers/balancesheet/search.py
"""资产负债表查询功能"""

import json
import sys
from pathlib import Path
from typing import Optional, List, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.balancesheet._shared.db import connect


def get_balancesheet(
    ts_code: str,
    end_date: str = None,
    report_type: str = "1"
) -> Optional[Dict]:
    """
    查询单条资产负债表记录
    
    Args:
        ts_code: 股票代码
        end_date: 报告期 YYYYMMDD，默认最新
        report_type: 报表类型，默认1（合并报表）
        
    Returns:
        记录字典，包含基础列和完整字段
    """
    conn = connect()
    try:
        if end_date:
            sql = """
                SELECT * FROM balancesheet 
                WHERE ts_code = ? AND end_date = ? AND report_type = ?
                ORDER BY ann_date DESC
                LIMIT 1
            """
            cur = conn.execute(sql, (ts_code, end_date, report_type))
        else:
            sql = """
                SELECT * FROM balancesheet 
                WHERE ts_code = ? AND report_type = ?
                ORDER BY end_date DESC, ann_date DESC
                LIMIT 1
            """
            cur = conn.execute(sql, (ts_code, report_type))
        
        row = cur.fetchone()
        if not row:
            return None
        
        result = dict(row)
        # 解析完整字段
        if result.get('payload_json'):
            full_data = json.loads(result['payload_json'])
            result.update(full_data)
        
        return result
    finally:
        conn.close()


def get_balancesheet_history(
    ts_code: str,
    start_date: str = None,
    end_date: str = None,
    report_type: str = "1",
    limit: int = None
) -> List[Dict]:
    """
    查询历史资产负债表记录
    
    Args:
        ts_code: 股票代码
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        report_type: 报表类型
        limit: 限制返回数量（如4表示最近4个季度）
        
    Returns:
        记录列表，按end_date降序
    """
    conn = connect()
    try:
        conditions = ["ts_code = ?", "report_type = ?"]
        params = [ts_code, report_type]
        
        if start_date:
            conditions.append("end_date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("end_date <= ?")
            params.append(end_date)
        
        sql = f"""
            SELECT * FROM balancesheet 
            WHERE {' AND '.join(conditions)}
            ORDER BY end_date DESC, ann_date DESC
        """
        
        if limit:
            sql += f" LIMIT {limit}"
        
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            result = dict(row)
            # 解析完整字段
            if result.get('payload_json'):
                full_data = json.loads(result['payload_json'])
                result.update(full_data)
            results.append(result)
        
        return results
    finally:
        conn.close()


def ensure_data(
    ts_code: str,
    end_date: str = None,
    years: int = 1,
    report_type: str = "1"
) -> bool:
    """
    确保有足够的历史数据，不足时自动拉取
    
    Args:
        ts_code: 股票代码
        end_date: 截止日期，默认当前日期
        years: 需要的数据年数
        report_type: 报表类型
        
    Returns:
        是否成功获取数据
    """
    from datetime import datetime, timedelta
    from fetchers.balancesheet import fetch_and_save
    
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    
    # 检查现有数据
    existing = get_balancesheet_history(
        ts_code=ts_code,
        end_date=end_date,
        report_type=report_type,
        limit=years * 4 + 4  # 多查一些确保
    )
    
    # 计算需要的日期范围（N+1年，确保有足够数据计算同比）
    need_years = years + 1
    start_date_dt = datetime.strptime(end_date, "%Y%m%d") - timedelta(days=need_years * 365)
    start_date = start_date_dt.strftime("%Y%m%d")
    
    # 如果数据不足，拉取
    if len(existing) < years * 4:
        print(f"数据不足（{len(existing)}条），拉取 {start_date} 至 {end_date} 的数据...")
        try:
            count = fetch_and_save(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                report_type=report_type
            )
            print(f"拉取完成，新增 {count} 条记录")
            return True
        except Exception as e:
            print(f"拉取失败: {e}")
            return False
    
    return True


def get_field_value(
    ts_code: str,
    field_name: str,
    end_date: str = None,
    report_type: str = "1",
    auto_fetch: bool = True
) -> Optional[float]:
    """
    查询特定字段值，支持自动拉取
    
    Args:
        ts_code: 股票代码
        field_name: 字段名（如'inventories'）
        end_date: 报告期，默认最新
        report_type: 报表类型
        auto_fetch: 是否自动拉取数据（如果数据库无数据）
        
    Returns:
        字段值（float），不存在返回None
    """
    if auto_fetch:
        ensure_data(ts_code, end_date, years=1, report_type=report_type)
    
    record = get_balancesheet(ts_code, end_date, report_type)
    if not record:
        return None
    
    # 先查基础列
    if field_name in record:
        value = record[field_name]
        if value is not None:
            return float(value)
    
    # 再从payload_json中查找
    if 'payload_json' in record:
        full_data = json.loads(record['payload_json'])
        value = full_data.get(field_name)
        if value is not None:
            return float(value)
    
    return None


def search_by_field(
    field_name: str,
    end_date: str,
    report_type: str = "1",
    comp_type: str = None,
    limit: int = 100,
    order: str = "DESC"
) -> List[Dict]:
    """
    跨公司查询特定字段
    
    Args:
        field_name: 字段名
        end_date: 报告期
        report_type: 报表类型
        comp_type: 公司类型过滤
        limit: 返回数量限制
        order: 排序方向（DESC/ASC）
        
    Returns:
        列表，每项包含ts_code和字段值
    """
    conn = connect()
    try:
        # 先检查是否是基础列
        base_cols = [
            'total_share', 'money_cap', 'accounts_receiv', 'inventories',
            'total_cur_assets', 'fix_assets', 'total_assets', 'st_borr',
            'acct_payable', 'total_cur_liab', 'total_liab', 'undistr_porfit',
            'total_hldr_eqy_exc_min_int'
        ]
        
        conditions = ["end_date = ?", "report_type = ?"]
        params = [end_date, report_type]
        
        if comp_type:
            conditions.append("comp_type = ?")
            params.append(comp_type)
        
        if field_name in base_cols:
            # 直接从基础列查询
            sql = f"""
                SELECT ts_code, {field_name} as value
                FROM balancesheet
                WHERE {' AND '.join(conditions)} AND {field_name} IS NOT NULL
                ORDER BY {field_name} {order}
                LIMIT ?
            """
            params.append(limit)
            cur = conn.execute(sql, params)
        else:
            # 需要解析JSON（性能较差，但支持所有字段）
            sql = f"""
                SELECT ts_code, payload_json
                FROM balancesheet
                WHERE {' AND '.join(conditions)}
                LIMIT ?
            """
            params.append(limit * 2)  # 多查一些，因为可能有些记录没有该字段
            cur = conn.execute(sql, params)
            
            # 解析并过滤
            results = []
            for row in cur.fetchall():
                try:
                    data = json.loads(row['payload_json'])
                    value = data.get(field_name)
                    if value is not None:
                        results.append({
                            'ts_code': row['ts_code'],
                            'value': float(value)
                        })
                except:
                    continue
            
            # 排序
            results.sort(key=lambda x: x['value'], reverse=(order == "DESC"))
            return results[:limit]
        
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()
