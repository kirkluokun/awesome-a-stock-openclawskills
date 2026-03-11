"""SQLite 异步数据层 — 5 表关联：articles / stocks / themes / article_stocks / article_themes"""

import aiosqlite
import json
from pathlib import Path

from .models import Article, ParsedResult, StockMention, ThemeMention

# 数据库文件位置：项目根目录/data/themes.db
DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "themes.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    source       TEXT NOT NULL,
    title        TEXT NOT NULL,
    url          TEXT DEFAULT '',
    content      TEXT DEFAULT '',
    images       TEXT DEFAULT '[]',
    publish_date TEXT DEFAULT '',
    fetched_at   TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    relevance    INTEGER DEFAULT 0,
    logic_summary TEXT DEFAULT '',
    raw_yaml     TEXT DEFAULT '',
    parse_status TEXT DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS stocks (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS themes (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL UNIQUE,
    category TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS article_stocks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL REFERENCES articles(id),
    stock_id   INTEGER NOT NULL REFERENCES stocks(id),
    context    TEXT DEFAULT '',
    logic      TEXT DEFAULT '',
    UNIQUE(article_id, stock_id)
);

CREATE TABLE IF NOT EXISTS article_themes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL REFERENCES articles(id),
    theme_id   INTEGER NOT NULL REFERENCES themes(id),
    UNIQUE(article_id, theme_id)
);

CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(publish_date);
CREATE INDEX IF NOT EXISTS idx_articles_fetched ON articles(fetched_at);
"""


async def _get_db() -> aiosqlite.Connection:
    """获取数据库连接（自动建表）"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.executescript(SCHEMA_SQL)
    return db


# ─── 去重检查 ───────────────────────────────────────────────────────

async def check_exists(content_hash: str) -> bool:
    """检查文章是否已存在（通过 content_hash）。用于 AI 解析之前去重。"""
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT 1 FROM articles WHERE content_hash = ?", (content_hash,)
        )
        return (await cursor.fetchone()) is not None
    finally:
        await db.close()


# ─── 写入 ─────────────────────────────────────────────────────────

