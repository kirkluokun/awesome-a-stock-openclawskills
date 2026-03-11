"""
Tushare API 客户端 — 纯函数封装层

每个函数对应一个 tushare 接口，统一处理：
- 日期格式化（YYYY-MM-DD → YYYYMMDD）
- 频率限制
- 异常转换
- 自动持久化到 SQLite（data/tushare.db）
"""

import os
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import tushare as ts

from .errors import TushareError, TokenError, ApiError
from .rate_limiter import RateLimiter
from .storage import DataStore

logger = logging.getLogger(__name__)

# 模块级单例，所有函数共用
_rate_limiter = RateLimiter(min_interval=0.3)
_pro_api: Optional[ts.pro_api] = None
_data_store: Optional[DataStore] = None


def _get_store() -> DataStore:
    """获取或初始化 DataStore 单例"""
    global _data_store
    if _data_store is None:
        db_path = Path(__file__).parent.parent.parent / "data" / "tushare.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _data_store = DataStore(str(db_path))
    return _data_store


def _format_date(date_str: Optional[str]) -> Optional[str]:
    """统一日期格式为 YYYYMMDD，None 原样返回"""
    if date_str is None:
        return None
    return date_str.replace("-", "")


def _get_api() -> ts.pro_api:
    """获取或初始化 tushare pro_api 单例"""
    global _pro_api
    if _pro_api is None:
        token = os.getenv("TUSHARE_API_KEY")
        if not token:
            raise TokenError(
                "TUSHARE_API_KEY 环境变量未设置。"
                "请在 MCP 配置的 env 中添加 TUSHARE_API_KEY。"
            )
        _pro_api = ts.pro_api(token)
    return _pro_api


def _call_api(api_name: str, **kwargs) -> pd.DataFrame:
    """
    通用 API 调用入口

    自动处理频率限制、异常包装、数据持久化。
    传入的 None 值参数会被过滤掉，不传给 tushare。
    成功获取数据后自动保存到 SQLite（失败不影响返回）。
    """
    # 过滤 None 参数，tushare 不接受 None
    params = {k: v for k, v in kwargs.items() if v is not None}

    _rate_limiter.wait()

    # TokenError 不应被下面的 except 包装，直接向上抛
    pro = _get_api()

    try:
        func = getattr(pro, api_name)
        df = func(**params)
    except TushareError:
        raise
    except Exception as e:
        error_msg = str(e)
        if "积分" in error_msg or "权限" in error_msg:
            raise ApiError(api_name, f"积分不足或权限不够: {error_msg}") from e
        raise ApiError(api_name, error_msg) from e

    if df is None:
        return pd.DataFrame()

    # 自动持久化：存储失败不影响正常返回
    if not df.empty:
        try:
            _get_store().save(api_name, params, df)
        except Exception:
            logger.warning("数据保存失败（api=%s），不影响返回", api_name, exc_info=True)

    return df


# ==================== 股票数据 ====================


