import asyncio
from aiogram import Bot

from app.database.services import RoomService
import app.keyboards.game.game_service as kb
from app.utils.game_values import TRUTHS, ACTIONS


def pick_truth(room) -> str | None:
    idx = (room.current_truth_number or 1) - 1
    if idx < 0 or idx >= len(TRUTHS):
        return None
    return TRUTHS[idx]

def pick_action(room) -> str | None:
    idx = (room.current_action_number or 1) - 1
    if idx < 0 or idx >= len(ACTIONS):
        return None
    return ACTIONS[idx]

class GameService:
    @staticmethod
    def availability(room) -> tuple[bool, bool]:
        allow_truth = (room.current_truth_number or 1) <= len(TRUTHS)
        allow_action = (room.current_action_number or 1) <= len(ACTIONS)
        return allow_truth, allow_action

    @classmethod
    async def end_game(cls, bot: Bot, room_id: int):
        await cls.broadcast(
            bot,
            room_id,
            "🏁 <b>Игра завершена!</b>\n\n"
            
            "Все вопросы и действия закончились. Спасибо за игру 🙌"
        )

        room = await RoomService.get_room(room_id=room_id, with_players=False)
        if room:
            await RoomService.finish_game(room_id=room_id, by_user_id=room.owner_id)

    @classmethod
    async def send_turn_prompt(cls, bot: Bot, room_id: int):
        room = await RoomService.get_room(room_id=room_id, with_players=True)
        if not room:
            return

        allow_truth, allow_action = cls.availability(room)

        if not allow_truth and not allow_action:
            await cls.end_game(bot, room_id)
            return

        players = getattr(room, "players", []) or []
        if not players:
            return

        turn = room.current_turn_number or 1
        idx = (turn - 1) % len(players)
        current_player = players[idx]

        text = (
            "🎲 <b>Твой ход!</b>\n\n"
            
            "Выбирай: <b>Правда</b> или <b>Действие</b>?"
        )

        await bot.send_message(
            chat_id=current_player.telegram_id,
            text=text,
            parse_mode="HTML",
            reply_markup=kb.choice_keyboard(
                room.id,
                current_player.telegram_id,
                turn,
                allow_truth=allow_truth,
                allow_action=allow_action
            )
        )

    @classmethod
    async def broadcast(cls, bot: Bot, room_id: int, text: str, *, exclude_ids: set[int] | None = None):
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