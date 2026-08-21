"""下游券商后端的 HTTP 调用封装（demo）。

本项目不内置任何真实后端地址：``BROKER_MCP_BACKEND_BASE_URL`` 由使用者
自行配置。为了让 demo 未接后端时也能跑通，工具可以传入 ``mock`` 示例数据——
后端地址未配置时直接返回该示例（响应中带 ``"mock": true`` 标记）。
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from . import config as cfg

logger = logging.getLogger(__name__)


async def backend_request(
    method: str,
    path: str,
    *,
    client_id: str,
    user_id: str = "",
    query: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    mock: Any = None,
) -> Any:
    """向下游券商后端发起请求并返回解析后的 JSON。

    - ``path``：相对路径（如 ``/api/v1/positions``），拼接到
      ``BROKER_MCP_BACKEND_BASE_URL`` 之后。
    - ``client_id``：调用方标识（来自 API key），通过 ``X-Client-Id`` header
      下发给后端，仅作示意——真实项目请按后端的鉴权约定改造。
    - ``user_id``：券商体系内的用户 ID（来自请求头 ``X-User-Id``），
      非空时通过 ``X-User-Id`` header 原样透传给后端，
      供持仓、订单等接口按用户维度执行。
    - ``mock``：后端地址未配置时返回的示例数据；为 ``None`` 时直接报错。
    """
    base_url = cfg.backend_base_url()
    if not base_url:
        if mock is not None:
            logger.info("[backend] 未配置后端地址，%s %s 返回示例数据", method, path)
            return {
                "mock": True,
                "note": (
                    "示例数据：未配置 BROKER_MCP_BACKEND_BASE_URL，"
                    "配置真实后端地址后将请求真实接口"
                ),
                "data": mock,
            }
        raise RuntimeError(
            f"下游后端地址未配置，无法请求 {method} {path}；"
            "请设置 BROKER_MCP_BACKEND_BASE_URL 环境变量"
        )

    url = f"{base_url.rstrip('/')}{path}"
    headers = {"X-Client-Id": client_id}
    if user_id:
        headers["X-User-Id"] = user_id
    logger.info("[backend] %s %s user=%s query=%s", method, url, user_id or "-", query)
    async with httpx.AsyncClient(timeout=cfg.backend_timeout()) as client:
        resp = await client.request(
            method=method,
            url=url,
            params=query or None,
            json=body,
            headers=headers,
        )
    try:
        return resp.json()
    except ValueError:
        return {"status_code": resp.status_code, "body": resp.text}
