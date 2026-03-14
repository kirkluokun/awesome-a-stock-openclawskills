# analyzers/broker_recommend/stats.py
"""券商金股统计功能"""

from collections import defaultdict
from ._shared.db import connect


def get_monthly_stats(month: str) -> dict:
    """
    获取指定月份的统计
    
    Returns:
        {
            "month": "202602",
            "by_company": [{"ts_code": "...", "name": "...", "count": 5, "brokers": [...]}],
            "by_broker": [{"broker": "...", "count": 10}]
        }
    """
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT ts_code, name, broker FROM broker_recommend WHERE month = ?",
            (month,)
        )
        rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    
    # 按公司统计
    company_stats = defaultdict(lambda: {"ts_code": "", "name": "", "count": 0, "brokers": []})
    for row in rows:
        key = row["ts_code"]
        company_stats[key]["ts_code"] = row["ts_code"]
        company_stats[key]["name"] = row["name"]
        company_stats[key]["count"] += 1
        company_stats[key]["brokers"].append(row["broker"])
    
    by_company = sorted(
        [
            {
                "ts_code": v["ts_code"],
                "name": v["name"],
                "count": v["count"],
                "brokers": list(set(v["brokers"]))
            }
            for v in company_stats.values()
        ],
        key=lambda x: x["count"],
        reverse=True
    )
    
    # 按券商统计
    broker_stats = defaultdict(int)
    for row in rows:
        broker_stats[row["broker"]] += 1
    
    by_broker = sorted(
        [{"broker": k, "count": v} for k, v in broker_stats.items()],
        key=lambda x: x["count"],
        reverse=True
    )
    
    return {
        "month": month,
        "by_company": by_company,
        "by_broker": by_broker
    }


def get_continuous_recommendations(ts_code: str, min_months: int = 2) -> list[str]:
    """
    获取连续被推荐的月份列表
    
    Args:
        ts_code: 股票代码
        min_months: 最少连续月份数
    
    Returns:
        连续月份列表，如 ["202501", "202502", "202503"]
    """
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT DISTINCT month FROM broker_recommend WHERE ts_code = ? ORDER BY month",
            (ts_code,)
        )
        months = [r["month"] for r in cur.fetchall()]
    finally:
        conn.close()
    
    if len(months) < min_months:
        return []
    
    # 找出连续月份（简化版：按字符串排序后检查是否连续）
    continuous = []
    current_seq = [months[0]]
    
    for i in range(1, len(months)):
        prev = int(months[i-1])
        curr = int(months[i])
        
        # 计算月份差
        prev_year = prev // 100
        prev_month = prev % 100
        curr_year = curr // 100
        curr_month = curr % 100
        
        # 判断是否连续
        if curr_year == prev_year and curr_month == prev_month + 1:
            # 同一年，月份+1
            current_seq.append(months[i])
        elif curr_year == prev_year + 1 and curr_month == 1 and prev_month == 12:
            # 跨年：12月 -> 1月
            current_seq.append(months[i])
        else:
            # 不连续
            if len(current_seq) >= min_months:
                continuous.append(current_seq)
            current_seq = [months[i]]
    
    if len(current_seq) >= min_months:
        continuous.append(current_seq)
    
    # 返回最长的连续序列
    return max(continuous, key=len) if continuous else []


def get_broker_recommendations(broker: str, month: str = None) -> list[dict]:
    """
    获取某券商的金股列表
    
    Args:
        broker: 券商名称
        month: 可选，指定月份
    
    Returns:
        金股列表
    """
    conn = connect()
    try:
        if month:
            cur = conn.execute(
                "SELECT month, ts_code, name FROM broker_recommend WHERE broker = ? AND month = ? ORDER BY ts_code",
                (broker, month)
            )
        else:
            cur = conn.execute(
                "SELECT month, ts_code, name FROM broker_recommend WHERE broker = ? ORDER BY month DESC, ts_code",
                (broker,)
            )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
