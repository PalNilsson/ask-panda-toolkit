from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Iterable

try:
    from importlib.metadata import entry_points, EntryPoint
except Exception:  # pragma: no cover
    from importlib_metadata import entry_points, EntryPoint  # type: ignore

PRIMARY_GROUP = "bamboo.tools"
LEGACY_GROUP = "askpanda.tools"


@dataclass(frozen=True)
class ResolvedTool:
    name: str
    namespace: str
    obj: Any
    entry_point: str


def _iter_entry_points(groups: Iterable[str]):
    eps = entry_points()
    for g in groups:
        try:
            selected = eps.select(group=g)  # type: ignore[attr-defined]
        except Exception:
            selected = eps.get(g, []) if isinstance(eps, dict) else []
        for ep in selected:
            yield ep


def list_tool_entry_points() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for ep in _iter_entry_points([PRIMARY_GROUP, LEGACY_GROUP]):
        out.append({"group": ep.group, "name": ep.name, "value": ep.value})
    return out


def find_tool_by_name(tool_name: str, namespace: Optional[str] = None) -> Optional[ResolvedTool]:
    wanted_suffix = f".{tool_name}" if tool_name and "." not in tool_name else tool_name

    for group in (PRIMARY_GROUP, LEGACY_GROUP):
        for ep in _iter_entry_points([group]):
            ep_name = ep.name
            if namespace:
                if ep_name != f"{namespace}.{tool_name}":
                    continue
            else:
                if wanted_suffix and not ep_name.endswith(wanted_suffix):
                    continue

            try:
                obj = ep.load()
            except Exception:
                continue

            ns, _, name = ep_name.partition(".")
            return ResolvedTool(
                name=name or tool_name,
                namespace=ns,
                obj=obj,
                entry_point=f"{ep.group}:{ep.name}={ep.value}",
            )
    return None
