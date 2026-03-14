#!/usr/bin/env bash
# 文字稿提纯 — 使用 Gemini CLI 对原始字幕文本进行结构化提纯
#
# 用法：
#   bash refine_transcript.sh --input raw_transcript.txt --output refined.md
#   bash refine_transcript.sh --input raw_transcript.txt --mode podcast
#   bash refine_transcript.sh --url "https://www.youtube.com/watch?v=xxx" --mode podcast
#
# 模式：
#   general  — 通用提纯：去重、修正、分段、提取要点
#   podcast  — 播客模式：按问答对拆解，识别主持人/嘉宾，每个问题独立总结
#   lecture  — 讲座模式：按知识点分章节，提取核心概念和定义
#   interview — 访谈模式：按话题轮次拆分，标注发言人立场
#
# 依赖：
#   - gemini CLI（/opt/homebrew/bin/gemini）
#   - yt-dlp（如果用 --url 直接从视频获取字幕）
#   - python3（字幕清洗）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INPUT=""
OUTPUT=""
URL=""
MODE="general"
MODEL="gemini-3-pro-preview"
TITLE=""
LANG="auto"

usage() {
  echo "用法: $(basename "$0") [选项]"
  echo ""
  echo "选项:"
  echo "  --input   <文件>    原始字幕/文字稿文件路径"
  echo "  --url     <URL>     YouTube URL（自动获取字幕后提纯）"
  echo "  --output  <文件>    输出文件路径（默认自动命名）"
  echo "  --mode    <模式>    提纯模式：general|podcast|lecture|interview（默认 general）"
  echo "  --model   <模型>    Gemini 模型（默认 gemini-3-pro-preview）"
  echo "  --title   <标题>    视频标题（可选，增强提纯效果）"
  echo "  --lang    <语言>    输出语言：zh|en|auto（默认 auto，自动检测）"
  echo "  -h, --help          显示帮助"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --input)
      [[ $# -lt 2 ]] && { echo "❌ --input 需要一个值"; usage; }
      INPUT="$2"; shift 2 ;;
    --url)
      [[ $# -lt 2 ]] && { echo "❌ --url 需要一个值"; usage; }
      URL="$2"; shift 2 ;;
    --output)
      [[ $# -lt 2 ]] && { echo "❌ --output 需要一个值"; usage; }
      OUTPUT="$2"; shift 2 ;;
    --mode)
      [[ $# -lt 2 ]] && { echo "❌ --mode 需要一个值"; usage; }
      MODE="$2"; shift 2 ;;
    --model)
      [[ $# -lt 2 ]] && { echo "❌ --model 需要一个值"; usage; }
      MODEL="$2"; shift 2 ;;
    --title)
      [[ $# -lt 2 ]] && { echo "❌ --title 需要一个值"; usage; }
      TITLE="$2"; shift 2 ;;
    --lang)
      [[ $# -lt 2 ]] && { echo "❌ --lang 需要一个值"; usage; }
      LANG="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "❌ 未知参数: $1"; usage ;;
  esac
done

# ===== 输入校验 =====
if [[ -z "$INPUT" && -z "$URL" ]]; then
  echo "❌ 必须指定 --input 或 --url"
  usage
fi

# ===== 如果指定了 URL，先获取字幕 =====
if [[ -n "$URL" ]]; then
  echo "📥 从 YouTube 获取字幕..."
  TEMP_TRANSCRIPT=$(mktemp /tmp/yt_raw_XXXXXX.txt)
  
  if python3 "$SCRIPT_DIR/get_transcript.py" "$URL" > "$TEMP_TRANSCRIPT" 2>/dev/null; then
    echo "✅ 字幕获取成功"
    INPUT="$TEMP_TRANSCRIPT"
  else
    echo "⚠️ 字幕获取失败，尝试 Gemini 逐字稿模式..."
    if python3 "$SCRIPT_DIR/youtube_transcript.py" "$URL" --out "$TEMP_TRANSCRIPT" 2>/dev/null; then
      # youtube_transcript.py 输出的是文件路径
      ACTUAL_FILE=$(cat "$TEMP_TRANSCRIPT" 2>/dev/null || echo "$TEMP_TRANSCRIPT")
      if [[ -f "$ACTUAL_FILE" ]]; then
        INPUT="$ACTUAL_FILE"
      else
        INPUT="$TEMP_TRANSCRIPT"
      fi
      echo "✅ Gemini 逐字稿获取成功"
    else
      echo "❌ 无法获取视频字幕，请手动提供文字稿文件"
      exit 1
    fi
  fi
  
  # 尝试获取标题
  if [[ -z "$TITLE" ]]; then
    TITLE=$(python3 -c "
import urllib.request, urllib.parse, json, sys
try:
    url = 'https://www.youtube.com/oembed?format=json&url=' + urllib.parse.quote(sys.argv[1], safe='')
    with urllib.request.urlopen(url, timeout=10) as r:
        print(json.loads(r.read())['title'])
except: pass
" "$URL" 2>/dev/null || true)
  fi
fi

# ===== 检查输入文件 =====
if [[ ! -f "$INPUT" ]]; then
  echo "❌ 输入文件不存在: $INPUT"
  exit 1
fi

RAW_LINES=$(wc -l < "$INPUT" | tr -d ' ')
RAW_CHARS=$(wc -c < "$INPUT" | tr -d ' ')
echo "📄 原始文本: ${RAW_LINES} 行, ${RAW_CHARS} 字符"

# ===== 自动输出路径 =====
if [[ -z "$OUTPUT" ]]; then
  TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
  # 输出到技能上级的 out/ 目录
  OUT_DIR="$SCRIPT_DIR/../../out"
  mkdir -p "$OUT_DIR"
  OUTPUT="$OUT_DIR/refined_${MODE}_${TIMESTAMP}.md"
fi

mkdir -p "$(dirname "$OUTPUT")"

# ===== 构建模式 Prompt =====
LANG_INSTRUCTION=""
if [[ "$LANG" == "zh" ]]; then
  LANG_INSTRUCTION="请用中文输出。"
elif [[ "$LANG" == "en" ]]; then
  LANG_INSTRUCTION="Please output in English."
else
  LANG_INSTRUCTION="请用与原文相同的语言输出。如果原文是中文则用中文，英文则用英文。"
fi

TITLE_LINE=""
if [[ -n "$TITLE" ]]; then
  TITLE_LINE="视频/音频标题：$TITLE"
fi

case "$MODE" in

  general)
    MODE_PROMPT="你是专业的文字稿编辑。请对以下原始字幕/文字稿进行提纯处理：

## 任务
1. **去重去噪**：删除重复句、无意义的口头禅（嗯、啊、那个）、字幕系统生成的噪音
2. **纠正错误**：修正明显的语音识别错误
3. **分段整理**：按内容主题合理分段，添加段落标题
4. **提取要点**：在文末附上核心要点总结（5-10 条）

## 输出格式
\`\`\`
# [标题]

## 要点速览
- 要点 1
- 要点 2
...

---

## [段落标题 1]
[整理后的文字内容]

## [段落标题 2]
[整理后的文字内容]
...
\`\`\`"
    ;;

  podcast)
    MODE_PROMPT="你是播客内容分析专家。请对以下播客原始字幕/文字稿进行**按问答结构拆解**的深度提纯：

## 任务
1. **识别角色**：识别主持人和嘉宾（如果无法确定名字，用 Host / Guest 标注）
2. **按问题拆解**：将整个播客按讨论的**核心问题/话题**拆分为独立段落
3. **每个问题段包含**：
   - 🎯 **问题/话题**：一句话概括这段讨论的核心问题
   - 💬 **讨论要点**：3-5 个要点，标注是谁说的
   - 📝 **原文精选**：保留最精彩的几句原话（修正口误但保留说话风格）
4. **去重去噪**：删除重复、口头禅、无意义过渡
5. **生成总览**：开头提供播客概要和所有问题的索引

## 输出格式
\`\`\`markdown
# 🎙️ [播客标题]

## 📋 概要
- **主题**：[一句话总结]
- **参与者**：[主持人 / 嘉宾]
- **核心议题数**：N 个

## 🗂️ 议题索引
1. [问题1简述]
2. [问题2简述]
...

---

## 议题 1：[问题/话题]
🎯 **核心问题**：[具体问题]

💬 **讨论要点**：
- [Host]：[观点1]
- [Guest]：[观点2]
- ...

📝 **精彩原话**：
> 「[保留的原话]」 —— [说话人]

---

## 议题 2：[问题/话题]
...

---

## 🔑 关键结论
1. [结论1]
2. [结论2]
...
\`\`\`"
    ;;

  lecture)
    MODE_PROMPT="你是教育内容编辑专家。请对以下讲座/教程的原始字幕进行**知识结构化**提纯：

## 任务
1. **章节划分**：按知识点/教学模块拆分为章节
2. **提取概念**：标注核心概念、定义、公式
3. **整理示例**：保留并标注讲解中的举例和案例
4. **生成知识点索引和学习笔记**

## 输出格式
\`\`\`markdown
# 📚 [讲座标题]

## 📋 知识点索引
1. [知识点1]
2. [知识点2]
...

---

## 第一章：[章节标题]

### 核心概念
- **[概念名]**：[定义/解释]

### 详细内容
[整理后的讲解内容]

### 举例说明
- [案例/示例]

---

## 📝 学习笔记
- [要点1]
- [要点2]
\`\`\`"
    ;;

  interview)
    MODE_PROMPT="你是专业访谈编辑。请对以下访谈原始字幕进行**按话题轮次**的结构化整理：

## 任务
1. **识别发言人**：区分采访者和受访者
2. **按话题轮次拆分**：每个话题转换处分段
3. **标注立场**：提炼每个发言人在各话题上的核心立场/观点
4. **保留精华**：原文中的金句和关键表述原样保留

## 输出格式
\`\`\`markdown
# 🎤 [访谈标题]

## 📋 访谈概要
- **受访者**：[姓名/身份]
- **采访者**：[姓名/身份]
- **核心话题**：N 个

---

## 话题 1：[话题名]
**采访者提问**：[问题]

**受访者观点**：
- [核心观点1]
- [核心观点2]

**原文精选**：
> 「[原话]」

---

## 🔑 核心观点总结
| 话题 | 受访者立场 |
|------|-----------|
| ... | ... |
\`\`\`"
    ;;

  *)
    echo "❌ 未知模式: $MODE（支持：general / podcast / lecture / interview）"
    exit 1
    ;;
esac

# ===== 读取原始文本 =====
RAW_TEXT=$(cat "$INPUT")

# ===== 组装完整 Prompt =====
FULL_PROMPT="${MODE_PROMPT}

${LANG_INSTRUCTION}
${TITLE_LINE}

## 原始文字稿
${RAW_TEXT}

---

请将提纯后的完整内容输出到文件：${OUTPUT}
不要输出其他解释，直接写文件。"

# ===== 执行 Gemini CLI =====
echo ""
echo "🧠 开始 Gemini 提纯处理..."
echo "  模式: $MODE"
echo "  模型: $MODEL"
echo "  输出: $OUTPUT"
echo ""

gemini -m "$MODEL" --yolo "$FULL_PROMPT"

# ===== 检查输出 =====
if [[ -f "$OUTPUT" ]]; then
  OUT_LINES=$(wc -l < "$OUTPUT" | tr -d ' ')
  echo ""
  echo "✅ 提纯完成"
  echo "  输入: ${RAW_LINES} 行 → 输出: ${OUT_LINES} 行"
  echo "  文件: $OUTPUT"
else
  echo ""
  echo "⚠️ 未找到输出文件 $OUTPUT"
  echo "  Gemini 可能将内容输出到了终端，请手动保存"
fi
