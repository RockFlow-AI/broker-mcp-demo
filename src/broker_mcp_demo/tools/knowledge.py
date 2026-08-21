"""知识库搜索（产品规则 / 操作流程 / 常见问题）。

下游路径为示意（demo）——真实项目通常由后端做向量检索 + 语义排序
（如 Azure Cognitive Search、Elasticsearch、Milvus 等），本 demo 不绑定
任何具体实现，接入时按后端接口约定调整 :func:`backend_request` 即可。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..backend import backend_request
from ..identity import current_client_id
from .decorators import log_tool

if TYPE_CHECKING:
    from fastmcp import FastMCP


def register(mcp: "FastMCP") -> None:
    """注册知识库搜索工具。"""

    @mcp.tool
    @log_tool
    async def search_knowledge_base(
        query: str,
        language: str = "zh-Hans",
        top: int = 10,
    ) -> Any:
        """搜索平台知识库——产品规则、操作流程、常见问题。

        开户、出入金、交易规则等平台相关问答的权威来源，
        适合 "怎么开户""出入金要多久" 这类 QA 式提问。

        - ``query``：搜索关键词，如 ``怎么开户``、``出入金要多久``。
        - ``language``：``zh-Hans`` / ``zh-Hant`` / ``en``，默认 ``zh-Hans``。
        - ``top``：返回条数，默认 10，范围 3~20。

        返回 ``results`` 列表，每条为命中的知识条目原文
        （形如 ``question: …\\nanswer: …``）。
        """
        query = query.strip()
        if not query:
            raise ValueError("query 不能为空")

        top = max(3, min(20, top))

        return await backend_request(
            "GET",
            "/api/v1/knowledge/search",
            client_id=current_client_id(),
            query={"query": query, "language": language, "top": top},
            mock={
                "results": [
                    "question: 怎么开户？\nanswer: 在 App 首页点击「开户」，"
                    "按提示上传证件并完成风险测评，通常 1 个工作日内审核完成。",
                    "question: 出入金要多久？\nanswer: 入金一般实时到账，"
                    "出金视银行处理时间 1~3 个工作日到账。",
                ]
            },
        )
