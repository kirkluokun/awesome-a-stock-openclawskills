PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS cashflow (
  ts_code TEXT NOT NULL,
  ann_date TEXT,
  end_date TEXT NOT NULL,
  n_cashflow_act REAL,
  n_cashflow_inv REAL,
  n_cashflow_fin REAL,
  c_cash_equ_beg_period REAL,
  c_cash_equ_end_period REAL,
  c_inf_fr_operate_a REAL,
  c_outf_operate_a REAL,
  source TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(ts_code, end_date)
);

CREATE INDEX IF NOT EXISTS idx_cashflow_ts_code ON cashflow(ts_code);
CREATE INDEX IF NOT EXISTS idx_cashflow_end_date ON cashflow(end_date);
CREATE INDEX IF NOT EXISTS idx_cashflow_ts_end ON cashflow(ts_code, end_date);
