-- analyzers/research/schema.sql
-- 研报元数据表
CREATE TABLE IF NOT EXISTS research_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,       -- 发布日期 (YYYYMMDD)
    ts_code TEXT,                   -- 股票代码 (如 000001.SZ)
    name TEXT,                      -- 股票名称
    title TEXT NOT NULL,            -- 研报标题
    abstr TEXT,                     -- 研报摘要
    report_type TEXT,               -- 报告类型 (深度/点评/行业等)
    author TEXT,                    -- 作者
    inst_csname TEXT,               -- 发布机构中文名
    ind_name TEXT,                  -- 行业名称
    url TEXT NOT NULL,              -- 研报原始URL (唯一键)
    local_path TEXT,                -- 本地PDF路径
    parsed_at TEXT,                 -- 解析完成时间
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,  -- 记录创建时间
    UNIQUE(url)
);

-- 索引：按股票代码查询
CREATE INDEX IF NOT EXISTS idx_rr_ts_code ON research_report(ts_code);
-- 索引：按发布日期查询
CREATE INDEX IF NOT EXISTS idx_rr_trade_date ON research_report(trade_date);
-- 索引：按行业查询
CREATE INDEX IF NOT EXISTS idx_rr_ind_name ON research_report(ind_name);
-- 索引：按机构查询
CREATE INDEX IF NOT EXISTS idx_rr_inst_csname ON research_report(inst_csname);
