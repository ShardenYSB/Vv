"""BotoHub integration with blacklist filtering and unresolved-resource reporting."""
from __future__ import annotations
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from .link_resolver import LinkResolver, ResolvedLink
from .resource_blocks import ResourceBlockService


class BotoHubClient(Protocol):
    async def get_tasks_extended(self, *, chat_id: int, max_op: int, only_has_check: bool,
                                 excluded_ids: list[str]) -> dict[str, Any]: ...


UnresolvedReporter = Callable[[str, str | None, int, str], Awaitable[None]]


class SponsorService:
    """Fetch tasks with two blacklist layers.

    ``excluded_ids`` prevents future selections in BotoHub. The local pass is still
    required because BotoHub can keep a sponsor list pinned for several minutes.
    """
    def __init__(self, botohub: BotoHubClient, blocks: ResourceBlockService,
                 resolver: LinkResolver, *, max_op: int = 20,
                 report_unresolved: UnresolvedReporter | None = None) -> None:
        self._botohub, self._blocks, self._resolver = botohub, blocks, resolver
        self._max_op, self._report_unresolved = max_op, report_unresolved

    async def get_sponsors(self, chat_id: int) -> list[dict[str, Any]]:
        excluded_ids = await self._blocks.get_blocked_ids()
        result = await self._botohub.get_tasks_extended(
            chat_id=chat_id, max_op=self._max_op, only_has_check=True, excluded_ids=excluded_ids
        )
        visible: list[dict[str, Any]] = []
        for task in result.get("tasks", []):
            resource_id = task.get("resource_id")
            url = task.get("url") or task.get("link")
            if not resource_id or await self._blocks.is_blocked(str(resource_id)):
                continue
            resolved = self._resolver.resolve(url, resource_type=task.get("resource_type"))
            if resolved is None:
                await self._report_bad(url, str(resource_id), chat_id, "unknown_telegram_link")
                continue
            visible.append({**task, "resolved_link": resolved})
        return visible

    async def _report_bad(self, url: str | None, resource_id: str | None, user_id: int, error_type: str) -> None:
        if self._report_unresolved:
            await self._report_unresolved(url or "", resource_id, user_id, error_type)
