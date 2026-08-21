"""工具通用装饰器：统一打印调用方、入参与耗时日志。

用 :func:`functools.wraps` 保留原函数签名与文档，FastMCP 仍能从中推断
参数 schema，因此可安全地夹在 ``@mcp.tool`` 与工具函数之间。
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Awaitable, Callable, TypeVar

from ..identity import current_client_id

logger = logging.getLogger("broker_mcp_demo.tools")

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def log_tool(func: F) -> F:
    """记录异步工具的调用开始、耗时与结果状态。"""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        name = func.__name__
        client = current_client_id()
        start = time.perf_counter()
        logger.info("[tool] %s 开始 client=%s kwargs=%s", name, client, kwargs)
        try:
            result = await func(*args, **kwargs)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.warning("[tool] %s 失败 耗时=%.1fms error=%s", name, elapsed_ms, exc)
            raise
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info("[tool] %s 完成 耗时=%.1fms", name, elapsed_ms)
        return result

    return wrapper  # type: ignore[return-value]