async def save_article(article: Article, parsed: ParsedResult | None = None) -> dict:
    """
    保存文章 + AI 解析结果（自动去重、自动创建 stock/theme 实体）。
    返回 {"status": "saved"|"skipped"|"filtered", "article_id": int|None}
    """
    # 噪音过滤
    if parsed and parsed.relevance < 5:
        return {"status": "filtered", "article_id": None,
                "reason": parsed.filter_reason or f"relevance={parsed.relevance}"}

    db = await _get_db()
    try:
        # 插入文章（去重）
        try:
            cursor = await db.execute(
                """INSERT INTO articles
                   (source, title, url, content, images, publish_date, fetched_at,
                    content_hash, relevance, logic_summary, raw_yaml, parse_status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    article.source, article.title, article.url, article.content,
                    json.dumps(article.images, ensure_ascii=False),
                    parsed.publish_date if parsed else article.publish_date,
                    article.fetched_at, article.content_hash,
                    parsed.relevance if parsed else 0,
                    parsed.logic_summary if parsed else "",
                    parsed.raw_yaml if parsed else "",
                    "parsed" if parsed and not parsed.parse_failed else "pending",
                ),
            )
            article_id = cursor.lastrowid
        except aiosqlite.IntegrityError:
            # 产业链来源：同一 industry_id 有新版本 → 覆盖旧数据（保留最新）
            if article.source == "industry_chain":
                cur2 = await db.execute(
                    "SELECT id FROM articles WHERE content_hash=?", (article.content_hash,)
                )
                row = await cur2.fetchone()
                if not row:
                    return {"status": "skipped", "article_id": None}
                article_id = row["id"]
                await db.execute(
                    """UPDATE articles
                       SET title=?, content=?, images=?, publish_date=?, fetched_at=?,
                           relevance=?, logic_summary=?, raw_yaml=?, parse_status=?
                       WHERE id=?""",
                    (
                        article.title, article.content,
                        json.dumps(article.images, ensure_ascii=False),
                        parsed.publish_date if parsed else article.publish_date,
                        article.fetched_at,
                        parsed.relevance if parsed else 0,
                        parsed.logic_summary if parsed else "",
                        parsed.raw_yaml if parsed else "",
                        "parsed" if parsed and not parsed.parse_failed else "pending",
                        article_id,
                    ),
                )
                # 重建关联数据
                if parsed and not parsed.parse_failed:
                    await db.execute("DELETE FROM article_stocks WHERE article_id=?", (article_id,))
                    await db.execute("DELETE FROM article_themes WHERE article_id=?", (article_id,))
                    for s in parsed.stocks:
                        stock_id = await _upsert_stock(db, s.code, s.name)
                        await _safe_insert(
                            db,
                            "INSERT OR IGNORE INTO article_stocks (article_id, stock_id, context, logic) VALUES (?,?,?,?)",
                            (article_id, stock_id, s.context, s.logic),
                        )
                    for t in parsed.themes:
                        theme_id = await _upsert_theme(db, t.name, t.category)
                        await _safe_insert(
                            db,
                            "INSERT OR IGNORE INTO article_themes (article_id, theme_id) VALUES (?,?)",
                            (article_id, theme_id),
                        )
                await db.commit()
                return {"status": "updated", "article_id": article_id}
            return {"status": "skipped", "article_id": None}

        # 写入关联数据
        if parsed and not parsed.parse_failed:
            for s in parsed.stocks:
                stock_id = await _upsert_stock(db, s.code, s.name)
                await _safe_insert(
                    db,
                    "INSERT OR IGNORE INTO article_stocks (article_id, stock_id, context, logic) VALUES (?,?,?,?)",
                    (article_id, stock_id, s.context, s.logic),
                )
            for t in parsed.themes:
                theme_id = await _upsert_theme(db, t.name, t.category)
                await _safe_insert(
                    db,
                    "INSERT OR IGNORE INTO article_themes (article_id, theme_id) VALUES (?,?)",
                    (article_id, theme_id),
                )

        await db.commit()
        return {"status": "saved", "article_id": article_id}
    finally:
        await db.close()


async def _upsert_stock(db: aiosqlite.Connection, code: str, name: str) -> int:
    """插入或获取股票 ID"""
    try:
        cursor = await db.execute(
            "INSERT INTO stocks (code, name) VALUES (?, ?)", (code, name)
        )
        return cursor.lastrowid
    except aiosqlite.IntegrityError:
        cursor = await db.execute("SELECT id FROM stocks WHERE code = ?", (code,))
        row = await cursor.fetchone()
        return row["id"]


async def _upsert_theme(db: aiosqlite.Connection, name: str, category: str) -> int:
    """插入或获取主题 ID"""
    try:
        cursor = await db.execute(
            "INSERT INTO themes (name, category) VALUES (?, ?)", (name, category)
        )
        return cursor.lastrowid
    except aiosqlite.IntegrityError:
        cursor = await db.execute("SELECT id FROM themes WHERE name = ?", (name,))
        row = await cursor.fetchone()
        return row["id"]


async def _safe_insert(db: aiosqlite.Connection, sql: str, params: tuple):
    """安全插入，忽略重复"""
    try:
        await db.execute(sql, params)
    except aiosqlite.IntegrityError:
        pass


# ─── 查询 ─────────────────────────────────────────────────────────

async def query_by_stock(stock: str, limit: int = 50) -> list[dict]:
    """按股票代码或名称查询相关文章（时间倒序）"""
    db = await _get_db()
    try:
        cursor = await db.execute(
            """SELECT a.*, s.code as stock_code, s.name as stock_name,
                      ars.context, ars.logic
               FROM articles a
               JOIN article_stocks ars ON a.id = ars.article_id
               JOIN stocks s ON s.id = ars.stock_id
               WHERE s.code = ? OR s.name LIKE ?
               ORDER BY a.publish_date DESC, a.fetched_at DESC
               LIMIT ?""",
            (stock, f"%{stock}%", limit),
        )
        return [_row_to_dict(r) for r in await cursor.fetchall()]
    finally:
        await db.close()


async def query_by_theme(theme: str, limit: int = 50) -> list[dict]:
    """按主题名称查询关联文章和股票"""
    db = await _get_db()
    try:
        cursor = await db.execute(
            """SELECT a.*, t.name as theme_name, t.category as theme_category
               FROM articles a
               JOIN article_themes at2 ON a.id = at2.article_id
               JOIN themes t ON t.id = at2.theme_id
               WHERE t.name LIKE ?
               ORDER BY a.publish_date DESC, a.fetched_at DESC
               LIMIT ?""",
            (f"%{theme}%", limit),
        )
        articles = [_row_to_dict(r) for r in await cursor.fetchall()]

        # 附加每篇文章的关联股票
        for art in articles:
            cursor2 = await db.execute(
                """SELECT s.code, s.name, ars.context, ars.logic
                   FROM article_stocks ars JOIN stocks s ON s.id = ars.stock_id
                   WHERE ars.article_id = ?""",
                (art["id"],),
            )
            art["stocks"] = [dict(r) for r in await cursor2.fetchall()]
        return articles
    finally:
        await db.close()


async def query_latest(days: int = 7, source: str | None = None, limit: int = 50) -> list[dict]:
    """查询最近 N 天的新增文章"""
    db = await _get_db()
    try:
        conditions = ["fetched_at >= datetime('now', ?)"]
        params: list = [f"-{days} days"]
        if source:
            conditions.append("source = ?")
            params.append(source)
        where = "WHERE " + " AND ".join(conditions)
        params.append(limit)

        cursor = await db.execute(
            f"SELECT * FROM articles {where} ORDER BY fetched_at DESC LIMIT ?",
            params,
        )
        return [_row_to_dict(r) for r in await cursor.fetchall()]
    finally:
        await db.close()


async def get_stock_timeline(stock: str) -> list[dict]:
    """获取某只股票的逻辑演变时间线"""
    db = await _get_db()
    try:
        cursor = await db.execute(
            """SELECT a.publish_date, a.title, a.source, a.url,
                      ars.context, ars.logic, a.logic_summary
               FROM articles a
               JOIN article_stocks ars ON a.id = ars.article_id
               JOIN stocks s ON s.id = ars.stock_id
               WHERE s.code = ? OR s.name LIKE ?
               ORDER BY a.publish_date ASC""",
            (stock, f"%{stock}%"),
        )
        return [dict(r) for r in await cursor.fetchall()]
    finally:
        await db.close()


async def get_stats() -> dict:
    """获取各数据源的统计信息"""
    db = await _get_db()
    try:
        cursor = await db.execute(
            """SELECT source, COUNT(*) as count, MAX(fetched_at) as last_fetch
               FROM articles GROUP BY source"""
        )
        rows = await cursor.fetchall()
        stats = {
            "sources": {row["source"]: {"count": row["count"], "last_fetch": row["last_fetch"]} for row in rows},
        }
        # 总计
        cursor = await db.execute("SELECT COUNT(*) as c FROM stocks")
        stats["total_stocks"] = (await cursor.fetchone())["c"]
        cursor = await db.execute("SELECT COUNT(*) as c FROM themes")
        stats["total_themes"] = (await cursor.fetchone())["c"]
        return stats
    finally:
        await db.close()


def _row_to_dict(row) -> dict:
    """将 Row 对象转为 dict，解析 JSON 字段"""
    d = dict(row)
    for json_field in ("images",):
        if json_field in d and isinstance(d[json_field], str):
            try:
                d[json_field] = json.loads(d[json_field])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


# ─── Backfill（回补全文+重新解析）───────────────────────────────────

async def get_articles_needing_backfill(max_content_len: int = 500) -> list[dict]:
    """
    获取需要回补全文的文章（内容过短 + 有 URL 的）。
    返回 [{id, url, title, source}, ...]，URL 去重。
    """
    db = await _get_db()
    try:
        cursor = await db.execute(
            """SELECT id, url, title, source FROM articles
               WHERE length(content) <= ? AND url != '' AND url IS NOT NULL
               ORDER BY id""",
            (max_content_len,),
        )
        rows = await cursor.fetchall()
        # URL 去重：同一 URL 只保留第一个
        seen_urls = set()
        results = []
        for row in rows:
            url = row["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                results.append(dict(row))
        return results
    finally:
        await db.close()


async def update_article_content(
    article_id: int,
    content: str,
    publish_date: str = "",
    parsed: "ParsedResult | None" = None,
) -> None:
    """
    更新文章的内容和日期，并可选重新写入 AI 解析结果。
    如果提供了 parsed，会清除旧的 article_stocks/article_themes 并重建。
    """
    db = await _get_db()
    try:
        # 更新文章基本字段
        updates = {"content": content}
        if publish_date:
            updates["publish_date"] = publish_date
        if parsed and not parsed.parse_failed:
            updates["relevance"] = parsed.relevance
            updates["logic_summary"] = parsed.logic_summary
            updates["raw_yaml"] = parsed.raw_yaml
            updates["parse_status"] = "parsed"
            if parsed.publish_date:
                updates["publish_date"] = parsed.publish_date

        set_clause = ", ".join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [article_id]
        await db.execute(f"UPDATE articles SET {set_clause} WHERE id=?", values)

        # 重建关联数据
        if parsed and not parsed.parse_failed:
            await db.execute("DELETE FROM article_stocks WHERE article_id=?", (article_id,))
            await db.execute("DELETE FROM article_themes WHERE article_id=?", (article_id,))

            for s in parsed.stocks:
                stock_id = await _upsert_stock(db, s.code, s.name)
                await _safe_insert(
                    db,
                    "INSERT OR IGNORE INTO article_stocks (article_id, stock_id, context, logic) VALUES (?,?,?,?)",
                    (article_id, stock_id, s.context, s.logic),
                )
            for t in parsed.themes:
                theme_id = await _upsert_theme(db, t.name, t.category)
                await _safe_insert(
                    db,
                    "INSERT OR IGNORE INTO article_themes (article_id, theme_id) VALUES (?,?)",
                    (article_id, theme_id),
                )

        await db.commit()
    finally:
        await db.close()

