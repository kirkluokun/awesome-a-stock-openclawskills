#!/usr/bin/env python3
"""
冈特斯开放平台公共 HTTP 客户端。

职责：
  - Token 获取与文件缓存（1 小时 TTL）
  - 统一 HTTP 请求封装（POST/GET）
  - SSL context 复用
  - 统一错误处理
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
import ssl
from pathlib import Path

# 路径常量
SKILL_ROOT = Path(__file__).parent.parent
TOKEN_CACHE_FILE = SKILL_ROOT / ".token_cache"

# API 常量
BASE_URL = "https://open.gangtise.com"
LOGIN_ENDPOINT = "/application/auth/oauth/open/loginV2"
TOKEN_TTL = 3500  # 缓存有效期（秒），略小于服务端 3600 秒

# 全局 SSL context（复用，避免每次创建）
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


# ─── 凭证加载 ───────────────────────────────────────────

# 复用 configure.py 的凭证逻辑
sys.path.insert(0, str(Path(__file__).parent))
from configure import get_credentials, check_configured


def require_configured() -> None:
    """检查凭证是否可用，不可用则退出。"""
    if not check_configured():
        print("未配置凭证，请先设置环境变量或运行 python3 scripts/configure.py", file=sys.stderr)
        sys.exit(1)


# ─── Token 缓存 ─────────────────────────────────────────

def _read_cached_token() -> str | None:
    """从缓存文件读取未过期的 token。"""
    if not TOKEN_CACHE_FILE.exists():
        return None
    try:
        with open(TOKEN_CACHE_FILE, 'r') as f:
            cache = json.load(f)
        # 检查是否过期
        if time.time() - cache.get('ts', 0) < TOKEN_TTL:
            return cache.get('token')
    except Exception:
        pass
    return None


def _write_cached_token(token: str) -> None:
    """将 token 写入缓存文件。"""
    try:
        with open(TOKEN_CACHE_FILE, 'w') as f:
            json.dump({'token': token, 'ts': time.time()}, f)
        os.chmod(TOKEN_CACHE_FILE, 0o600)
    except Exception:
        pass  # 缓存写入失败不影响功能


def get_token() -> str | None:
    """
    获取 access token（带缓存）。

    优先读缓存，未命中则调用 loginV2 并缓存。
    返回值已包含 Bearer 前缀。
    """
    # 1. 尝试缓存
    cached = _read_cached_token()
    if cached:
        return cached

    # 2. 调用 loginV2
    ak, sk = get_credentials()
    if not ak or not sk:
        return None

    data = {"accessKey": ak, "secretAccessKey": sk}
    result = post(LOGIN_ENDPOINT, data, auth=False)
    if result and result.get('code') == '000000' and result.get('data'):
        token = result['data'].get('accessToken')
        if token:
            _write_cached_token(token)
            return token

    print("Token 获取失败", file=sys.stderr)
    return None


# ─── HTTP 请求 ───────────────────────────────────────────

def post(endpoint: str, data: dict, auth: bool = True, timeout: int = 30) -> dict | None:
    """
    发送 POST 请求到冈特斯 API。

    参数:
      endpoint: API 路径（如 /application/open-data/...）
      data: 请求体字典
      auth: 是否附加 Authorization header
      timeout: 超时秒数
    返回:
      解析后的 JSON dict，失败返回 None。
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    if auth:
        token = get_token()
        if not token:
            return None
        headers['Authorization'] = token if token.startswith('Bearer ') else f'Bearer {token}'

    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, context=_ssl_ctx, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        _handle_http_error(e)
    except Exception as e:
        print(f"请求错误: {e}", file=sys.stderr)
    return None


def get(endpoint: str, params: dict | None = None, timeout: int = 30) -> urllib.response.addinfourl | None:
    """
    发送 GET 请求，返回原始 response 对象（用于文件下载等）。

    调用方负责读取和关闭 response。失败返回 None。
    """
    token = get_token()
    if not token:
        return None

    url = f"{BASE_URL}{endpoint}"
    if params:
        qs = '&'.join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"

    req = urllib.request.Request(
        url,
        headers={'Authorization': token if token.startswith('Bearer ') else f'Bearer {token}'},
        method='GET'
    )

    try:
        return urllib.request.urlopen(req, context=_ssl_ctx, timeout=timeout)
    except urllib.error.HTTPError as e:
        _handle_http_error(e)
    except Exception as e:
        print(f"请求错误: {e}", file=sys.stderr)
    return None


def post_stream(endpoint: str, data: dict, timeout: int = 120):
    """
    发送 POST 请求并返回原始 response 用于 SSE 流式读取。

    调用方负责逐行读取。失败返回 None。
    """
    token = get_token()
    if not token:
        return None

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Authorization': token if token.startswith('Bearer ') else f'Bearer {token}',
    }

    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    try:
        return urllib.request.urlopen(req, context=_ssl_ctx, timeout=timeout)
    except urllib.error.HTTPError as e:
        _handle_http_error(e)
    except Exception as e:
        print(f"请求错误: {e}", file=sys.stderr)
    return None


# ─── 错误处理 ───────────────────────────────────────────

def _handle_http_error(e: urllib.error.HTTPError) -> None:
    """统一处理 HTTP 错误，尝试解析冈特斯业务错误码。"""
    try:
        body = e.read().decode('utf-8', errors='replace')
        err = json.loads(body)
        code = err.get('code', '')
        msg = err.get('msg', '')
        if code or msg:
            print(f"错误 [{code}]: {msg}", file=sys.stderr)
            return
    except Exception:
        pass
    print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
