from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..general import delete_message_keyboard


def confirm_rules(room_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Запустить игру", callback_data=f"room:confirm_start:{room_id}")]
    ])


def choice_keyboard(room_id: int, player_id: int, turn: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🟩 Правда", callback_data=f"room:choice:{room_id}:{player_id}:{turn}:truth"),
        InlineKeyboardButton(text="🟥 Действие", callback_data=f"room:choice:{room_id}:{player_id}:{turn}:action"),
    ]])


def range_keyboard(room_id: int, player_id: int, turn: int, kind: str) -> InlineKeyboardMarkup:
    ranges = [(1,10),(11,20),(21,30),(31,40),(41,50),(51,60),(61,70),(71,80),(81,90),(91,100)]
    rows = []
    row = []
    for a, b in ranges:
        row.append(InlineKeyboardButton(
            text=f"{a}-{b}",
            callback_data=f"room:range:{room_id}:{player_id}:{turn}:{kind}:{a}:{b}"
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    rows.append([InlineKeyboardButton(
        text="✍️ Ввести номер вручную",
        callback_data=f"room:manual:{room_id}:{player_id}:{turn}:{kind}"
    )])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def done_keyboard(room_id: int, player_id: int, turn: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Готово", callback_data=f"room:done:{room_id}:{player_id}:{turn}")]
    ])
