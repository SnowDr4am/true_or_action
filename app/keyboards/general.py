from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


delete_message_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🗑️ Удалить сообщение", callback_data="delete-message")]
])

def generate_simple_keyboard(button_text: str, callback_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=button_text, callback_data=callback_data)]
    ])

def generate_url_keyboard(button_text: str, url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=button_text, url=url)]
    ])