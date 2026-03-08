# 🤖 Awesome A-Stock OpenClaw Skills

精选的 OpenClaw / Claude 代理技能集合，专注于 A 股投资研究与分析。

## 什么是 OpenClaw Skills？

OpenClaw Skills 是基于 Markdown 的 AI 代理技能定义文件，可以扩展 Claude 等 AI 助手的能力，使其具备专业的金融分析、数据获取、研究协作等功能。

## 技能列表

### 🤖 Agent — 智能体增强
| 技能               | 描述                |
| ------------------ | ------------------- |
| `agent-evolver`    | 技能进化器          |
| `agent-idea-coach` | 创意教练            |
| `agent-personas`   | 角色扮演/多人格代理 |

### 📡 Capture — 数据抓取
| 技能                      | 描述                |
| ------------------------- | ------------------- |
| `capture-arxiv-watcher`   | ArXiv 论文监控      |
| `capture-blogwatcher`     | 博客/RSS 监控       |
| `capture-gangtise-kb`     | 港股通知识库采集    |
| `capture-grok-search`     | Grok 搜索抓取       |
| `capture-jiucai`          | 韭菜公社数据采集    |
| `capture-openclaw-serper` | Serper 搜索引擎集成 |
| `capture-reddit-search`   | Reddit 搜索         |

### 💻 Code — 代码工具
| 技能                | 描述         |
| ------------------- | ------------ |
| `code-coding-agent` | 编程辅助代理 |

### 📊 Data — 数据分析
| 技能                                      | 描述             |
| ----------------------------------------- | ---------------- |
| `data-backtesting-trading-strategies`     | 交易策略回测     |
| `data-financial-timeseries-data-analysis` | 金融时间序列分析 |
| `data-visualization`                      | 数据可视化       |

### 🔬 Deep — 深度研究
| 技能                       | 描述                |
| -------------------------- | ------------------- |
| `deep-fact-checker`        | 事实核查            |
| `deep-gemini-deepresearch` | Gemini 深度研究代理 |
| `deep-research-company`    | 公司深度研究        |

### 🧠 Memory — 记忆与认知
| 技能                             | 描述         |
| -------------------------------- | ------------ |
| `memory-cognitive-memory`        | 认知记忆系统 |
| `memory-ontology-0.1.2`          | 本体知识图谱 |
| `memory-self-improving-1.0.11`   | 自我改进记忆 |
| `memory-thinking-model-enhancer` | 思维模型增强 |

### 📰 News — 新闻聚合
| 技能                       | 描述          |
| -------------------------- | ------------- |
| `news-aggregator-skill`    | 新闻聚合器    |
| `news-bbc-news`            | BBC 新闻      |
| `news-cctv-news-fetcher`   | CCTV 新闻抓取 |
| `news-daily-ai-news-skill` | 每日 AI 新闻  |
| `news-newsapi-search`      | NewsAPI 搜索  |
| `news-summary`             | 新闻摘要      |

### 📈 Stock — 股票工具
| 技能                       | 描述                                    |
| -------------------------- | --------------------------------------- |
| `stock-trade-journal`      | 交易日志（Markdown + SQLite 双写）      |
| `stock-trade-signal-1.0.0` | 买卖信号（全球 37,565+ 标的）           |
| `stock-tushare-pro-mcp`    | Tushare Pro MCP（158+ 接口，A/港/美股） |

### 🐝 Swarm — 多智能体协作
| 技能                     | 描述                              |
| ------------------------ | --------------------------------- |
| `swarm-research-tracker` | 自主研究代理状态追踪              |
| `swarm-war-room`         | 多代理作战室（头脑风暴/系统设计） |

## 使用方式

将技能文件夹复制到你的 Claude 项目的 `.agent/skills/` 目录下即可使用。

```bash
# 示例：安装 Tushare MCP 技能
cp -r stock-tushare-pro-mcp /path/to/your-project/.agent/skills/
```

> **注意：** 部分技能需要配置 API key（如 `stock-tushare-pro-mcp` 需要 `TUSHARE_API_KEY`），请参阅各技能的 SKILL.md 了解具体要求。

## 许可证

MIT License
