from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..general import delete_message_keyboard


def choice_keyboard(room_id: int, player_id: int, turn: int, *, allow_truth: bool, allow_action: bool) -> InlineKeyboardMarkup:
    row = []
    if allow_truth:
        row.append(InlineKeyboardButton(
            text="🟩 Правда",
            callback_data=f"room:choice:{room_id}:{player_id}:{turn}:truth"
        ))
    if allow_action:
        row.append(InlineKeyboardButton(
            text="🟥 Действие",
            callback_data=f"room:choice:{room_id}:{player_id}:{turn}:action"
        ))

    return InlineKeyboardMarkup(inline_keyboard=[row])

def done_keyboard(room_id: int, player_id: int, turn: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Готово", callback_data=f"room:done:{room_id}:{player_id}:{turn}")]
    ])
