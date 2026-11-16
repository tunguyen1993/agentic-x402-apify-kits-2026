"""Zero-dependency MCP stdio server for 2026 x402 benchmarks, guardrails, and Apify kit catalogs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

__version__ = "1.1.0"

if TYPE_CHECKING:
    from agentic_x402_mcp.mcp_server import (
        DATASET_FILES,
        MCP_PROTOCOL_VERSION,
        AgenticX402MCPServer,
        main,
        resolve_dataset_root,
        run_self_test,
    )

__all__ = [
    "__version__",
    "MCP_PROTOCOL_VERSION",
    "DATASET_FILES",
    "AgenticX402MCPServer",
    "resolve_dataset_root",
    "run_self_test",
    "main",
]

_EXPORTED_FROM_SERVER = frozenset({
    "MCP_PROTOCOL_VERSION",
    "DATASET_FILES",
    "AgenticX402MCPServer",
    "resolve_dataset_root",
    "run_self_test",
    "main",
})


def __getattr__(name: str) -> Any:
    if name in _EXPORTED_FROM_SERVER:
        from agentic_x402_mcp import mcp_server

        return getattr(mcp_server, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
