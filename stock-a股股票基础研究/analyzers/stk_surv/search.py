# analyzers/stk_surv/search.py
"""机构调研检索功能"""

from datetime import datetime, timedelta
from ._shared.db import connect


def search_by_company(company_name: str, days: int = None) -> list[dict]:
    """
    按公司名称搜索调研
    
    Args:
        company_name: 公司名称（支持模糊匹配）
        days: 可选，最近N天
    
    Returns:
        调研事件列表
    """
    conn = connect()
    try:
        conditions = ["name LIKE ?"]
        params = [f"%{company_name}%"]
        
        if days:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            conditions.append("surv_date >= ?")
            params.append(cutoff_date)
        
        sql = f"""
            SELECT id, ts_code, name, surv_date, rece_place, rece_mode, comp_rece
            FROM stk_surv_event
            WHERE {' AND '.join(conditions)}
            ORDER BY surv_date DESC
        """
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def search_by_org(org_name: str, days: int = None) -> list[dict]:
    """
    按机构名称搜索（该机构参加了哪些调研）
    
    Args:
        org_name: 机构名称（支持模糊匹配）
        days: 可选，最近N天
    
    Returns:
        调研事件列表
    """
    conn = connect()
    try:
        conditions = ["p.rece_org LIKE ?"]
        params = [f"%{org_name}%"]
        
        if days:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            conditions.append("e.surv_date >= ?")
            params.append(cutoff_date)
        
        sql = f"""
            SELECT DISTINCT e.id, e.ts_code, e.name, e.surv_date, 
                   e.rece_place, e.rece_mode, e.comp_rece
            FROM stk_surv_event e
            JOIN stk_surv_participant p ON e.id = p.event_id
            WHERE {' AND '.join(conditions)}
            ORDER BY e.surv_date DESC
        """
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def search_by_person(person_name: str, days: int = None) -> list[dict]:
    """
    按参与人员姓名搜索
    
    Args:
        person_name: 人员姓名（支持模糊匹配）
        days: 可选，最近N天
    
    Returns:
        调研事件列表
    """
    conn = connect()
    try:
        conditions = ["p.fund_visitors LIKE ?"]
        params = [f"%{person_name}%"]
        
        if days:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            conditions.append("e.surv_date >= ?")
            params.append(cutoff_date)
        
        sql = f"""
            SELECT DISTINCT e.id, e.ts_code, e.name, e.surv_date,
                   e.rece_place, e.rece_mode, e.comp_rece
            FROM stk_surv_event e
            JOIN stk_surv_participant p ON e.id = p.event_id
            WHERE {' AND '.join(conditions)}
            ORDER BY e.surv_date DESC
        """
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_survey_detail(event_id: int) -> dict:
    """
    获取某次调研的详细信息
    
    Args:
        event_id: 事件ID
    
    Returns:
        {
            "event": {...},
            "participants": [...]
        }
    """
    conn = connect()
    try:
        # 获取事件信息
        cur = conn.execute(
            "SELECT * FROM stk_surv_event WHERE id = ?",
            (event_id,)
        )
        event_row = cur.fetchone()
        if not event_row:
            return None
        
        event = dict(event_row)
        
        # 获取参与人员
        cur = conn.execute(
            "SELECT fund_visitors, rece_org, org_type FROM stk_surv_participant WHERE event_id = ?",
            (event_id,)
        )
        participants = [dict(r) for r in cur.fetchall()]
        
        return {
            "event": event,
            "participants": participants
        }
    finally:
        conn.close()
