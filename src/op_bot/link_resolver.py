"""Strict parsing of Telegram links before they become inline buttons."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import parse_qs, urlparse
import re

_USERNAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{4,31}$")
_INVITE = re.compile(r"^[A-Za-z0-9_-]{5,}$")


class LinkType(StrEnum):
    CHANNEL = "channel"
    GROUP = "group"
    BOT = "bot"
    INVITE = "invite"


@dataclass(frozen=True, slots=True)
class ResolvedLink:
    url: str
    kind: LinkType
    username: str | None = None
    parameters: dict[str, list[str]] | None = None


class LinkResolver:
    """Allow only canonical public Telegram and invite URL formats.

    Telegram cannot reliably distinguish a public group from a channel by its URL.
    Public targets are therefore classified as a channel unless task metadata supplies
    ``resource_type`` (``group`` or ``bot``).  A ``start`` parameter identifies bots.
    """

    _hosts = {"t.me", "telegram.me", "www.t.me", "www.telegram.me"}

    def resolve(self, url: str | None, *, resource_type: str | None = None) -> ResolvedLink | None:
        if not url or not isinstance(url, str) or any(ch.isspace() for ch in url):
            return None
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc.lower() not in self._hosts:
            return None
        if parsed.fragment or parsed.params:
            return None
        path = parsed.path.strip("/")
        query = parse_qs(parsed.query, keep_blank_values=True)
        # t.me/+token and t.me/joinchat/token are the only allowed invite forms.
        invite_token = path[1:] if path.startswith("+") else None
        if path.startswith("joinchat/"):
            bits = path.split("/")
            invite_token = bits[1] if len(bits) == 2 else None
        if invite_token is not None:
            if not _INVITE.fullmatch(invite_token) or query:
                return None
            return ResolvedLink(url=url, kind=LinkType.INVITE, parameters=query or None)
        if "/" in path or not _USERNAME.fullmatch(path):
            return None
        kind = LinkType.BOT if "start" in query or resource_type == "bot" else (
            LinkType.GROUP if resource_type == "group" else LinkType.CHANNEL
        )
        return ResolvedLink(url=url, kind=kind, username=path, parameters=query or None)
