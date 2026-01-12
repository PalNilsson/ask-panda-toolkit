"""Dummy documentation/RAG tool.

Later, replace the dummy implementation with:
- local KB retrieval (BM25/FAISS)
- PanDA/ATLAS docs ingestion
- optional LLM synthesis
"""
from __future__ import annotations
from typing import Any, Dict, List
from .base import text_content

class PandaDocSearchTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
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

    async def call(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        query = arguments.get("query", "")
        top_k = int(arguments.get("top_k", 5))
        # Dummy "results"
        hits = [
            f"[{i+1}] Dummy KB hit for: '{query}' (score={1.0 - i*0.1:.2f})"
            for i in range(max(1, min(top_k, 5)))
        ]
        return text_content("AskPanDA Doc Search (dummy)\n\n" + "\n".join(hits))

panda_doc_search_tool = PandaDocSearchTool()
