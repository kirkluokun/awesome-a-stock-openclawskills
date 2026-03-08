---
name: gangtise-kb
description: 岗底斯开放平台投研数据服务。提供知识库搜索（券商研报、公告、纪要）、公司盈利预测、经济数据指标查询、电话会议列表、研报溯源下载等功能。当用户询问股票、公司、行业、宏观经济数据、研究报告时使用。
---

# Gangtise Knowledge Base Skill

冈特斯开放平台投研数据技能，提供知识库搜索、盈利预测、经济指标查询、电话会议、研报溯源下载等功能。

## Credential Configuration

凭证加载优先级（从高到低）：

1. **环境变量**（推荐）
   ```bash
   export GANGTISE_ACCESS_KEY="your-access-key"
   export GANGTISE_SECRET_KEY="your-secret-key"
   ```

2. **`.env` 文件**（项目根目录）
   ```
   GANGTISE_ACCESS_KEY=your-access-key
   GANGTISE_SECRET_KEY=your-secret-key
   ```

3. **`config.json`**（兼容旧配置，不推荐）

交互式配置（自动写入 `.env`）：
```bash
python3 scripts/configure.py
```

API 凭证获取地址: https://open.gangtise.com

## Authentication

- OAuth2 认证：Access Key + Secret Key → `loginV2` → accessToken
- V2 接口返回的 accessToken **已携带 Bearer 前缀**
- Token 有效期 3600 秒，脚本自动缓存到 `.token_cache`，1 小时内复用

## Available Scripts

### 知识库搜索 (query_kb.py)

```bash
python3 scripts/query_kb.py "比亚迪最新消息"
python3 scripts/query_kb.py "特斯拉" --type 10,40 --top 5 --days 180
python3 scripts/query_kb.py "宁德时代" --json
```

参数：`--type` 资源类型 | `--top` 返回数量(默认20,最大20) | `--days` 搜索天数 | `--json` 原始输出

### 盈利预测 (forecast.py)

```bash
python3 scripts/forecast.py 600519.SH
python3 scripts/forecast.py 000858.SZ --json
```

返回历年实际值(A) + 未来预测值(E)，含归母净利润、EPS、PE、ROE、毛利率等。

### 经济数据指标 (indicator.py)

```bash
python3 scripts/indicator.py "比亚迪仰望销量"
python3 scripts/indicator.py "2024年GDP增速" --stream
python3 scripts/indicator.py "光伏行业产能" --json
```

AI Agent 查询行业数据、宏观经济、公司经营指标。非流式约等待 10 秒。

### 电话会议列表 (meeting_list.py)

```bash
python3 scripts/meeting_list.py
python3 scripts/meeting_list.py --stock 600519.SH
python3 scripts/meeting_list.py --topic 银行 --size 20 --days 30
```

参数：`--stock` 股票过滤 | `--topic` 主题过滤 | `--days` 天数 | `--page`/`--size` 分页

### 溯源下载 (download_resource.py)

```bash
python3 scripts/download_resource.py --type 10 --id SOURCE_ID
python3 scripts/download_resource.py --type 10 --id SOURCE_ID --output report.pdf
```

通过 sourceId 下载研报 PDF 原文或获取第三方链接。type 40 不支持。

### Token 获取 (get_token.py)

```bash
python3 scripts/get_token.py
```

## API Endpoints

| 功能 | 方法 | 路径 |
|------|------|------|
| 认证 | POST | `/application/auth/oauth/open/loginV2` |
| 知识库搜索 | POST | `/application/open-data/ai/search/knowledge/batch` |
| 盈利预测 | POST | `/application/open-data/report/forecast/info` |
| 指标查询 | POST | `/application/open-ai/ai/search/indicator` |
| 会议列表 | POST | `/application/open-meeting/cnfr/getList` |
| 溯源下载 | GET | `/application/open-data/ai/resource/download` |

## Resource Types

| 代码 | 类型 | 搜索 | 溯源下载 |
|------|------|------|----------|
| 10 | 券商研究报告 | ✅ | ✅ (部分券商有白名单限制) |
| 20 | 内部研究报告 | ✅ | ✅ |
| 40 | 首席分析师观点 | ✅ | ❌ |
| 50 | 公司公告 | ✅ | ✅ |
| 60 | 会议平台纪要 | ✅ | ✅ |
| 70 | 调研纪要公告 | ✅ | ✅ |
| 80 | 网络资源纪要 | ✅ | ✅ (返回 URL) |
| 90 | 产业公众号 | ✅ | ✅ (返回 URL) |

## Knowledge Names

- `system_knowledge_doc` — 系统库（默认）
- `tenant_knowledge_doc` — 租户库

## 安全说明

- `.env`、`config.json`、`.token_cache` 权限自动设为 600
- 请勿将上述文件提交到版本控制
