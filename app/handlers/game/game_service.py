import random
import asyncio
from aiogram import Bot

from app.database.services import RoomService
import app.keyboards.game.game_service as kb
from app.utils.game_values import TRUTHS, ACTIONS


def pick_truth_by_number(number: int) -> str | None:
    idx = number - 1
    if 0 <= idx < len(TRUTHS):
        return TRUTHS[idx]
    return None

def pick_action_by_number(number: int) -> str | None:
    idx = number - 1
    if 0 <= idx < len(ACTIONS):
        return ACTIONS[idx]
    return None


class GameService:
    @classmethod
    async def send_turn_prompt(cls, bot: Bot, room_id: int):
        room = await RoomService.get_room(room_id=room_id, with_players=True)
        if not room:
            return

        players = getattr(room, "players", []) or []
        if not players:
            return

        turn = room.current_turn_number or 1
        idx = (turn - 1) % len(players)
        current_player = players[idx]

        await bot.send_message(
            chat_id=current_player.telegram_id,
            text=(
            "🎲 <b>Твой ход!</b>\n\n"
            
            "Выбирай: <b>Правда</b> или <b>Действие</b>?"
            ),
            parse_mode="HTML",
            reply_markup=kb.choice_keyboard(room.id, current_player.telegram_id, turn),
        )

    @classmethod
    async def broadcast(
            cls,
            bot: Bot,
            room_id: int,
            text: str,
            *,
            exclude_ids: set[int] | None = None
    ):
        exclude_ids = exclude_ids or set()

        room = await RoomService.get_room(room_id=room_id, with_players=True)
        if not room:
            return

        players = getattr(room, "players", []) or []
        if not players:
            return

        await asyncio.gather(
            *[
                bot.send_message(
                    chat_id=p.telegram_id,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=kb.delete_message_keyboard,
                )
                for p in players
                if p.telegram_id not in exclude_ids
            ],
            return_exceptions=True
        )

    @staticmethod
    def roll_in_range(a: int, b: int) -> int:
        return random.randint(a, b)