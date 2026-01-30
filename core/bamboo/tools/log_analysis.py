"""Dummy log analysis tool (maps to your previous LogAnalysisAgent).

Later:
- download logs via PanDA job/task links
- parse pilot/job logs
- classify failures
- optionally call LLM for narrative summary
"""
from __future__ import annotations
from typing import Any
from .base import text_content


class PandaLogAnalysisTool:
    """Dummy tool that analyzes a log snippet and returns a short summary.

    The current implementation uses simple heuristics to classify the error and
    suggest next steps. This is a placeholder for a richer pipeline that may
    include log retrieval, parsing, and LLM-based summarization.
    """

    @staticmethod
    def get_definition() -> dict[str, Any]:
        """Return the tool discovery definition.

        The returned dictionary includes the tool name, description and an
        input schema describing expected arguments for clients.

        Returns:
            Dict[str, Any]: MCP-compatible tool discovery definition.
        """
        return {
            "name": "panda_log_analysis",
            "description": "Analyze a job/task failure log snippet (dummy implementation).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "log_text": {"type": "string", "description": "Log text or snippet"},
                    "context": {"type": "string", "description": "Optional context (site, task id, etc.)"},
                },
                "required": ["log_text"],
            },
        }

    async def call(self, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        """Analyze the provided log snippet and return a human-readable summary.

        Args:
            arguments: Mapping with keys ``log_text`` (required) and optional
                ``context`` providing additional metadata.

        Returns:
            List[Dict[str, Any]]: A one-element text content list produced by
            the ``text_content`` helper containing classification and advice.
        """
        log_text = arguments.get("log_text", "")
        context = arguments.get("context", "")
        # Toy heuristics
        lower = log_text.lower()
        if "timeout" in lower or "timed out" in lower:
            classification = "Timeout"
            advice = "Check walltime limits, network/storage slowness, or stuck payload."
        elif "segmentation fault" in lower or "sigsegv" in lower:
            classification = "Payload crash (SIGSEGV)"
            advice = "Check software release, memory pressure, and reproducibility of the failing input."
        elif "no space left" in lower:
            classification = "Disk full"
            advice = "Check scratch space quotas and local disk usage on the worker node."
        else:
            classification = "Unknown"
            advice = "Collect more context (error code, pilot error diag, site, release) and re-run with debug."

        return text_content(
            (
                "Log analysis (dummy)\n"
                f"- context: {context or '(none)'}\n"
                f"- classification: {classification}\n"
                f"- suggested next step: {advice}\n\n"
                "First 300 chars of log:\n"
            ) + log_text[:300]
        )


panda_log_analysis_tool = PandaLogAnalysisTool()
