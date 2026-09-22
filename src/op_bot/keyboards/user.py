from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
 rows = [[InlineKeyboardButton(text='👤 Профиль', callback_data='profile')], [InlineKeyboardButton(text='👥 Рефералы', callback_data='referrals'), InlineKeyboardButton(text='🎯 Задания', callback_data='tasks')], [InlineKeyboardButton(text='⭐ Получить Stars', callback_data='stars'), InlineKeyboardButton(text='ℹ️ Помощь', callback_data='help')]]
 if is_admin:
  rows.append([InlineKeyboardButton(text='⚙️ Админ-панель', callback_data='admin:home')])
 return InlineKeyboardMarkup(inline_keyboard=rows)
def sponsors(tasks: list[dict], check_callback: str = 'sponsors:check') -> InlineKeyboardMarkup:
 rows=[[InlineKeyboardButton(text=f'📢 Подписаться №{i}', url=t.get('button_url') or t['resolved_link'].url)] for i,t in enumerate(tasks,1)]
 return InlineKeyboardMarkup(inline_keyboard=[*rows,[InlineKeyboardButton(text='🔄 Проверить подписки', callback_data=check_callback)]])
def task(url: str) -> InlineKeyboardMarkup:
 return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='📢 Выполнить задание',url=url)],[InlineKeyboardButton(text='✅ Проверить',callback_data='task:check')],[InlineKeyboardButton(text='⏭ Пропустить',callback_data='task:skip')],[InlineKeyboardButton(text='⬅️ Назад',callback_data='home')]])
def back() -> InlineKeyboardMarkup:
 return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='⬅️ Назад', callback_data='home')]])
def referrals(share_text: str) -> InlineKeyboardMarkup:
 return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='📤 Пригласить друга',switch_inline_query=share_text)],[InlineKeyboardButton(text='⬅️ Назад',callback_data='home')]])
def task_providers(tgrass_enabled: bool) -> InlineKeyboardMarkup:
 rows=[[InlineKeyboardButton(text='🎯 Задания BotoHub',callback_data='tasks:botohub')]]
 if tgrass_enabled: rows.append([InlineKeyboardButton(text='🌿 Задания Tgrass',callback_data='tasks:tgrass')])
 rows.append([InlineKeyboardButton(text='⬅️ Назад',callback_data='home')])
 return InlineKeyboardMarkup(inline_keyboard=rows)
