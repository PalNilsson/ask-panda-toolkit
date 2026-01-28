"""Dummy documentation/RAG tool.

Later, replace the dummy implementation with:
- local KB retrieval (BM25/FAISS)
- PanDA/ATLAS docs ingestion
- optional LLM synthesis
"""
from __future__ import annotations
from typing import Any
from askpanda_mcp.tools.base import text_content


class PandaDocSearchTool:
    """Dummy document search tool used for AskPanDA development.

    This placeholder implements a minimal searchable interface that clients
    can call while the real knowledge-base-backed retrieval and RAG logic is
    being developed. It returns a small human-readable text payload with
    simulated hits.
    """

    @staticmethod
    def get_definition() -> dict[str, Any]:
        """Return the tool discovery definition.

        The dictionary describes the tool name, description and input schema
        so clients can discover and validate calls to this tool.

        Returns:
            Dict[str, Any]: Tool definition compatible with the MCP discovery
            format used elsewhere in the project.
        """
        return {
            "name": "panda_doc_search",
            "description": "Search AskPanDA documentation knowledge base (dummy implementation).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for"},
                    "top_k": {"type": "integer", "description": "How many hits to return", "default": 5},
                },
                "required": ["query"],
            },
        }

    async def call(self, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute the dummy document search.

        Args:
            arguments: Mapping with keys expected by the tool (``query`` and
                optional ``top_k``).

        Returns:
            List[Dict[str, Any]]: A list of content blocks to return to the
            caller. The current implementation returns a single text block
            produced by the ``text_content`` helper.
        """
        query = arguments.get("query", "")
        top_k = int(arguments.get("top_k", 5))
        # Dummy "results"
        hits = [
            f"[{(i + 1)}] Dummy KB hit for: '{query}' (score={(1.0 - i * 0.1):.2f})"
            for i in range(max(1, min(top_k, 5)))
        ]
        return text_content("AskPanDA Doc Search (dummy)\n\n" + "\n".join(hits))


panda_doc_search_tool = PandaDocSearchTool()
