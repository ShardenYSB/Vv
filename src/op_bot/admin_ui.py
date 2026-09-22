"""Inline-only admin UI definitions. Callback payloads are stable and text-free."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Button:
    text: str
    callback_data: str

@dataclass(frozen=True, slots=True)
class Screen:
    text: str
    keyboard: tuple[tuple[Button, ...], ...]


def admin_home(*, users: int, referrals: int, stars: int, tasks: int, blocked: int) -> Screen:
    return Screen(
        f"⚙️ АДМИН-ПАНЕЛЬ\n\n👥 Пользователей: {users:,}\n👥 Рефералов: {referrals:,}\n"
        f"⭐ Stars выдано: {stars:,}\n🎯 Выполнено заданий: {tasks:,}\n🚫 Заблокировано ресурсов: {blocked:,}",
        ((Button("⭐ Награды", "admin:rewards"),), (Button("👥 Пользователи", "admin:users"), Button("📊 Статистика", "admin:stats")),
         (Button("🚫 Заблокированные", "admin:blocked"), Button("🔗 Управление ОП", "admin:op")),
         (Button("📢 Рассылка", "admin:broadcast"),), (Button("⚙️ Настройки", "admin:settings"),)),
    )


def block_confirmation(url: str, resource_id: str) -> Screen:
    return Screen(f"🚫 Заблокировать ресурс?\n\nПосле блокировки этот ресурс не будет\nпоказываться пользователям в ОП.\n\n🔗 {url}\n\n🆔 {resource_id}",
                  ((Button("✅ Заблокировать", f"block:confirm:{resource_id}"), Button("❌ Отмена", "admin:back")),))


def reward_picker(range_id: int, lower: int, upper: int, current: int) -> Screen:
    buttons = tuple(tuple(Button(f"{value} ⭐", f"reward:set:{range_id}:{value}") for value in row)
                    for row in ((0, 1, 2), (3, 4, 5), (10, 15)))
    return Screen(f"⭐ Изменение награды\n\nДиапазон:\n{lower}–{upper} спонсоров\n\nТекущая награда:\n{current} ⭐\n\nВыберите новую награду:",
                  (*buttons, (Button("❌ Отмена", "admin:rewards"),)))


def unresolved_resource(url: str, resource_id: str | None, unresolved_id: int) -> Screen:
    """Admin card for a failed URL; no operator needs to type a command."""
    return Screen(
        f"⚠️ Обнаружена неизвестная ссылка\n\n🔗 URL:\n{url}\n\n🆔 Resource ID:\n{resource_id or 'не указан'}",
        ((Button("🚫 Заблокировать", f"unresolved:block:{unresolved_id}"),),
         (Button("🔄 Повторить", f"unresolved:retry:{unresolved_id}"), Button("📝 Игнорировать", f"unresolved:ignore:{unresolved_id}")),
         (Button("⬅️ Назад", "admin:back"),)),
    )


def op_management(*, max_op: int, blocked: int) -> Screen:
    return Screen(f"🔗 УПРАВЛЕНИЕ ОП\n\n📊 Максимум спонсоров: {max_op}\n\n🚫 Заблокированных: {blocked}",
        ((Button("🔢 Максимум ОП", "op:max"),), (Button("🚫 Заблокированные", "admin:blocked"), Button("📋 Последние ресурсы", "op:recent")), (Button("⬅️ Назад", "admin:home"),)))
