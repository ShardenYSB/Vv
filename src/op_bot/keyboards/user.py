from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu() -> InlineKeyboardMarkup:
 return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='👤 Профиль', callback_data='profile')],[InlineKeyboardButton(text='👥 Рефералы', callback_data='referrals'),InlineKeyboardButton(text='🎯 Задания', callback_data='tasks')],[InlineKeyboardButton(text='⭐ Получить Stars', callback_data='stars'),InlineKeyboardButton(text='ℹ️ Помощь', callback_data='help')]])
def sponsors(tasks: list[dict]) -> InlineKeyboardMarkup:
 rows=[[InlineKeyboardButton(text=f'📢 Подписаться №{i}', url=t['resolved_link'].url)] for i,t in enumerate(tasks,1)]
 return InlineKeyboardMarkup(inline_keyboard=[*rows,[InlineKeyboardButton(text='🔄 Проверить подписки', callback_data='sponsors:check')]])
def task(url: str) -> InlineKeyboardMarkup:
 return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='📢 Выполнить задание',url=url)],[InlineKeyboardButton(text='✅ Проверить',callback_data='task:check')],[InlineKeyboardButton(text='⏭ Пропустить',callback_data='task:skip')],[InlineKeyboardButton(text='⬅️ Назад',callback_data='home')]])
def back() -> InlineKeyboardMarkup:
 return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='⬅️ Назад', callback_data='home')]])
def referrals(share_text: str) -> InlineKeyboardMarkup:
 return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='📤 Пригласить друга',switch_inline_query=share_text)],[InlineKeyboardButton(text='⬅️ Назад',callback_data='home')]])
