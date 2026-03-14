---
name: arxiv-watcher
description: 搜索并摘要 ArXiv 上的论文。当用户询问最新研究、ArXiv 上的特定主题，或需要 AI 论文每日摘要时使用。
---

# ArXiv 论文追踪器

本技能通过 ArXiv API 查找并摘要最新研究论文。

## 功能

- **搜索**：按关键词、作者或分类查找论文。
- **摘要**：获取论文摘要并提供简明概述。
- **保存记忆**：自动将已摘要的论文记录到 `memory/RESEARCH_LOG.md`，用于长期追踪。
- **深度阅读**：如有需要，通过 `web_fetch` 访问 PDF 链接提取更多详情。

## 工作流

1. 使用 `scripts/search_arxiv.sh "<query>"` 获取 XML 结果。
2. 解析 XML（查找 `<entry>`、`<title>`、`<summary>`、`<link title="pdf">`）。
3. 向用户展示查找结果。
4. **必须执行**：将讨论过的论文标题、作者、日期和摘要追加至 `memory/RESEARCH_LOG.md`，格式如下：
   ```markdown
   ### [YYYY-MM-DD] 论文标题
   - **Authors**: 作者列表
   - **Link**: ArXiv 链接
   - **Summary**: 论文简要摘要及其研究意义。
   ```

## 示例

- "搜索 ArXiv 上关于 LLM reasoning 的最新论文。"
- "告诉我 ID 为 2512.08769 的论文讲了什么。"
- "给我总结一下今天 ArXiv 上关于 AI 智能体的最新动态。"

## 资源

- `scripts/search_arxiv.sh`：直接访问 ArXiv API 的脚本。
