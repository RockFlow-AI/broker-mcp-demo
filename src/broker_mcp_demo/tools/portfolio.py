"""持仓 / 资产 / 订单查询工具。

下游路径均为示意（demo），真实项目请按后端接口约定调整。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..backend import backend_request
from ..identity import current_client_id
from .decorators import log_tool

if TYPE_CHECKING:
    from fastmcp import FastMCP


def register(mcp: "FastMCP") -> None:
    """注册持仓 / 资产 / 订单相关工具。"""

    @mcp.tool
    @log_tool
    async def get_positions() -> Any:
        """查询当前持仓列表（含成本、市值与浮动盈亏）。"""
        return await backend_request(
            "GET",
            "/api/v1/positions",
            client_id=current_client_id(),
            mock={
                "positions": [
                    {"symbol": "AAPL", "market": "US", "quantity": 10,
                     "avgCost": 210.0, "marketValue": 2265.0, "unrealizedPnl": 165.0},
                    {"symbol": "00700.HK", "market": "HK", "quantity": 100,
                     "avgCost": 360.0, "marketValue": 37520.0, "unrealizedPnl": 1520.0},
                ]
            },
        )

    @mcp.tool
    @log_tool
    async def get_assets() -> Any:
        """查询账户资产（现金、持仓市值、总资产等）。"""
        return await backend_request(
            "GET",
            "/api/v1/assets",
            client_id=current_client_id(),
            mock={
                "currency": "USD",
                "cash": 12500.0,
                "marketValue": 7065.0,
                "totalAssets": 19565.0,
                "buyingPower": 25000.0,
            },
        )

    @mcp.tool
    @log_tool
    async def get_orders(status: str = "OPEN", limit: int = 20) -> Any:
        """查询订单列表。

        - ``status``：``OPEN``（未完成，默认）/ ``FILLED``（已成交）/
          ``CANCELLED``（已撤销）/ ``ALL``（全部）。
        - ``limit``：最多返回条数，默认 20。
        """
        status = status.strip().upper()
        valid = {"OPEN", "FILLED", "CANCELLED", "ALL"}
        if status not in valid:
            raise ValueError(f"status 仅支持 {sorted(valid)}，收到 {status!r}")
        return await backend_request(
            "GET",
            "/api/v1/orders",
            client_id=current_client_id(),
            query={"status": status, "limit": limit},
            mock={
                "orders": [
                    {"orderId": "demo-order-1001", "symbol": "AAPL", "market": "US",
                     "side": "BUY", "orderType": "LIMIT_ORDER", "price": 220.0,
                     "quantity": 5, "filledQuantity": 0, "status": "OPEN"},
                ]
            },
        )

    @mcp.tool
    @log_tool
    async def get_order(order_id: str) -> Any:
        """查询单个订单详情。

        - ``order_id``：订单 ID，来自 ``get_orders`` 或 ``create_order`` 的返回。
        """
        order_id = order_id.strip()
        if not order_id:
            raise ValueError("order_id 不能为空")
        return await backend_request(
            "GET",
            f"/api/v1/orders/{order_id}",
            client_id=current_client_id(),
            mock={
                "orderId": order_id, "symbol": "AAPL", "market": "US",
                "side": "BUY", "orderType": "LIMIT_ORDER", "price": 220.0,
                "quantity": 5, "filledQuantity": 0, "status": "OPEN",
                "createdAt": 1755741600000,
            },
        )

    @mcp.tool
    @log_tool
    async def cancel_order(order_id: str) -> Any:
        """撤销一个未成交订单。

        - ``order_id``：要撤销的订单 ID。

        撤单是不可逆操作，调用前请与用户确认。
        """
        order_id = order_id.strip()
        if not order_id:
            raise ValueError("order_id 不能为空")
        return await backend_request(
            "DELETE",
            f"/api/v1/orders/{order_id}",
            client_id=current_client_id(),
            mock={"orderId": order_id, "status": "CANCELLED"},
        )
