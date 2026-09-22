"""Inline-only Aiogram user routes."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from op_bot.botohub import BotoHubError, BotoHubService
from op_bot.keyboards.user import back, main_menu, referrals, sponsors, task
from op_bot.link_resolver import LinkResolver
from op_bot.sponsors import SponsorService

router = Router()
log = logging.getLogger(__name__)


def _start_referral(text: str | None, user_id: int) -> int | None:
    if not text:
        return None
    parts = text.split(maxsplit=1)
    if len(parts) != 2 or not parts[1].startswith("ref_"):
        return None
    try:
        referrer = int(parts[1][4:])
    except ValueError:
        return None
    return None if referrer == user_id else referrer


async def _show_home(message: Message, users, telegram_id: int, *, edit: bool, settings) -> None:
    user, referrals_count, tasks_count, _ = await users.profile(telegram_id)
    text = f"👋 Добро пожаловать!\n\n⭐ Баланс: {user.stars_balance} Stars\n👥 Рефералов: {referrals_count}\n🎯 Выполнено заданий: {tasks_count}"
    if edit:
        await message.edit_text(text, reply_markup=main_menu(telegram_id in settings.admin_ids))
    else:
        await message.answer(text, reply_markup=main_menu(telegram_id in settings.admin_ids))


async def _sponsor_screen(message: Message, sponsor_service: SponsorService, users, user_id: int, *, edit: bool, settings) -> None:
    try:
        sponsor_tasks = await sponsor_service.get_sponsors(user_id)
    except BotoHubError:
        text = "⚠️ Сервис временно недоступен.\n\nПопробуйте ещё раз через несколько секунд."
        if edit:
            await message.edit_text(text, reply_markup=back())
        else:
            await message.answer(text, reply_markup=back())
        return
    if not sponsor_tasks or all(item.get("completed") for item in sponsor_tasks):
        reward = await users.confirm_referral_after_sponsors(user_id, len(sponsor_tasks))
        await _show_home(message, users, user_id, edit=edit, settings=settings)
        if reward:
            await message.answer(f"🎉 Ваш пригласивший получил {reward} ⭐ за выполненные вами подписки.")
        return
    status = "\n".join("🟢 Выполнено" if item.get("completed") else "🔴 Не выполнено" for item in sponsor_tasks)
    text = "🔐 Для доступа к боту необходимо выполнить обязательные подписки.\n\n" + status + "\n\nПосле подписки нажмите кнопку проверки."
    if edit:
        await message.edit_text(text, reply_markup=sponsors(sponsor_tasks))
    else:
        await message.answer(text, reply_markup=sponsors(sponsor_tasks))


@router.message(CommandStart())
async def start(message: Message, sponsor_service: SponsorService, users, settings) -> None:
    if not message.from_user:
        return
    referrer = _start_referral(message.text, message.from_user.id)
    await users.register(message.from_user.id, message.from_user.username, message.from_user.first_name, referrer)
    log.info("USER_REGISTERED user_id=%s referrer=%s", message.from_user.id, referrer)
    await _sponsor_screen(message, sponsor_service, users, message.from_user.id, edit=False, settings=settings)


@router.callback_query(F.data == "sponsors:check")
async def check_sponsors(callback: CallbackQuery, sponsor_service: SponsorService, users, settings) -> None:
    await callback.answer()
    await _sponsor_screen(callback.message, sponsor_service, users, callback.from_user.id, edit=True, settings=settings)


@router.callback_query(F.data == "home")
async def home(callback: CallbackQuery, users, settings) -> None:
    await _show_home(callback.message, users, callback.from_user.id, edit=True, settings=settings)
    await callback.answer()


async def _render_task(callback: CallbackQuery, result: dict, task_service) -> None:
    if result.get("fake"):
        await callback.message.edit_text("⚠️ Получение новых заданий временно недоступно.", reply_markup=back())
        return
    url, resource_id = result.get("url"), result.get("resource_id")
    if not url or resource_id in (None, ""):
        await callback.message.edit_text("🎯 Все задания выполнены.", reply_markup=main_menu())
        return
    resolved = LinkResolver().resolve(str(url), resource_type=result.get("resource_type"))
    if not resolved:
        log.warning("TASK_REJECTED_INVALID_URL user_id=%s resource_id=%s", callback.from_user.id, resource_id)
        await callback.message.edit_text("⚠️ Не удалось безопасно обработать это задание. Попробуйте получить следующее.", reply_markup=back())
        return
    reward = int(result.get("reward", 0) or 0)
    await task_service.present(callback.from_user.id, str(resource_id), str(url), reward)
    await callback.message.edit_text(f"🎯 Задание\n\n⭐ Награда: {reward} ⭐\n\nПосле выполнения нажмите «Проверить».", reply_markup=task(resolved.url))


@router.callback_query(F.data == "tasks")
async def get_task(callback: CallbackQuery, botohub: BotoHubService, task_service, users) -> None:
    # Callback data can be forged; never trust the menu path as an authorization check.
    if not await users.has_sponsor_access(callback.from_user.id):
        await callback.answer("Сначала выполните обязательные подписки.", show_alert=True)
        return
    try:
        result = await botohub.get_task(callback.from_user.id)
    except BotoHubError:
        await callback.answer("Сервис временно недоступен", show_alert=True)
        return
    await _render_task(callback, result, task_service)
    await callback.answer()


@router.callback_query(F.data.in_({"task:check", "task:skip"}))
async def advance_task(callback: CallbackQuery, botohub: BotoHubService, task_service, users) -> None:
    skip = callback.data == "task:skip"
    if not await users.has_sponsor_access(callback.from_user.id):
        await callback.answer("Сначала выполните обязательные подписки.", show_alert=True)
        return
    try:
        result = await botohub.get_task(callback.from_user.id, skip=skip)
    except BotoHubError:
        await callback.answer("Сервис временно недоступен", show_alert=True)
        return
    notification = None
    if skip:
        await task_service.abandon_presented(callback.from_user.id)
    elif result.get("prev_success"):
        paid = await task_service.complete_presented(callback.from_user.id)
        if paid:
            notification = "✅ Задание проверено. Награда начислена!"
    await _render_task(callback, result, task_service)
    await callback.answer(notification)


@router.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery, users) -> None:
    try:
        user, referrals_count, tasks_count, referral_earned = await users.profile(callback.from_user.id)
    except LookupError:
        await callback.answer("Нажмите /start", show_alert=True)
        return
    text = f"👤 Ваш профиль\n\n🆔 ID: {user.telegram_id}\n\n⭐ Stars: {user.stars_balance}\n👥 Рефералов: {referrals_count}\n\n🎯 Выполнено заданий: {tasks_count}\n\n🏆 Получено за рефералов: {referral_earned} ⭐"
    await callback.message.edit_text(text, reply_markup=back())
    await callback.answer()


@router.callback_query(F.data == "referrals")
async def referrals_screen(callback: CallbackQuery, users) -> None:
    try:
        user, count, _, earned = await users.profile(callback.from_user.id)
    except LookupError:
        await callback.answer("Нажмите /start", show_alert=True)
        return
    me = await callback.bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{user.telegram_id}"
    text = f"👥 Реферальная система\n\nПриглашай друзей и получай Stars.\n\n🔗 Твоя ссылка:\n{link}\n\n👤 Приглашено: {count}\n⭐ Заработано: {earned}"
    await callback.message.edit_text(text, reply_markup=referrals(f"Присоединяйся: {link}"))
    await callback.answer()


@router.callback_query(F.data.in_({"stars", "help"}))
async def informational_screen(callback: CallbackQuery) -> None:
    text = "⭐ Stars начисляются за подтверждённые задания и рефералов." if callback.data == "stars" else "ℹ️ Выполните обязательные подписки, затем выбирайте задания через меню."
    await callback.message.edit_text(text, reply_markup=back())
    await callback.answer()
