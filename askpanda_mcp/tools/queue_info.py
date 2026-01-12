"""Dummy queue/site info tool (maps to your previous QueueQueryAgent)."""
from __future__ import annotations
from typing import Any, Dict, List
import json
import os

from .base import text_content
from ..config import Config

class PandaQueueInfoTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "name": "panda_queue_info",
            "description": "Return site/queue information from queuedata.json (dummy local file).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "site": {"type": "string", "description": "Site name, e.g. BNL-ATLAS"},
                },
                "required": ["site"],
            },
        }

    async def call(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        site = arguments.get("site", "")
        path = Config.QUEUE_DATA_PATH
        # Resolve relative to package if user kept defaults
        if not os.path.isabs(path):
            here = os.path.dirname(__file__)
            path = os.path.abspath(os.path.join(here, "..", path))
        try:
            data = json.load(open(path, "r", encoding="utf-8"))
        except Exception as e:
            return text_content(f"Could not read queue data at {path}: {e}")
        info = data.get(site)
        if not info:
            known = ", ".join(sorted(data.keys()))
            return text_content(f"Unknown site '{site}'. Known sites: {known}")
        pretty = json.dumps(info, indent=2)
        return text_content(f"Queue info for {site} (dummy)\n\n{pretty}")

panda_queue_info_tool = PandaQueueInfoTool()
