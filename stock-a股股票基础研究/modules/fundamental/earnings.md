# 业绩监控

拉取业绩预告/快报/正式业绩，对比券商盈利预测，生成超预期/符合/低于预期告警。

## 使用

```bash
cd stock-research-group

# 1. 拉取数据（自动识别 period）→ 对比 → 输出
python analyzers/earnings/ingest.py
python analyzers/earnings/compare.py
python analyzers/earnings/pipeline.py

# 2. 生成报告（文字 + CSV）
python interpreters/earnings/summary.py
```

## 增量拉取

```bash
# 每日 report_rc（支持分页，解决超3000条限制）
python fetchers/report_rc_daily.py --date 20260203
python fetchers/report_rc_daily.py --days 3
```

## 定时任务

每日 17:00、22:00 自动执行 `ingest → compare → run`（见 `jobs.json`）。

## 输出

| 文件 | 说明 |
|------|------|
| `output/report_YYYYMMDD.txt` | 文字报告（按超预期/符合/低于分类） |
| `output/alerts_YYYYMMDD.csv` | CSV 存档（含预期上下限、偏差） |