def stock_basic(
    ts_code: Optional[str] = None,
    name: Optional[str] = None,
    market: Optional[str] = None,
    list_status: Optional[str] = None,
    exchange: Optional[str] = None,
    is_hs: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    股票列表基础信息

    Args:
        ts_code: TS 股票代码（如 000001.SZ）
        name: 股票名称
        market: 市场类别（主板/创业板/科创板/CDR/北交所）
        list_status: 上市状态（L上市 D退市 P暂停），默认 L
        exchange: 交易所（SSE上交所 SZSE深交所 BSE北交所）
        is_hs: 是否沪深港通（N否 H沪股通 S深股通）
        fields: 返回字段，逗号分隔
    """
    return _call_api(
        "stock_basic",
        ts_code=ts_code,
        name=name,
        market=market,
        list_status=list_status,
        exchange=exchange,
        is_hs=is_hs,
        fields=fields,
    )


def trade_cal(
    exchange: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    is_open: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    交易日历

    Args:
        exchange: 交易所（SSE上交所 SZSE深交所），默认 SSE
        start_date: 开始日期
        end_date: 结束日期
        is_open: 是否交易（0休市 1交易）
        fields: 返回字段
    """
    return _call_api(
        "trade_cal",
        exchange=exchange,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        is_open=is_open,
        fields=fields,
    )


def daily(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    A股日线行情

    Args:
        ts_code: 股票代码（如 000001.SZ）
        trade_date: 交易日期（YYYYMMDD）
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "daily",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def daily_basic(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    每日指标（PE/PB/市值等）

    Args:
        ts_code: 股票代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "daily_basic",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def adj_factor(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    复权因子

    Args:
        ts_code: 股票代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "adj_factor",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 财务数据 ====================


def income(
    ts_code: str,
    ann_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    report_type: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    利润表

    Args:
        ts_code: 股票代码（必填）
        ann_date: 公告日期
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        period: 报告期（如 20231231）
        report_type: 报告类型
        fields: 返回字段
    """
    return _call_api(
        "income",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        period=_format_date(period),
        report_type=report_type,
        fields=fields,
    )


def balancesheet(
    ts_code: str,
    ann_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    report_type: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    资产负债表

    Args:
        ts_code: 股票代码（必填）
        ann_date: 公告日期
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        period: 报告期
        report_type: 报告类型
        fields: 返回字段
    """
    return _call_api(
        "balancesheet",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        period=_format_date(period),
        report_type=report_type,
        fields=fields,
    )


def cashflow(
    ts_code: str,
    ann_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    report_type: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    现金流量表

    Args:
        ts_code: 股票代码（必填）
        ann_date: 公告日期
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        period: 报告期
        report_type: 报告类型
        fields: 返回字段
    """
    return _call_api(
        "cashflow",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        period=_format_date(period),
        report_type=report_type,
        fields=fields,
    )


def fina_indicator(
    ts_code: str,
    ann_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    财务指标数据（ROE、净利润率等）

    Args:
        ts_code: 股票代码（必填）
        ann_date: 公告日期
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        period: 报告期
        fields: 返回字段
    """
    return _call_api(
        "fina_indicator",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        period=_format_date(period),
        fields=fields,
    )


# ==================== 指数数据 ====================


def index_daily(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    指数日线行情

    Args:
        ts_code: 指数代码（如 000300.SH 沪深300）
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "index_daily",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 宏观利率 ====================


def yc_cb(
    ts_code: Optional[str] = None,
    curve_type: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    curve_term: Optional[float] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    国债收益率曲线

    Args:
        ts_code: 收益率曲线编码（如 1001.CB 国债收益率曲线）
        curve_type: 曲线类型（0到期 1即期）
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        curve_term: 期限（如 10.0 表示10年期）
        fields: 返回字段
    """
    return _call_api(
        "yc_cb",
        ts_code=ts_code,
        curve_type=curve_type,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        curve_term=curve_term,
        fields=fields,
    )


def shibor_lpr(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    LPR 贷款基础利率

    Args:
        date: 日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "shibor_lpr",
        date=_format_date(date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 业绩数据 ====================


def forecast(
    ts_code: Optional[str] = None,
    ann_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    type: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    业绩预告

    Args:
        ts_code: 股票代码（与 ann_date 二选一）
        ann_date: 公告日期（与 ts_code 二选一）
        start_date: 公告开始日期
        end_date: 公告结束日期
        period: 报告期（如 20231231）
        type: 预告类型（预增/预减/扭亏/首亏/续亏/续盈/略增/略减）
        fields: 返回字段
    """
    return _call_api(
        "forecast",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        period=_format_date(period),
        type=type,
        fields=fields,
    )


def express(
    ts_code: str,
    ann_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    业绩快报

    Args:
        ts_code: 股票代码（必填）
        ann_date: 公告日期
        start_date: 公告开始日期
        end_date: 公告结束日期
        period: 报告期
        fields: 返回字段
    """
    return _call_api(
        "express",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        period=_format_date(period),
        fields=fields,
    )


# ==================== 券商预测 ====================


def report_rc(
    ts_code: Optional[str] = None,
    report_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    券商盈利预测数据

    Args:
        ts_code: 股票代码
        report_date: 报告日期
        start_date: 报告开始日期
        end_date: 报告结束日期
        fields: 返回字段
    """
    return _call_api(
        "report_rc",
        ts_code=ts_code,
        report_date=_format_date(report_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def research_report(
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    report_type: Optional[str] = None,
    ts_code: Optional[str] = None,
    inst_csname: Optional[str] = None,
    ind_name: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    券商研究报告（含PDF下载链接）

    历史数据从20170101开始，增量每天两次更新。需单独开权限。

    Args:
        trade_date: 研报日期
        start_date: 研报开始日期
        end_date: 研报结束日期
        report_type: 研报类别（个股研报/行业研报）
        ts_code: 股票代码
        inst_csname: 券商名称
        ind_name: 行业名称
        fields: 返回字段
    """
    return _call_api(
        "research_report",
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        report_type=report_type,
        ts_code=ts_code,
        inst_csname=inst_csname,
        ind_name=ind_name,
        fields=fields,
    )


# ==================== 行业分类 ====================


def index_classify(
    index_code: Optional[str] = None,
    level: Optional[str] = None,
    src: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    申万行业分类

    Args:
        index_code: 指数代码
        level: 行业级别（L1一级 L2二级 L3三级）
        src: 指数版本（SW2014 或 SW2021）
        fields: 返回字段
    """
    return _call_api(
        "index_classify",
        index_code=index_code,
        level=level,
        src=src,
        fields=fields,
    )


# ==================== 新闻 ====================


def news(
    start_date: str,
    end_date: str,
    src: str,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    新闻快讯

    Args:
        start_date: 开始日期时间（格式：2024-01-01 09:00:00）
        end_date: 结束日期时间
        src: 新闻来源（sina/wallstreetcn/10jqka/eastmoney/yuncaijing）
        fields: 返回字段
    """
    # 新闻接口的日期格式特殊，不做 YYYYMMDD 转换
    return _call_api(
        "news",
        start_date=start_date,
        end_date=end_date,
        src=src,
        fields=fields,
    )


# ==================== 融资融券 ====================


def margin(
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    exchange_id: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    融资融券汇总数据

    Args:
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        exchange_id: 交易所代码（SSE/SZSE/BSE）
        fields: 返回字段
    """
    return _call_api(
        "margin",
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        exchange_id=exchange_id,
        fields=fields,
    )


def margin_detail(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    融资融券交易明细

    Args:
        ts_code: 股票代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "margin_detail",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 龙虎榜 ====================


def top_list(
    trade_date: str,
    ts_code: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    龙虎榜每日明细

    Args:
        trade_date: 交易日期（必填）
        ts_code: 股票代码
        fields: 返回字段
    """
    return _call_api(
        "top_list",
        trade_date=_format_date(trade_date),
        ts_code=ts_code,
        fields=fields,
    )


def top_inst(
    trade_date: str,
    ts_code: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    龙虎榜机构交易明细

    Args:
        trade_date: 交易日期（必填）
        ts_code: 股票代码
        fields: 返回字段
    """
    return _call_api(
        "top_inst",
        trade_date=_format_date(trade_date),
        ts_code=ts_code,
        fields=fields,
    )


# ==================== 股东数据 ====================


def stk_holdernumber(
    ts_code: Optional[str] = None,
    ann_date: Optional[str] = None,
    enddate: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    股东户数

    Args:
        ts_code: 股票代码
        ann_date: 公告日期
        enddate: 截止日期
        start_date: 公告开始日期
        end_date: 公告结束日期
        fields: 返回字段
    """
    return _call_api(
        "stk_holdernumber",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        enddate=_format_date(enddate),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def top10_holders(
    ts_code: str,
    period: Optional[str] = None,
    ann_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    前十大股东

    Args:
        ts_code: 股票代码（必填）
        period: 报告期（YYYYMMDD）
        ann_date: 公告日期
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        fields: 返回字段
    """
    return _call_api(
        "top10_holders",
        ts_code=ts_code,
        period=_format_date(period),
        ann_date=_format_date(ann_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def top10_floatholders(
    ts_code: str,
    period: Optional[str] = None,
    ann_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    前十大流通股东

    Args:
        ts_code: 股票代码（必填）
        period: 报告期（YYYYMMDD）
        ann_date: 公告日期
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        fields: 返回字段
    """
    return _call_api(
        "top10_floatholders",
        ts_code=ts_code,
        period=_format_date(period),
        ann_date=_format_date(ann_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 公司行为 ====================


def dividend(
    ts_code: Optional[str] = None,
    ann_date: Optional[str] = None,
    record_date: Optional[str] = None,
    ex_date: Optional[str] = None,
    imp_ann_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    分红送股数据

    Args:
        ts_code: 股票代码（至少一个参数不能为空）
        ann_date: 公告日
        record_date: 股权登记日期
        ex_date: 除权除息日
        imp_ann_date: 实施公告日
        fields: 返回字段
    """
    return _call_api(
        "dividend",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        record_date=_format_date(record_date),
        ex_date=_format_date(ex_date),
        imp_ann_date=_format_date(imp_ann_date),
        fields=fields,
    )


def repurchase(
    ann_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    股票回购

    Args:
        ann_date: 公告日期
        start_date: 公告开始日期
        end_date: 公告结束日期
        fields: 返回字段
    """
    return _call_api(
        "repurchase",
        ann_date=_format_date(ann_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def share_float(
    ts_code: Optional[str] = None,
    ann_date: Optional[str] = None,
    float_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    限售股解禁

    Args:
        ts_code: 股票代码
        ann_date: 公告日期
        float_date: 解禁日期
        start_date: 解禁开始日期
        end_date: 解禁结束日期
        fields: 返回字段
    """
    return _call_api(
        "share_float",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        float_date=_format_date(float_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def pledge_stat(
    ts_code: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    股权质押统计

    Args:
        ts_code: 股票代码
        end_date: 截止日期
        fields: 返回字段
    """
    return _call_api(
        "pledge_stat",
        ts_code=ts_code,
        end_date=_format_date(end_date),
        fields=fields,
    )


def pledge_detail(
    ts_code: str,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    股权质押明细

    Args:
        ts_code: 股票代码（必填）
        fields: 返回字段
    """
    return _call_api(
        "pledge_detail",
        ts_code=ts_code,
        fields=fields,
    )


def stk_surv(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    机构调研数据

    Args:
        ts_code: 股票代码
        trade_date: 调研日期
        start_date: 调研开始日期
        end_date: 调研结束日期
        fields: 返回字段
    """
    return _call_api(
        "stk_surv",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 资金流向 ====================


def moneyflow(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    个股资金流向

    Args:
        ts_code: 股票代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "moneyflow",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def moneyflow_hsgt(
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    沪深港通资金流向

    Args:
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "moneyflow_hsgt",
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def hsgt_top10(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    market_type: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    沪深港通十大成交股

    Args:
        ts_code: 股票代码（与 trade_date 二选一）
        trade_date: 交易日期（与 ts_code 二选一）
        start_date: 开始日期
        end_date: 结束日期
        market_type: 市场类型（1沪市 3深市）
        fields: 返回字段
    """
    return _call_api(
        "hsgt_top10",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        market_type=market_type,
        fields=fields,
    )


def ggt_top10(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    market_type: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    港股通十大成交股

    Args:
        ts_code: 股票代码（与 trade_date 二选一）
        trade_date: 交易日期（与 ts_code 二选一）
        start_date: 开始日期
        end_date: 结束日期
        market_type: 市场类型（2港股通沪 4港股通深）
        fields: 返回字段
    """
    return _call_api(
        "ggt_top10",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        market_type=market_type,
        fields=fields,
    )


# ==================== 概念板块 ====================


def kpl_concept(
    trade_date: Optional[str] = None,
    ts_code: Optional[str] = None,
    name: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    概念板块列表（开盘啦数据源，每日盘后更新）

    Args:
        trade_date: 交易日期
        ts_code: 题材代码（xxxxxx.KP格式）
        name: 题材名称
        fields: 返回字段
    """
    return _call_api(
        "kpl_concept",
        trade_date=_format_date(trade_date),
        ts_code=ts_code,
        name=name,
        fields=fields,
    )


def kpl_concept_cons(
    trade_date: Optional[str] = None,
    ts_code: Optional[str] = None,
    con_code: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    概念板块成分股（开盘啦数据源）

    Args:
        trade_date: 交易日期
        ts_code: 题材代码（xxxxxx.KP格式）
        con_code: 成分股代码（如 000001.SZ）
        fields: 返回字段
    """
    return _call_api(
        "kpl_concept_cons",
        trade_date=_format_date(trade_date),
        ts_code=ts_code,
        con_code=con_code,
        fields=fields,
    )


# ==================== Shibor ====================


def shibor(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    Shibor 利率报价

    Args:
        date: 日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "shibor",
        date=_format_date(date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 港股行情 ====================


def hk_basic(
    ts_code: Optional[str] = None,
    list_status: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    港股基础信息

    Args:
        ts_code: TS代码（如 00001.HK）
        list_status: 上市状态（L上市 D退市 P暂停）
        fields: 返回字段
    """
    return _call_api(
        "hk_basic",
        ts_code=ts_code,
        list_status=list_status,
        fields=fields,
    )


def hk_tradecal(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    is_open: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    港股交易日历

    Args:
        start_date: 开始日期
        end_date: 结束日期
        is_open: 是否交易（0休市 1交易）
        fields: 返回字段
    """
    return _call_api(
        "hk_tradecal",
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        is_open=is_open,
        fields=fields,
    )


def hk_daily(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    港股日线行情

    Args:
        ts_code: 股票代码（如 00001.HK）
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "hk_daily",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def hk_adjfactor(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    港股复权因子

    Args:
        ts_code: 股票代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "hk_adjfactor",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def ggt_daily(
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    港股通每日成交统计

    Args:
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "ggt_daily",
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 港股财务 ====================


def hk_income(
    ts_code: str,
    period: Optional[str] = None,
    ind_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    港股利润表

    Args:
        ts_code: 股票代码（必填，如 00001.HK）
        period: 报告期（YYYYMMDD）
        ind_name: 指标名
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        fields: 返回字段
    """
    return _call_api(
        "hk_income",
        ts_code=ts_code,
        period=_format_date(period),
        ind_name=ind_name,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def hk_balancesheet(
    ts_code: str,
    period: Optional[str] = None,
    ind_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    港股资产负债表

    Args:
        ts_code: 股票代码（必填）
        period: 报告期（YYYYMMDD）
        ind_name: 指标名
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        fields: 返回字段
    """
    return _call_api(
        "hk_balancesheet",
        ts_code=ts_code,
        period=_format_date(period),
        ind_name=ind_name,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def hk_cashflow(
    ts_code: str,
    period: Optional[str] = None,
    ind_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    港股现金流量表

    Args:
        ts_code: 股票代码（必填）
        period: 报告期（YYYYMMDD）
        ind_name: 指标名
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        fields: 返回字段
    """
    return _call_api(
        "hk_cashflow",
        ts_code=ts_code,
        period=_format_date(period),
        ind_name=ind_name,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def hk_fina_indicator(
    ts_code: str,
    period: Optional[str] = None,
    report_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    港股财务指标（PE/PB/ROE等）

    Args:
        ts_code: 股票代码（必填）
        period: 报告期（YYYYMMDD）
        report_type: 报告期类型（Q1/Q2/Q3/Q4）
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        fields: 返回字段
    """
    return _call_api(
        "hk_fina_indicator",
        ts_code=ts_code,
        period=_format_date(period),
        report_type=report_type,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 美股行情 ====================


def us_basic(
    ts_code: Optional[str] = None,
    classify: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    美股基础信息

    Args:
        ts_code: 股票代码（如 AAPL）
        classify: 股票分类（ADR/GDR/EQ）
        fields: 返回字段
    """
    return _call_api(
        "us_basic",
        ts_code=ts_code,
        classify=classify,
        fields=fields,
    )


def us_tradecal(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    is_open: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    美股交易日历

    Args:
        start_date: 开始日期
        end_date: 结束日期
        is_open: 是否交易（0休市 1交易）
        fields: 返回字段
    """
    return _call_api(
        "us_tradecal",
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        is_open=is_open,
        fields=fields,
    )


def us_daily(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    美股日线行情（未复权）

    Args:
        ts_code: 股票代码（如 AAPL）
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "us_daily",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def us_adjfactor(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    美股复权因子

    Args:
        ts_code: 股票代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "us_adjfactor",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 美股财务 ====================


def us_income(
    ts_code: str,
    period: Optional[str] = None,
    ind_name: Optional[str] = None,
    report_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    美股利润表

    Args:
        ts_code: 股票代码（必填，如 AAPL）
        period: 报告期（YYYYMMDD，季度最后一天）
        ind_name: 指标名
        report_type: 报告期类型（Q1/Q2/Q3/Q4）
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        fields: 返回字段
    """
    return _call_api(
        "us_income",
        ts_code=ts_code,
        period=_format_date(period),
        ind_name=ind_name,
        report_type=report_type,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def us_balancesheet(
    ts_code: str,
    period: Optional[str] = None,
    ind_name: Optional[str] = None,
    report_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    美股资产负债表

    Args:
        ts_code: 股票代码（必填）
        period: 报告期（YYYYMMDD，季度最后一天）
        ind_name: 指标名
        report_type: 报告期类型（Q1/Q2/Q3/Q4）
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        fields: 返回字段
    """
    return _call_api(
        "us_balancesheet",
        ts_code=ts_code,
        period=_format_date(period),
        ind_name=ind_name,
        report_type=report_type,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def us_cashflow(
    ts_code: str,
    period: Optional[str] = None,
    ind_name: Optional[str] = None,
    report_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    美股现金流量表

    Args:
        ts_code: 股票代码（必填）
        period: 报告期（YYYYMMDD，季度最后一天）
        ind_name: 指标名
        report_type: 报告期类型（Q1/Q2/Q3/Q4）
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        fields: 返回字段
    """
    return _call_api(
        "us_cashflow",
        ts_code=ts_code,
        period=_format_date(period),
        ind_name=ind_name,
        report_type=report_type,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 基金 ====================


def fund_basic(
    ts_code: Optional[str] = None,
    market: Optional[str] = None,
    status: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    公募基金列表

    Args:
        ts_code: 基金代码
        market: 交易市场（E场内 O场外），默认 E
        status: 存续状态（D摘牌 I发行 L上市中）
        fields: 返回字段
    """
    return _call_api(
        "fund_basic",
        ts_code=ts_code,
        market=market,
        status=status,
        fields=fields,
    )


def fund_nav(
    ts_code: Optional[str] = None,
    nav_date: Optional[str] = None,
    market: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    公募基金净值

    Args:
        ts_code: 基金代码（与 nav_date 二选一）
        nav_date: 净值日期（与 ts_code 二选一）
        market: E场内 O场外
        start_date: 净值开始日期
        end_date: 净值结束日期
        fields: 返回字段
    """
    return _call_api(
        "fund_nav",
        ts_code=ts_code,
        nav_date=_format_date(nav_date),
        market=market,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def fund_div(
    ts_code: Optional[str] = None,
    ann_date: Optional[str] = None,
    ex_date: Optional[str] = None,
    pay_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    公募基金分红

    Args:
        ts_code: 基金代码（四选一）
        ann_date: 公告日（四选一）
        ex_date: 除息日（四选一）
        pay_date: 派息日（四选一）
        fields: 返回字段
    """
    return _call_api(
        "fund_div",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        ex_date=_format_date(ex_date),
        pay_date=_format_date(pay_date),
        fields=fields,
    )


def fund_portfolio(
    ts_code: Optional[str] = None,
    symbol: Optional[str] = None,
    ann_date: Optional[str] = None,
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    公募基金持仓（季度更新）

    Args:
        ts_code: 基金代码（三选一）
        symbol: 股票代码（三选一）
        ann_date: 公告日期（三选一）
        period: 季度
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        fields: 返回字段
    """
    return _call_api(
        "fund_portfolio",
        ts_code=ts_code,
        symbol=symbol,
        ann_date=_format_date(ann_date),
        period=_format_date(period),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def fund_company(
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    公募基金管理人列表

    Args:
        fields: 返回字段
    """
    return _call_api(
        "fund_company",
        fields=fields,
    )


def fund_manager(
    ts_code: Optional[str] = None,
    ann_date: Optional[str] = None,
    name: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    公募基金经理

    Args:
        ts_code: 基金代码（支持多只，逗号分隔）
        ann_date: 公告日期
        name: 基金经理姓名
        fields: 返回字段
    """
    return _call_api(
        "fund_manager",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        name=name,
        fields=fields,
    )


def fund_share(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    market: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    基金规模数据（含ETF份额）

    Args:
        ts_code: 基金代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        market: 市场代码（SH上交所 SZ深交所）
        fields: 返回字段
    """
    return _call_api(
        "fund_share",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        market=market,
        fields=fields,
    )


def fund_adj(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    基金复权因子

    Args:
        ts_code: 基金代码（支持多只输入）
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "fund_adj",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== ETF ====================


def fund_daily(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    场内基金/ETF日线行情

    Args:
        ts_code: 基金代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "fund_daily",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def etf_basic(
    ts_code: Optional[str] = None,
    index_code: Optional[str] = None,
    list_status: Optional[str] = None,
    exchange: Optional[str] = None,
    mgr: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    ETF基本信息

    Args:
        ts_code: ETF代码
        index_code: 跟踪指数代码
        list_status: 上市状态（L上市 D退市 P待上市）
        exchange: 交易所（SH上交所 SZ深交所）
        mgr: 管理人简称
        fields: 返回字段
    """
    return _call_api(
        "etf_basic",
        ts_code=ts_code,
        index_code=index_code,
        list_status=list_status,
        exchange=exchange,
        mgr=mgr,
        fields=fields,
    )


# ==================== 期货 ====================


def fut_mapping(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    期货主力与连续合约映射

    Args:
        ts_code: 合约代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "fut_mapping",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def fut_daily(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    南华期货指数日线行情

    Args:
        ts_code: 指数代码（以 .NH 结尾）
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "index_daily",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def fut_wsr(
    trade_date: Optional[str] = None,
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    exchange: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    仓单日报

    Args:
        trade_date: 交易日期
        symbol: 产品代码
        start_date: 开始日期
        end_date: 结束日期
        exchange: 交易所代码
        fields: 返回字段
    """
    return _call_api(
        "fut_wsr",
        trade_date=_format_date(trade_date),
        symbol=symbol,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        exchange=exchange,
        fields=fields,
    )


def ft_limit(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    exchange: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    期货合约涨跌停价格

    Args:
        ts_code: 合约代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        exchange: 交易所代码
        fields: 返回字段
    """
    return _call_api(
        "ft_limit",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        exchange=exchange,
        fields=fields,
    )


def fut_weekly_detail(
    week: Optional[str] = None,
    prd: Optional[str] = None,
    start_week: Optional[str] = None,
    end_week: Optional[str] = None,
    exchange: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    期货主要品种交易周报

    Args:
        week: 周期（如 202001 表示 2020 年第 1 周）
        prd: 期货品种（支持多品种逗号分隔）
        start_week: 开始周期
        end_week: 结束周期
        exchange: 交易所
        fields: 返回字段
    """
    return _call_api(
        "fut_weekly_detail",
        week=week,
        prd=prd,
        start_week=start_week,
        end_week=end_week,
        exchange=exchange,
        fields=fields,
    )


# ==================== 外汇 ====================


def fx_obasic(
    exchange: Optional[str] = None,
    classify: Optional[str] = None,
    ts_code: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    外汇基础信息（FXCM 交易商）

    Args:
        exchange: 交易商（如 FXCM）
        classify: 分类（FX/INDEX/COMMODITY/METAL/BUND/CRYPTO/FX_BASKET）
        ts_code: TS代码
        fields: 返回字段
    """
    return _call_api(
        "fx_obasic",
        exchange=exchange,
        classify=classify,
        ts_code=ts_code,
        fields=fields,
    )


def fx_daily(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    exchange: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    外汇日线行情

    Args:
        ts_code: TS代码（如 USDCNH.FXCM）
        trade_date: 交易日期（GMT）
        start_date: 开始日期
        end_date: 结束日期
        exchange: 交易商（如 FXCM）
        fields: 返回字段
    """
    return _call_api(
        "fx_daily",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        exchange=exchange,
        fields=fields,
    )


# ==================== 宏观经济 ====================


def cn_gdp(
    q: Optional[str] = None,
    start_q: Optional[str] = None,
    end_q: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    国内生产总值（GDP）

    Args:
        q: 季度（如 2019Q1）
        start_q: 开始季度
        end_q: 结束季度
        fields: 返回字段
    """
    return _call_api(
        "cn_gdp",
        q=q,
        start_q=start_q,
        end_q=end_q,
        fields=fields,
    )


def cn_pmi(
    m: Optional[str] = None,
    start_m: Optional[str] = None,
    end_m: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    采购经理指数（PMI）

    Args:
        m: 月度（如 202401）
        start_m: 开始月度
        end_m: 结束月度
        fields: 返回字段
    """
    return _call_api(
        "cn_pmi",
        m=m,
        start_m=start_m,
        end_m=end_m,
        fields=fields,
    )


# ==================== 期权 ====================


def opt_basic(
    ts_code: Optional[str] = None,
    exchange: Optional[str] = None,
    opt_code: Optional[str] = None,
    call_put: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    期权合约信息

    Args:
        ts_code: TS期权代码
        exchange: 交易所代码（SSE/SZSE/CFFEX/DCE/SHFE/CZCE）
        opt_code: 标准合约代码
        call_put: 期权类型（C认购 P认沽）
        fields: 返回字段
    """
    return _call_api(
        "opt_basic",
        ts_code=ts_code,
        exchange=exchange,
        opt_code=opt_code,
        call_put=call_put,
        fields=fields,
    )


def opt_daily(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    exchange: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    期权日线行情

    Args:
        ts_code: TS合约代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        exchange: 交易所代码
        fields: 返回字段
    """
    return _call_api(
        "opt_daily",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        exchange=exchange,
        fields=fields,
    )


# ==================== 可转债 ====================


def cb_basic(
    ts_code: Optional[str] = None,
    list_date: Optional[str] = None,
    exchange: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    可转债基础信息

    Args:
        ts_code: 转债代码
        list_date: 上市日期
        exchange: 交易所代码
        fields: 返回字段
    """
    return _call_api(
        "cb_basic",
        ts_code=ts_code,
        list_date=_format_date(list_date),
        exchange=exchange,
        fields=fields,
    )


def cb_daily(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    可转债行情

    Args:
        ts_code: 转债代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "cb_daily",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def cb_issue(
    ts_code: Optional[str] = None,
    ann_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    可转债发行

    Args:
        ts_code: 转债代码
        ann_date: 公告日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "cb_issue",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def cb_rate(
    ts_code: str,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    可转债票面利率

    Args:
        ts_code: 转债代码（必填）
        fields: 返回字段
    """
    return _call_api(
        "cb_rate",
        ts_code=ts_code,
        fields=fields,
    )


def cb_call(
    ts_code: Optional[str] = None,
    ann_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    可转债赎回信息

    Args:
        ts_code: 转债代码
        ann_date: 公告日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "cb_call",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def cb_share(
    ts_code: str,
    ann_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    可转债转股结果

    Args:
        ts_code: 转债代码（必填）
        ann_date: 公告日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "cb_share",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def cb_price_chg(
    ts_code: str,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    可转债转股价变动

    Args:
        ts_code: 转债代码（必填）
        fields: 返回字段
    """
    return _call_api(
        "cb_price_chg",
        ts_code=ts_code,
        fields=fields,
    )


def repo_daily(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    债券回购日行情

    Args:
        ts_code: 回购代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "repo_daily",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 指数扩展 ====================


def index_basic(
    ts_code: Optional[str] = None,
    name: Optional[str] = None,
    market: Optional[str] = None,
    publisher: Optional[str] = None,
    category: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    指数基本信息

    Args:
        ts_code: 指数代码
        name: 指数简称
        market: 交易所或服务商
        publisher: 发布商
        category: 指数类别
        fields: 返回字段
    """
    return _call_api(
        "index_basic",
        ts_code=ts_code,
        name=name,
        market=market,
        publisher=publisher,
        category=category,
        fields=fields,
    )


def index_weight(
    index_code: str,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    指数成分和权重

    Args:
        index_code: 指数代码（必填，如 000300.SH）
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "index_weight",
        index_code=index_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def index_weekly(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    指数周线行情

    Args:
        ts_code: 指数代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "index_weekly",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def index_monthly(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    指数月线行情

    Args:
        ts_code: 指数代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "index_monthly",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def sw_daily(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    申万行业指数日行情（含 PE/PB 实时值）

    Args:
        ts_code: 指数代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "sw_daily",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== A股行情扩展 ====================


def weekly(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    A股周线行情

    Args:
        ts_code: 股票代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "weekly",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def monthly(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    A股月线行情

    Args:
        ts_code: 股票代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "monthly",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def stk_limit(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    每日涨跌停价格

    Args:
        ts_code: 股票代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "stk_limit",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 财务补充 ====================


def fina_audit(
    ts_code: str,
    ann_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    财务审计意见

    Args:
        ts_code: 股票代码（必填）
        ann_date: 公告日期
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        period: 报告期
        fields: 返回字段
    """
    return _call_api(
        "fina_audit",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        period=_format_date(period),
        fields=fields,
    )


def fina_mainbz(
    ts_code: str,
    period: Optional[str] = None,
    type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    主营业务构成

    Args:
        ts_code: 股票代码（必填）
        period: 报告期（YYYYMMDD）
        type: 类型（P按产品 D按地区，默认P）
        start_date: 报告期开始日期
        end_date: 报告期结束日期
        fields: 返回字段
    """
    return _call_api(
        "fina_mainbz",
        ts_code=ts_code,
        period=_format_date(period),
        type=type,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def disclosure_date(
    ts_code: Optional[str] = None,
    end_date: Optional[str] = None,
    pre_date: Optional[str] = None,
    actual_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    财报披露日期

    Args:
        ts_code: 股票代码
        end_date: 财报周期（如 20231231）
        pre_date: 计划披露日期
        actual_date: 实际披露日期
        fields: 返回字段
    """
    return _call_api(
        "disclosure_date",
        ts_code=ts_code,
        end_date=_format_date(end_date),
        pre_date=_format_date(pre_date),
        actual_date=_format_date(actual_date),
        fields=fields,
    )


# ==================== 公告与研究 ====================


def anns(
    ts_code: Optional[str] = None,
    ann_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    上市公司公告（全量）

    Args:
        ts_code: 股票代码
        ann_date: 公告日期
        start_date: 公告开始日期
        end_date: 公告结束日期
        fields: 返回字段
    """
    return _call_api(
        "anns_d",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def stk_managers(
    ts_code: Optional[str] = None,
    ann_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    上市公司管理层

    Args:
        ts_code: 股票代码（支持多个）
        ann_date: 公告日期
        start_date: 公告开始日期
        end_date: 公告结束日期
        fields: 返回字段
    """
    return _call_api(
        "stk_managers",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def broker_recommend(
    month: str,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    券商月度金股

    Args:
        month: 月度（YYYYMM 格式，必填）
        fields: 返回字段
    """
    return _call_api(
        "broker_recommend",
        month=month,
        fields=fields,
    )


# ==================== 股票信息扩展 ====================


def namechange(
    ts_code: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    股票曾用名

    Args:
        ts_code: TS 股票代码
        start_date: 公告开始日期
        end_date: 公告结束日期
        fields: 返回字段
    """
    return _call_api(
        "namechange",
        ts_code=ts_code,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def suspend_d(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    suspend_type: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    每日停复牌信息

    Args:
        ts_code: 股票代码（可输入多值）
        trade_date: 交易日期
        start_date: 停复牌查询开始日期
        end_date: 停复牌查询结束日期
        suspend_type: 停复牌类型（S 停牌 R 复牌）
        fields: 返回字段
    """
    return _call_api(
        "suspend_d",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        suspend_type=suspend_type,
        fields=fields,
    )


def new_share(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    IPO 新股列表

    Args:
        start_date: 上网发行开始日期
        end_date: 上网发行结束日期
        fields: 返回字段
    """
    return _call_api(
        "new_share",
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 同花顺板块 ====================


def ths_index(
    ts_code: Optional[str] = None,
    exchange: Optional[str] = None,
    type: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    同花顺概念和行业指数

    Args:
        ts_code: 指数代码
        exchange: 市场类型（A-A股 HK-港股 US-美股）
        type: 指数类型（N-概念 I-行业 R-地域 S-特色 ST-风格 TH-主题 BB-宽基）
        fields: 返回字段
    """
    return _call_api(
        "ths_index",
        ts_code=ts_code,
        exchange=exchange,
        type=type,
        fields=fields,
    )


def ths_daily(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    同花顺板块指数行情

    Args:
        ts_code: 指数代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "ths_daily",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def ths_member(
    ts_code: Optional[str] = None,
    con_code: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    同花顺概念板块成分

    Args:
        ts_code: 板块指数代码
        con_code: 股票代码
        fields: 返回字段
    """
    return _call_api(
        "ths_member",
        ts_code=ts_code,
        con_code=con_code,
        fields=fields,
    )


# ==================== 大宗交易 ====================


def block_trade(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    大宗交易

    Args:
        ts_code: 股票代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "block_trade",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 股东增减持与港股通持股 ====================


def stk_holdertrade(
    ts_code: Optional[str] = None,
    ann_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    trade_type: Optional[str] = None,
    holder_type: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    股东增减持

    Args:
        ts_code: TS 股票代码
        ann_date: 公告日期
        start_date: 公告开始日期
        end_date: 公告结束日期
        trade_type: 交易类型（IN 增持 DE 减持）
        holder_type: 股东类型（C 公司 P 个人 G 高管）
        fields: 返回字段
    """
    return _call_api(
        "stk_holdertrade",
        ts_code=ts_code,
        ann_date=_format_date(ann_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        trade_type=trade_type,
        holder_type=holder_type,
        fields=fields,
    )


def ccass_hold(
    ts_code: Optional[str] = None,
    hk_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    中央结算系统持股明细（港股通持股）

    Args:
        ts_code: 股票代码（如 605009.SH）
        hk_code: 港交所代码（如 95009）
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "ccass_hold_detail",
        ts_code=ts_code,
        hk_code=hk_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def ccass_hold_stat(
    ts_code: Optional[str] = None,
    hk_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    中央结算系统持股汇总

    按交易所披露，当日数据在下一交易日早上 9 点前入库。积分要求：120+。

    Args:
        ts_code: 股票代码（如 605009.SH）
        hk_code: 港交所代码（如 95009）
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "ccass_hold",
        ts_code=ts_code,
        hk_code=hk_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def stk_nineturn(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    freq: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    神奇九转指标（TD序列）

    数据从 20230101 开始，每天 21 点更新，积分要求：6000。
    trade_date/start_date/end_date 使用 datetime 格式（YYYY-MM-DD HH:MM:SS），不做日期转换。

    Args:
        ts_code: 股票代码
        trade_date: 交易日期（格式：YYYY-MM-DD HH:MM:SS）
        freq: 频率（daily）
        start_date: 开始时间
        end_date: 结束时间
        fields: 返回字段
    """
    return _call_api(
        "stk_nineturn",
        ts_code=ts_code,
        trade_date=trade_date,
        freq=freq,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )


# ==================== Phase 5d-1: 金融基础补全 ====================


def stock_company(
    ts_code: Optional[str] = None,
    exchange: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    上市公司基本信息（注册地、法人、总经理、董秘等）

    Args:
        ts_code: 股票代码
        exchange: 交易所代码（SSE/SZSE/BSE）
        fields: 返回字段
    """
    return _call_api(
        "stock_company",
        ts_code=ts_code,
        exchange=exchange,
        fields=fields,
    )


def stock_hsgt(
    type: str,
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    沪深港通股票列表

    Args:
        type: 类型（必填，HK_SZ/SZ_HK/HK_SH/SH_HK）
        ts_code: 股票代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "stock_hsgt",
        type=type,
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def stock_st(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    ST 股票列表

    Args:
        ts_code: 股票代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "stock_st",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def stk_ah_comparison(
    hk_code: Optional[str] = None,
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    AH 股比价数据

    Args:
        hk_code: 港股股票代码（xxxxx.HK）
        ts_code: A 股股票代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "stk_ah_comparison",
        hk_code=hk_code,
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def stk_factor_pro(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    股票每日技术面因子（专业版）

    含 MA/MACD/KDJ/BOLL/RSI/WR/CCI 等指标，后缀 _bfq 不复权，_qfq 前复权，_hfq 后复权。
    积分要求：5000+，单次最多 10000 条。

    Args:
        ts_code: 股票代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段（默认返回全部）
    """
    return _call_api(
        "stk_factor_pro",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def index_global(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    国际主要指数日线行情

    Args:
        ts_code: TS 指数代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "index_global",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def index_dailybasic(
    trade_date: Optional[str] = None,
    ts_code: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    大盘指数每日指标（市盈率、换手率等）

    Args:
        trade_date: 交易日期
        ts_code: TS 代码
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "index_dailybasic",
        trade_date=_format_date(trade_date),
        ts_code=ts_code,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def daily_info(
    trade_date: Optional[str] = None,
    ts_code: Optional[str] = None,
    exchange: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    沪深市场每日交易统计

    Args:
        trade_date: 交易日期
        ts_code: 板块代码
        exchange: 股票市场（SH/SZ）
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "daily_info",
        trade_date=_format_date(trade_date),
        ts_code=ts_code,
        exchange=exchange,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def fut_basic(
    exchange: str,
    fut_type: Optional[str] = None,
    fut_code: Optional[str] = None,
    list_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    期货合约列表

    Args:
        exchange: 交易所代码（必填，CFFEX/DCE/CZCE/SHFE/INE/GFEX）
        fut_type: 合约类型（1 普通 2 主力与连续）
        fut_code: 标准合约代码
        list_date: 上市开始日期
        fields: 返回字段
    """
    return _call_api(
        "fut_basic",
        exchange=exchange,
        fut_type=fut_type,
        fut_code=fut_code,
        list_date=_format_date(list_date),
        fields=fields,
    )


def stk_rewards(
    ts_code: str,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    管理层薪酬和持股

    Args:
        ts_code: TS 股票代码（必填）
        end_date: 报告期
        fields: 返回字段
    """
    return _call_api(
        "stk_rewards",
        ts_code=ts_code,
        end_date=_format_date(end_date),
        fields=fields,
    )


def index_member_all(
    l1_code: Optional[str] = None,
    l2_code: Optional[str] = None,
    l3_code: Optional[str] = None,
    ts_code: Optional[str] = None,
    is_new: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    申万行业成分（分级）

    Args:
        l1_code: 一级行业代码
        l2_code: 二级行业代码
        l3_code: 三级行业代码
        ts_code: 股票代码
        is_new: 是否最新（Y/N，默认 Y）
        fields: 返回字段
    """
    return _call_api(
        "index_member_all",
        l1_code=l1_code,
        l2_code=l2_code,
        l3_code=l3_code,
        ts_code=ts_code,
        is_new=is_new,
        fields=fields,
    )


def ci_daily(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    中信行业指数日行情

    Args:
        ts_code: 行业代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "ci_daily",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def ci_index_member(
    l1_code: Optional[str] = None,
    l2_code: Optional[str] = None,
    l3_code: Optional[str] = None,
    ts_code: Optional[str] = None,
    is_new: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    中信行业成分

    Args:
        l1_code: 一级行业代码
        l2_code: 二级行业代码
        l3_code: 三级行业代码
        ts_code: 股票代码
        is_new: 是否最新（Y/N，默认 Y）
        fields: 返回字段
    """
    return _call_api(
        "ci_index_member",
        l1_code=l1_code,
        l2_code=l2_code,
        l3_code=l3_code,
        ts_code=ts_code,
        is_new=is_new,
        fields=fields,
    )


def eco_cal(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    currency: Optional[str] = None,
    country: Optional[str] = None,
    event: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    全球财经事件日历

    Args:
        date: 日期
        start_date: 开始日期
        end_date: 结束日期
        currency: 货币代码
        country: 国家（如 中国、美国）
        event: 事件（支持模糊匹配）
        fields: 返回字段
    """
    return _call_api(
        "eco_cal",
        date=_format_date(date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        currency=currency,
        country=country,
        event=event,
        fields=fields,
    )


def cctv_news(
    date: str,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    新闻联播文字稿

    Args:
        date: 日期（必填，YYYYMMDD）
        fields: 返回字段
    """
    return _call_api(
        "cctv_news",
        date=_format_date(date),
        fields=fields,
    )


# ==================== Phase 5d-2: 利率/宏观/黄金 ====================


def hibor(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    Hibor 利率（香港银行同业拆借利率）

    Args:
        date: 日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "hibor",
        date=_format_date(date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def libor(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    curr_type: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    Libor 利率（伦敦银行同业拆借利率）

    Args:
        date: 日期
        start_date: 开始日期
        end_date: 结束日期
        curr_type: 货币代码（USD/EUR/JPY/GBP/CHF，默认 USD）
        fields: 返回字段
    """
    return _call_api(
        "libor",
        date=_format_date(date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        curr_type=curr_type,
        fields=fields,
    )


def us_tycr(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    美国国债收益率曲线利率

    Args:
        date: 日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段（如 m1,y1）
    """
    return _call_api(
        "us_tycr",
        date=_format_date(date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def us_trycr(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    美国国债实际收益率曲线利率（TIPS）

    Args:
        date: 日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "us_trycr",
        date=_format_date(date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def us_tltr(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    美国国债长期利率

    Args:
        date: 日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "us_tltr",
        date=_format_date(date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def us_trltr(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    美国国债长期利率平均值

    Args:
        date: 日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "us_trltr",
        date=_format_date(date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def us_tbr(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    美国短期国债利率

    Args:
        date: 日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段（如 w4_bd,w52_ce）
    """
    return _call_api(
        "us_tbr",
        date=_format_date(date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def cn_m(
    m: Optional[str] = None,
    start_m: Optional[str] = None,
    end_m: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    中国货币供应量（月度，M0/M1/M2）

    Args:
        m: 月度（如 202001）
        start_m: 开始月度
        end_m: 结束月度
        fields: 返回字段（如 month,m0,m1,m2）
    """
    return _call_api(
        "cn_m",
        m=m,
        start_m=start_m,
        end_m=end_m,
        fields=fields,
    )


def sf_month(
    m: Optional[str] = None,
    start_m: Optional[str] = None,
    end_m: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    社会融资增量（月度）

    Args:
        m: 月份（YYYYMM，支持多个逗号分隔）
        start_m: 开始月份
        end_m: 结束月份
        fields: 返回字段
    """
    return _call_api(
        "sf_month",
        m=m,
        start_m=start_m,
        end_m=end_m,
        fields=fields,
    )


def sge_basic(
    ts_code: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    上海黄金基础信息

    Args:
        ts_code: 合约代码（支持多个，逗号分隔）
        fields: 返回字段
    """
    return _call_api(
        "sge_basic",
        ts_code=ts_code,
        fields=fields,
    )


def sge_daily(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    上海黄金现货日行情

    Args:
        ts_code: 合约代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "sge_daily",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def gz_index(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    广州民间借贷利率

    Args:
        date: 日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "gz_index",
        date=_format_date(date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def wz_index(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    温州民间借贷利率

    Args:
        date: 日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "wz_index",
        date=_format_date(date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 东财板块 ====================


def dc_index(
    ts_code: Optional[str] = None,
    name: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    东财概念和行业指数行情

    Args:
        ts_code: 指数代码
        name: 指数名称
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "dc_index",
        ts_code=ts_code,
        name=name,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def dc_member(
    ts_code: Optional[str] = None,
    con_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    东财概念和行业板块成分

    Args:
        ts_code: 板块指数代码
        con_code: 成分股代码
        trade_date: 交易日期
        fields: 返回字段
    """
    return _call_api(
        "dc_member",
        ts_code=ts_code,
        con_code=con_code,
        trade_date=_format_date(trade_date),
        fields=fields,
    )


def dc_hot(
    trade_date: Optional[str] = None,
    ts_code: Optional[str] = None,
    market: Optional[str] = None,
    hot_type: Optional[str] = None,
    is_new: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    东财人气榜（热股数据）

    Args:
        trade_date: 交易日期
        ts_code: 股票代码
        market: 市场
        hot_type: 热度类型
        is_new: 是否最新
        fields: 返回字段
    """
    return _call_api(
        "dc_hot",
        trade_date=_format_date(trade_date),
        ts_code=ts_code,
        market=market,
        hot_type=hot_type,
        is_new=is_new,
        fields=fields,
    )


# ==================== 通达信板块 ====================


def tdx_index(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    idx_type: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    通达信板块指数行情

    Args:
        ts_code: 指数代码
        trade_date: 交易日期
        idx_type: 指数类型
        fields: 返回字段
    """
    return _call_api(
        "tdx_index",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        idx_type=idx_type,
        fields=fields,
    )


def tdx_daily(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    通达信板块指数日线行情

    Args:
        ts_code: 指数代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "tdx_daily",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def tdx_member(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    通达信板块成分

    Args:
        ts_code: 板块指数代码
        trade_date: 交易日期
        fields: 返回字段
    """
    return _call_api(
        "tdx_member",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        fields=fields,
    )


# ==================== 涨跌停 ====================


def limit_list_d(
    trade_date: Optional[str] = None,
    ts_code: Optional[str] = None,
    limit_type: Optional[str] = None,
    exchange: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    每日涨跌停统计（涨停/跌停/炸板）

    Args:
        trade_date: 交易日期
        ts_code: 股票代码
        limit_type: 涨跌停类型(U涨停 D跌停 Z炸板)
        exchange: 交易所
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "limit_list_d",
        trade_date=_format_date(trade_date),
        ts_code=ts_code,
        limit_type=limit_type,
        exchange=exchange,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def limit_cpt_list(
    trade_date: Optional[str] = None,
    ts_code: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    涨停股票连板天梯

    Args:
        trade_date: 交易日期
        ts_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "limit_cpt_list",
        trade_date=_format_date(trade_date),
        ts_code=ts_code,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== ETF 补充 ====================


def etf_share_size(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    exchange: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    ETF每日份额规模

    Args:
        ts_code: ETF代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        exchange: 交易所(SH/SZ)
        fields: 返回字段
    """
    return _call_api(
        "etf_share_size",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        exchange=exchange,
        fields=fields,
    )


def etf_index(
    ts_code: Optional[str] = None,
    pub_date: Optional[str] = None,
    base_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    ETF跟踪指数基准信息

    Args:
        ts_code: ETF代码
        pub_date: 发布日期
        base_date: 基日
        fields: 返回字段
    """
    return _call_api(
        "etf_index",
        ts_code=ts_code,
        pub_date=_format_date(pub_date),
        base_date=_format_date(base_date),
        fields=fields,
    )


# ==================== 筹码分析 ====================


def cyq_chips(
    ts_code: str,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    筹码分布

    Args:
        ts_code: 股票代码（必填）
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "cyq_chips",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


def cyq_perf(
    ts_code: str,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    筹码分布指标

    Args:
        ts_code: 股票代码（必填）
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "cyq_perf",
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 游资 ====================


def hm_list(
    name: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    游资名录

    Args:
        name: 游资名称
        fields: 返回字段
    """
    return _call_api(
        "hm_list",
        name=name,
        fields=fields,
    )


def hm_detail(
    trade_date: Optional[str] = None,
    ts_code: Optional[str] = None,
    hm_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    游资每日明细

    Args:
        trade_date: 交易日期
        ts_code: 股票代码
        hm_name: 游资名称
        start_date: 开始日期
        end_date: 结束日期
        fields: 返回字段
    """
    return _call_api(
        "hm_detail",
        trade_date=_format_date(trade_date),
        ts_code=ts_code,
        hm_name=hm_name,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        fields=fields,
    )


# ==================== 期货补充 ====================


def fut_settle(
    trade_date: Optional[str] = None,
    ts_code: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    exchange: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    期货结算参数

    Args:
        trade_date: 交易日期
        ts_code: 合约代码
        start_date: 开始日期
        end_date: 结束日期
        exchange: 交易所代码
        fields: 返回字段
    """
    return _call_api(
        "fut_settle",
        trade_date=_format_date(trade_date),
        ts_code=ts_code,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        exchange=exchange,
        fields=fields,
    )


def fut_holding(
    trade_date: Optional[str] = None,
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    exchange: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    期货每日持仓排名

    Args:
        trade_date: 交易日期
        symbol: 品种代码
        start_date: 开始日期
        end_date: 结束日期
        exchange: 交易所代码
        fields: 返回字段
    """
    return _call_api(
        "fut_holding",
        trade_date=_format_date(trade_date),
        symbol=symbol,
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        exchange=exchange,
        fields=fields,
    )


def fut_wm(
    freq: str,
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    exchange: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    期货周/月线行情

    Args:
        freq: 频率（必填，W周线/M月线）
        ts_code: 合约代码
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
        exchange: 交易所代码
        fields: 返回字段
    """
    return _call_api(
        "fut_weekly_monthly",
        freq=freq,
        ts_code=ts_code,
        trade_date=_format_date(trade_date),
        start_date=_format_date(start_date),
        end_date=_format_date(end_date),
        exchange=exchange,
        fields=fields,
    )


# ==================== 分钟行情 ====================
# 注意：分钟行情的 start_date/end_date 使用 datetime 格式
# （YYYY-MM-DD HH:MM:SS 或 YYYYMMDD），不走 _format_date


def stk_mins(
    ts_code: str,
    freq: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    A股分钟行情

    Args:
        ts_code: 股票代码（必填）
        freq: 频率（必填，1min/5min/15min/30min/60min）
        start_date: 开始时间（支持 YYYYMMDD HH:MM:SS）
        end_date: 结束时间
        fields: 返回字段
    """
    return _call_api(
        "stk_mins",
        ts_code=ts_code,
        freq=freq,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )


def hk_mins(
    ts_code: str,
    freq: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    港股分钟行情

    Args:
        ts_code: 港股代码（必填）
        freq: 频率（必填，1min/5min/15min/30min/60min）
        start_date: 开始时间
        end_date: 结束时间
        fields: 返回字段
    """
    return _call_api(
        "hk_mins",
        ts_code=ts_code,
        freq=freq,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )


def etf_mins(
    ts_code: str,
    freq: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    ETF分钟行情

    Args:
        ts_code: ETF代码（必填）
        freq: 频率（必填，1min/5min/15min/30min/60min）
        start_date: 开始时间
        end_date: 结束时间
        fields: 返回字段
    """
    return _call_api(
        "etf_mins",
        ts_code=ts_code,
        freq=freq,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )


def opt_mins(
    ts_code: str,
    freq: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    期权分钟行情

    Args:
        ts_code: 期权合约代码（必填）
        freq: 频率（必填，1min/5min/15min/30min/60min）
        start_date: 开始时间
        end_date: 结束时间
        fields: 返回字段
    """
    return _call_api(
        "opt_mins",
        ts_code=ts_code,
        freq=freq,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )


def rt_min(
    ts_code: str,
    freq: str,
    fields: Optional[str] = None,
) -> pd.DataFrame:
    """
    实时分钟行情（需特殊权限）

    Args:
        ts_code: 股票代码（必填）
        freq: 频率（必填）
        fields: 返回字段
    """
    return _call_api(
        "rt_min",
        ts_code=ts_code,
        freq=freq,
        fields=fields,
    )
