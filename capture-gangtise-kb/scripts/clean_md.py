#!/usr/bin/env python3
"""
clean_md.py — Gangtise 纪要 HTML→Markdown 清洗脚本

用法:
  # 清洗单个文件（原地覆盖）
  python3 scripts/clean_md.py file.md

  # 清洗单个文件（输出到新文件）
  python3 scripts/clean_md.py file.md -o clean_file.md

  # 批量清洗目录下所有 .md / .txt
  python3 scripts/clean_md.py dir/

  # 从 stdin 读取，stdout 输出（管道模式）
  cat dirty.md | python3 scripts/clean_md.py -

清洗规则:
  1. 删除 <span class='meeting_summary_num' ...>N</span> 隐藏时间戳
  2. HTML 标签转 Markdown（h1→#, h2→##, strong→**, li→-, p→段落等）
  3. 清理 HTML 实体（&nbsp; &amp; &lt; &gt; &quot; &#xNNNN;）
  4. 修复多余空行（连续3+空行合并为2）
  5. 修复行尾多余空格
"""

import re
import sys
import argparse
from pathlib import Path


def clean_gangtise_html(text: str) -> str:
    """将 Gangtise 纪要的 HTML 混合文本转为干净 Markdown。"""

    # ── Step 0: 删除隐藏的时间戳 span ──
    # <span class='meeting_summary_num' style='display:none' data-time-start='...' data-time-end='...'>N</span>
    text = re.sub(
        r"<span\s+class=['\"]meeting_summary_num['\"][^>]*>.*?</span>",
        "",
        text,
        flags=re.DOTALL,
    )

    # ── Step 1: 块级标签转 Markdown ──

    # <h1>...</h1> → # ...
    text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"\n# \1\n", text, flags=re.DOTALL)
    # <h2>...</h2> → ## ...
    text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"\n## \1\n", text, flags=re.DOTALL)
    # <h3>...</h3> → ### ...
    text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"\n### \1\n", text, flags=re.DOTALL)
    # <h4>...</h4> → #### ...
    text = re.sub(r"<h4[^>]*>(.*?)</h4>", r"\n#### \1\n", text, flags=re.DOTALL)

    # <strong>...</strong> / <b>...</b> → **...**
    text = re.sub(r"<(?:strong|b)[^>]*>(.*?)</(?:strong|b)>", r"**\1**", text, flags=re.DOTALL)
    # <em>...</em> / <i>...</i> → *...*
    text = re.sub(r"<(?:em|i)[^>]*>(.*?)</(?:em|i)>", r"*\1*", text, flags=re.DOTALL)

    # <li><p>...</p></li> → 先去掉内层 p
    text = re.sub(r"<li>\s*<p>(.*?)</p>\s*</li>", r"<li>\1</li>", text, flags=re.DOTALL)

    # <li>...</li> → - ...
    text = re.sub(r"<li[^>]*>(.*?)</li>", lambda m: "- " + m.group(1).strip(), text, flags=re.DOTALL)

    # <p>...</p> → 段落（前后加空行）
    text = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\1\n", text, flags=re.DOTALL)

    # <br\s*/?>  → 换行
    text = re.sub(r"<br\s*/?>", "\n", text)

    # ── Step 2: 删除剩余 HTML 标签 ──
    # 先删 <ul>, </ul>, <ol>, </ol> 等容器标签（不影响内容）
    text = re.sub(r"</?(?:ul|ol|div|section|article|header|footer|nav|table|thead|tbody|tr|td|th|blockquote|figure|figcaption|details|summary|main|aside|span|a|img|code|pre|sup|sub)[^>]*>", "", text)
    # 兜底：删除所有残留的 HTML 标签
    text = re.sub(r"<[^>]+>", "", text)

    # ── Step 3: HTML 实体 ──
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&apos;", "'")
    text = text.replace("&#39;", "'")
    # 处理 &#xNNNN; 和 &#NNNN; 数字实体
    text = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), text)
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)

    # ── Step 4: 清理格式 ──
    # 行尾多余空格（保留 Markdown 的两个空格换行）
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    # 连续3+空行 → 2空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 标题前确保有空行
    text = re.sub(r"([^\n])\n(#{1,4} )", r"\1\n\n\2", text)
    # 列表项 "- " 前如果紧跟文本，加空行
    text = re.sub(r"([^\n-])\n(- )", r"\1\n\n\2", text)

    return text.strip() + "\n"


def process_file(path: Path, output: Path | None = None):
    """清洗单个文件。"""
    content = path.read_text(encoding="utf-8", errors="ignore")
    cleaned = clean_gangtise_html(content)
    dest = output or path
    dest.write_text(cleaned, encoding="utf-8")
    print(f"✅ {path} → {dest}  ({len(content)} → {len(cleaned)} bytes)")


def main():
    parser = argparse.ArgumentParser(description="Gangtise 纪要 HTML→Markdown 清洗")
    parser.add_argument("input", help="文件路径、目录路径、或 '-' 表示 stdin")
    parser.add_argument("-o", "--output", help="输出文件路径（单文件模式）", default=None)
    args = parser.parse_args()

    if args.input == "-":
        # stdin → stdout
        text = sys.stdin.read()
        sys.stdout.write(clean_gangtise_html(text))
        return

    p = Path(args.input)
    if p.is_file():
        process_file(p, Path(args.output) if args.output else None)
    elif p.is_dir():
        files = sorted(p.glob("*.md")) + sorted(p.glob("*.txt"))
        if not files:
            print(f"⚠️  {p} 下没有 .md / .txt 文件")
            return
        for f in files:
            process_file(f)
        print(f"\n共清洗 {len(files)} 个文件")
    else:
        print(f"❌ 路径不存在: {p}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
