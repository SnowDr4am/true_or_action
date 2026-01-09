from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from ..main import user_router
from app.database.services import RoomService
import app.keyboards.game.game_service as kb
from .game_service import GameService, pick_truth_by_number, pick_action_by_number
from app.utils.states import TurnState


@user_router.callback_query(F.data.startswith("room:start_game:"))
async def handle_create_room(callback: CallbackQuery):
    await callback.answer()

    room_id = int(callback.data.split(":")[-1])

    await callback.message.edit_text(
        "🎮 <b>Правда или действие — правила игры</b>\n\n"

        "🔥 <b>Внимание и фокус</b>\n"
        "1. Во время игры следи, чтобы все внимание было направлено на человека, который задает вопрос и на человека, "
        "который исполняет действие или отвечает на этот вопрос\n\n"
        
        "2. Поправляй людей, которые ведут себя не так\n\n"
        
        "3. Следи за тем, чтобы люди не смеялись, а создавали сексуальный вайб\n\n"
    
        "4. Каждый 10-й вопрос раскрывает какую-то сексуальную тему\n\n"

        "🔥 <b>Памятка по действиям</b>\n"
        "10 / 20 / 30 / 40 / 50 — <b>Жизнь за 5 минут</b>\n"
        "60 — уединение в отдельную комнату\n"
        "70 — свет в комнате\n"
        "80 — поцелуй в губы\n"
        "90 — поцелуй в живот\n"
        "95 — БДСМ-сессия\n"
        "100 — снятие трусов зубами",
        parse_mode="HTML",
        reply_markup = kb.confirm_rules(room_id)
    )

@user_router.callback_query(F.data.startswith("room:confirm_start:"))
async def handle_confirm_start(callback: CallbackQuery):
    await callback.answer()

    try:
        await callback.message.delete()
    except Exception:
        pass

    room_id = int(callback.data.split(":")[-1])

    await RoomService.start_game(room_id=room_id, by_user_id=callback.from_user.id)

    await GameService.broadcast(
        callback.bot,
        room_id,
        "🚀 <b>Игра стартовала</b>\n\n"
        
        "Первый игрок уже выбирает: правда или действие"
    )

    await GameService.send_turn_prompt(callback.bot, room_id)

@user_router.callback_query(F.data.startswith("room:choice:"))
async def handle_choice(callback: CallbackQuery):
    await callback.answer()

    _, _, room_id, player_id, turn, kind = callback.data.split(":")
    room_id = int(room_id)
    player_id = int(player_id)
    turn = int(turn)

    if callback.from_user.id != player_id:
        return

    room = await RoomService.get_room(room_id=room_id, with_players=False)
    if not room or (room.current_turn_number or 1) != turn:
        return

    kind_ru = "Правда" if kind == "truth" else "Действие"

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        f"🎯 Ты выбрал <b>{kind_ru}</b>\n\n"
        f"Выбери диапазон (тогда я рандомно выберу номер) или введи номер вручную.",
        parse_mode="HTML",
        reply_markup=kb.range_keyboard(room_id, player_id, turn, kind),
    )

@user_router.callback_query(F.data.startswith("room:manual:"))
async def handle_manual(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    _, _, room_id, player_id, turn, kind = callback.data.split(":")
    room_id = int(room_id)
    player_id = int(player_id)
    turn = int(turn)

    if callback.from_user.id != player_id:
        return

    room = await RoomService.get_room(room_id=room_id, with_players=False)
    if not room or (room.current_turn_number or 1) != turn:
        return

    await state.set_state(TurnState.waiting_number)
    await state.update_data(room_id=room_id, player_id=player_id, turn=turn, kind=kind)

    await callback.message.answer(
        "✍️ Введи номер цифрой (например: <b>17</b>)",
        parse_mode="HTML",
        reply_markup=kb.delete_message_keyboard
    )

@user_router.callback_query(F.data.startswith("room:range:"))
async def handle_range(callback: CallbackQuery):
    await callback.answer()

    try:
        await callback.message.delete()
    except Exception:
        pass

    _, _, room_id, player_id, turn, kind, a, b = callback.data.split(":")
    room_id = int(room_id)
    player_id = int(player_id)
    turn = int(turn)
    a = int(a)
    b = int(b)

    if callback.from_user.id != player_id:
        return

    room = await RoomService.get_room(room_id=room_id, with_players=False)
    if not room or (room.current_turn_number or 1) != turn:
        return

    number = GameService.roll_in_range(a, b)
    await finalize_turn(callback, room_id, player_id, turn, kind, number)

@user_router.message(TurnState.waiting_number)
async def handle_number_message(message: Message, state: FSMContext):
    data = await state.get_data()
    room_id = int(data["room_id"])
    player_id = int(data["player_id"])
    turn = int(data["turn"])
    kind = data["kind"]

    if message.from_user.id != player_id:
        return

    text = (message.text or "").strip()
    if not text.isdigit():
        return await message.answer("Нужна цифра 🙂 Например: <b>17</b>", parse_mode="HTML")

    number = int(text)
    await state.clear()

    await finalize_turn(message, room_id, player_id, turn, kind, number)

async def finalize_turn(event, room_id: int, player_id: int, turn: int, kind: str, number: int):
    bot = event.bot

    kind_ru = "Правда" if kind == "truth" else "Действие"
    task = pick_truth_by_number(number) if kind == "truth" else pick_action_by_number(number)

    if task is None:
        task = "⚠️ Такого номера нет в списке"

    await GameService.broadcast(
        bot,
        room_id,
        (
            f"👤 <b>{event.from_user.full_name}</b> выбрал <b>{kind_ru}</b>\n"
            f"🔢 Номер: <b>{number}</b>\n\n"
            f"🎯 Выпало:\n<b>{task}</b>"
        ),
        exclude_ids={player_id},
    )

    try:
        await bot.send_message(
            chat_id=player_id,
            text=(
                f"✅ Твой выбор — <b>{kind_ru}</b>\n"
                f"🔢 Номер: <b>{number}</b>\n\n"
                f"🎯 Твоё задание:\n<b>{task}</b>\n\n"
                "Как закончишь — жми кнопку ниже"
            ),
            parse_mode="HTML",
            reply_markup=kb.done_keyboard(room_id, player_id, turn),
        )
    except Exception:
        pass

@user_router.callback_query(F.data.startswith("room:done:"))
async def handle_done(callback: CallbackQuery):
    await callback.answer()

    _, _, room_id, player_id, turn = callback.data.split(":")
    room_id = int(room_id)
    player_id = int(player_id)
    turn = int(turn)

    if callback.from_user.id != player_id:
        return

    room = await RoomService.get_room(room_id=room_id, with_players=False)
    if not room or (room.current_turn_number or 1) != turn:
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await GameService.broadcast(
        callback.bot,
        room_id,
        f"✅ <b>{callback.from_user.full_name}</b> закончил свой ход\n\n"
        "Передаём очередь дальше",
        exclude_ids={callback.from_user.id},
    )

    await RoomService.bump_turn(room_id=room_id)
    await GameService.send_turn_prompt(callback.bot, room_id)