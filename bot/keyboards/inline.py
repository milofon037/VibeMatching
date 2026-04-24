from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def edit_gender_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Мужчина", callback_data="answer:gender:male"),
                InlineKeyboardButton(text="Женщина", callback_data="answer:gender:female"),
            ]
        ]
    )


def preferred_gender_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Мужчины", callback_data="answer:preferred_gender:male"),
                InlineKeyboardButton(
                    text="Женщины", callback_data="answer:preferred_gender:female"
                ),
            ],
            [InlineKeyboardButton(text="Все", callback_data="answer:preferred_gender:any")],
        ]
    )


def search_mode_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Только мой город", callback_data="mode:local"),
                InlineKeyboardButton(text="Все анкеты", callback_data="mode:global"),
            ]
        ]
    )


def feed_actions_keyboard(profile_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❤️ Лайк", callback_data=f"feed:like:{profile_id}"),
                InlineKeyboardButton(text="⏭ Скип", callback_data=f"feed:skip:{profile_id}"),
                InlineKeyboardButton(
                    text="🚨 Жалоба", callback_data=f"feed:complaint:{profile_id}"
                ),
            ],
        ]
    )


def cancel_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Отменить", callback_data="edit:cancel")]]
    )


def edit_gender_with_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Мужчина", callback_data="answer:gender:male"),
                InlineKeyboardButton(text="Женщина", callback_data="answer:gender:female"),
            ],
            [InlineKeyboardButton(text="Отменить", callback_data="edit:cancel")],
        ]
    )


def complaint_reason_keyboard(profile_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Спам", callback_data=f"complaint:{profile_id}:spam")],
            [InlineKeyboardButton(text="Фейк", callback_data=f"complaint:{profile_id}:fake")],
            [
                InlineKeyboardButton(
                    text="Неприемлемый контент",
                    callback_data=f"complaint:{profile_id}:inappropriate",
                )
            ],
        ]
    )


def incoming_like_actions_keyboard(profile_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❤️ Ответить лайком", callback_data=f"incoming:like:{profile_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Пропустить", callback_data=f"incoming:skip:{profile_id}"
                ),
            ]
        ]
    )


def my_profile_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Изменить имя", callback_data="edit:name")],
            [InlineKeyboardButton(text="Изменить возраст", callback_data="edit:age")],
            [InlineKeyboardButton(text="Изменить пол", callback_data="edit:gender")],
            [InlineKeyboardButton(text="Изменить интерес", callback_data="edit:interests")],
            [InlineKeyboardButton(text="Изменить город", callback_data="edit:city")],
            [InlineKeyboardButton(text="Изменить описание", callback_data="edit:bio")],
            [InlineKeyboardButton(text="Изменить фото", callback_data="edit:photo")],
        ]
    )


def interests_selection_keyboard(
    interests: list[dict[str, int | str]], selected_ids: set[int]
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for interest in interests:
        interest_id = int(interest["id"])
        name = str(interest["name"])
        marker = "✅ " if interest_id in selected_ids else ""
        row.append(
            InlineKeyboardButton(
                text=f"{marker}{name}",
                callback_data=f"interest:select:{interest_id}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def interests_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить", callback_data="interest:confirm")],
            [InlineKeyboardButton(text="Заполнить еще раз", callback_data="interest:reset")],
        ]
    )
