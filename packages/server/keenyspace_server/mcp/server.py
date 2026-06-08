from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP
from fastmcp.tools import Tool

from .blueprint_tools import get_instructions_tool, list_blueprints_tool
from .page_tools import list_pages_tool, search_workspace_tool
from .recent_tool import get_recent_changes_tool
from .tools import append_log, compile_status_tool, compile_tool, ping, read_page
from .workspace_tools import get_workspace_info_tool, list_workspaces_tool

# Each Tier-1 tool mapped to its CONTRACT name. FastMCP's add_tool(fn) derives
# the tool name from fn.__name__, so the `*_tool`-suffixed functions would
# register under the wrong wire names (e.g. "get_instructions_tool"). Clients,
# the keenyspace CLI, and CLAUDE.md all call the bare names — register every
# tool explicitly so the wire contract is the single source of truth and is
# immune to future function renames.
_TIER1_TOOLS: list[tuple[Callable[..., Any], str]] = [
    (read_page, "read_page"),
    (append_log, "append_log"),
    (compile_tool, "compile"),
    (compile_status_tool, "compile_status"),
    (list_workspaces_tool, "list_workspaces"),
    (get_workspace_info_tool, "get_workspace_info"),
    (list_pages_tool, "list_pages"),
    (search_workspace_tool, "search_workspace"),
    (get_recent_changes_tool, "get_recent_changes"),
    (list_blueprints_tool, "list_blueprints"),
    (get_instructions_tool, "get_instructions"),
]


def build_mcp_skeleton() -> FastMCP:
    mcp: FastMCP = FastMCP("KeenySpace-skeleton")
    mcp.add_tool(ping)
    return mcp


def build_mcp() -> FastMCP:
    mcp: FastMCP = FastMCP("KeenySpace")
    for fn, name in _TIER1_TOOLS:
        mcp.add_tool(Tool.from_function(fn, name=name))
    return mcp
