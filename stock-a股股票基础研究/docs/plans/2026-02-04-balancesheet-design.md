# 资产负债表数据获取与分析设计

## 目标

实现资产负债表数据的获取、存储、查询和基础财务分析功能，支持用户查询如"xx公司的存货如何"等基础财务问题。

## 数据源

- **接口**: `balancesheet` / `balancesheet_vip` (Tushare)
- **积分要求**: 2000积分（单公司）/ 5000积分（全量VIP）
- **参数**: `ts_code`, `ann_date`, `start_date`, `end_date`, `period`, `report_type`, `comp_type`
- **字段数**: 约160个字段

## 存储方案

### 数据库表结构

**表名**: `balancesheet`

**基础列**（常用字段，支持直接SQL查询）:
- `ts_code` TEXT NOT NULL - 股票代码
- `ann_date` TEXT - 公告日期
- `f_ann_date` TEXT - 实际公告日期
- `end_date` TEXT NOT NULL - 报告期
- `report_type` TEXT - 报表类型（1合并报表，2单季合并等）
- `comp_type` TEXT - 公司类型（1一般工商业，2银行，3保险，4证券）
- `end_type` TEXT - 报告期类型
- `total_share` REAL - 期末总股本
- `money_cap` REAL - 货币资金
- `accounts_receiv` REAL - 应收账款
- `inventories` REAL - 存货
- `total_cur_assets` REAL - 流动资产合计
- `fix_assets` REAL - 固定资产
- `total_assets` REAL - 资产总计
- `st_borr` REAL - 短期借款
- `acct_payable` REAL - 应付账款
- `total_cur_liab` REAL - 流动负债合计
- `total_liab` REAL - 负债合计
- `undistr_porfit` REAL - 未分配利润
- `total_hldr_eqy_exc_min_int` REAL - 股东权益合计（不含少数股东权益）
- `source` TEXT - 数据来源
- `payload_json` TEXT NOT NULL - 完整JSON数据（所有160个字段）
- `created_at` TEXT NOT NULL - 创建时间
- `updated_at` TEXT NOT NULL - 更新时间

**唯一约束**: `UNIQUE(ts_code, ann_date, end_date, report_type)`

**索引**:
- `idx_balancesheet_ts_code` ON balancesheet(ts_code)
- `idx_balancesheet_end_date` ON balancesheet(end_date)
- `idx_balancesheet_ts_end` ON balancesheet(ts_code, end_date)

### 存储策略说明

- **基础列**: 提取20个最常用字段，支持直接SQL查询和排序
- **payload_json**: 存储完整API返回数据，确保不丢失任何字段
- **灵活性**: 不同公司类型（银行/保险/证券）字段差异大，JSON存储保证兼容性

## 数据获取层 (fetchers)

### 文件结构

```
fetchers/
├── balancesheet.py          # 资产负债表数据获取
└── _shared/
    └── db.py                # 数据库工具（复用earnings层）
```

### 核心函数

**`fetch_balancesheet()`**
- 调用 `finance_basic.py` 中的 `fetch_balancesheet()` 获取数据
- 处理API错误和限流
- 返回 DataFrame

**`upsert_balancesheet()`**
- 将数据入库，使用 upsert 逻辑
- 唯一键: `(ts_code, ann_date, end_date, report_type)`
- 提取常用字段到基础列，完整数据存入 `payload_json`

## 数据分析层 (analyzers)

### 文件结构

```
analyzers/
├── balancesheet/
│   ├── _shared/
│   │   └── db.py           # 数据库连接和工具函数
│   ├── schema.sql          # 表结构定义
│   ├── search.py           # 数据查询功能
│   └── pipeline.py         # 流程入口（CLI）
└── financial_analysis/
    └── reference.md         # 财务分析参考文档
```

### 查询功能 (search.py)

**`get_balancesheet()`**
- 查询单条记录：`ts_code` + `end_date` + `report_type`（可选）
- 返回基础列 + 解析后的完整字段字典

**`get_balancesheet_history()`**
- 查询历史记录：`ts_code` + `start_date` + `end_date` + `report_type`（可选）
- 返回按 `end_date` 排序的列表
- 支持指定报告期数量（如最近4个季度）

