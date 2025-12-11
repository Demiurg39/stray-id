"""Inline keyboard for dog card actions."""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from stray_id.locales import get_text
from stray_id.models.user import Language


# Callback data prefixes
MARK_SIGHTING = "sighting:"
SUBSCRIBE = "subscribe:"
REPORT = "report:"
SHARE = "share:"


def get_dog_card_keyboard(
    dog_id: int,
    lang: Language = Language.RU,
) -> InlineKeyboardMarkup:
    """Get dog card action buttons.

    Layout:
    [📍 Отметить встречу]
    [📍 На карте] [🔔 Подписаться]
    [⚠️ Сообщить о проблеме]
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("btn_mark_sighting", lang),
                callback_data=f"{MARK_SIGHTING}{dog_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=get_text("btn_show_on_map", lang),
                callback_data=f"map:{dog_id}",
            ),
            InlineKeyboardButton(
                text=get_text("btn_subscribe", lang),
                callback_data=f"{SUBSCRIBE}{dog_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=get_text("btn_report_problem", lang),
                callback_data=f"{REPORT}{dog_id}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_not_found_keyboard(lang: Language = Language.RU) -> InlineKeyboardMarkup:
    """Keyboard for 'dog not found' result."""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("btn_yes_register", lang),
                callback_data="register_from_search",
            ),
            InlineKeyboardButton(
                text=get_text("btn_no_cancel", lang),
                callback_data="cancel",
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
