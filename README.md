# 🤖 Awesome A-Stock OpenClaw Skills

精选的 OpenClaw / Claude 代理技能集合，专注于 A 股投资研究与分析。

## 什么是 OpenClaw Skills？

OpenClaw Skills 是基于 Markdown 的 AI 代理技能定义文件，可以扩展 Claude 等 AI 助手的能力，使其具备专业的金融分析、数据获取、研究协作等功能。

## 技能列表

### 📡 Capture — 数据抓取
| 技能 | 描述 |
| --- | --- |
| `capture-30天热点` | 30 天热点趋势追踪 |
| `capture-arxiv论文热点跟踪` | ArXiv 论文监控 |
| `capture-blogwatcher` | 博客/RSS 监控 |
| `capture-gangtise` | 港股通知识库采集 |
| `capture-reddit-search` | Reddit 搜索 |
| `capture-search-x` | X (Twitter) 搜索 |
| `capture-youtube` | YouTube 视频内容抓取 |
| `capture-韭菜公社` | 韭菜公社数据采集 |

### 💻 Code — 代码工具
| 技能 | 描述 |
| --- | --- |
| `code-CodingAgent` | 编程辅助代理 |

### 📊 Data — 数据分析
| 技能 | 描述 |
| --- | --- |
| `data-回测框架` | 交易策略回测 |
| `data-时间序列分析` | 金融时间序列分析 |
| `data-数据可视化` | 数据可视化 |

### 🔬 Deep — 深度研究
| 技能 | 描述 |
| --- | --- |
| `deep-gemini深度研究` | Gemini 深度研究代理 |
| `deep-事实检测` | 事实核查 |
| `deep-公司快速研究` | 公司深度研究 |

### 🧠 Memory — 记忆与认知
| 技能 | 描述 |
| --- | --- |
| `memory-Agent进化论` | 技能进化器 |
| `memory-Idea教练` | 创意教练 |
| `memory-ontology-0.1.2` | 本体知识图谱 |
| `memory-self-improving-1.0.11` | 自我改进记忆 |
| `memory-thinking-model-enhancer` | 思维模型增强 |
| `memory-认知记忆` | 认知记忆系统 |
| `memory-框架学习技能` | 框架学习与迁移 |

### 📰 News — 新闻聚合
| 技能 | 描述 |
| --- | --- |
| `news-aggregator-skill` | 新闻聚合器 |
| `news-bbc-news` | BBC 新闻 |
| `news-cctv-news-fetcher` | CCTV 新闻抓取 |
| `news-daily-ai-news-skill` | 每日 AI 新闻 |
| `news-newsapi-search` | NewsAPI 搜索 |
| `news-summary` | 新闻摘要 |

### 📈 Stock — 股票工具
| 技能 | 描述 |
| --- | --- |
| `stock-a股技术分析数据准备` | A 股技术面数据准备 |
| `stock-a股股票基础研究` | A 股基础研究 |
| `stock-a股自选股监控` | A 股自选股监控 |
| `stock-a股量化监控系统` | A 股量化监控系统 |
| `stock-tushare数据mcp` | Tushare Pro MCP（158+ 接口，A/港/美股） |
| `stock-yahoo-finance` | Yahoo Finance 数据 |
| `stock-买卖信号追踪` | 买卖信号（全球 37,565+ 标的） |
| `stock-交易记录工具` | 交易日志（Markdown + SQLite 双写） |
| `stock-信息交叉验证` | 多源信息交叉验证 |
| `stock-持仓组合监控` | 持仓组合监控 |
| `stock-美股分析组合` | 美股分析组合 |
| `stock-美股基础数据` | 美股基础数据 |
| `stock-美股股价查询` | 美股股价查询 |
| `stock-股票分析工具` | 股票综合分析工具 |
| `stock-调研纪要总结` | 调研纪要总结 |

### 🐝 Swarm — 多智能体协作
| 技能 | 描述 |
| --- | --- |
| `swarm-personas` | 角色扮演/多人格代理 |
| `swarm-war-room` | 多代理作战室（头脑风暴/系统设计） |

### 🔧 Tool — 工具类
| 技能 | 描述 |
| --- | --- |
| `tool-serper检索` | Serper Google 搜索引擎集成 |

## 使用方式

将技能文件夹复制到你的 Claude 项目的 `.agent/skills/` 目录下即可使用。

```bash
# 示例：安装 Tushare MCP 技能
cp -r stock-tushare数据mcp /path/to/your-project/.agent/skills/
```

> **注意：** 部分技能需要配置 API key（如 `stock-tushare数据mcp` 需要 `TUSHARE_API_KEY`），请参阅各技能目录下的 `.env.example` 了解具体要求。

## 许可证

MIT License
