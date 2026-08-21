"""交易工具（下单）。

下游路径为示意（demo），真实项目请按后端接口约定调整。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..backend import backend_request
from ..identity import current_client_id, current_user_id
from .decorators import log_tool

if TYPE_CHECKING:
    from fastmcp import FastMCP

_SIDES = {"BUY", "SELL"}
_ORDER_TYPES = {"MARKET_ORDER", "LIMIT_ORDER"}
_VALIDITIES = {"GOOD_FOR_DAY", "GOOD_TILL_CANCELLED"}


def register(mcp: "FastMCP") -> None:
    """注册交易相关工具。"""

    @mcp.tool
    @log_tool
    async def create_order(
        symbol: str,
        market: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        validity: str = "GOOD_FOR_DAY",
    ) -> Any:
        """创建（提交）一个交易订单。

        - ``symbol``：标的代码，须与 ``search_ticker`` 返回的一致。
        - ``market``：市场代码，如 ``US``、``HK``。
        - ``side``：``BUY`` / ``SELL``。
        - ``order_type``：``MARKET_ORDER``（市价）/ ``LIMIT_ORDER``（限价，
          必须带 ``price``）。
        - ``quantity``：数量（股数）。
        - ``price``：限价单价格；市价单省略。
        - ``validity``：``GOOD_FOR_DAY``（当日有效，默认）/
          ``GOOD_TILL_CANCELLED``（撤单前有效）。

        下单会产生真实交易，调用前先用 ``get_assets`` 确认资金，并与用户
        确认关键参数（标的、方向、数量、价格）。
        """
        side = side.strip().upper()
        order_type = order_type.strip().upper()
        validity = validity.strip().upper()
        if side not in _SIDES:
            raise ValueError(f"side 仅支持 {sorted(_SIDES)}，收到 {side!r}")
        if order_type not in _ORDER_TYPES:
            raise ValueError(f"order_type 仅支持 {sorted(_ORDER_TYPES)}，收到 {order_type!r}")
        if validity not in _VALIDITIES:
            raise ValueError(f"validity 仅支持 {sorted(_VALIDITIES)}，收到 {validity!r}")
        if quantity <= 0:
            raise ValueError("quantity 必须大于 0")
        if order_type == "LIMIT_ORDER" and (price is None or price <= 0):
            raise ValueError("LIMIT_ORDER 必须提供大于 0 的 price")

        body: dict[str, Any] = {
            "symbol": symbol.strip(),
            "market": market.strip().upper(),
            "side": side,
            "orderType": order_type,
            "quantity": quantity,
            "validity": validity,
        }
        if price is not None:
            body["price"] = price

        return await backend_request(
            "POST",
            "/api/v1/orders",
            client_id=current_client_id(),
            user_id=current_user_id(),
            body=body,
            mock={"orderId": "demo-order-1002", "status": "OPEN", **body},
        )
