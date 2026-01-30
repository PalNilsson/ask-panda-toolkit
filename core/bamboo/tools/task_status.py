"""
task_status.py

Improved canonical wrapper for bamboo.tools.task_status that ensures the
exported tool object `panda_task_status_tool` exposes a robust get_definition()
including an 'inputSchema' key so UI/registry validation passes.

This file wraps an existing implementation if present (preferred as task_status_impl
or similar). If none found, it provides a helpful stub.
"""
from __future__ import annotations
import asyncio
import inspect
import importlib
from typing import Any, Optional

# Try to import a real implementation under a different name first to avoid self-import.
_real = None
_import_errors = []

candidates = [
    "bamboo.tools.task_status_atlas",
    "bamboo.tools.task_status_orig",
    "bamboo.tools.task_status_original",
    "bamboo.tools.task_status_backup",
    # do not import "bamboo.tools.task_status" here to avoid recursion
]

for name in candidates:
    try:
        mod = importlib.import_module(name)
        if mod is not None and getattr(mod, "__name__", "") != __name__:
            _real = mod
            break
    except Exception as e:
        _import_errors.append((name, repr(e)))
        continue

# If no alternative module found, try to import plain 'task_status' (may point to original in some setups)
if _real is None:
    try:
        mod_plain = importlib.import_module("task_status")
        if getattr(mod_plain, "__name__", "") != __name__:
            _real = mod_plain
    except Exception as e:
        _import_errors.append(("task_status", repr(e)))
        _real = None

# Helper to find a callable in a module
def _find_callable_in_module(mod) -> Optional[Any]:
    # If module defines a canonical tool object with .call, use that
    if hasattr(mod, "panda_task_status_tool") and hasattr(mod.panda_task_status_tool, "call"):
        return getattr(mod, "panda_task_status_tool").call  # may be async or sync
    # module-level call()
    if hasattr(mod, "call") and callable(mod.call):
        return mod.call
    # common function names
    for name in ("panda_task_status", "get_task_status", "task_status", "run", "handle"):
        if hasattr(mod, name) and callable(getattr(mod, name)):
            return getattr(mod, name)
    return None

# Final fallback: provide a stub that returns an informative error
async def _stub_call(arguments: dict) -> Any:
    return {
        "error": "no underlying task_status implementation found",
        "message": "Restore the original implementation as task_status_impl.py or ensure the module exports callable functions.",
        "import_attempts": _import_errors,
        "provided_arguments": arguments,
    }

# Wrap a callable (sync or async) into an async function
def _wrap_callable(fn):
    if inspect.iscoroutinefunction(fn):
        async def _async_fn(args):
            return await fn(args)
        return _async_fn
    else:
        async def _async_fn(args):
            return await asyncio.to_thread(fn, args)
        return _async_fn

_detected_callable = None
if _real is not None:
    _detected_callable = _find_callable_in_module(_real)

if _detected_callable is not None:
    _async_caller = _wrap_callable(_detected_callable)
else:
    _async_caller = _stub_call

# Create the canonical tool object with a robust get_definition including inputSchema
class _Tool:
    def __init__(self):
        # attempt to reuse definition from real module if present
        if _real is not None and hasattr(_real, "get_definition"):
            try:
                base_def = _real.get_definition() or {}
            except Exception:
                base_def = {}
        else:
            base_def = {}

        # Ensure required fields exist and include a sensible inputSchema
        self._def = {
            "name": base_def.get("name", "panda_task_status"),
            "description": base_def.get("description", "PanDA task status (wrapped)"),
            "inputSchema": base_def.get("inputSchema", {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "PanDA task id"},
                    "query": {"type": "string", "description": "Original user query string (optional)"},
                },
                # task_id is the primary required field for this tool
                "required": ["task_id"],
                "additionalProperties": True
            }),
            "examples": base_def.get("examples", [
                {"task_id": 48254358, "query": "what is the status of task 48254358?"}
            ]),
            "tags": base_def.get("tags", ["panda", "monitoring", "task"]),
        }

        # If the real module indicated a detected source, add that for debugging
        if _real is not None:
            try:
                self._def.setdefault("metadata", {})["detected_module"] = getattr(_real, "__name__", "unknown")
            except Exception:
                pass

    def get_definition(self):
        return self._def

    async def call(self, arguments: dict) -> Any:
        # Prefer passing the arguments through to the underlying implementation if present.
        if _real is not None:
            # If the real module exposes an awaitable call, try to use it
            try:
                # If real exposes panda_task_status_tool with .call
                if hasattr(_real, "panda_task_status_tool") and hasattr(_real.panda_task_status_tool, "call"):
                    fn = _real.panda_task_status_tool.call
                    if inspect.iscoroutinefunction(fn):
                        return await fn(arguments)
                    else:
                        return await asyncio.to_thread(fn, arguments)
                # module-level call
                if hasattr(_real, "call") and callable(_real.call):
                    fn = _real.call
                    if inspect.iscoroutinefunction(fn):
                        return await fn(arguments)
                    else:
                        return await asyncio.to_thread(fn, arguments)
                # fallback: detect common function names
                for name in ("panda_task_status", "get_task_status", "task_status", "run", "handle"):
                    if hasattr(_real, name) and callable(getattr(_real, name)):
                        fn = getattr(_real, name)
                        if inspect.iscoroutinefunction(fn):
                            return await fn(arguments)
                        else:
                            return await asyncio.to_thread(fn, arguments)
            except Exception as e:
                # If the underlying implementation raises, return the exception info for debugging
                return {"error": "underlying task_status raised", "exception": repr(e), "provided_arguments": arguments}

        # No real implementation found — return stub response
        return await _stub_call(arguments)

panda_task_status_tool = _Tool()

# For backwards-compatibility, also expose module-level async call
async def call(arguments: dict) -> Any:
    return await panda_task_status_tool.call(arguments)
