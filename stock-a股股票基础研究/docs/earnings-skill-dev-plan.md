# 业绩监控 Skill 开发计划

## 目标
实现一个每日可由 openclaw 调度的流水线，完成拉取、入库、对比、输出 JSON，并为后续解读 agent 提供输入。

## 任务分解

### 1. 数据库与表结构
- 新建 `finance.db`
- 建表：`report_rc`、`forecast`、`express`、`income`、`disclosure_date`、`alerts`、`job_runs`
- 每表采用“基础列 + payload_json”方案
- 定义唯一键与 upsert 逻辑

### 2. 拉取与入库
- 封装统一拉取入口（全量）
- 为每个接口写入库函数
- 处理字段缺失与类型转换
- 写入 `job_runs` 记录执行状态

### 3. 对比与告警
- 聚合预期：mean/median/max
- 实际值优先级逻辑
- 生成 `alerts` 表数据
- 记录 `changes`（券商预期上调/下调/修正）

### 4. 输出 JSON
- 结构化输出文件到 `scripts/output/`
- 包含 `run_meta/summary/alerts/changes`

### 5. 解读 Agent 对接
- 预留一个入口读取 JSON
- 生成精炼文本（由另一个 agent 执行）

## 验证
- 本地跑一次全量流程
- 核对表行数与 JSON 输出
