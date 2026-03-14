-- analyzers/broker_recommend/schema.sql
CREATE TABLE IF NOT EXISTS broker_recommend (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,              -- 月度 YYYYMM
    broker TEXT NOT NULL,             -- 券商名称
    ts_code TEXT NOT NULL,            -- 股票代码
    name TEXT NOT NULL,               -- 股票简称
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(month, broker, ts_code)
);

CREATE INDEX IF NOT EXISTS idx_br_month ON broker_recommend(month);
CREATE INDEX IF NOT EXISTS idx_br_ts_code ON broker_recommend(ts_code);
CREATE INDEX IF NOT EXISTS idx_br_broker ON broker_recommend(broker);
