"""查询产业链排名 + 关联股票"""
import asyncio
import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "themes.db"

async def main():
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT a.id, a.title, a.content, a.logic_summary, a.publish_date, a.relevance
            FROM articles a
            WHERE a.source = 'industry_chain'
            ORDER BY a.fetched_at DESC
            LIMIT 15
        ''')
        rows = await cursor.fetchall()
        if not rows:
            print("暂无产业链数据，请先执行抓取。")
            return

        print(f"=== 产业链排行 Top {len(rows)} ===\n")
        for row in rows:
            print(f"🔥 {row['title']}")
            if row['logic_summary']:
                print(f"   逻辑: {row['logic_summary']}")
            # 关联股票
            c2 = await db.execute('''
                SELECT s.code, s.name, ars.logic
                FROM article_stocks ars JOIN stocks s ON s.id = ars.stock_id
                WHERE ars.article_id = ?
            ''', (row['id'],))
            stocks = await c2.fetchall()
            if stocks:
                print(f"   关联股票: {', '.join(s['name'] + '(' + s['code'] + ')' for s in stocks)}")
            print()

if __name__ == "__main__":
    asyncio.run(main())
