# 使用示例

## 场景1: 快速监控个人持仓

### 配置监控股票

编辑 `web_app.py`：

```python
WATCHED_STOCKS = [
    '600900',  # 长江电力
    '601985',  # 中国核电
    '000858',  # 五粮液
    '600519',  # 贵州茅台
]
```

### 启动监控

```bash
python3 web_app.py
```

访问 `http://localhost:5000`，即可看到实时价格、涨跌幅排行。

## 场景2: 自动化交易时段监控

### 设置Cron任务

```bash
openclaw cron add \
  --name "A股数据更新" \
  --schedule "*/5 9-15 * * 1-5" \
  --tz "Asia/Shanghai" \
  --session main \
  --payload '{"kind":"systemEvent","text":"cd ~/.openclaw/skills/a-stock-monitor/scripts && python3 smart_market_updater.py"}'
```

系统会在交易时间自动更新数据，非交易时间自动跳过。

## 场景3: 市场情绪追踪

### 获取情绪评分

```python
import requests

response = requests.get('http://localhost:5000/api/market/sentiment')
data = response.json()

print(f"市场情绪: {data['level']} {data['emoji']}")
print(f"评分: {data['score']}/100")
print(f"涨停: {data['stats']['limit_up']}只")
print(f"跌停: {data['stats']['limit_down']}只")
print(f"上涨: {data['stats']['gainers']}只")
print(f"下跌: {data['stats']['losers']}只")
```

### 输出示例

```
市场情绪: 偏乐观 🟢
评分: 57/100
涨停: 15只
跌停: 3只
上涨: 2460只
下跌: 2534只
```

## 场景4: 结合OpenClaw创建智能告警

### 创建告警脚本

创建 `custom_alert.py`：

```python
import requests
import subprocess

def check_alert():
    # 获取监控股票
    response = requests.get('http://localhost:5000/api/stocks')
    stocks = response.json()['data']
    
    alerts = []
    for stock in stocks:
        # 涨跌超过5%告警
        if abs(stock['change_pct']) > 5:
            alerts.append(f"{stock['name']} ({stock['code']}): {stock['change_pct']:+.2f}%")
    
    if alerts:
        message = "🚨 股票异动告警\n\n" + "\n".join(alerts)
        # 发送到飞书
        webhook = "https://open.larksuite.com/open-apis/bot/v2/hook/YOUR_WEBHOOK"
        subprocess.run(['curl', '-X', 'POST', webhook, 
                       '-H', 'Content-Type: application/json',
                       '-d', f'{{"msg_type":"text","content":{{"text":"{message}"}}}}'])

if __name__ == '__main__':
    check_alert()
```

### 设置告警任务

```bash
openclaw cron add \
  --name "股票异动告警" \
  --schedule "*/15 9-15 * * 1-5" \
  --tz "Asia/Shanghai" \
  --session main \
  --payload '{"kind":"systemEvent","text":"python3 /path/to/custom_alert.py"}'
```

## 场景5: 导出每日数据报告

### 创建报告脚本

创建 `daily_report.py`：

```python
import requests
from datetime import datetime

def generate_report():
    # 获取市场情绪
    sentiment = requests.get('http://localhost:5000/api/market/sentiment').json()
    
    # 获取监控股票
    stocks = requests.get('http://localhost:5000/api/stocks').json()['data']
    
    # 生成报告
    report = f"""
# A股监控日报 - {datetime.now().strftime('%Y-%m-%d')}

## 市场情绪
- 评分: {sentiment['score']}/100
- 等级: {sentiment['level']} {sentiment['emoji']}
- 涨停: {sentiment['stats']['limit_up']}只
- 跌停: {sentiment['stats']['limit_down']}只

## 持仓情况
"""
    
    for stock in sorted(stocks, key=lambda x: x['change_pct'], reverse=True):
        report += f"- {stock['name']} ({stock['code']}): ¥{stock['price']} ({stock['change_pct']:+.2f}%)\n"
    
    # 保存报告
    filename = f"report_{datetime.now().strftime('%Y%m%d')}.md"
    with open(filename, 'w') as f:
        f.write(report)
    
    print(f"✅ 报告已生成: {filename}")

if __name__ == '__main__':
    generate_report()
```

### 定时生成报告

```bash
openclaw cron add \
  --name "每日股市报告" \
  --schedule "0 15 * * 1-5" \
  --tz "Asia/Shanghai" \
  --session main \
  --payload '{"kind":"systemEvent","text":"python3 /path/to/daily_report.py"}'
```

每天收盘后自动生成报告。

## 场景6: 多账户监控（分组管理）

### 创建多配置文件

`config_account1.py`:
```python
WATCHED_STOCKS = ['600900', '601985', '600905']  # 账户1持仓
```

`config_account2.py`:
```python
WATCHED_STOCKS = ['000858', '600519', '000333']  # 账户2持仓
```

### 启动多个监控实例

```bash
# 账户1 - 端口5001
PORT=5001 CONFIG=config_account1.py python3 web_app.py &

# 账户2 - 端口5002
PORT=5002 CONFIG=config_account2.py python3 web_app.py &
```

修改 `web_app.py` 支持环境变量：

```python
import os
import importlib

# 读取配置
config_file = os.getenv('CONFIG', 'config')
config = importlib.import_module(config_file.replace('.py', ''))
WATCHED_STOCKS = config.WATCHED_STOCKS

# 读取端口
port = int(os.getenv('PORT', 5000))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=port)
```

## 场景7: 集成到交易策略

### 根据市场情绪调整仓位

```python
import requests

def adjust_position():
    # 获取市场情绪
    sentiment = requests.get('http://localhost:5000/api/market/sentiment').json()
    score = sentiment['score']
    
    # 根据情绪调整仓位
    if score >= 70:
        position = 0.8  # 乐观时高仓位
    elif score >= 50:
        position = 0.5  # 中性时中等仓位
    else:
        position = 0.2  # 悲观时低仓位
    
    print(f"市场情绪: {sentiment['level']} ({score}分)")
    print(f"建议仓位: {position*100}%")
    
    return position

if __name__ == '__main__':
    adjust_position()
```

## 场景8: 历史数据回溯

### 查询历史情绪

```python
import sqlite3
from datetime import datetime, timedelta

def query_history(days=7):
    conn = sqlite3.connect('stock_cache.db')
    cursor = conn.cursor()
    
    # 获取最近N天的数据
    start_date = datetime.now() - timedelta(days=days)
    
    cursor.execute('''
        SELECT date(update_time) as date, 
               AVG(change_pct) as avg_change,
               COUNT(*) as total
        FROM stocks
        WHERE update_time >= ?
        GROUP BY date(update_time)
        ORDER BY date DESC
    ''', (start_date,))
    
    results = cursor.fetchall()
    conn.close()
    
    for date, avg_change, total in results:
        print(f"{date}: 平均涨幅 {avg_change:.2f}%, 有效数据 {total}条")

if __name__ == '__main__':
    query_history(7)
```

## 更多示例

查看 SKILL.md 了解更多配置选项和高级用法。
