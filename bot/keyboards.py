from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def profile_actions_keyboard(profile_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Like", callback_data=f"like:{profile_id}"),
                InlineKeyboardButton(text="Skip", callback_data=f"skip:{profile_id}"),
            ]
        ]
    )
