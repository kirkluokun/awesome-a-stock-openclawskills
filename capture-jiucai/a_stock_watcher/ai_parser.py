"""AI 解析层 — 调用 Gemini 2.5 Flash 提取股票、主题、投资逻辑，同时过滤噪音"""

import os
import yaml
from google import genai

from .models import ParsedResult, StockMention, ThemeMention

# Gemini 客户端（延迟初始化）
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY 环境变量未设置")
        _client = genai.Client(api_key=api_key)
    return _client


PARSE_PROMPT = """你是一个 A 股投研分析师。请分析以下文章内容，提取结构化信息。

## 任务
1. **评估相关性** (relevance, 0-10)：与 A 股投资是否相关？广告/软文/水文/无实质分析 → 给低分。
2. **提取发布日期** (publish_date)
3. **提取涉及的股票** (stocks)：代码、名称、上下文片段、投资逻辑
4. **提取涉及的主题** (themes)：主题名称、分类（消费/科技/医药/周期/金融/新能源 等）
5. **总结投资逻辑** (logic_summary)

## 输出要求
请严格输出以下 YAML 格式，不要额外的 markdown 包裹：

relevance: <0-10整数>
publish_date: "<YYYY-MM-DD或空>"
stocks:
  - code: "<6位股票代码>"
    name: "<股票名称>"
    context: "<提及该股票的上下文片段（50字内）>"
    logic: "<该股票的投资逻辑（50字内）>"
themes:
  - name: "<主题名称>"
    category: "<分类>"
logic_summary: "<整体投资逻辑总结（100字内）>"

如果文章无关 A 股投资，relevance 设为低分，其余字段可以为空列表。

## 文章标题
{title}

## 文章内容
{content}
"""


async def parse_article(title: str, content: str) -> ParsedResult:
    """
    调用 Gemini 2.5 Flash 解析文章，返回结构化结果。
    
    - relevance < 5 → 标记为噪音，调用方决定是否入库
    - 解析失败 → parse_failed=True，保留原文
    """
    if not content.strip():
        return ParsedResult(
            relevance=0, parse_failed=True,
            filter_reason="空内容",
        )

    prompt = PARSE_PROMPT.format(title=title, content=content[:8000])

    try:
        client = _get_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw_text = response.text.strip()

        # 清理可能的 markdown 包裹
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        parsed_yaml = yaml.safe_load(raw_text)
        if not isinstance(parsed_yaml, dict):
            return ParsedResult(
                relevance=0, raw_yaml=raw_text,
                parse_failed=True, filter_reason="AI 输出不是有效 YAML dict",
            )

        relevance = int(parsed_yaml.get("relevance", 0))
        result = ParsedResult(
            relevance=relevance,
            publish_date=str(parsed_yaml.get("publish_date", "")),
            logic_summary=str(parsed_yaml.get("logic_summary", "")),
            raw_yaml=raw_text,
            parse_failed=False,
        )

        # 解析股票
        for s in parsed_yaml.get("stocks", []) or []:
            if isinstance(s, dict) and s.get("code"):
                result.stocks.append(StockMention(
                    code=str(s["code"]),
                    name=str(s.get("name", "")),
                    context=str(s.get("context", "")),
                    logic=str(s.get("logic", "")),
                ))

        # 解析主题
        for t in parsed_yaml.get("themes", []) or []:
            if isinstance(t, dict) and t.get("name"):
                result.themes.append(ThemeMention(
                    name=str(t["name"]),
                    category=str(t.get("category", "")),
                ))

        # 噪音标记
        if relevance < 5:
            result.filter_reason = f"低相关性 relevance={relevance}"

        return result

    except Exception as e:
        return ParsedResult(
            relevance=0, parse_failed=True,
            filter_reason=f"AI 解析异常: {str(e)}",
        )


IMAGE_PARSE_PROMPT = """你是一个 A 股投研分析师。请分析这张产业链图片/图表，提取结构化信息。

## 任务
1. 识别图中涉及的**所有股票**（代码+名称）
2. 识别图中展示的**产业链结构**和**投资逻辑**
3. 提取关键数据点

## 输出要求
请严格输出以下 YAML 格式，不要额外的 markdown 包裹：

relevance: 8
publish_date: ""
stocks:
  - code: "<6位股票代码>"
    name: "<股票名称>"
    context: "<在图中的角色/位置>"
    logic: "<投资逻辑>"
themes:
  - name: "<产业/主题名称>"
    category: "<分类>"
logic_summary: "<整体产业链逻辑总结（150字内）>"

图片对应的产业名称: {industry_name}
"""


async def parse_image(image_path: str, industry_name: str = "") -> ParsedResult:
    """
    调用 Gemini Vision 分析图片，提取股票名单和产业链逻辑。

    Args:
        image_path: 截图文件的绝对路径
        industry_name: 产业链名称（上下文）
    """
    try:
        from google.genai import types
        client = _get_client()

        # 读取图片文件
        with open(image_path, "rb") as f:
            image_data = f.read()

        prompt = IMAGE_PARSE_PROMPT.format(industry_name=industry_name)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=image_data, mime_type="image/png"),
                prompt,
            ],
        )
        raw_text = response.text.strip()

        # 清理可能的 markdown 包裹
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        parsed_yaml = yaml.safe_load(raw_text)
        if not isinstance(parsed_yaml, dict):
            return ParsedResult(
                relevance=5, raw_yaml=raw_text,
                parse_failed=True, filter_reason="图片AI输出不是有效YAML",
            )

        relevance = int(parsed_yaml.get("relevance", 5))
        result = ParsedResult(
            relevance=relevance,
            publish_date=str(parsed_yaml.get("publish_date", "")),
            logic_summary=str(parsed_yaml.get("logic_summary", "")),
            raw_yaml=raw_text,
            parse_failed=False,
        )

        for s in parsed_yaml.get("stocks", []) or []:
            if isinstance(s, dict) and s.get("code"):
                result.stocks.append(StockMention(
                    code=str(s["code"]),
                    name=str(s.get("name", "")),
                    context=str(s.get("context", "")),
                    logic=str(s.get("logic", "")),
                ))

        for t in parsed_yaml.get("themes", []) or []:
            if isinstance(t, dict) and t.get("name"):
                result.themes.append(ThemeMention(
                    name=str(t["name"]),
                    category=str(t.get("category", "")),
                ))

        return result

    except Exception as e:
        return ParsedResult(
            relevance=0, parse_failed=True,
            filter_reason=f"图片AI解析异常: {str(e)}",
        )

