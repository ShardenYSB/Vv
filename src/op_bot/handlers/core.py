"""Inline-only Aiogram user routes."""
from __future__ import annotations

import logging
from urllib.parse import urlparse

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from op_bot.botohub import BotoHubError, BotoHubService
from op_bot.keyboards.user import back, main_menu, referrals, sponsors, task, task_providers
from op_bot.link_resolver import LinkResolver
from op_bot.sponsors import SponsorService
from op_bot.tgrass import TgrassError, TgrassUser

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


def _safe_offer_url(url: object) -> str | None:
    if not isinstance(url, str) or any(char.isspace() for char in url):
        return None
    parsed = urlparse(url)
    return url if parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password else None


def _tgrass_user(user) -> TgrassUser:
    return TgrassUser(user.id, user.username, user.language_code, bool(user.is_premium))


async def _sponsor_screen(message: Message, sponsor_service: SponsorService, users, user, *, edit: bool, settings, tgrass) -> None:
    try:
        sponsor_tasks = await sponsor_service.get_sponsors(user.id)
    except BotoHubError:
        text = "⚠️ Сервис временно недоступен.\n\nПопробуйте ещё раз через несколько секунд."
        if edit:
            await message.edit_text(text, reply_markup=back())
        else:
            await message.answer(text, reply_markup=back())
        return
    tgrass_tasks: list[dict] = []
    tgrass_done = True
    if tgrass:
        try:
            response = await tgrass.get_offers(_tgrass_user(user))
            tgrass_done = response.get("status") in {"ok", "no_offers"}
            tgrass_tasks = [
                {"button_url": safe_url, "completed": bool(offer.get("subscribed")), "name": offer.get("name")}
                for offer in response.get("offers", [])
                if (safe_url := _safe_offer_url(offer.get("link")))
            ]
        except TgrassError:
            log.warning("TGRASS_OFFERS_ERROR user_id=%s", user.id, exc_info=True)
            tgrass_done = True
    all_tasks = sponsor_tasks + tgrass_tasks
    if (not sponsor_tasks or all(item.get("completed") for item in sponsor_tasks)) and tgrass_done:
        reward = await users.confirm_referral_after_sponsors(user.id, len(all_tasks))
        await _show_home(message, users, user.id, edit=edit, settings=settings)
        if reward:
            await message.answer(f"🎉 Ваш пригласивший получил {reward} ⭐ за выполненные вами подписки.")
        return
    status = "\n".join("🟢 Выполнено" if item.get("completed") else "🔴 Не выполнено" for item in all_tasks)
    text = "🔐 Для доступа к боту необходимо выполнить обязательные подписки.\n\n" + status + "\n\nПосле подписки нажмите кнопку проверки."
    if edit:
        await message.edit_text(text, reply_markup=sponsors(all_tasks))
    else:
        await message.answer(text, reply_markup=sponsors(all_tasks))


@router.message(CommandStart())
async def start(message: Message, sponsor_service: SponsorService, users, settings, tgrass) -> None:
    if not message.from_user:
        return
    referrer = _start_referral(message.text, message.from_user.id)
    await users.register(message.from_user.id, message.from_user.username, message.from_user.first_name, referrer)
    log.info("USER_REGISTERED user_id=%s referrer=%s", message.from_user.id, referrer)
    await _sponsor_screen(message, sponsor_service, users, message.from_user, edit=False, settings=settings, tgrass=tgrass)


@router.callback_query(F.data == "sponsors:check")
async def check_sponsors(callback: CallbackQuery, sponsor_service: SponsorService, users, settings, tgrass) -> None:
    await callback.answer()
    await _sponsor_screen(callback.message, sponsor_service, users, callback.from_user, edit=True, settings=settings, tgrass=tgrass)


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
async def task_menu(callback: CallbackQuery, users, tgrass) -> None:
    if not await users.has_sponsor_access(callback.from_user.id):
        await callback.answer("Сначала выполните обязательные подписки.", show_alert=True)
        return
    await callback.message.edit_text("🎯 Выберите источник заданий.", reply_markup=task_providers(bool(tgrass)))
    await callback.answer()


@router.callback_query(F.data == "tasks:botohub")
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


@router.callback_query(F.data == "tasks:tgrass")
async def tgrass_tasks(callback: CallbackQuery, users, tgrass) -> None:
    if not tgrass:
        await callback.answer("Tgrass не подключён.", show_alert=True)
        return
    if not await users.has_sponsor_access(callback.from_user.id):
        await callback.answer("Сначала выполните обязательные подписки.", show_alert=True)
        return
    try:
        response = await tgrass.get_offers(_tgrass_user(callback.from_user), tasks=True)
    except TgrassError:
        await callback.answer("Tgrass временно недоступен.", show_alert=True)
        return
    offers = [
        {"button_url": safe_url, "completed": bool(offer.get("subscribed"))}
        for offer in response.get("offers", [])
        if (safe_url := _safe_offer_url(offer.get("link")))
    ]
    if response.get("status") in {"ok", "no_offers"} or not offers:
        await callback.message.edit_text("🌿 В Tgrass сейчас нет доступных заданий.", reply_markup=back())
    else:
        await callback.message.edit_text("🌿 Задания Tgrass\n\nВыполните все действия и нажмите проверку.", reply_markup=sponsors(offers, "tasks:tgrass:check"))
    await callback.answer()


@router.callback_query(F.data == "tasks:tgrass:check")
async def check_tgrass_tasks(callback: CallbackQuery, users, tgrass) -> None:
    if not tgrass:
        await callback.answer("Tgrass не подключён.", show_alert=True)
        return
    try:
        response = await tgrass.get_offers(_tgrass_user(callback.from_user), tasks=True)
    except TgrassError:
        await callback.answer("Tgrass временно недоступен.", show_alert=True)
        return
    if response.get("status") == "ok":
        await callback.message.edit_text("✅ Задания Tgrass выполнены.", reply_markup=back())
        await callback.answer("Проверка пройдена.")
        return
    offers = [
        {"button_url": safe_url, "completed": bool(offer.get("subscribed"))}
        for offer in response.get("offers", [])
        if (safe_url := _safe_offer_url(offer.get("link")))
    ]
    if offers:
        await callback.message.edit_text("🌿 Задания Tgrass\n\nНе все задания выполнены. Выполните оставшиеся и проверьте снова.", reply_markup=sponsors(offers, "tasks:tgrass:check"))
    await callback.answer("Не все задания выполнены.", show_alert=True)


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
