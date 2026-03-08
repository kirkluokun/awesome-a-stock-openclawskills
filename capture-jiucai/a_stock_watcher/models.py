"""数据模型定义"""

from dataclasses import dataclass, field
from datetime import datetime
import hashlib


@dataclass
class Article:
    """原始文章条目"""
    title: str
    source: str  # study_hot | industry_chain | action
    url: str = ""
    content: str = ""  # 全文内容
    images: list[str] = field(default_factory=list)  # 图片路径列表
    publish_date: str = ""  # 发布日期
    fetched_at: str = field(default_factory=lambda: datetime.now().isoformat())
    content_hash: str = ""
    _parsed: object = field(default=None, repr=False)  # 已有的AI解析结果

    def __post_init__(self):
        if not self.content_hash:
            raw = f"{self.source}:{self.title}:{self.url}"
            self.content_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class StockMention:
    """文章中提及的股票"""
    code: str  # 股票代码，如 600519
    name: str  # 股票名称，如 贵州茅台
    context: str = ""  # 提及的上下文片段
    logic: str = ""  # 投资逻辑


@dataclass
class ThemeMention:
    """文章中涉及的主题"""
    name: str  # 主题名称，如 "白酒复苏"
    category: str = ""  # 分类，如 "消费"、"科技"


@dataclass
class ParsedResult:
    """AI 解析文章后的结构化结果"""
    relevance: int = 0  # 0-10，<5 自动丢弃
    publish_date: str = ""
    stocks: list[StockMention] = field(default_factory=list)
    themes: list[ThemeMention] = field(default_factory=list)
    logic_summary: str = ""
    raw_yaml: str = ""  # AI 原始输出
    parse_failed: bool = False
    filter_reason: str = ""  # 被过滤的原因
