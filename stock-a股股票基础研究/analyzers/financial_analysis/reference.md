# 财务分析参考文档

## 基础指标定义

### 资产类指标
- **货币资金** (`money_cap`): 公司持有的现金及银行存款
- **应收账款** (`accounts_receiv`): 公司因销售商品、提供服务等应收取的款项
- **存货** (`inventories`): 公司持有的商品、在产品、原材料等
- **流动资产合计** (`total_cur_assets`): 一年内可变现的资产总和
- **固定资产** (`fix_assets`): 公司长期使用的有形资产
- **总资产** (`total_assets`): 公司拥有的全部资产

### 负债类指标
- **短期借款** (`st_borr`): 一年内需要偿还的借款
- **应付账款** (`acct_payable`): 公司因采购商品、接受服务等应支付的款项
- **流动负债合计** (`total_cur_liab`): 一年内需要偿还的负债总和
- **总负债** (`total_liab`): 公司需要偿还的全部负债

### 权益类指标
- **未分配利润** (`undistr_porfit`): 公司累计未分配的利润
- **股东权益合计** (`total_hldr_eqy_exc_min_int`): 股东拥有的净资产

## 常用财务比率

### 偿债能力指标
- **流动比率** = 流动资产合计 / 流动负债合计
  - 标准值: > 2 较好，< 1 有风险
- **速动比率** = (流动资产合计 - 存货) / 流动负债合计
  - 标准值: > 1 较好
- **资产负债率** = 总负债 / 总资产
  - 标准值: < 60% 较好，> 80% 风险较高

### 资产结构指标
- **存货占比** = 存货 / 总资产
- **应收账款占比** = 应收账款 / 总资产
- **固定资产占比** = 固定资产 / 总资产

## 常见问题分析模板

### "xx公司的存货如何"
1. **查询数据**: 获取存货金额 (`inventories`)
2. **计算占比**: 存货 / 总资产
3. **趋势分析**: 对比最近4个季度的存货变化
4. **风险评估**: 
   - 存货占比过高（>30%）可能积压
   - 存货快速增长但收入未增长需警惕

### "xx公司的偿债能力"
1. **查询数据**: 流动资产、流动负债、总负债、总资产
2. **计算比率**: 流动比率、速动比率、资产负债率
3. **评估**: 对比行业标准值

### "xx公司的资产结构"
1. **查询数据**: 各类资产金额
2. **计算占比**: 各类资产 / 总资产
3. **分析**: 资产配置是否合理

## 数据获取方法

### 查询单字段
```python
from analyzers.balancesheet.search import get_field_value
value = get_field_value('000001.SZ', 'inventories')
```

### 查询完整记录
```python
from analyzers.balancesheet.search import get_balancesheet
record = get_balancesheet('000001.SZ', end_date='20241231')
```

### 查询历史数据
```python
from analyzers.balancesheet.search import get_balancesheet_history
records = get_balancesheet_history('000001.SZ', limit=4)
```

### 计算同比/环比
```python
# 获取两年数据
records = get_balancesheet_history('000001.SZ', limit=8)

# 计算同比（去年同期）
if len(records) >= 4:
    current = records[0]['inventories']
    last_year = records[4]['inventories']
    yoy_growth = (current - last_year) / last_year * 100
```

## 注意事项

1. **公司类型差异**: 银行/保险/证券的资产负债表结构不同，查询时注意 `comp_type`
2. **报告类型**: 默认使用 `report_type=1`（合并报表），其他类型需明确指定
3. **数据完整性**: 某些字段可能为空（如银行没有"存货"），需要容错处理
4. **时间范围**: 计算同比需要至少4个季度数据，建议拉取N+1年数据
