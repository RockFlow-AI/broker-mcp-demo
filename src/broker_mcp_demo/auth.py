"""API key 鉴权。

本 demo 不走 OAuth 2.1，采用最简单的 **静态 API key**：
客户端在请求头携带 ``Authorization: Bearer <api-key>``，服务端与
``BROKER_MCP_API_KEYS`` 中配置的 key 逐一比对，命中即放行。

实现上复用 FastMCP 的 :class:`TokenVerifier`（它本身就是一个
``AuthProvider``，自带端点级强制鉴权中间件）：把 API key 当作 Bearer token
校验，未携带或 key 无效的请求（含 initialize / tools/list）一律 401。
不发布任何 OAuth 元数据路由，客户端无需走授权流程，配好 key 即用。
"""

from __future__ import annotations

import logging

from fastmcp.server.auth import AccessToken, AuthProvider, TokenVerifier

from . import config as cfg

logger = logging.getLogger(__name__)


class ApiKeyVerifier(TokenVerifier):
    """把 Bearer token 当作静态 API key 校验。"""

    def __init__(self, keys: dict[str, str]) -> None:
        super().__init__()
        # {api_key: client_id}
        self._keys = keys

    async def verify_token(self, token: str) -> AccessToken | None:
        client_id = self._keys.get(token)
        if client_id is None:
            logger.info("API key 校验失败（key 未配置或已失效）")
            return None
        return AccessToken(
            token=token,
            client_id=client_id,
            scopes=[],
            expires_at=None,  # 静态 key 不过期，吊销 = 从配置中移除
        )


def build_auth_provider() -> AuthProvider | None:
    """构造 API key 鉴权 provider；返回 None 表示鉴权已禁用（仅本地调试）。"""
    if cfg.auth_disabled():
        logger.warning("鉴权已禁用（BROKER_MCP_AUTH_DISABLED=true），仅供本地调试")
        return None

    keys = cfg.api_keys()
    if not keys:
        raise ValueError(
            "未配置任何 API key：请设置 BROKER_MCP_API_KEYS"
            "（如 demo-key-1:alice,demo-key-2:bob），"
            "或设 BROKER_MCP_AUTH_DISABLED=true 关闭鉴权（仅本地调试）"
        )
    logger.info("API key 鉴权已启用，共 %d 个 key", len(keys))
    return ApiKeyVerifier(keys)
