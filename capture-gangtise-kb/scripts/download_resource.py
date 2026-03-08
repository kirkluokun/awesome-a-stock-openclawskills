#!/usr/bin/env python3
"""
通过 sourceId 溯源下载原始资源（研报 PDF、公告等）。

用法:
  python3 scripts/download_resource.py --type 10 --id SOURCE_ID
  python3 scripts/download_resource.py --type 10 --id SOURCE_ID --output report.pdf
"""
import json
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _client import require_configured, get as http_get

DOWNLOAD_ENDPOINT = "/application/open-data/ai/resource/download"

# 溯源支持的资源类型（不支持 40 首席分析师观点）
SUPPORTED_TYPES = {10, 20, 50, 60, 70, 80, 90}


def download_resource(resource_type: int, source_id: str, output_path: str | None = None) -> str | None:
    """
    下载溯源资源。

    返回:
      - 第三方 URL 字符串（Content-Type 为 json 时）
      - 保存的文件路径（文件流时）
      - None（失败时）
    """
    if resource_type not in SUPPORTED_TYPES:
        print(f"错误: resourceType {resource_type} 不支持溯源（type 40 不可用）", file=sys.stderr)
        return None

    params = {"resourceType": resource_type, "sourceId": source_id}
    response = http_get(DOWNLOAD_ENDPOINT, params, timeout=60)
    if not response:
        return None

    try:
        content_type = response.headers.get('Content-Type', '')

        # 返回第三方 URL
        if 'application/json' in content_type:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('url')

        # 返回文件流，保存到本地
        if output_path is None:
            cd = response.headers.get('Content-Disposition', '')
            if 'filename=' in cd:
                output_path = cd.split('filename=')[-1].strip('"\'')
            else:
                ext = '.pdf' if 'pdf' in content_type else '.bin'
                output_path = f"resource_{source_id}{ext}"

        with open(output_path, 'wb') as f:
            f.write(response.read())
        return output_path
    except Exception as e:
        print(f"下载错误: {e}", file=sys.stderr)
        return None
    finally:
        response.close()


def auto_clean_md(filepath: str) -> str | None:
    """如果文件是 .md 或 .txt，自动调用 clean_md 清洗 HTML→Markdown，原地覆盖。"""
    p = Path(filepath)
    if p.suffix.lower() not in ('.md', '.txt'):
        return None
    try:
        from clean_md import clean_gangtise_html
        content = p.read_text(encoding='utf-8', errors='ignore')
        cleaned = clean_gangtise_html(content)
        p.write_text(cleaned, encoding='utf-8')
        return str(p)
    except ImportError:
        # clean_md.py 不存在时静默跳过
        return None
    except Exception as e:
        print(f"⚠️  自动清洗失败: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description='溯源下载原始资源')
    parser.add_argument('--type', type=int, required=True, help='资源类型 (10/20/50/60/70/80/90)')
    parser.add_argument('--id', required=True, help='sourceId')
    parser.add_argument('--output', help='输出文件路径（可选）')
    parser.add_argument('--no-clean', action='store_true', help='跳过自动 MD 清洗')

    args = parser.parse_args()
    require_configured()

    result = download_resource(args.type, args.id, args.output)
    if result:
        print(result)
        # 自动清洗
        if not args.no_clean and Path(result).is_file():
            cleaned = auto_clean_md(result)
            if cleaned:
                print(f"✅ 已自动清洗: {cleaned}", file=sys.stderr)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
