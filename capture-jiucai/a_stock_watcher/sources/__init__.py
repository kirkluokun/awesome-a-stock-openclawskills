"""数据源注册表"""

from .study_hot import StudyHotScraper
from .industry_chain import IndustryChainScraper
from .action import ActionScraper

# source_name → Scraper 类的映射
import functools

# source_name → Scraper 工厂（带默认参数）
SOURCES = {
    "study_hot": StudyHotScraper,                                         # scroll_rounds=5 → limit=25
    "industry_chain": IndustryChainScraper,                               # max_items=15
    "action": functools.partial(ActionScraper, lookback_days=2),          # 日常增量只拉近 2 天
}

__all__ = ["SOURCES", "StudyHotScraper", "IndustryChainScraper", "ActionScraper"]
