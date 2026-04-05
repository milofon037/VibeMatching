from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def no_profile_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="0. Создать анкету")]],
        resize_keyboard=True,
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1. Моя анкета")],
            [KeyboardButton(text="2. Мой рейтинг"), KeyboardButton(text="3. Кого я лайкал")],
            [KeyboardButton(text="4. Кто лайкал меня"), KeyboardButton(text="5. Мои мэтчи")],
            [KeyboardButton(text="6. Реферальная ссылка"), KeyboardButton(text="7. Смотреть анкеты")],
        ],
        resize_keyboard=True,
    )


def likes_navigation_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Следующая"), KeyboardButton(text="Выйти")]],
        resize_keyboard=True,
    )


def gender_keyboard(allow_any: bool = False) -> ReplyKeyboardMarkup:
    row = [KeyboardButton(text="male"), KeyboardButton(text="female"), KeyboardButton(text="other")]
    keyboard = [row]
    if allow_any:
        keyboard.append([KeyboardButton(text="any")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def yes_no_skip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="skip")]],
        resize_keyboard=True,
    )


def search_mode_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="local"), KeyboardButton(text="global")]],
        resize_keyboard=True,
    )


def profile_edit_field_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="name"), KeyboardButton(text="age")],
            [KeyboardButton(text="city"), KeyboardButton(text="bio")],
            [KeyboardButton(text="interests"), KeyboardButton(text="gender")],
            [KeyboardButton(text="preferred_gender"), KeyboardButton(text="preferred_age_min")],
            [KeyboardButton(text="preferred_age_max"), KeyboardButton(text="search_city_mode")],
            [KeyboardButton(text="done")],
        ],
        resize_keyboard=True,
    )


def profile_edit_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Имя", callback_data="edit:name"), InlineKeyboardButton(text="Возраст", callback_data="edit:age")],
            [InlineKeyboardButton(text="Город", callback_data="edit:city"), InlineKeyboardButton(text="Описание", callback_data="edit:bio")],
            [InlineKeyboardButton(text="Интересы", callback_data="edit:interests"), InlineKeyboardButton(text="Пол", callback_data="edit:gender")],
            [
                InlineKeyboardButton(text="Предп. пол", callback_data="edit:preferred_gender"),
                InlineKeyboardButton(text="Мин. возраст", callback_data="edit:preferred_age_min"),
            ],
            [
                InlineKeyboardButton(text="Макс. возраст", callback_data="edit:preferred_age_max"),
                InlineKeyboardButton(text="Режим поиска", callback_data="edit:search_city_mode"),
            ],
        ]
    )


def profile_actions_keyboard(profile_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Like", callback_data=f"like:{profile_id}"),
                InlineKeyboardButton(text="Skip", callback_data=f"skip:{profile_id}"),
            ]
        ]
    )
