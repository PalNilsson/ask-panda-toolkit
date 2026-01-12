"""Dummy pilot monitor tool (maps to your previous PilotMonitorAgent)."""
from __future__ import annotations
from typing import Any, Dict, List
from .base import text_content

class PandaPilotStatusTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "name": "panda_pilot_status",
            "description": "Return pilot counts/failures for a site (dummy implementation).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "site": {"type": "string", "description": "Site name, e.g. BNL-ATLAS"},
                    "window_minutes": {"type": "integer", "description": "Lookback window in minutes", "default": 60},
                },
                "required": ["site"],
            },
        }

    async def call(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        site = arguments.get("site", "")
        window = int(arguments.get("window_minutes", 60))
        # Dummy numbers
        return text_content(
            f"Pilot status for {site} (dummy)\n"
            f"- window_minutes: {window}\n"
            f"- pilots_running: 128\n"
            f"- pilots_idle: 12\n"
            f"- pilots_failed: 3\n"
            "Replace with real Grafana/Harvester/PanDA monitor queries."
        )

panda_pilot_status_tool = PandaPilotStatusTool()
