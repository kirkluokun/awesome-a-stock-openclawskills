# A股监控系统 - 安装指南

## 系统要求

- Python 3.9+
- pip3
- OpenClaw Gateway (可选，用于自动化任务)

## 安装步骤

### 1. 安装Python依赖

```bash
pip3 install akshare flask ccxt
```

### 2. 初始化数据库

首次运行会自动创建SQLite数据库：

```bash
cd <skill-path>/scripts
python3 stock_cache_db.py
```

### 3. 导入演示数据（可选）

非交易时间可以先导入演示数据进行测试：

```python
import sqlite3
from datetime import datetime

demo_stocks = [
    ('600900', '长江电力', 26.85, -0.52, 158900000, 4267850000),
    ('601985', '中国核电', 9.32, -0.64, 256800000, 2393760000),
    ('600905', '三峡能源', 8.45, -0.71, 442100000, 3735645000),
]

conn = sqlite3.connect('stock_cache.db')
cursor = conn.cursor()

for code, name, price, change_pct, volume, amount in demo_stocks:
    cursor.execute('''
        UPDATE stocks 
        SET price = ?, change_pct = ?, volume = ?, amount = ?, update_time = ?
        WHERE code = ?
    ''', (price, change_pct, volume, amount, datetime.now(), code))

conn.commit()
conn.close()
```

### 4. 配置监控股票

编辑 `web_app.py`：

```python
WATCHED_STOCKS = [
    '600900',  # 长江电力
    '601985',  # 中国核电
    '600905',  # 三峡能源
    # 添加你想监控的股票代码
]
```

### 5. 启动Web服务

```bash
python3 web_app.py
```

访问 `http://localhost:5000`

### 6. 设置自动化任务（可选）

使用OpenClaw Cron定时更新数据：

```bash
openclaw cron add \
  --name "A股全市场数据更新" \
  --schedule "*/5 9-15 * * 1-5" \
  --tz "Asia/Shanghai" \
  --session main \
  --payload '{"kind":"systemEvent","text":"cd <skill-path>/scripts && python3 smart_market_updater.py"}'
```

## 验证安装

### 测试数据获取

```bash
python3 update_all_market_data.py
```

应该看到：
```
🔄 开始获取全市场A股数据...
✅ 获取成功: 5810 只股票
💾 保存到数据库...
✅ 数据更新完成!
```

### 测试市场情绪

```bash
python3 market_sentiment.py
```

应该看到JSON格式的情绪评分。

### 测试交易时间判断

```bash
python3 is_trading_time.py
```

显示当前是否为交易时间。

## 常见问题

### Q: ModuleNotFoundError: No module named 'akshare'
A: 运行 `pip3 install akshare`

### Q: 端口5000被占用
A: 修改 `web_app.py` 中的端口号：
```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)  # 改为5001
```

### Q: 数据全部显示为null
A: 非交易时间akshare返回空数据，等待交易时间或导入演示数据

### Q: Web界面一直转圈
A: 数据库无有效数据，运行 `python3 update_all_market_data.py`

## 卸载

```bash
# 删除技能目录
rm -rf <skill-path>

# 删除数据库（可选）
rm <skill-path>/scripts/stock_cache.db

# 删除Cron任务
openclaw cron list  # 找到任务ID
openclaw cron remove <job-id>
```

## 下一步

- 查看 SKILL.md 了解详细使用方法
- 查看 API.md 了解API接口文档
- 查看 EXAMPLES.md 了解使用示例
