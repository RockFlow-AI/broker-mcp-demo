"""配置读取：全部来自环境变量（前缀 ``BROKER_MCP_``），支持 ``.env``。

本项目是 demo，不内置任何真实服务地址——下游券商后端地址、API key 等
均由使用者通过环境变量自行配置，参考 ``.env.example``。
"""

from __future__ import annotations

import os
from pathlib import Path

_ENV_PREFIX = "BROKER_MCP_"


def load_dotenv(path: str | Path = ".env") -> None:
    """极简 .env 加载：仅当同名环境变量不存在时注入，不引入第三方依赖。"""
    env_file = Path(path)
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def _get(name: str, default: str = "") -> str:
    return os.environ.get(_ENV_PREFIX + name, default).strip()


def _get_bool(name: str, default: bool = False) -> bool:
    raw = _get(name)
    if not raw:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


# ---- 服务自身 ----

def transport() -> str:
    """``http``（默认）或 ``stdio``。"""
    return _get("TRANSPORT", "http").lower()


def host() -> str:
    return _get("HOST", "0.0.0.0")


def port() -> int:
    return int(_get("PORT", "8000"))


# ---- 鉴权（API key）----

def auth_disabled() -> bool:
    """``true`` 时关闭鉴权，仅本地调试用；stdio 模式强制关闭。"""
    return _get_bool("AUTH_DISABLED", default=False)


def api_keys() -> dict[str, str]:
    """解析 ``BROKER_MCP_API_KEYS``，返回 ``{api_key: client_id}``。

    格式为逗号分隔的条目，每条为 ``key`` 或 ``key:client_id``：

        BROKER_MCP_API_KEYS=demo-key-1:alice,demo-key-2:bob,standalone-key

    未指定 client_id 时以 key 前 8 位作为标识。
    """
    keys: dict[str, str] = {}
    for entry in _get("API_KEYS").split(","):
        entry = entry.strip()
        if not entry:
            continue
        key, _, client_id = entry.partition(":")
        key = key.strip()
        if key:
            keys[key] = client_id.strip() or key[:8]
    return keys


# ---- 下游券商后端 ----

def backend_base_url() -> str:
    """下游券商后端根地址（demo 不内置真实地址，由使用者配置）。

    留空时工具返回内置示例数据（mock），方便未接后端时直接体验。
    """
    return _get("BACKEND_BASE_URL")


def backend_timeout() -> float:
    return float(_get("BACKEND_TIMEOUT", "30"))
