"""Healthcheck tool."""
from __future__ import annotations
from typing import Any, Dict, List
from .base import text_content
from ..config import Config

class HealthTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "name": "askpanda_health",
            "description": "Return server name/version and enabled integrations.",
            "inputSchema": {"type": "object", "properties": {}},
        }

    async def call(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        return text_content(
            f"AskPanDA MCP Server OK\n"
            f"- name: {Config.SERVER_NAME}\n"
            f"- version: {Config.SERVER_VERSION}\n"
            f"- ENABLE_REAL_PANDA: {Config.ENABLE_REAL_PANDA}\n"
            f"- ENABLE_REAL_LLM: {Config.ENABLE_REAL_LLM}"
        )

askpanda_health_tool = HealthTool()
