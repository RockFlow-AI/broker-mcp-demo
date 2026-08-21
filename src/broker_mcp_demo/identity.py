"""从鉴权上下文解析调用方身份。

调用方身份由两层组成：

- ``client_id``：API key 解析出的调用方（哪家券商），来自鉴权上下文；
- ``user_id``：券商 App 发起会话时透传的用户 ID（券商自己体系内的用户），
  由 Agent 在请求头 ``X-User-Id`` 中原样带上。

两者组合即可确定「哪家券商的哪个用户」，持仓、资产、订单、下单等
工具据此向券商后端按用户维度执行。
"""

from __future__ import annotations

from fastmcp.server.dependencies import get_access_token, get_http_headers


def current_client_id() -> str:
    """返回当前请求 API key 对应的 client_id；鉴权禁用时返回 ``anonymous``。"""
    try:
        token = get_access_token()
    except Exception:
        return "anonymous"
    if token is None:
        return "anonymous"
    return token.client_id or "anonymous"


def current_user_id() -> str:
    """返回请求头 ``X-User-Id`` 中的用户 ID；未携带（或 stdio 模式）时返回空串。"""
    try:
        headers = get_http_headers()
    except Exception:
        return ""
    return (headers.get("x-user-id") or "").strip()
