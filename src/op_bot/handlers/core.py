"""Aiogram routes. Only /start is a command; navigation is callback-only."""
from __future__ import annotations
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from op_bot.botohub import BotoHubService, BotoHubTemporaryError
from op_bot.keyboards.user import main_menu, sponsors, task

router = Router(); log = logging.getLogger(__name__)

def _start_referral(text: str | None, user_id: int) -> int | None:
 if not text: return None
 parts=text.split(maxsplit=1)
 if len(parts) != 2 or not parts[1].startswith('ref_'): return None
 try: referrer=int(parts[1][4:])
 except ValueError: return None
 return None if referrer == user_id else referrer

async def _sponsor_screen(target: Message | CallbackQuery, service: BotoHubService, user_id: int):
 try: result=await service.get_sponsors(user_id)
 except BotoHubTemporaryError: return await target.answer('⚠️ Сервис временно недоступен.\n\nПопробуйте ещё раз через несколько секунд.')
 tasks=result.get('tasks', [])
 if result.get('completed') or not tasks: return await target.answer('👋 Добро пожаловать!\n\n⭐ Баланс: 0 Stars\n👥 Рефералов: 0\n🎯 Выполнено заданий: 0', reply_markup=main_menu())
 status='\n'.join('🟢 Выполнено' if item.get('completed') else '🔴 Не выполнено' for item in tasks)
 return await target.answer(f'🔐 Для доступа к боту необходимо выполнить обязательные подписки.\n\n{status}\n\nПосле подписки нажмите кнопку проверки.',reply_markup=sponsors(tasks))

@router.message(CommandStart())
async def start(message: Message, botohub: BotoHubService, users):
 referrer = _start_referral(message.text, message.from_user.id)
 await users.register(message.from_user.id, message.from_user.username, message.from_user.first_name, referrer)
 log.info('USER_REGISTERED user_id=%s referrer=%s', message.from_user.id, referrer)
 await _sponsor_screen(message, botohub, message.from_user.id)
@router.callback_query(F.data == 'sponsors:check')
async def check_sponsors(callback: CallbackQuery, botohub: BotoHubService):
 await callback.answer(); await _sponsor_screen(callback.message,botohub,callback.from_user.id)
@router.callback_query(F.data == 'home')
async def home(callback: CallbackQuery):
 await callback.message.edit_text('👋 Добро пожаловать!',reply_markup=main_menu()); await callback.answer()
@router.callback_query(F.data == 'tasks')
async def get_task(callback: CallbackQuery, botohub: BotoHubService):
 try: result=await botohub.get_task(callback.from_user.id)
 except BotoHubTemporaryError: await callback.answer('Сервис временно недоступен',show_alert=True); return
 if result.get('fake'): await callback.message.edit_text('⚠️ Получение новых заданий временно недоступно.'); return
 url=result.get('url')
 if not url: await callback.message.edit_text('🎯 Все задания выполнены.',reply_markup=main_menu()); return
 await callback.message.edit_text(f"🎯 Задание\n\n⭐ Награда: {result.get('reward', 0)} ⭐\n\nПосле выполнения нажмите «Проверить».",reply_markup=task(url)); await callback.answer()

@router.callback_query(F.data == 'profile')
async def profile(callback: CallbackQuery, users):
 try:
  user, referrals_count, tasks_count, referral_earned = await users.profile(callback.from_user.id)
 except LookupError:
  await callback.answer('Нажмите /start', show_alert=True); return
 await callback.message.edit_text(f'👤 Ваш профиль\n\n🆔 ID: {user.telegram_id}\n\n⭐ Stars: {user.stars_balance}\n👥 Рефералов: {referrals_count}\n\n🎯 Выполнено заданий: {tasks_count}\n\n🏆 Получено за рефералов: {referral_earned} ⭐', reply_markup=main_menu())
 await callback.answer()

@router.callback_query(F.data == 'referrals')
async def referrals_screen(callback: CallbackQuery, users):
 from op_bot.keyboards.user import referrals
 try: user, count, _, earned = await users.profile(callback.from_user.id)
 except LookupError: await callback.answer('Нажмите /start', show_alert=True); return
 me=await callback.bot.get_me(); link=f'https://t.me/{me.username}?start=ref_{user.telegram_id}'
 await callback.message.edit_text(f'👥 Реферальная система\n\nПриглашай друзей и получай Stars.\n\n🔗 Твоя ссылка:\n{link}\n\n👤 Приглашено: {count}\n⭐ Заработано: {earned}',reply_markup=referrals(f'Присоединяйся: {link}'))
 await callback.answer()
