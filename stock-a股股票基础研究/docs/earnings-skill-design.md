# 业绩监控 Skill 设计

## 目标
每日由 openclaw 定时触发，执行“全量拉取 → 增量入库 → 对比 → 结构化输出”，供后续 agent 解读并汇报给主 agent。

## 数据源与范围
- 券商一致预期：`report_rc`，使用 `np` 作为市场预期口径
- 业绩预告：`forecast/forecast_vip`
- 业绩快报：`express/express_vip`
- 正式业绩：`income/income_vip`（利润表）
- 预披露时间：`disclosure_date`

## 核心约束
- 定时由 openclaw 负责（例如每日 17:00/22:00）
- 每次执行拉取全量数据
- 同代码不重复，支持修复/更新
- 银行/非银报表结构差异，需要容错

## 存储方案（SQLite）
- 位置：`openclaw-skills/stock-research-group/finance.db`
- 每接口一张表，统一“基础列 + payload_json”
- 基础列示例：`ts_code`、`ann_date`、`end_date`、`report_date`、`org_name`、`source`、`created_at`、`updated_at`
- `payload_json`：保存原始记录，解决字段不一致问题

## 去重与增量更新
- 以每表唯一键做 upsert
  - `report_rc`: `ts_code + report_date + org_name`
  - `forecast/express/income`: `ts_code + ann_date + end_date`
- 更新时记录 `change_type`（新增/修正/上调/下调/不变）与 `change_log`

## 对比逻辑
- 预期口径：对 `report_rc` 的 `np` 计算 `mean/median/max`
- 实际优先级：
  1) 业绩预告 `net_profit_min/max`（用上限）
  2) 业绩快报 `n_income`
  3) 利润表 `n_income`
- 判定规则：实际值 **高于预期上限（max）** 即标记“显著超预期”
- 同时输出与 mean/median/max 的差异比例

## 输出
- 结构化 JSON，供解读 agent 使用
- 输出示例字段：
  - `run_meta`：执行时间、成功/失败统计
  - `summary`：新增/更新/异常数量
  - `alerts`：超预期列表
  - `changes`：券商预期上调/下调列表

## 健壮性
- 统一重试与限频处理
- 失败任务记录到 `job_runs`，下次补拉
- 字段缺失不影响入库，仅影响对比
- 幂等执行，重复运行不产生重复数据
