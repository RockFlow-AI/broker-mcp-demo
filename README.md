# Broker MCP Demo

基于 [FastMCP](https://github.com/jlowin/fastmcp) 的券商 MCP Server **Demo**（Python 版），
做了两点简化：

- **鉴权用静态 API key**（`Authorization: Bearer <api-key>`），不走 OAuth；
- **不内置任何真实服务地址**：下游券商后端地址由使用者通过环境变量自行配置，
  未配置时各工具返回内置示例数据（响应带 `"mock": true` 标记），开箱即可体验。

## 架构

```
┌─────────────┐  Bearer <api-key>  ┌────────────────────┐   HTTP   ┌──────────────┐
│  MCP Client │───────────────────▶│  Broker MCP Demo   │─────────▶│  券商后端服务  │
│  (Claude…)  │◀───────────────────│  (API key 校验)     │◀─────────│ （自行配置）   │
└─────────────┘                    └────────────────────┘          └──────────────┘
```

请求流程：

1. 客户端带 `Authorization: Bearer <api-key>` 请求 `POST /mcp`。
2. 服务端将 key 与 `BROKER_MCP_API_KEYS` 中配置的逐一比对，命中放行、否则 `401`。
3. 工具调用被代理到 `BROKER_MCP_BACKEND_BASE_URL` 指向的券商后端；
   未配置时返回内置示例数据。

## 工具

共 9 个示例工具，覆盖行情、持仓 / 订单、交易三类。下游接口路径均为示意，
接入真实后端时按约定改 [tools/](src/broker_mcp_demo/tools/) 里的 `path` 即可。

### 行情（[market.py](src/broker_mcp_demo/tools/market.py)）

| 工具 | 参数 | 说明 |
|------|------|------|
| `search_ticker` | `keyword` | 按公司名 / 代码搜索标的，解析出 `market` + `symbol` |
| `get_latest_quote` | `market`, `symbol` | 查询标的最新行情 |
| `get_chart` | `market`, `symbol`, `span=1month` | 历史 K 线；`span` 支持 `1day` / `1week` / `1month` / `1year` / `5year` |

### 持仓 / 资产 / 订单（[portfolio.py](src/broker_mcp_demo/tools/portfolio.py)）

| 工具 | 参数 | 说明 |
|------|------|------|
| `get_positions` | — | 当前持仓列表（含盈亏） |
| `get_assets` | — | 账户资产（现金、市值、总资产等） |
| `get_orders` | `status=OPEN`, `limit=20` | 订单列表；`status` 支持 `OPEN` / `FILLED` / `CANCELLED` / `ALL` |
| `get_order` | `order_id` | 单个订单详情 |
| `cancel_order` | `order_id` | 撤销一个未成交订单 |

### 交易（[trade.py](src/broker_mcp_demo/tools/trade.py)）

| 工具 | 参数 | 说明 |
|------|------|------|
| `create_order` | `symbol`, `market`, `side`, `order_type`, `quantity`, `price?`, `validity` | 创建（提交）一个交易订单 |

- `order_type`：`MARKET_ORDER`（市价）/ `LIMIT_ORDER`（限价，需带 `price`）。
- `side`：`BUY` / `SELL`；`validity`：`GOOD_FOR_DAY` / `GOOD_TILL_CANCELLED`。

> 每个工具都套了 [decorators.py](src/broker_mcp_demo/tools/decorators.py) 的 `log_tool`
> 装饰器，统一打印调用方（API key 对应的 client_id）、入参与耗时日志。新增工具时
> 在对应模块 `register(mcp)` 内用 `@mcp.tool` + `@log_tool` 声明，并在
> [tools/\_\_init\_\_.py](src/broker_mcp_demo/tools/__init__.py) 的 `register_tools()` 注册。

## 运行

```bash
pip install -r requirements.txt

cp .env.example .env   # 按需修改 API key、后端地址
python -m broker_mcp_demo
```

默认监听 `0.0.0.0:8000`，MCP 端点为 `/mcp`，健康检查为 `/health`。

### 配置

全部通过环境变量（前缀 `BROKER_MCP_`）或 `.env` 注入，参考 [.env.example](.env.example)：

| 变量 | 说明 |
|------|------|
| `BROKER_MCP_API_KEYS` | **必填**（除非关闭鉴权）。逗号分隔，每条为 `key` 或 `key:client_id`，如 `demo-key-1:alice,demo-key-2:bob` |
| `BROKER_MCP_BACKEND_BASE_URL` | 下游券商后端根地址（demo 不内置真实地址，自行配置）；留空时工具返回示例数据 |
| `BROKER_MCP_HOST` / `BROKER_MCP_PORT` | 监听地址 / 端口，默认 `0.0.0.0:8000` |
| `BROKER_MCP_TRANSPORT` | `http`（默认）或 `stdio` |
| `BROKER_MCP_AUTH_DISABLED` | `true` 关闭鉴权，仅本地调试用 |
| `BROKER_MCP_BACKEND_TIMEOUT` | 下游请求超时秒数，默认 `30` |

### 客户端接入

以 Claude Code 为例（HTTP 模式 + API key）：

```bash
claude mcp add --transport http broker-demo http://localhost:8000/mcp \
  --header "Authorization: Bearer demo-key-1"
```

或在 MCP 客户端的 JSON 配置中：

```json
{
  "mcpServers": {
    "broker-demo": {
      "type": "http",
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer demo-key-1"
      }
    }
  }
}
```

### stdio 模式

用于本地调试，走 stdin/stdout 且不启用鉴权：

```bash
BROKER_MCP_TRANSPORT=stdio python -m broker_mcp_demo
```

## 目录结构

```
src/broker_mcp_demo/
├── __main__.py     入口（python -m broker_mcp_demo）
├── config.py       环境变量 / .env 配置读取
├── auth.py         API key 鉴权（ApiKeyVerifier）
├── identity.py     从鉴权上下文解析 client_id
├── backend.py      下游后端 HTTP 调用封装（未配置地址时回退示例数据）
├── server.py       FastMCP 实例装配
└── tools/          MCP 工具
    ├── __init__.py     register_tools() 注册入口
    ├── decorators.py   log_tool 计时日志装饰器
    ├── market.py       行情
    ├── portfolio.py    持仓 / 资产 / 订单
    └── trade.py        下单
```

## License

[Apache-2.0](LICENSE)
