#!/usr/bin/env bash
# Lite Research — 使用 Gemini CLI 快速生成研究草稿
#
# 用法：
#   bash lite_research.sh --topic "量子计算" --outline outline.md --output ./output/ --model gemini-3-pro-preview

set -euo pipefail

# ===== 参数解析（带值校验）=====
TOPIC=""
OUTLINE=""
OUTPUT_DIR="."
MODEL="gemini-3-pro-preview"
SLUG=""

usage() {
  echo "用法: $(basename "$0") --topic <主题> [--outline <提纲>] [--output <目录>] [--model <模型>]"
  echo ""
  echo "参数:"
  echo "  --topic   <主题>    研究主题（必填）"
  echo "  --outline <文件>    提纲 markdown 文件路径（可选）"
  echo "  --output  <目录>    输出目录（默认当前目录）"
  echo "  --model   <模型>    Gemini 模型（默认 gemini-3-pro-preview）"
  echo "  --slug    <slug>    输出文件名前缀（可选，默认自动生成）"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --topic)
      [[ $# -lt 2 ]] && { echo "❌ --topic 需要一个值"; usage; }
      TOPIC="$2"; shift 2 ;;
    --outline)
      [[ $# -lt 2 ]] && { echo "❌ --outline 需要一个值"; usage; }
      OUTLINE="$2"; shift 2 ;;
    --output)
      [[ $# -lt 2 ]] && { echo "❌ --output 需要一个值"; usage; }
      OUTPUT_DIR="$2"; shift 2 ;;
    --model)
      [[ $# -lt 2 ]] && { echo "❌ --model 需要一个值"; usage; }
      MODEL="$2"; shift 2 ;;
    --slug)
      [[ $# -lt 2 ]] && { echo "❌ --slug 需要一个值"; usage; }
      SLUG="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "❌ 未知参数: $1"; usage ;;
  esac
done

if [[ -z "$TOPIC" ]]; then
  echo "❌ 必须指定 --topic"
  usage
fi

# ===== 生成 slug（兼容中文）=====
if [[ -z "$SLUG" ]]; then
  # 用 Python 生成安全 slug（支持中文 + ASCII）
  SLUG=$(python3 -c "
import hashlib, re, sys
topic = sys.argv[1]
# 保留中文、字母、数字、连字符
safe = re.sub(r'[^\w\u4e00-\u9fff-]', '_', topic)[:30].strip('_')
if not safe:
    safe = hashlib.md5(topic.encode()).hexdigest()[:8]
print(safe)
" "$TOPIC" 2>/dev/null || echo "research_$(date +%s)")
fi

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="$OUTPUT_DIR/${SLUG}_${TIMESTAMP}_draft.md"

# ===== 构建 Prompt =====
PROMPT="请对以下主题进行深度调研，生成一份结构化的研究草稿。

## 研究主题
$TOPIC
"

if [[ -n "$OUTLINE" ]]; then
  if [[ ! -f "$OUTLINE" ]]; then
    echo "⚠️ 提纲文件不存在: $OUTLINE (忽略)"
  else
    OUTLINE_CONTENT=$(cat "$OUTLINE")
    PROMPT="$PROMPT
## 研究提纲（必须严格按照此结构组织报告）

$OUTLINE_CONTENT
"
  fi
fi

PROMPT="$PROMPT
## 输出要求
1. 按提纲结构组织内容
2. 每个论点附具体数据、案例或引用
3. 标注信息来源
4. 标注不确定或需要验证的内容
5. 报告篇幅不少于 500 行
6. 使用中文撰写

请将完整报告输出到文件：$OUTPUT_FILE
"

echo "🔬 启动 Lite Research"
echo "  主题: $TOPIC"
echo "  模型: $MODEL"
echo "  输出: $OUTPUT_FILE"
echo "  提纲: ${OUTLINE:-无}"
echo ""

# ===== 执行 Gemini CLI =====
gemini -m "$MODEL" --yolo "$PROMPT"

# ===== 检查输出 =====
if [[ -f "$OUTPUT_FILE" ]]; then
  LINES=$(wc -l < "$OUTPUT_FILE")
  echo ""
  echo "✅ 研究草稿已完成"
  echo "  文件: $OUTPUT_FILE"
  echo "  行数: $LINES"
else
  echo ""
  echo "⚠️ 未找到输出文件 $OUTPUT_FILE"
  echo "  Gemini 可能将内容输出到了终端或其他位置"
fi
