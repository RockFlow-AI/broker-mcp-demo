"""MCP 工具注册入口。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import market, portfolio, trade

if TYPE_CHECKING:
    from fastmcp import FastMCP


def register_tools(mcp: "FastMCP") -> None:
    """把所有 MCP 工具注册到 ``mcp`` 实例上。

    每个工具模块提供一个 ``register(mcp)`` 函数，新增模块时按此追加。
    """
    market.register(mcp)     # 标的搜索 / 最新行情 / K 线
    portfolio.register(mcp)  # 持仓 / 资产 / 订单查询 / 撤单
    trade.register(mcp)      # 下单
