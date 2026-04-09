from aiogram.fsm.state import State, StatesGroup


class CreateProfileState(StatesGroup):
    name = State()
    age = State()
    city = State()
    bio = State()
    interests = State()
    photo = State()


class UpdateProfileState(StatesGroup):
    value = State()
