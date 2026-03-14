PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS stk_factor (
  ts_code TEXT NOT NULL,
  trade_date TEXT NOT NULL,
  close REAL,
  close_hfq REAL,
  close_qfq REAL,
  pct_chg REAL,
  vol REAL,
  amount REAL,
  turnover_rate REAL,
  pe_ttm REAL,
  pb REAL,
  total_mv REAL,
  circ_mv REAL,
  macd_dif_qfq REAL,
  macd_dea_qfq REAL,
  macd_qfq REAL,
  kdj_k_qfq REAL,
  kdj_d_qfq REAL,
  kdj_qfq REAL,
  rsi_qfq_6 REAL,
  rsi_qfq_12 REAL,
  rsi_qfq_24 REAL,
  boll_upper_qfq REAL,
  boll_mid_qfq REAL,
  boll_lower_qfq REAL,
  ma_qfq_5 REAL,
  ma_qfq_10 REAL,
  ma_qfq_20 REAL,
  ma_qfq_60 REAL,
  ma_qfq_250 REAL,
  source TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(ts_code, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_stk_factor_ts_code ON stk_factor(ts_code);
CREATE INDEX IF NOT EXISTS idx_stk_factor_trade_date ON stk_factor(trade_date);
