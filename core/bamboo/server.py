"""
Bamboo MCP Server entry point. "Stdio server".

Uses the official MCP stdio transport.

Run:
  npx @modelcontextprotocol/inspector python3 -m bamboo.server
  python3 -m bamboo.server
"""

from __future__ import annotations

from mcp.server.stdio import stdio_server
from mcp.server import Server
from bamboo.core import create_server


async def main() -> None:
    """Run the Bamboo MCP stdio server.

    Bootstraps the MCP Server by creating the application via
    ``create_server()`` and serving it over the stdio transport returned by
    ``stdio_server()``.
    """
    app: Server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
