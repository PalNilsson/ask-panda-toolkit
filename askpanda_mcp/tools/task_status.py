"""PanDA task status tool.

This MCP tool fetches task metadata from the PanDA monitor JSON endpoints and returns
a concise summary (status, job counts, recent errors).

The tool is intended to be selected when the user prompt contains the substring
"task <integer>" (e.g. "what is the status of task 123?").
"""

from __future__ import annotations

# The task status tool contains several small helpers and branching logic.
# We keep a targeted set of pylint disables for complex logic that would
# require a larger refactor to split further.
# pylint: disable=too-complex,too-many-nested-blocks,consider-using-alias

import asyncio
import json
import os
import re
from collections import Counter, deque
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, List

import httpx

from .base import text_content


_TASK_ID_RE = re.compile(r"\btask\s+(\d+)\b", re.IGNORECASE)


@dataclass(frozen=True)
class TaskSummary:
    """A normalized task summary extracted from PanDA metadata."""

    task_id: int
    status: str
    job_counts: Mapping[str, int]
    error_codes: tuple[int, ...]
    error_diags: tuple[str, ...]
    monitor_url: str


def _panda_base_url() -> str:
    """Return the PanDA monitor base URL.

    You can override the default using the environment variable `PANDA_BASE_URL`.

    Returns:
        Base URL as a string.
    """
    return os.getenv("PANDA_BASE_URL", "https://bigpanda.cern.ch").rstrip("/")


def extract_task_id_from_text(text: str) -> int | None:
    """Extract a task ID from a user prompt.

    Args:
        text: Free-form user prompt.

    Returns:
        The extracted task ID, or None if not found.
    """
    m = _TASK_ID_RE.search(text or "")
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


async def _fetch_task_metadata(task_id: int, *, timeout_s: float = 30.0) -> dict[str, Any]:
    """Fetch task metadata JSON from PanDA monitor.

    Uses the endpoint:
        {PANDA_BASE_URL}/task/<task_id>/?json

    Args:
        task_id: PanDA task ID.
        timeout_s: HTTP timeout in seconds.

    Returns:
        Parsed JSON as a dictionary.

    Raises:
        httpx.HTTPError: For network/HTTP errors.
        ValueError: If the response is not JSON/dict-like.
    """
    base = _panda_base_url()
    url = f"{base}/task/{task_id}/?json"

    # Retry a couple of times for transient issues.
    retries = int(os.getenv("ASKPANDA_PANDA_RETRIES", "2"))
    backoff = float(os.getenv("ASKPANDA_PANDA_BACKOFF_SECONDS", "0.8"))

    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout_s, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                if not isinstance(data, dict):
                    raise ValueError(f"Unexpected JSON type: {type(data)}")
                return data
        except (httpx.HTTPError, ValueError) as exc:
            last_exc = exc
            if attempt >= retries:
                raise
            # simple exponential backoff
            await asyncio.sleep(backoff * (2 ** attempt))

    assert last_exc is not None
    raise last_exc  # pragma: no cover


