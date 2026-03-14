-- analyzers/stk_surv/schema.sql
CREATE TABLE IF NOT EXISTS stk_surv_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_code TEXT NOT NULL,
    name TEXT NOT NULL,
    surv_date TEXT NOT NULL,
    rece_place TEXT,
    rece_mode TEXT,
    comp_rece TEXT,
    content TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ts_code, surv_date)
);

CREATE INDEX IF NOT EXISTS idx_surv_event_ts_code ON stk_surv_event(ts_code);
CREATE INDEX IF NOT EXISTS idx_surv_event_date ON stk_surv_event(surv_date);
CREATE INDEX IF NOT EXISTS idx_surv_event_name ON stk_surv_event(name);

CREATE TABLE IF NOT EXISTS stk_surv_participant (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    fund_visitors TEXT,
    rece_org TEXT,
    org_type TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES stk_surv_event(id),
    UNIQUE(event_id, fund_visitors, rece_org)
);

CREATE INDEX IF NOT EXISTS idx_surv_part_event_id ON stk_surv_participant(event_id);
CREATE INDEX IF NOT EXISTS idx_surv_part_org ON stk_surv_participant(rece_org);
CREATE INDEX IF NOT EXISTS idx_surv_part_visitor ON stk_surv_participant(fund_visitors);
