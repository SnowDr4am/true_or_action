from aiogram.fsm.state import StatesGroup, State

class TurnState(StatesGroup):
    waiting_number = State()