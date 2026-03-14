---
name: jiyao-summary
description: |
  本地纪要结构化摘要工具。将公司调研纪要、业绩说明会、电话会议、路演记录提炼为标准化要点卡片。
  支持中英文自动识别，默认使用 OpenAI gpt-5.4，可切换 Gemini CLI（gemini-3.1-pro-preview）。
  触发场景：(1) 用户发送纪要文件路径请求总结 (2) 用户粘贴纪要文本请求提炼要点
  (3) "帮我总结这份纪要" "提炼一下要点" "做个纪要摘要"
metadata:
  openclaw:
    emoji: "📋"
    requires:
      bins: ["python3"]
      env: ["OPENAI_API_KEY"]
---

# 纪要摘要工具

专门处理股票研究场景下的纪要内容，输出标准化结构化摘要。

## 使用方式

### 从文件摘要
```bash
python3 {skillDir}/summarize.py /path/to/纪要.txt
python3 {skillDir}/summarize.py /path/to/earnings_call.pdf --lang en
```

### 从对话文本摘要
将纪要内容直接粘贴后，agent 会提取内容传给脚本：
```bash
echo "纪要内容..." | python3 {skillDir}/summarize.py -
```

### 切换模型
```bash
# 默认 OpenAI gpt-5.4
python3 {skillDir}/summarize.py 纪要.txt

# 切换 Gemini CLI
python3 {skillDir}/summarize.py 纪要.txt --model gemini
```

### 输出选项
```bash
# 指定输出目录
python3 {skillDir}/summarize.py 纪要.txt -o ~/Desktop/研究摘要

# 同步到 Obsidian
python3 {skillDir}/summarize.py 纪要.txt --obsidian --obsidian-path ~/Documents/Obsidian/纪要

# 只输出到对话，不保存文件
python3 {skillDir}/summarize.py 纪要.txt --no-save
```

## 参数说明

| 参数 | 默认值 | 说明 |
|---|---|---|
| `input` | stdin | 文件路径，或 `-` 从 stdin 读取 |
| `--lang` | auto | `cn` / `en` / `auto`（自动检测） |
| `--model` | openai | `openai`（gpt-5.4）/ `gemini`（gemini-3.1-pro-preview） |
| `--output-dir` / `-o` | `~/Desktop/纪要摘要` | 输出目录 |
| `--title` / `-t` | 纪要 | 输出文件名前缀 |
| `--obsidian` | false | 是否同步到 Obsidian |
| `--obsidian-path` | 空 | Obsidian 保存路径 |
| `--no-save` | false | 只输出到 stdout，不保存文件 |
