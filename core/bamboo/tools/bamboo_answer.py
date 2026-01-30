"""
bamboo/tools/bamboo_answer.py  (LLM summarizing task metadata)

ATLAS-focused orchestration:
- Extract task id from question/messages
- Call task_status tool to get structured evidence
- Call bamboo_llm_answer (passthrough) with a prompt that includes:
    - original user question
    - compact JSON evidence
- Return a single text content entry
"""
from __future__ import annotations

import json
import re
from typing import Any
from collections.abc import Sequence

from bamboo.llm.types import Message
from bamboo.tools.base import text_content, coerce_messages
from bamboo.tools.llm_passthrough import askpanda_llm_answer_tool
from bamboo.tools.task_status import panda_task_status_tool


# More permissive extraction
_TASK_PATTERN = re.compile(r"(?i)\btask[:#/\-\s]*([0-9]{1,12})\b")


def _extract_task_id(text: str) -> int | None:
    m = _TASK_PATTERN.search(text or "")
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def _coerce_messages(raw: Sequence[Any]) -> list[Message]:
    return coerce_messages(raw)


def _compact(obj: Any, limit: int = 6000) -> str:
    """Compact JSON for prompt; keep it bounded."""
    try:
        s = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    except Exception:
        s = str(obj)
    if len(s) > limit:
        return s[:limit] + "…(truncated)"
    return s


class AskPandaAnswerTool:
    @staticmethod
    def get_definition() -> dict[str, Any]:
        return {
            "name": "askpanda_answer",
            "description": "ATLAS AskPanDA entrypoint. Uses tools + LLM to answer, summarizing task metadata when applicable.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "User question. Required if messages is empty."},
                    "messages": {
                        "type": "array",
                        "description": "Optional full chat history as a list of {role, content}.",
                        "items": {
                            "type": "object",
                            "properties": {"role": {"type": "string"}, "content": {"type": "string"}},
                            "required": ["role", "content"],
                        },
                    },
                    "bypass_routing": {"type": "boolean", "default": False},
                    "include_raw": {"type": "boolean", "default": False, "description": "Forward include_jobs/include_raw to task tool when used."},
                },
            },
        }

    async def call(self, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        question = str(arguments.get("question", "") or "").strip()
        messages_raw = arguments.get("messages") or []
        messages = _coerce_messages(messages_raw) if messages_raw else []
        bypass = bool(arguments.get("bypass_routing", False))
        include_raw = bool(arguments.get("include_raw", False))

        if not question and not messages:
            raise ValueError("Either 'question' or non-empty 'messages' must be provided.")

        if not question and messages:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    content_val = msg.get("content")
                    if content_val:
                        question = str(content_val).strip()
                        break

        if bypass:
            delegated = await askpanda_llm_answer_tool.call({"messages": messages} if messages else {"question": question})
            body = str(delegated[0].get("text", "")) if delegated and isinstance(delegated[0], dict) else str(delegated)
            return text_content(body)

        task_id = _extract_task_id(question)
        if task_id is None:
            delegated = await askpanda_llm_answer_tool.call({"messages": messages} if messages else {"question": question})
            body = str(delegated[0].get("text", "")) if delegated and isinstance(delegated[0], dict) else str(delegated)
            return text_content(body)

        # Call task status tool (our impl returns dict with evidence/text)
        tool_result = await panda_task_status_tool.call({"task_id": task_id, "query": question, "include_jobs": True if include_raw else True})
        evidence = tool_result.get("evidence", tool_result)

        # If task not found / non-json, ask LLM to explain clearly with next steps.
        system = (
            "You are AskPanDA for the ATLAS experiment. "
            "Given a user's question and a JSON evidence object from BigPanDA, "
            "write a concise, helpful answer.\n"
            "Rules:\n"
            "- If evidence.not_found is true or evidence.http_status==404: say the task was not found and suggest checking the ID.\n"
            "- If evidence indicates non-JSON/HTTP error: explain BigPanDA returned an error and include monitor_url.\n"
            "- Otherwise: summarize status, task name, owner, start/end times, dsinfo and dataset failures if present.\n"
            "- If job_counts is empty but datasets_summary exists, still describe datasets_summary.\n"
            "- Always include the BigPanDA monitor link.\n"
            "- Keep it under ~8 bullet points.\n"
        )

        prompt_user = (
            f"User question:\n{question}\n\n"
            f"Evidence JSON:\n{_compact(evidence)}\n"
        )

        delegated = await askpanda_llm_answer_tool.call(
            {"messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt_user}]}
        )
        body = str(delegated[0].get("text", "")) if delegated and isinstance(delegated[0], dict) else str(delegated)
        return text_content(body)


askpanda_answer_tool = AskPandaAnswerTool()
