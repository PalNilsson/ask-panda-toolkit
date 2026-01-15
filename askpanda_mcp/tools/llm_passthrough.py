"""Direct LLM passthrough tool.

This tool is intentionally simple: it forwards the full chat prompt (history)
to the configured **default** LLM profile and returns the model's raw text.

Use-cases:
  1) Sanity-check that LLM configuration (keys, provider adapters, networking)
     works end-to-end through MCP.
  2) Provide an explicit "bypass reasoning engine" path later, when the
     orchestration layer starts selecting tools.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from askpanda_mcp.prompts.templates import get_askpanda_system_prompt
from askpanda_mcp.tools.base import text_content

from askpanda_mcp.llm.runtime import get_llm_manager, get_llm_selector
from askpanda_mcp.llm.types import GenerateParams, Message


class LLMPassthroughTool:
    """Calls the default LLM with the full provided prompt."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Returns the MCP tool definition."""
        return {
            "name": "askpanda_llm_answer",
            "description": (
                "Send the full prompt (optionally including chat history) to the "
                "default LLM profile and return the raw response text."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "User question (used if messages is not provided).",
                    },
                    "messages": {
                        "type": "array",
                        "description": (
                            "Optional full chat history as a list of {role, content}. "
                            "If provided, it is sent to the LLM as-is (plus a system prompt)."
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string"},
                                "content": {"type": "string"},
                            },
                            "required": ["role", "content"],
                        },
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Sampling temperature.",
                        "default": 0.2,
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Optional max tokens for the completion.",
                    },
                },
            },
        }

    async def call(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Executes the passthrough call.

        Args:
            arguments: Tool arguments.

        Returns:
            MCP text content containing the model response.
        """
        selector = get_llm_selector()
        manager = get_llm_manager()

        # Determine which profile is considered "default".
        default_profile = getattr(selector, "default_profile", "default")
        registry = getattr(selector, "registry", None)
        if registry is None:
            raise RuntimeError("LLM selector does not expose a registry.")

        model_spec = registry.get(default_profile)
        debug = f"[LLM selected] provider={model_spec.provider} model={model_spec.model}"
        client = await manager.get_client(model_spec)

        temperature = float(arguments.get("temperature", 0.2))
        max_tokens = arguments.get("max_tokens")
        max_tokens_int = int(max_tokens) if max_tokens is not None else None

        # Build message list.
        sys_prompt = await get_askpanda_system_prompt()
        sys_text = getattr(sys_prompt, "text", None) or getattr(sys_prompt, "content", None)
        if isinstance(sys_text, list):
            # Some MCP prompt objects use content items.
            sys_text = "\n".join([str(x.get("text", "")) for x in sys_text if isinstance(x, dict)])
        system_message: Message = {"role": "system", "content": str(sys_text or "")}

        messages_arg = arguments.get("messages")
        messages: List[Message] = [system_message]
        if isinstance(messages_arg, list) and messages_arg:
            messages.extend(_coerce_messages(messages_arg))
        else:
            question = str(arguments.get("question", "")).strip()
            if not question:
                raise ValueError("Either 'question' or non-empty 'messages' must be provided.")
            messages.append({"role": "user", "content": question})

        resp = await client.generate(messages=messages, params=GenerateParams(temperature=temperature, max_tokens=max_tokens_int))
        return text_content(f"{debug}\n\n{resp.text}")


def _coerce_messages(raw: Sequence[Any]) -> List[Message]:
    """Coerces a list of dict-like chat messages into normalized Message items."""
    out: List[Message] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "user"))
        content = str(item.get("content", ""))
        if not content:
            continue
        if role not in ("system", "user", "assistant", "tool"):
            role = "user"
        out.append({"role": role, "content": content})
    return out


askpanda_llm_answer_tool = LLMPassthroughTool()
