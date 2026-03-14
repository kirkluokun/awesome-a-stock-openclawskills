PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS fina_mainbz (
  ts_code TEXT NOT NULL,
  end_date TEXT NOT NULL,
  bz_item TEXT NOT NULL,
  bz_type TEXT,
  bz_sales REAL,
  bz_profit REAL,
  bz_cost REAL,
  curr_type TEXT,
  source TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(ts_code, end_date, bz_item)
);

CREATE INDEX IF NOT EXISTS idx_fina_mainbz_ts_code ON fina_mainbz(ts_code);
CREATE INDEX IF NOT EXISTS idx_fina_mainbz_end_date ON fina_mainbz(end_date);
CREATE INDEX IF NOT EXISTS idx_fina_mainbz_ts_end ON fina_mainbz(ts_code, end_date);
