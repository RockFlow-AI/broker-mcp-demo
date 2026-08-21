"""行情工具（标的搜索 / 最新行情 / 历史 K 线）。

下游路径均为示意（demo），真实项目请按后端接口约定调整
:func:`backend_request` 的 ``path`` 与参数。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from ..backend import backend_request
from ..identity import current_client_id
from .decorators import log_tool

if TYPE_CHECKING:
    from fastmcp import FastMCP


def register(mcp: "FastMCP") -> None:
    """注册行情相关工具。"""

    @mcp.tool
    @log_tool
    async def search_ticker(keyword: str) -> Any:
        """按关键词搜索可交易标的，把公司名/代码解析成 ``market`` + ``symbol``。

        - ``keyword``：公司名或标的代码，中英文均可，如 ``苹果``、``AAPL``。

        返回标的列表，每条含 ``symbol``、``name``、``market``。后续工具请
        原样使用返回的 ``symbol``（如港股 ``00700.HK`` 的后缀不可去掉）。
        """
        keyword = keyword.strip()
        if not keyword:
            raise ValueError("keyword 不能为空")
        return await backend_request(
            "GET",
            f"/api/v1/tickers/search/{quote(keyword, safe='')}",
            client_id=current_client_id(),
            mock={
                "tickers": [
                    {"symbol": "AAPL", "name": "Apple Inc.", "market": "US", "price": 226.5},
                    {"symbol": "00700.HK", "name": "腾讯控股", "market": "HK", "price": 375.2},
                ]
            },
        )

    @mcp.tool
    @log_tool
    async def get_latest_quote(market: str, symbol: str) -> Any:
        """查询某标的的最新行情（现价、涨跌幅、成交量等）。

        - ``market``：市场代码，如 ``US``、``HK``。
        - ``symbol``：标的代码，如 ``AAPL``、``00700.HK``（须与
          ``search_ticker`` 返回的 ``symbol`` 一致，不要截断）。
        """
        return await backend_request(
            "GET",
            f"/api/v1/markets/{market}/quotes/{symbol}",
            client_id=current_client_id(),
            mock={
                "symbol": symbol,
                "market": market,
                "price": 226.5,
                "change": 1.35,
                "changePercent": 0.6,
                "volume": 41253600,
                "timestamp": 1755741600000,
            },
        )

    @mcp.tool
    @log_tool
    async def get_chart(market: str, symbol: str, span: str = "1month") -> Any:
        """查询某标的的历史 K 线。

        - ``market``：市场代码，如 ``US``、``HK``。
        - ``symbol``：标的代码。
        - ``span``：时间跨度，支持 ``1day`` / ``1week`` / ``1month`` /
          ``1year`` / ``5year``。

        返回 K 线列表，每条含 ``begin``（毫秒时间戳）、``open`` / ``close`` /
        ``high`` / ``low``、``volume``。
        """
        span = span.strip()
        valid_spans = {"1day", "1week", "1month", "1year", "5year"}
        if span not in valid_spans:
            raise ValueError(f"span 仅支持 {sorted(valid_spans)}，收到 {span!r}")
        return await backend_request(
            "GET",
            f"/api/v1/markets/{market}/charts/{symbol}",
            client_id=current_client_id(),
            query={"span": span},
            mock={
                "meta": {"interval": "1day", "previousClose": 225.15},
                "historicals": [
                    {"begin": 1755568800000, "open": 224.9, "close": 225.15,
                     "high": 226.0, "low": 224.1, "volume": 38921400},
                    {"begin": 1755655200000, "open": 225.3, "close": 226.5,
                     "high": 227.2, "low": 225.0, "volume": 41253600},
                ],
            },
        )
