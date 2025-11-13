"""Minimal MCP server scaffolding for jgrants-mcp."""

from .server import MCPConfig, app, settings  # noqa: F401

__version__ = "0.1.0"


def placeholder() -> str:
    """Placeholder helper until the real FastMCP entrypoint is added."""
    return "jgrants_mcp_server placeholder"


__all__ = ["app", "settings", "MCPConfig", "placeholder", "__version__"]
