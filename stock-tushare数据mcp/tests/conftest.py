"""
测试配置

Mock tushare pro_api，避免测试依赖真实 API。
"""

import os
from unittest.mock import MagicMock

import pandas as pd
import pytest


@pytest.fixture(autouse=True)
def mock_tushare_env(monkeypatch):
    """确保测试环境有 TUSHARE_TOKEN"""
    monkeypatch.setenv("TUSHARE_TOKEN", "test_token_for_unit_tests")


@pytest.fixture(autouse=True)
def reset_client_singleton():
    """每个测试重置 client 模块的 _pro_api 单例"""
    from tushare_mcp import client
    client._pro_api = None
    yield
    client._pro_api = None


@pytest.fixture()
def mock_pro_api(monkeypatch):
    """
    Mock tushare.pro_api，返回可配置的 MagicMock。
    用法：在测试中设置 mock_pro_api.daily.return_value = some_df
    """
    mock_api = MagicMock()
    monkeypatch.setattr("tushare.pro_api", lambda token: mock_api)
    return mock_api


def make_df(data: dict) -> pd.DataFrame:
    """快速创建测试用 DataFrame"""
    return pd.DataFrame(data)
