PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS fina_indicator (
  ts_code TEXT NOT NULL,
  ann_date TEXT,
  end_date TEXT NOT NULL,
  roe REAL,
  roa REAL,
  grossprofit_margin REAL,
  netprofit_margin REAL,
  current_ratio REAL,
  quick_ratio REAL,
  debt_to_assets REAL,
  assets_turn REAL,
  inv_turn REAL,
  ar_turn REAL,
  eps REAL,
  profit_to_gr REAL,
  source TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(ts_code, end_date)
);

CREATE INDEX IF NOT EXISTS idx_fina_indicator_ts_code ON fina_indicator(ts_code);
CREATE INDEX IF NOT EXISTS idx_fina_indicator_end_date ON fina_indicator(end_date);
CREATE INDEX IF NOT EXISTS idx_fina_indicator_ts_end ON fina_indicator(ts_code, end_date);
