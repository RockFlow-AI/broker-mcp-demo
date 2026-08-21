"""程序入口：``python -m broker_mcp_demo``。"""

from __future__ import annotations

import logging
import os

from . import config as cfg
from .server import create_server


def _init_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    _init_logging()
    cfg.load_dotenv()

    if cfg.transport() == "stdio":
        # stdio 模式用于本地调试或目录扫描，走 stdin/stdout，不启用鉴权。
        os.environ["BROKER_MCP_AUTH_DISABLED"] = "true"
        mcp = create_server()
        logging.getLogger(__name__).info("以 stdio 模式启动")
        mcp.run(transport="stdio")
        return

    mcp = create_server()
    logging.getLogger(__name__).info(
        "以 http 模式启动，监听 %s:%s，MCP 端点 /mcp", cfg.host(), cfg.port()
    )
    # stateless_http=True：不维护内存会话，每个请求独立处理，便于多副本部署。
    mcp.run(
        transport="http",
        host=cfg.host(),
        port=cfg.port(),
        stateless_http=True,
    )


if __name__ == "__main__":
    main()
