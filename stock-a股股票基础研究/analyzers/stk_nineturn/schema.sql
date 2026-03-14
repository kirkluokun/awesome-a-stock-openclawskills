PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS stk_nineturn (
  ts_code TEXT NOT NULL,
  trade_date TEXT NOT NULL,
  freq TEXT NOT NULL DEFAULT 'daily',
  open REAL,
  high REAL,
  low REAL,
  close REAL,
  vol REAL,
  amount REAL,
  up_count INTEGER,
  down_count INTEGER,
  nine_up_turn TEXT,
  nine_down_turn TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(ts_code, trade_date, freq)
);

CREATE INDEX IF NOT EXISTS idx_nineturn_ts_code ON stk_nineturn(ts_code);
CREATE INDEX IF NOT EXISTS idx_nineturn_trade_date ON stk_nineturn(trade_date);
CREATE INDEX IF NOT EXISTS idx_nineturn_signal ON stk_nineturn(nine_up_turn, nine_down_turn);
