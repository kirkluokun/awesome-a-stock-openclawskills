"""
Tushare MCP 异常类型定义

所有自定义异常都继承自 TushareError，方便统一捕获。
"""


class TushareError(Exception):
    """Tushare MCP 基础异常"""
    pass


class InsufficientPointsError(TushareError):
    """积分不足，无法调用该接口"""
    pass


class RateLimitError(TushareError):
    """API 调用频率超限"""
    pass


class ApiError(TushareError):
    """Tushare API 返回错误"""

    def __init__(self, api_name: str, message: str) -> None:
        self.api_name = api_name
        super().__init__(f"[{api_name}] {message}")


class TokenError(TushareError):
    """Token 未配置或无效"""
    pass
