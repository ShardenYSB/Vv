"""Protected inline administration routes; no text command is required."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from op_bot.admin_ui import admin_home
from op_bot.keyboards.admin import blocked_resources_markup, screen_markup
from op_bot.keyboards.user import back

router = Router(name="admin")


def _is_admin(callback: CallbackQuery, settings) -> bool:
    return callback.from_user.id in settings.admin_ids


async def _deny(callback: CallbackQuery) -> None:
    await callback.answer("Недостаточно прав.", show_alert=True)


async def _home(callback: CallbackQuery, admin_service, settings) -> None:
    stats = await admin_service.dashboard()
    screen = admin_home(**stats)
    await callback.message.edit_text(screen.text, reply_markup=screen_markup(screen))


@router.callback_query(F.data == "admin:home")
async def home(callback: CallbackQuery, admin_service, settings) -> None:
    if not _is_admin(callback, settings):
        await _deny(callback)
        return
    await _home(callback, admin_service, settings)
    await callback.answer()


@router.callback_query(F.data == "admin:blocked")
async def blocked(callback: CallbackQuery, blocks, settings) -> None:
    if not _is_admin(callback, settings):
        await _deny(callback)
        return
    await _show_blocked(callback, blocks)
    await callback.answer()


async def _show_blocked(callback: CallbackQuery, blocks) -> None:
    resources = await blocks.list_blocked()
    if not resources:
        await callback.message.edit_text("🚫 Заблокированные ресурсы\n\nСписок пуст.", reply_markup=back())
    else:
        labels = [(item.resource_id, item.url.rsplit("/", 1)[-1] or item.resource_id) for item in resources]
        await callback.message.edit_text("🚫 Заблокированные ресурсы\n\nНажмите ресурс, чтобы разблокировать его.", reply_markup=blocked_resources_markup(labels))


@router.callback_query(F.data.startswith("admin:unblock:"))
async def unblock(callback: CallbackQuery, blocks, admin_service, settings) -> None:
    if not _is_admin(callback, settings):
        await _deny(callback)
        return
    resource_id = callback.data.removeprefix("admin:unblock:")
    if not resource_id:
        await callback.answer("Некорректный ресурс.", show_alert=True)
        return
    changed = await blocks.unblock(resource_id)
    if changed:
        await admin_service.log(callback.from_user.id, "UNBLOCK_RESOURCE", "resource", resource_id, old_value="blocked", new_value="active")
    await callback.answer("✅ Ресурс разблокирован." if changed else "Ресурс уже разблокирован.", show_alert=True)
    await _show_blocked(callback, blocks)


@router.callback_query(F.data.in_({"admin:rewards", "admin:users", "admin:stats", "admin:op", "admin:broadcast", "admin:settings"}))
async def placeholder(callback: CallbackQuery, settings) -> None:
    if not _is_admin(callback, settings):
        await _deny(callback)
        return
    await callback.message.edit_text("⚙️ Раздел готов к подключению бизнес-настроек. Используйте «Назад», чтобы вернуться в панель.", reply_markup=back())
    await callback.answer()
