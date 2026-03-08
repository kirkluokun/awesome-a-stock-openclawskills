"""查询最近异动板块"""
import asyncio
import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "themes.db"

async def main():
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT a.title, a.content, a.publish_date, a.logic_summary
            FROM articles a
            WHERE a.source = 'action'
            ORDER BY a.publish_date DESC, a.fetched_at DESC
            LIMIT 20
        ''')
        rows = await cursor.fetchall()
        if not rows:
            print("暂无异动数据，请先执行抓取。")
            return

        current_date = None
        print(f"=== 最近异动板块（共 {len(rows)} 条）===\n")
        for row in rows:
            # 按日期分组
            if row['publish_date'] != current_date:
                current_date = row['publish_date']
                print(f"--- {current_date} ---")
            print(f"📊 {row['title']}")
            content = row['content'][:300] if row['content'] else ''
            if content:
                print(f"   {content}")
            if row['logic_summary']:
                print(f"   逻辑: {row['logic_summary']}")
            print()

if __name__ == "__main__":
    asyncio.run(main())
