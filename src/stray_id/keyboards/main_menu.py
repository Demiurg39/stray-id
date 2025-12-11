"""Main menu Reply Keyboard."""

from telegram import ReplyKeyboardMarkup, KeyboardButton

from stray_id.locales import get_text
from stray_id.models.user import Language


def get_main_menu(lang: Language = Language.RU) -> ReplyKeyboardMarkup:
    """Get main menu Reply Keyboard.

    Layout:
    ┌─────────────────┬─────────────────┐
    │  📸 Кто это?    │  ➕ Добавить    │
    ├─────────────────┼─────────────────┤
    │  🆘 Потеряшка   │  👤 Профиль     │
    └─────────────────┴─────────────────┘
    """
    keyboard = [
        [
            KeyboardButton(get_text("btn_identify", lang)),
            KeyboardButton(get_text("btn_add", lang)),
        ],
        [
            KeyboardButton(get_text("btn_lost", lang)),
            KeyboardButton(get_text("btn_profile", lang)),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_location_keyboard(lang: Language = Language.RU) -> ReplyKeyboardMarkup:
    """Keyboard with location request button."""
    keyboard = [
        [
            KeyboardButton(
                get_text("btn_send_location", lang),
                request_location=True,
            )
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_language_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard for language selection."""
    keyboard = [
        [
            KeyboardButton("🇷🇺 Русский"),
            KeyboardButton("🇰🇬 Кыргызча"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
    )
