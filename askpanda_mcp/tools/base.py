"""Common tool patterns used by this skeleton."""
from __future__ import annotations
from typing import Any, Dict, List, Protocol

MCPContent = Dict[str, Any]

class MCPTool(Protocol):
    @staticmethod
    def get_definition() -> Dict[str, Any]: ...
    async def call(self, arguments: Dict[str, Any]) -> List[MCPContent]: ...

def text_content(text: str) -> List[MCPContent]:
    return [{"type": "text", "text": text}]
