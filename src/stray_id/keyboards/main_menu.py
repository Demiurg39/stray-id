"""Main menu Reply Keyboard."""

from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from stray_id.locales import get_text
from stray_id.models.user import Language


def get_main_menu(lang: Language = Language.RU) -> ReplyKeyboardMarkup:
    """Get main menu Reply Keyboard (3 buttons).

    Layout:
    ┌──────────┬──────────┬──────────┐
    │ 📸 Кто   │ 🐶 Лента │ 󰍜  Меню  │
    │  это?    │          │          │
    └──────────┴──────────┴──────────┘
    """
    keyboard = [
        [
            KeyboardButton(get_text("btn_identify", lang)),
            KeyboardButton(get_text("btn_feed", lang)),
            KeyboardButton(get_text("btn_menu", lang)),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_hamburger_menu(lang: Language = Language.RU) -> InlineKeyboardMarkup:
    """Get hamburger menu (☰) inline keyboard.

    Options:
    - 🆘 Я потерял собаку
    - 👤 Профиль
    - ℹ️ О проекте
    - 💝 Донаты
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("menu_lost", lang),
                callback_data="menu:lost",
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("menu_profile", lang),
                callback_data="menu:profile",
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("menu_about", lang),
                callback_data="menu:about",
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("menu_donate", lang),
                callback_data="menu:donate",
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


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


def get_contact_keyboard(lang: Language = Language.RU) -> ReplyKeyboardMarkup:
    """Keyboard with contact sharing button."""
    keyboard = [
        [
            KeyboardButton(
                get_text("btn_send_contact", lang),
                request_contact=True,
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
