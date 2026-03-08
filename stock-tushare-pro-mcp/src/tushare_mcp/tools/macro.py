"""
宏观经济 MCP Tools

包含：yc_cb（国债收益率曲线）, shibor_lpr（LPR贷款基础利率）, shibor（Shibor利率报价）,
      cn_gdp（国内生产总值）, cn_pmi（采购经理指数）, eco_cal（全球财经事件）,
      hibor, libor, us_tycr, us_trycr, us_tltr, us_trltr, us_tbr,
      cn_m（货币供应量）, sf_month（社融增量）, sge_basic/sge_daily（上海黄金）,
      gz_index（广州民间借贷利率）, wz_index（温州民间借贷利率）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将宏观利率相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_yc_cb(
        ts_code: Optional[str] = None,
        curve_type: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        curve_term: Optional[float] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询国债收益率曲线（中债），用于 WACC 无风险利率。

        Args:
            ts_code: 收益率曲线编码（如 1001.CB 国债收益率曲线）
            curve_type: 曲线类型（0到期 1即期）
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            curve_term: 期限（如 10.0 表示10年期）
            fields: 返回字段
            _format: 输出格式（json/markdown）
            _limit: 最大返回行数
        """
        try:
            df = client.yc_cb(
                ts_code=ts_code,
                curve_type=curve_type,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                curve_term=curve_term,
                fields=fields,
            )
            return format_response(df, "yc_cb", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_lpr(
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询LPR贷款基础利率，用于债务成本参考（WACC计算）。

        Args:
            date: 日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式（json/markdown）
            _limit: 最大返回行数
        """
        try:
            df = client.shibor_lpr(
                date=date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "shibor_lpr", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_shibor(
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询Shibor利率数据,含隔夜/1周/2周/1月/3月/6月/9月/1年各期限报价。积分要求:120。

        Args:
            date: 日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.shibor(
                date=date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "shibor", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_cn_gdp(
        q: Optional[str] = None,
        start_q: Optional[str] = None,
        end_q: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询国内生产总值(GDP),按季度发布。积分要求:600。

        Args:
            q: 季度(如2019Q1)
            start_q: 开始季度
            end_q: 结束季度
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.cn_gdp(
                q=q,
                start_q=start_q,
                end_q=end_q,
                fields=fields,
            )
            return format_response(df, "cn_gdp", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_cn_pmi(
        m: Optional[str] = None,
        start_m: Optional[str] = None,
        end_m: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询采购经理指数(PMI),含制造业和非制造业。积分要求:2000。

        Args:
            m: 月度(如202401)
            start_m: 开始月度
            end_m: 结束月度
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.cn_pmi(
                m=m,
                start_m=start_m,
                end_m=end_m,
                fields=fields,
            )
            return format_response(df, "cn_pmi", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_eco_cal(
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        currency: Optional[str] = None,
        country: Optional[str] = None,
        event: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询全球财经事件日历(央行利率决议、经济数据发布等)。积分要求:2000。

        Args:
            date: 日期
            start_date: 开始日期
            end_date: 结束日期
            currency: 货币代码
            country: 国家(如 中国、美国)
            event: 事件(支持模糊匹配)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.eco_cal(
                date=date,
                start_date=start_date,
                end_date=end_date,
                currency=currency,
                country=country,
                event=event,
                fields=fields,
            )
            return format_response(df, "eco_cal", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_hibor(
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询Hibor利率(香港银行同业拆借利率)。积分要求:120。

        Args:
            date: 日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.hibor(
                date=date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "hibor", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_libor(
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        curr_type: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询Libor利率(伦敦银行同业拆借利率)。积分要求:120。

        Args:
            date: 日期
            start_date: 开始日期
            end_date: 结束日期
            curr_type: 货币代码(USD/EUR/JPY/GBP/CHF,默认USD)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.libor(
                date=date,
                start_date=start_date,
                end_date=end_date,
                curr_type=curr_type,
                fields=fields,
            )
            return format_response(df, "libor", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_us_tycr(
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询美国国债收益率曲线利率。积分要求:120。

        Args:
            date: 日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段(如 m1,y1,y10)
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.us_tycr(
                date=date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "us_tycr", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_us_trycr(
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询美国国债实际收益率曲线利率(TIPS)。积分要求:120。

        Args:
            date: 日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.us_trycr(
                date=date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "us_trycr", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_us_tltr(
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询美国国债长期利率。积分要求:120。

        Args:
            date: 日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.us_tltr(
                date=date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "us_tltr", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_us_trltr(
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询美国国债长期利率平均值。积分要求:120。

        Args:
            date: 日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.us_trltr(
                date=date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "us_trltr", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_us_tbr(
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询美国短期国债利率。积分要求:120。

        Args:
            date: 日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段(如 w4_bd,w52_ce)
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.us_tbr(
                date=date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "us_tbr", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_cn_m(
        m: Optional[str] = None,
        start_m: Optional[str] = None,
        end_m: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询中国货币供应量(月度,M0/M1/M2)。积分要求:600。

        Args:
            m: 月度(如 202001)
            start_m: 开始月度
            end_m: 结束月度
            fields: 返回字段(如 month,m0,m1,m2)
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.cn_m(
                m=m,
                start_m=start_m,
                end_m=end_m,
                fields=fields,
            )
            return format_response(df, "cn_m", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_sf_month(
        m: Optional[str] = None,
        start_m: Optional[str] = None,
        end_m: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询社会融资增量(月度)。积分要求:2000。

        Args:
            m: 月份(YYYYMM,支持多个逗号分隔)
            start_m: 开始月份
            end_m: 结束月份
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.sf_month(
                m=m,
                start_m=start_m,
                end_m=end_m,
                fields=fields,
            )
            return format_response(df, "sf_month", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_sge_basic(
        ts_code: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询上海黄金基础信息(合约列表)。积分要求:5000。

        Args:
            ts_code: 合约代码(支持多个,逗号分隔)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.sge_basic(
                ts_code=ts_code,
                fields=fields,
            )
            return format_response(df, "sge_basic", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_sge_daily(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询上海黄金现货日行情。积分要求:2000。

        Args:
            ts_code: 合约代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.sge_daily(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "sge_daily", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_gz_index(
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询广州民间借贷利率。积分要求:2000。

        Args:
            date: 日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.gz_index(
                date=date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "gz_index", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_wz_index(
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询温州民间借贷利率。积分要求:2000。

        Args:
            date: 日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.wz_index(
                date=date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "wz_index", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
