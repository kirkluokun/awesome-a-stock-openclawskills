PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS balancesheet (
  ts_code TEXT NOT NULL,
  ann_date TEXT,
  f_ann_date TEXT,
  end_date TEXT NOT NULL,
  report_type TEXT,
  comp_type TEXT,
  end_type TEXT,
  total_share REAL,
  money_cap REAL,
  accounts_receiv REAL,
  inventories REAL,
  total_cur_assets REAL,
  fix_assets REAL,
  total_assets REAL,
  st_borr REAL,
  acct_payable REAL,
  total_cur_liab REAL,
  total_liab REAL,
  undistr_porfit REAL,
  total_hldr_eqy_exc_min_int REAL,
  source TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(ts_code, end_date, report_type)
);

CREATE INDEX IF NOT EXISTS idx_balancesheet_ts_code ON balancesheet(ts_code);
CREATE INDEX IF NOT EXISTS idx_balancesheet_end_date ON balancesheet(end_date);
CREATE INDEX IF NOT EXISTS idx_balancesheet_ts_end ON balancesheet(ts_code, end_date);
