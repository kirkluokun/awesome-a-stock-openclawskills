"""按股票名称/代码查询关联文章和投资逻辑

用法: uv run python scripts/query_stock.py <股票名称或代码>
示例: uv run python scripts/query_stock.py 贵州茅台
      uv run python scripts/query_stock.py 600519
"""
import asyncio
import sys
import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "themes.db"

async def main(keyword: str):
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT a.title, a.publish_date, a.logic_summary, s.name, s.code, ars.logic, ars.context
            FROM articles a
            JOIN article_stocks ars ON a.id = ars.article_id
            JOIN stocks s ON s.id = ars.stock_id
            WHERE s.name LIKE ? OR s.code = ?
            ORDER BY a.publish_date DESC LIMIT 10
        ''', (f'%{keyword}%', keyword))
        rows = await cursor.fetchall()

        if not rows:
            print(f"未找到与 '{keyword}' 相关的记录。")
            return

        print(f"=== 与 '{keyword}' 相关的文章（共 {len(rows)} 条）===\n")
        for row in rows:
            print(f"[{row['publish_date']}] {row['title']}")
            print(f"  股票: {row['name']}({row['code']})")
            if row['logic']:
                print(f"  逻辑: {row['logic']}")
            if row['context']:
                print(f"  上下文: {row['context']}")
            print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: uv run python scripts/query_stock.py <股票名称或代码>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
