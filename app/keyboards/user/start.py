from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.database.models import User
from ..general import delete_message_keyboard, generate_simple_keyboard


def generate_start_menu(user: User) -> InlineKeyboardMarkup:
    buttons = []

    if user.room:
        room = user.room

        is_owner = room.owner_id == user.telegram_id

        if is_owner:
            buttons.append([InlineKeyboardButton(text="▶️ Начать игру", callback_data=f"room:start_game:{room.id}")])
            buttons.append([InlineKeyboardButton(text="🔒 Удалить комнату", callback_data=f"room:close:{room.id}")])
        else:
            buttons.append([InlineKeyboardButton(text="🚪 Покинуть комнату", callback_data="room:leave")])

        buttons.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="room:refresh")])
    else:
        buttons.append([InlineKeyboardButton(text="➕ Создать комнату", callback_data="room:create")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)