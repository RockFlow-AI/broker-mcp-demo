"""从鉴权上下文解析调用方身份。"""

from __future__ import annotations

from fastmcp.server.dependencies import get_access_token


def current_client_id() -> str:
    """返回当前请求 API key 对应的 client_id；鉴权禁用时返回 ``anonymous``。"""
    try:
        token = get_access_token()
    except Exception:
        return "anonymous"
    if token is None:
        return "anonymous"
    return token.client_id or "anonymous"
