"""AskPanDA MCP Server entry point.

Run:
  npx @modelcontextprotocol/inspector python3 -m askpanda_mcp.server

This skeleton follows the structure of the uploaded minimal MCP server,
but swaps in AskPanDA-oriented tools with dummy implementations.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools.health import askpanda_health_tool
from .tools.doc_rag import panda_doc_search_tool
from .tools.queue_info import panda_queue_info_tool
from .tools.task_status import panda_task_status_tool
from .tools.log_analysis import panda_log_analysis_tool
from .tools.pilot_monitor import panda_pilot_status_tool

from .prompts.templates import get_askpanda_system_prompt, get_failure_triage_prompt
from .config import Config

app = Server(Config.SERVER_NAME)

TOOLS = {
    "askpanda_health": askpanda_health_tool,
    "panda_doc_search": panda_doc_search_tool,
    "panda_queue_info": panda_queue_info_tool,
    "panda_task_status": panda_task_status_tool,
    "panda_log_analysis": panda_log_analysis_tool,
    "panda_pilot_status": panda_pilot_status_tool,
}

@app.list_tools()
async def list_tools():
    defs = [tool.get_definition() for tool in TOOLS.values()]  # currently dicts
    return [Tool(**d) for d in defs]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    tool = TOOLS.get(name)
    if not tool:
        raise ValueError(f"Unknown tool: {name}. Known: {', '.join(TOOLS.keys())}")
    return await tool.call(arguments or {})

@app.list_prompts()
async def list_prompts():
    return [
        {
            "name": "askpanda_system",
            "description": "Core system prompt for AskPanDA behavior.",
            "arguments": [],
        },
        {
            "name": "failure_triage",
            "description": "Template prompt for triaging a failure log snippet.",
            "arguments": [
                {"name": "log_text", "description": "Log text or snippet", "required": True}
            ],
        },
    ]

@app.get_prompt()
async def get_prompt(name: str, arguments: Dict[str, Any]):
    if name == "askpanda_system":
        return await get_askpanda_system_prompt()
    if name == "failure_triage":
        return await get_failure_triage_prompt(arguments.get("log_text", ""))
    raise ValueError(f"Unknown prompt: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
