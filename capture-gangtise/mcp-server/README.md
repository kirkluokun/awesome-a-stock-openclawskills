# Gangtise KB MCP Server

冈特斯开放平台 MCP 服务，为 equity-research 等投研技能提供研报/纪要/预测数据。

## 架构

```
capture-gangtise-kb/
├── scripts/          ← 原有脚本（不动）
│   ├── _client.py    ← HTTP 客户端 + Token 缓存
│   ├── query_kb.py
│   ├── forecast.py
│   ├── indicator.py
│   ├── meeting_list.py
│   └── download_resource.py
└── mcp-server/       ← MCP 包装层（本目录）
    ├── server.py     ← FastMCP server，直接 import ../scripts/
    ├── pyproject.toml
    └── .venv/        ← 仅含 fastmcp
```

server.py 直接 import `../scripts/` 里的函数，不重复实现任何逻辑。

## 工具列表

| Tool | 说明 | 主要参数 |
|------|------|---------|
| `gangtise_kb_search` | 知识库语义搜索（研报/公告/纪要） | `query`, `resource_types`, `top`, `days` |
| `gangtise_forecast` | 公司盈利预测（EPS/PE/ROE） | `stock_code` |
| `gangtise_indicator` | 行业/宏观数据 AI 查询 | `text` |
| `gangtise_meetings` | 电话会议/路演纪要列表 | `stock`, `topic`, `days` |
| `gangtise_download_url` | 研报溯源下载链接 | `resource_type`, `source_id` |

### resource_types 对照

| 代码 | 类型 |
|------|------|
| 10 | 券商研报 |
| 20 | 内部研报 |
| 40 | 分析师观点（不支持下载）|
| 50 | 公告 |
| 60 | 会议纪要 |
| 70 | 调研纪要 |
| 80 | 网络资源 |
| 90 | 产业公众号 |

## 凭证

密钥存放于 `../env`（父目录），通过 `GANGTISE_ACCESS_KEY` / `GANGTISE_SECRET_KEY` 环境变量注入，已在 `~/.claude.json` 全局 mcpServers 中配置。

## 依赖安装

```bash
cd mcp-server
uv venv --python 3.11
uv pip install fastmcp --python .venv/bin/python
```

## 全局注册

已注册为 `gangtise-kb`，重启 Claude Code 后生效。
