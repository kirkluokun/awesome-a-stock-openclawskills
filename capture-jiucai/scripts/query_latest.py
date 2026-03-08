"""查询近2天的热点段子 + 主题热度统计"""
import asyncio
import aiosqlite
from collections import Counter
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "themes.db"

async def main():
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        # 最近2天的文章
        cursor = await db.execute('''
            SELECT a.id, a.title, a.publish_date, a.logic_summary, a.content
            FROM articles a
            WHERE a.source = 'study_hot'
              AND a.publish_date >= date("now", "-2 days")
            ORDER BY a.publish_date DESC, a.id DESC
            LIMIT 30
        ''')
        articles = await cursor.fetchall()
        if not articles:
            print("近2天暂无段子数据，请先执行抓取。")
            return

        print(f"=== 近2天共 {len(articles)} 篇文章 ===\n")
        all_themes = []
        for art in articles:
            print(f"📰 [{art['publish_date']}] {art['title']}")
            if art['logic_summary']:
                print(f"   💡 {art['logic_summary']}")
            # 关联股票
            c2 = await db.execute('''
                SELECT s.name, s.code, ars.logic
                FROM article_stocks ars JOIN stocks s ON s.id = ars.stock_id
                WHERE ars.article_id = ?
            ''', (art['id'],))
            stocks = await c2.fetchall()
            if stocks:
                stock_str = ', '.join(f"{s['name']}({s['code']})" for s in stocks[:5])
                print(f"   📈 关联股票: {stock_str}")
            # 收集主题
            c3 = await db.execute('''
                SELECT t.name FROM themes t
                JOIN article_themes at ON t.id = at.theme_id
                WHERE at.article_id = ?
            ''', (art['id'],))
            themes = [r['name'] for r in await c3.fetchall()]
            all_themes.extend(themes)
            if themes:
                print(f"   🏷️ 主题: {', '.join(themes[:4])}")
            print()

        # 主题热度统计
        if all_themes:
            print("=== 近2天 Top 主题热度 ===")
            for theme, count in Counter(all_themes).most_common(10):
                print(f"  {theme}: {count} 篇")

if __name__ == "__main__":
    asyncio.run(main())
