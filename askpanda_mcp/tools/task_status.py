"""Dummy task query tool (maps to your previous TaskQueryAgent)."""
from __future__ import annotations
from typing import Any, Dict, List
from .base import text_content

class PandaTaskStatusTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "name": "panda_task_status",
            "description": "Return a summary for a PanDA task ID (dummy implementation).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "PanDA task ID"},
                },
                "required": ["task_id"],
            },
        }

    async def call(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        task_id = int(arguments.get("task_id"))
        # Dummy status payload
        summary = {
            "task_id": task_id,
            "status": "running",
            "n_jobs_total": 1000,
            "n_jobs_done": 420,
            "n_jobs_failed": 7,
            "last_update_utc": "2026-01-12T00:00:00Z",
            "note": "Dummy payload. Replace with real PanDA monitor/API calls.",
        }
        import json
        return text_content("Task status (dummy)\n\n" + json.dumps(summary, indent=2))

panda_task_status_tool = PandaTaskStatusTool()
