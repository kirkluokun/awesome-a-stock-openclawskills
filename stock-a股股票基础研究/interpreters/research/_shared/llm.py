# interpreters/research/_shared/llm.py
"""Gemini LLM 工具"""

import json
import os
import re
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[5]
load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def init_genai():
    """初始化 Gemini"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    genai.configure(api_key=GEMINI_API_KEY)


def extract_insights(text: str) -> dict:
    """
    用 Gemini 提取研报摘要和观点
    
    Args:
        text: 研报文本
    
    Returns:
        {
            "summary": "摘要",
            "key_points": ["观点1", "观点2"],
            "investment_advice": "投资建议",
            "risk_warning": "风险提示"
        }
    """
    init_genai()
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    prompt = f"""分析以下券商研报内容，提取关键信息。

要求：
1. 摘要：100字以内概括核心内容
2. 核心观点：提取 3-5 个关键观点，每个 50 字以内
3. 投资建议：如有明确建议（买入/增持/中性/减持/卖出），提取出来
4. 风险提示：如有风险提示，简要列出

输出格式（严格 JSON）：
{{
    "summary": "...",
    "key_points": ["...", "..."],
    "investment_advice": "...",
    "risk_warning": "..."
}}

研报内容：
{text[:8000]}
"""
    
    try:
        response = model.generate_content(prompt)
        # 解析 JSON
        content = response.text
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass
    except Exception as e:
        print(f"LLM 调用失败: {e}")
    
    # 解析失败，返回空结构
    return {
        "summary": "",
        "key_points": [],
        "investment_advice": "",
        "risk_warning": ""
    }
