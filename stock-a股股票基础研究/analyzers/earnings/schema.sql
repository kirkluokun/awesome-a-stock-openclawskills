PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS report_rc (
  ts_code TEXT NOT NULL,
  report_date TEXT NOT NULL,
  org_name TEXT NOT NULL,
  period TEXT,
  np REAL,
  eps REAL,
  quarter TEXT,
  source TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  change_type TEXT,
  change_log TEXT,
  UNIQUE (ts_code, report_date, org_name, period)
);

CREATE TABLE IF NOT EXISTS forecast (
  ts_code TEXT NOT NULL,
  ann_date TEXT,
  end_date TEXT NOT NULL,
  net_profit_min REAL,
  net_profit_max REAL,
  type TEXT,
  source TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  change_type TEXT,
  change_log TEXT,
  UNIQUE (ts_code, ann_date, end_date)
);

CREATE TABLE IF NOT EXISTS express (
  ts_code TEXT NOT NULL,
  ann_date TEXT,
  end_date TEXT NOT NULL,
  n_income REAL,
  source TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  change_type TEXT,
  change_log TEXT,
  UNIQUE (ts_code, ann_date, end_date)
);

CREATE TABLE IF NOT EXISTS income (
  ts_code TEXT NOT NULL,
  ann_date TEXT,
  end_date TEXT NOT NULL,
  n_income REAL,
  report_type TEXT,
  comp_type TEXT,
  source TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  change_type TEXT,
  change_log TEXT,
  UNIQUE (ts_code, ann_date, end_date)
);

CREATE TABLE IF NOT EXISTS disclosure_date (
  ts_code TEXT NOT NULL,
  end_date TEXT NOT NULL,
  pre_date TEXT,
  ann_date TEXT,
  actual_date TEXT,
  source TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  change_type TEXT,
  change_log TEXT,
  UNIQUE (ts_code, end_date)
);

CREATE TABLE IF NOT EXISTS alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts_code TEXT NOT NULL,
  end_date TEXT NOT NULL,
  actual_value REAL NOT NULL,
  expected_mean REAL,
  expected_median REAL,
  expected_max REAL,
  delta_mean REAL,
  delta_median REAL,
  delta_max REAL,
  source TEXT NOT NULL,
  created_at TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  UNIQUE (ts_code, end_date, source, actual_value)
);

CREATE TABLE IF NOT EXISTS job_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_at TEXT NOT NULL,
  status TEXT NOT NULL,
  error TEXT,
  meta_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_report_rc_ts_code ON report_rc (ts_code);
CREATE INDEX IF NOT EXISTS idx_report_rc_period ON report_rc (period);
CREATE INDEX IF NOT EXISTS idx_forecast_ts_code ON forecast (ts_code);
CREATE INDEX IF NOT EXISTS idx_express_ts_code ON express (ts_code);
CREATE INDEX IF NOT EXISTS idx_income_ts_code ON income (ts_code);
CREATE INDEX IF NOT EXISTS idx_disclosure_ts_code ON disclosure_date (ts_code);
CREATE INDEX IF NOT EXISTS idx_alerts_ts_code ON alerts (ts_code);
