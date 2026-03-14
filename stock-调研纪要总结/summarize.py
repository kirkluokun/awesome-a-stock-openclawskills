#!/usr/bin/env python3
"""
纪要摘要工具
将研究纪要/会议纪要提炼为结构化要点卡片
支持 OpenAI gpt-5.4 / Gemini CLI
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime


# ──────────────────────────────────────────────
# 模板回退（templates/ 目录不存在时使用）
# ──────────────────────────────────────────────
FALLBACK_CN = """# {公司名} · {会议类型} · {日期}

## 基本信息
- 来源公司：
- 会议类型：
- 日期：

## 核心观点
1.
2.
3.

## 业绩与数据要点
| 指标 | 数值 | 同比/环比 | 点评 |
|---|---|---|---|

## 管理层态度与指引
- 当前判断：
- 前瞻指引：

## 风险与不确定因素
-

## 投资启示
"""

FALLBACK_EN = """# {Company} · {Event Type} · {Date}

## Overview
- Company:
- Event:
- Date:

## Key Takeaways
1.
2.
3.

## Financial Highlights
| Metric | Value | YoY/QoQ | Commentary |
|---|---|---|---|

## Management Tone & Guidance
- Current assessment:
- Forward guidance:

## Risks
-

## Investment Implications
"""


def read_input(input_arg: str | None) -> str:
    """读取输入：文件路径 / stdin"""
    if input_arg is None or input_arg == "-":
        print("📥 从 stdin 读取内容...", file=sys.stderr)
        return sys.stdin.read()

    path = Path(input_arg).expanduser()
    if not path.exists():
        print(f"❌ 文件不存在: {path}", file=sys.stderr)
        sys.exit(1)

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _read_pdf(path)
    return path.read_text(encoding="utf-8")


def _read_pdf(path: Path) -> str:
    """PDF 提取文本（依赖 pdfplumber）"""
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
    except ImportError:
        print("⚠️  未安装 pdfplumber，尝试用 pdftotext...", file=sys.stderr)
        result = subprocess.run(
            ["pdftotext", str(path), "-"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout
        print("❌ PDF 解析失败，请安装 pdfplumber: pip install pdfplumber", file=sys.stderr)
        sys.exit(1)


def detect_input_lang(text: str) -> str:
    """检测输入语言（用于调整提示词，不影响输出模板）"""
    cn_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return "cn" if cn_chars > len(text) * 0.1 else "en"


def load_template() -> str:
    """加载中文输出模板（统一输出格式）"""
    tmpl_path = Path(__file__).parent / "templates" / "cn.md"
    if tmpl_path.exists():
        return tmpl_path.read_text(encoding="utf-8")
    return FALLBACK_CN


def build_system_prompt(template: str, input_lang: str) -> str:
    """系统提示词根据输入语言调整，输出模板统一用中文"""
    base = (
        "你是专业的股票研究分析师，专门处理公司调研纪要、业绩说明会、电话会议记录。\n"
        "请严格按照以下模板格式输出摘要，保留所有章节标题，每个章节必须有实质内容。\n"
        "数据要精准，观点要提炼，不要复述原文。输出语言为中文。\n"
    )
    if input_lang == "en":
        base += "输入内容为英文，请阅读后用中文按模板输出。\n"
    return base + f"\n模板格式：\n{template}"


def summarize_openai(content: str, template: str, lang: str, model: str) -> str:
    """调用 OpenAI API 进行摘要"""
    try:
        from openai import OpenAI
    except ImportError:
        print("❌ 未安装 openai SDK: pip install openai", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ 未设置 OPENAI_API_KEY", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    user_msg = (
        f"请对以下纪要进行结构化摘要：\n\n{content}"
        if lang == "cn"
        else f"Please summarize the following transcript:\n\n{content}"
    )

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": build_system_prompt(template, lang)},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content


def summarize_gemini(content: str, template: str, lang: str, gemini_model: str) -> str:
    """通过 Gemini CLI 进行摘要"""
    system = build_system_prompt(template, lang)
    user_msg = (
        f"请对以下纪要进行结构化摘要：\n\n{content}"
        if lang == "cn"
        else f"Please summarize the following transcript:\n\n{content}"
    )
    full_prompt = f"{system}\n\n---\n\n{user_msg}"

    result = subprocess.run(
        ["gemini", "--model", gemini_model, "-p", full_prompt],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"❌ Gemini CLI 错误:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def save_output(summary: str, output_dir: str, title: str) -> Path:
    """保存摘要到文件"""
    out_dir = Path(output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    safe_title = title[:20].replace("/", "-").replace("\\", "-")
    filename = f"{date_str}_{safe_title}.md"
    out_path = out_dir / filename
    out_path.write_text(summary, encoding="utf-8")
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="纪要摘要工具 — 将调研纪要提炼为结构化要点卡片"
    )
    parser.add_argument(
        "input", nargs="?", default=None,
        help="纪要文件路径（.txt/.md/.pdf），留空从 stdin 读取"
    )
    parser.add_argument(
        "--model", choices=["openai", "gemini"], default="openai",
        help="使用的模型（默认 openai）"
    )
    parser.add_argument(
        "--openai-model", default="gpt-5.4",
        help="OpenAI 模型名称（默认 gpt-5.4）"
    )
    parser.add_argument(
        "--gemini-model", default="gemini-3.1-pro-preview",
        help="Gemini 模型名称（默认 gemini-3.1-pro-preview）"
    )
    parser.add_argument(
        "--output-dir", "-o", default="~/Desktop/纪要摘要",
        help="输出目录（默认 ~/Desktop/纪要摘要）"
    )
    parser.add_argument(
        "--title", "-t", default="纪要",
        help="输出文件名前缀"
    )
    parser.add_argument(
        "--obsidian", "--ob", action="store_true",
        help="同时保存到 Obsidian"
    )
    parser.add_argument(
        "--obsidian-path", default="",
        help="Obsidian 保存路径"
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="只输出到 stdout，不保存文件"
    )

    args = parser.parse_args()

    # 1. 读取内容
    content = read_input(args.input)
    if not content.strip():
        print("❌ 输入内容为空", file=sys.stderr)
        sys.exit(1)

    # 2. 检测输入语言（调整提示词，输出始终为中文模板）
    input_lang = detect_input_lang(content)
    print(f"🌐 输入语言：{'中文' if input_lang == 'cn' else '英文'} → 输出：中文", file=sys.stderr)

    # 3. 加载模板（统一中文）
    template = load_template()

    # 4. 执行摘要
    print(f"🔄 使用 {args.model} 进行摘要...", file=sys.stderr)
    if args.model == "openai":
        summary = summarize_openai(content, template, input_lang, args.openai_model)
    else:
        summary = summarize_gemini(content, template, input_lang, args.gemini_model)

    # 5. 输出
    print(summary)

    if not args.no_save:
        out_path = save_output(summary, args.output_dir, args.title)
        print(f"\n✅ 已保存至: {out_path}", file=sys.stderr)

        if args.obsidian and args.obsidian_path:
            ob_dir = Path(args.obsidian_path).expanduser()
            ob_dir.mkdir(parents=True, exist_ok=True)
            ob_path = ob_dir / out_path.name
            ob_path.write_text(summary, encoding="utf-8")
            print(f"📚 已同步至 Obsidian: {ob_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
