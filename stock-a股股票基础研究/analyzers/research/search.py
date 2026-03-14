# analyzers/research/search.py
"""搜索研报"""

from ._shared.db import connect


def search_reports(
    ts_code: str = None,
    ind_name: str = None,
    keyword: str = None,
    inst_csname: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
) -> list[dict]:
    """
    从 DB 搜索研报
    
    Args:
        ts_code: 股票代码
        ind_name: 行业名称（模糊匹配）
        keyword: 标题关键词（模糊匹配）
        inst_csname: 券商名称（模糊匹配）
        start_date/end_date: 日期范围
        limit: 返回条数上限
    
    Returns:
        研报元数据列表
    """
    conn = connect()
    
    conditions = []
    params = []
    
    if ts_code:
        conditions.append("ts_code = ?")
        params.append(ts_code)
    if ind_name:
        conditions.append("ind_name LIKE ?")
        params.append(f"%{ind_name}%")
    if keyword:
        conditions.append("title LIKE ?")
        params.append(f"%{keyword}%")
    if inst_csname:
        conditions.append("inst_csname LIKE ?")
        params.append(f"%{inst_csname}%")
    if start_date:
        conditions.append("trade_date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("trade_date <= ?")
        params.append(end_date)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    sql = f"""
        SELECT id, trade_date, ts_code, name, title, abstr, report_type,
               author, inst_csname, ind_name, url, local_path, parsed_at
        FROM research_report
        WHERE {where_clause}
        ORDER BY trade_date DESC
        LIMIT ?
    """
    params.append(limit)
    
    try:
        cur = conn.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    
    return rows


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="搜索研报")
    parser.add_argument("--ts-code", help="股票代码")
    parser.add_argument("--ind", help="行业名称")
    parser.add_argument("--keyword", help="标题关键词")
    parser.add_argument("--inst", help="券商名称")
    parser.add_argument("--start", help="开始日期")
    parser.add_argument("--end", help="结束日期")
    parser.add_argument("--limit", type=int, default=20, help="返回条数")
    args = parser.parse_args()
    
    results = search_reports(
        ts_code=args.ts_code,
        ind_name=args.ind,
        keyword=args.keyword,
        inst_csname=args.inst,
        start_date=args.start,
        end_date=args.end,
        limit=args.limit,
    )
    
    for r in results:
        print(f"[{r['trade_date']}] {r['title'][:50]}...")
    print(f"\n共 {len(results)} 条")
