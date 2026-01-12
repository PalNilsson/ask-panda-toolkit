"""Prompt templates.

In MCP, prompts are a discoverable interface for clients.
Keep prompts small and composable; use tools for data access.
"""
from __future__ import annotations
from typing import Any, Dict, List

def _text_msg(text: str) -> Dict[str, Any]:
    return {"role": "assistant", "content": {"type": "text", "text": text}}

async def get_askpanda_system_prompt() -> Dict[str, Any]:
    return {
        "messages": [
            _text_msg(
                "You are AskPanDA, an assistant for PanDA/ATLAS workflow operations. "
                "Prefer calling tools for factual data (task status, queue info, pilots). "
                "If data is missing, ask for identifiers (task id, job id, site) and propose next steps."
            )
        ]
    }

async def get_failure_triage_prompt(log_text: str) -> Dict[str, Any]:
    return {
        "messages": [
            _text_msg(
                "Analyze the following failure log and produce: "
                "(1) classification, (2) likely root causes, (3) immediate mitigation, "
                "(4) what additional metadata to collect.\n\n"
                f"LOG:\n{log_text}"
            )
        ]
    }
