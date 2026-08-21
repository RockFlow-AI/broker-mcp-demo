"""FastMCP 服务实例的装配。"""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

from fastmcp import FastMCP

from . import __version__
from .auth import build_auth_provider
from .tools import register_tools

SERVER_NAME = "Broker MCP Demo"

SERVER_DESCRIPTION = (
    "券商 MCP Server Demo：提供行情查询、持仓资产、订单查询、"
    "交易下单与撤单等示例工具。全部端点采用 API key 鉴权"
    "（Authorization: Bearer <api-key>）。"
)

SERVER_INSTRUCTIONS = """\
券商交易服务 MCP Demo（API key 鉴权），提供行情、持仓资产、交易三类工具。

使用要点：
- 拿到公司名/模糊代码时，先用 search_ticker 解析出 symbol 与 market，\
后续工具原样使用返回的 symbol（港股形如 00700.HK，后缀不可去掉）。
- 行情查询：get_latest_quote（最新行情）、get_chart（K 线）。
- 账户视角：get_positions（持仓）、get_assets（资产）、\
get_orders / get_order（订单）。
- 交易操作：create_order（下单）与 cancel_order（撤单）会产生真实交易，\
调用前先用 get_assets 确认资金，并与用户确认关键参数\
（标的、方向、数量、价格）。
- 未配置下游后端地址时，各工具返回带 "mock": true 标记的示例数据，\
仅用于演示，不代表真实行情与账户状态。
- 鉴权：请求需携带 Authorization: Bearer <api-key>；返回 401 时说明 \
api-key 缺失或无效，请引导用户在 MCP 客户端配置中检查 key，不要反复重试。
"""


def create_server() -> FastMCP:
    """按配置创建并返回一个 FastMCP 实例。"""
    # 端点级强制鉴权：auth provider（TokenVerifier）自带 RequireAuthMiddleware，
    # 未携带 / 无效 API key 的请求（含 initialize / tools/list）一律 401。
    auth = build_auth_provider()
    mcp = FastMCP(
        name=SERVER_NAME,
        version=__version__,
        auth=auth,
        instructions=SERVER_INSTRUCTIONS,
    )

    register_tools(mcp)

    @mcp.custom_route("/health", methods=["GET"])
    async def health(_: Request) -> PlainTextResponse:  # 部署健康检查
        return PlainTextResponse("ok")

    @mcp.custom_route("/", methods=["GET"], include_in_schema=False)
    async def index(_: Request) -> JSONResponse:  # 浏览器访问根路径时的说明
        return JSONResponse(
            {
                "name": SERVER_NAME,
                "version": __version__,
                "description": SERVER_DESCRIPTION,
                "mcp_endpoint": "/mcp",
                "authentication": (
                    "API key 鉴权：在 MCP 客户端为本 server 配置请求头 "
                    "Authorization: Bearer <api-key>，key 由服务端 "
                    "BROKER_MCP_API_KEYS 环境变量下发。"
                ),
            }
        )

    return mcp