def _extract_task_info(payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """Extract task info dict from possibly varied payload shapes."""
    if isinstance(payload.get("task"), list) and payload.get("task"):
        if isinstance(payload["task"][0], dict):
            return payload["task"][0]
    if isinstance(payload.get("task"), dict):
        return payload.get("task")
    return None


def _process_jobs(jobs: Any) -> tuple[dict[str, int], tuple[int, ...], tuple[str, ...]]:
    """Process jobs list and return (job_counts, error_codes, error_diags)."""
    job_counts: Counter[str] = Counter()
    error_codes: deque[int] = deque(maxlen=50)
    error_diags: deque[str] = deque(maxlen=20)

    if isinstance(jobs, list):
        for job in jobs:
            if not isinstance(job, dict):
                continue
            js = str(job.get("jobstatus") or job.get("status") or "unknown")
            job_counts[js] += 1

            # Collect a small sample of errors for quick diagnosis.
            for k, v in job.items():
                lk = k.lower()
                if "errorcode" in lk:
                    try:
                        iv = int(v)
                        if iv > 0:
                            error_codes.append(iv)
                    except (ValueError, TypeError):
                        pass
                if "errordiag" in lk and isinstance(v, str) and v.strip():
                    error_diags.append(v.strip())

    # De-duplicate diags while preserving order
    seen = set()
    uniq_diags = []
    for d in error_diags:
        if d in seen:
            continue
        seen.add(d)
        uniq_diags.append(d)

    return dict(job_counts), tuple(error_codes), tuple(uniq_diags)


def _summarize_task(task_id: int, payload: Mapping[str, Any]) -> TaskSummary:
    """Build a compact TaskSummary from PanDA task metadata JSON.

    Args:
        task_id: PanDA task ID.
        payload: The JSON payload returned by the monitor.

    Returns:
        TaskSummary.
    """
    base = _panda_base_url()
    monitor_url = f"{base}/task/{task_id}/"

    task_info = _extract_task_info(payload)

    status = _try_status(
        (task_info or {}).get("taskstatus"),
        (task_info or {}).get("status"),
        payload.get("taskstatus"),
        payload.get("status"),
    )

    job_counts, error_codes, uniq_diags = _process_jobs(payload.get("jobs"))

    return TaskSummary(
        task_id=task_id,
        status=status,
        job_counts=job_counts,
        error_codes=error_codes,
        error_diags=uniq_diags,
        monitor_url=monitor_url,
    )


def _try_status(*candidates: Any) -> str:
    """Return the first non-empty candidate as string, or 'unknown'."""
    for cand in candidates:
        if cand:
            return str(cand)
    return "unknown"


def _format_job_counts(job_counts: Mapping[str, int]) -> list[str]:
    """Format job_counts mapping into human-readable lines."""
    lines: List[str] = []
    if job_counts:
        lines.append("Job counts:")
        for k, v in sorted(job_counts.items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"- {k}: {v}")
    else:
        lines.append("Job counts: (not available in metadata)")
    return lines


def _format_error_codes_and_diags(error_codes: tuple[int, ...], error_diags: tuple[str, ...]) -> list[str]:
    """Format recent error codes and diagnostics into lines."""
    lines: List[str] = []
    if error_codes:
        lines.append("Recent error codes (sample):")
        counts = Counter(error_codes)
        for code, cnt in counts.most_common(10):
            lines.append(f"- {code}: {cnt}")
        lines.append("")
    if error_diags:
        lines.append("Recent error diagnostics (sample):")
        for d in error_diags[:10]:
            d1 = d.replace("\n", " ").strip()
            if len(d1) > 400:
                d1 = d1[:400] + "..."
            lines.append(f"- {d1}")
        lines.append("")
    return lines


def _format_payload_debug(payload: Any) -> list[str]:
    """Return a short debug representation of the payload (keys + snippet)."""
    lines: List[str] = []
    if isinstance(payload, dict):
        lines.append(f"Payload keys: {sorted(payload.keys())}")
    try:
        raw = json.dumps(payload, indent=2)
        lines.append("\nRaw payload (snippet):\n")
        lines.append(raw[:5000])
    except (TypeError, ValueError):
        # If serialization fails, ignore the raw payload snippet.
        pass
    return lines


class PandaTaskStatusTool:
    """Provide an MCP tool that returns a summary for a PanDA task.

    Input:
        - task_id (int) OR
        - question (str) containing "task <integer>"

    Output:
        A human-readable summary plus a monitor URL.
    """

    @staticmethod
    def get_definition() -> dict[str, Any]:
        """Return the MCP tool definition."""
        return {
            "name": "panda_task_status",
            "description": (
                "Fetch PanDA task metadata and summarize status, job counts, and errors. "
                "Selection hint: the user prompt should include 'task <integer>'."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "PanDA task ID"},
                    "question": {
                        "type": "string",
                        "description": "User prompt containing 'task <integer>' (used to extract task_id)",
                    },
                    "include_raw": {
                        "type": "boolean",
                        "description": "If true, append the raw JSON payload.",
                        "default": False,
                    },
                },
                "anyOf": [{"required": ["task_id"]}, {"required": ["question"]}],
            },
        }

    async def call(self, arguments: dict[str, Any]) -> Any:
        """Execute the tool.

        Args:
            arguments: Tool arguments.

        Returns:
            MCP text content.
        """
        task_id = arguments.get("task_id")
        question = arguments.get("question") or ""
        include_raw = bool(arguments.get("include_raw", False))
        if os.getenv("ASKPANDA_PANDA_DEBUG", "") == "1":
            include_raw = True

        if task_id is None:
            task_id = extract_task_id_from_text(str(question))
        if task_id is None:
            return text_content(
                "Error: could not determine task id. Please include 'task <integer>' in the prompt "
                "or pass task_id explicitly."
            )

        try:
            payload = await _fetch_task_metadata(int(task_id))
        except httpx.HTTPStatusError as exc:
            return text_content(
                f"Error: PanDA monitor returned HTTP {exc.response.status_code} for task {task_id}.\n"
                f"URL: {_panda_base_url()}/task/{task_id}/?json"
            )
        except httpx.HTTPError as exc:
            return text_content(f"Error: failed to fetch task metadata for task {task_id}: {exc}")

        summary = _summarize_task(int(task_id), payload)

        lines = []

        # Detect "not found" cases. Some PanDA monitor endpoints may return 200 with
        # an empty/near-empty payload rather than a 404.
        # Heuristics: missing task info and missing jobs.
        task_block = payload.get("task")
        jobs_block = payload.get("jobs")
        has_task = bool(task_block) and (isinstance(task_block, (list, dict)))
        has_jobs = isinstance(jobs_block, list) and len(jobs_block) > 0
        if not has_task and not has_jobs:
            lines.append(
                f"Task {task_id} was not found (no metadata returned). Monitor: {summary.monitor_url}"
            )
            # Always show top-level keys for debugging.
            if isinstance(payload, dict):
                lines.extend(_format_payload_debug(payload))
            return text_content("\n".join(lines))

        lines.append(f"Task {summary.task_id}")
        lines.append(f"Status: {summary.status}")
        lines.append(f"Monitor: {summary.monitor_url}")
        lines.append("")

        lines.extend(_format_job_counts(summary.job_counts))
        lines.append("")

        lines.extend(_format_error_codes_and_diags(summary.error_codes, summary.error_diags))

        if not include_raw and summary.status == "unknown" and isinstance(payload, dict):
            lines.extend(_format_payload_debug(payload))

        if include_raw:
            lines.append("Raw payload:\n")
            lines.append(json.dumps(payload, indent=2)[:200000])  # guard against extreme size

        return text_content("\n".join(lines))


panda_task_status_tool = PandaTaskStatusTool()
