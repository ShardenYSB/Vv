"""Conversion of framework-independent admin screens into Aiogram markup."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from op_bot.admin_ui import Screen


def screen_markup(screen: Screen) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button.text, callback_data=button.callback_data) for button in row]
            for row in screen.keyboard
        ]
    )


def blocked_resources_markup(resources: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"🚫 {label[:45]}", callback_data=f"admin:unblock:{resource_id}")]
        for resource_id, label in resources
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