**`get_field_value()`**
- 查询特定字段值：`ts_code` + `field_name` + `end_date`
- 自动从基础列或 payload_json 中提取
- 支持字段别名映射（如"存货" → "inventories"）

**`search_by_field()`**
- 跨公司查询：`field_name` + `end_date` + 排序条件
- 返回所有公司的该字段值，按金额排序
- 支持过滤条件（如 `comp_type`）

### 自动拉取策略

**触发条件**:
- 查询时数据库无数据
- 查询需要的历史数据不足（如需要4年数据但只有2年）

**拉取策略**:
- **默认**: 拉取最近4个季度（1年）
- **历史需求**: 如果查询需要N年数据，自动拉取 N+1 年（如3年同比需要4年）
- **全量拉取**: 支持手动触发全量拉取（用于初始化）

**实现逻辑**:
```python
def ensure_data(ts_code: str, end_date: str = None, years: int = 1):
    """确保有足够的数据"""
    existing = get_balancesheet_history(ts_code, end_date=end_date)
    if len(existing) < years * 4:  # 需要N年数据
        # 计算需要拉取的日期范围
        start_date = calculate_start_date(end_date, years + 1)
        fetch_balancesheet(ts_code, start_date=start_date, end_date=end_date)
```

## 财务分析参考文档

### 文件位置

`analyzers/financial_analysis/reference.md`

### 内容结构

1. **基础指标定义**
   - 资产类指标（存货、应收账款、固定资产等）
   - 负债类指标（短期借款、应付账款等）
   - 权益类指标（股东权益、未分配利润等）

2. **常用财务比率**
   - 流动比率 = 流动资产 / 流动负债
   - 速动比率 = (流动资产 - 存货) / 流动负债
   - 资产负债率 = 总负债 / 总资产
   - 存货周转率 = 营业成本 / 平均存货（需要利润表数据）

3. **常见问题模板**
   - "xx公司的存货如何" → 检查：存货金额、占总资产比例、历史趋势
   - "xx公司的偿债能力" → 计算：流动比率、速动比率、资产负债率
   - "xx公司的资产结构" → 分析：流动资产/非流动资产比例、固定资产占比

4. **数据获取指引**
   - 如何从数据库查询数据
   - 如何解析 payload_json 获取完整字段
   - 如何计算同比/环比增长率

## 数据流

```
用户查询 "比亚迪的存货如何"
    ↓
analyzers/balancesheet/search.py
    ↓
检查数据库是否有数据
    ↓ (无数据)
fetchers/balancesheet.py
    ↓
Tushare API
    ↓
入库 (analyzers/balancesheet/_shared/db.py)
    ↓
查询并返回数据
    ↓
基础分析（参考 reference.md）
    ↓
返回结果
```

## 实现优先级

### Phase 1: 数据获取与存储
1. ✅ 创建 `schema.sql`
2. ✅ 实现 `fetchers/balancesheet.py`
3. ✅ 实现数据库入库逻辑
4. ✅ 测试单公司数据拉取

### Phase 2: 基础查询
1. ✅ 实现 `analyzers/balancesheet/search.py`
2. ✅ 实现自动拉取逻辑
3. ✅ 创建 `pipeline.py` CLI入口
4. ✅ 测试查询功能

### Phase 3: 财务分析参考
1. ✅ 创建 `reference.md`
2. ✅ 实现基础字段查询
3. ✅ 实现简单计算（同比、环比）

### Phase 4: 高级分析（未来）
- 跨表分析（结合利润表、现金流量表）
- 行业对比
- 风险评估模型

## 注意事项

1. **公司类型差异**: 银行/保险/证券字段差异大，查询时需要考虑 `comp_type`
2. **报告类型**: `report_type=1` 为合并报表（默认），其他类型需明确指定
3. **数据完整性**: 某些字段可能为空（如银行没有"存货"），需要容错处理
4. **性能优化**: 常用字段用基础列，避免频繁解析JSON
5. **历史数据**: 支持按需拉取，避免一次性拉取过多数据
