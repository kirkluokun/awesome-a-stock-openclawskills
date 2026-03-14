---
name: reddit-search
description: 搜索 Reddit 的子版块并获取相关信息。
homepage: https://github.com/TheSethRose/clawdbot
metadata: {"clawdbot":{"emoji":"📮","requires":{"bins":["node","npx"],"env":[]}}}
---

# Reddit 搜索

搜索 Reddit 子版块并获取相关信息。

## 快速开始

```bash
{baseDir}/scripts/reddit-search info programming
{baseDir}/scripts/reddit-search search javascript
{baseDir}/scripts/reddit-search popular 10
{baseDir}/scripts/reddit-search posts typescript 5
```

## 命令

### 获取子版块信息

```bash
{baseDir}/scripts/reddit-search info <subreddit>
```

显示订阅人数、NSFW 状态、创建日期和版块介绍（含侧栏链接）。

### 搜索子版块

```bash
{baseDir}/scripts/reddit-search search <query> [limit]
```

搜索与关键词匹配的子版块。默认返回 10 个结果。

### 列出热门子版块

```bash
{baseDir}/scripts/reddit-search popular [limit]
```

列出最热门的子版块。默认返回 10 个结果。

### 列出新建子版块

```bash
{baseDir}/scripts/reddit-search new [limit]
```

列出新创建的子版块。默认返回 10 个结果。

### 获取子版块热帖

```bash
{baseDir}/scripts/reddit-search posts <subreddit> [limit]
```

获取子版块中按热度排序的热门帖子。默认返回 5 条。

## 示例

```bash
# 获取 r/programming 的版块信息
{baseDir}/scripts/reddit-search info programming

# 搜索 JavaScript 相关社区（返回20个）
{baseDir}/scripts/reddit-search search javascript 20

# 列出前15个热门子版块
{baseDir}/scripts/reddit-search popular 15

# 列出新建子版块
{baseDir}/scripts/reddit-search new 10

# 获取 r/typescript 的前5条热帖
{baseDir}/scripts/reddit-search posts typescript 5
```
