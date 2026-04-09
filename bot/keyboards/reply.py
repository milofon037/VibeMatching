from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def no_profile_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Создать анкету")]],
        resize_keyboard=True,
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Смотреть анкеты")],
            [KeyboardButton(text="Моя анкета"), KeyboardButton(text="Рейтинг")],
            [KeyboardButton(text="Изменить режим поиска")],
            [KeyboardButton(text="Кто меня лайкал"), KeyboardButton(text="Кого я лайкал")],
            [KeyboardButton(text="Метчи"), KeyboardButton(text="Реферальная ссылка")],
        ],
        resize_keyboard=True,
    )


def next_or_exit_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Следующая"), KeyboardButton(text="Выйти")]],
        resize_keyboard=True,
    )
