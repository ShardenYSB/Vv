from op_bot.link_resolver import LinkResolver, LinkType
from op_bot.repositories import InMemoryBlockedResourceRepository
from op_bot.resource_blocks import ResourceBlockService
from op_bot.sponsors import SponsorService


def test_resolver_supports_public_invite_and_bot_links():
    resolver = LinkResolver()
    assert resolver.resolve("https://t.me/channel").kind is LinkType.CHANNEL
    assert resolver.resolve("https://telegram.me/group_name", resource_type="group").kind is LinkType.GROUP
    assert resolver.resolve("https://t.me/bot_name?start=123").kind is LinkType.BOT
    assert resolver.resolve("https://t.me/+AbCdEf").kind is LinkType.INVITE
    assert resolver.resolve("http://t.me/channel") is None
    assert resolver.resolve("https://example.com/channel") is None
    assert resolver.resolve("https://t.me/channel/extra") is None


class FakeBotoHub:
    def __init__(self): self.request = None
    async def get_tasks_extended(self, **kwargs):
        self.request = kwargs
        return {"tasks": [
            {"resource_id": "blocked", "url": "https://t.me/blocked"},
            {"resource_id": "valid", "url": "https://t.me/valid_channel"},
            {"resource_id": "bad", "url": "https://invalid.example/a"},
        ]}


def test_sponsors_send_exclusions_filter_pinned_and_report_bad():
    import asyncio
    asyncio.run(_sponsors_send_exclusions_filter_pinned_and_report_bad())


async def _sponsors_send_exclusions_filter_pinned_and_report_bad():
    repo = InMemoryBlockedResourceRepository()
    blocks = ResourceBlockService(repo)
    await blocks.block("blocked", "https://t.me/blocked", 1)
    reports = []
    async def report(*args): reports.append(args)
    client = FakeBotoHub()
    service = SponsorService(client, blocks, LinkResolver(), max_op=15, report_unresolved=report)

    tasks = await service.get_sponsors(42)

    assert client.request == {"chat_id": 42, "max_op": 15, "only_has_check": True, "excluded_ids": ["blocked"]}
    assert [task["resource_id"] for task in tasks] == ["valid"]
    assert reports == [("https://invalid.example/a", "bad", 42, "unknown_telegram_link")]

from op_bot.rewards import get_referral_reward
from op_bot.config import Settings
from op_bot.admin_ui import admin_home
from op_bot.keyboards.admin import screen_markup

def test_referral_rewards_follow_configured_ranges():
    assert [get_referral_reward(value) for value in (0, 2, 3, 5, 6, 8, 9, 15, 16, 20, 21)] == [0, 0, 1, 1, 2, 2, 3, 3, 5, 5, 0]


def test_settings_rejects_unfilled_example_values(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "CHANGE_ME_PASTE_BOTFATHER_TOKEN_HERE")
    monkeypatch.setenv("BOTOHUB_TOKEN", "real-token")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/db")
    try:
        Settings.from_env()
    except RuntimeError as error:
        assert "BOT_TOKEN" in str(error)
    else:
        raise AssertionError("placeholder configuration must be rejected")


def test_settings_parses_admins_and_max_op(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "telegram-token")
    monkeypatch.setenv("BOTOHUB_TOKEN", "hub-token")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/db")
    monkeypatch.setenv("ADMIN_IDS", " 100,200 ")
    monkeypatch.setenv("MAX_OP", "15")
    settings = Settings.from_env()
    assert settings.admin_ids == frozenset({100, 200})
    assert settings.max_op == 15


def test_admin_dashboard_is_an_inline_keyboard():
    screen = admin_home(users=1, referrals=2, stars=3, tasks=4, blocked=5)
    markup = screen_markup(screen)
    assert "Пользователей: 1" in screen.text
    assert any(button.callback_data == "admin:blocked" for row in markup.inline_keyboard for button in row)
