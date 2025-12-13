"""Inline keyboard for dog card actions."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from stray_id.locales import get_text
from stray_id.models.dog import Dog, DogStatus
from stray_id.models.user import Language
from stray_id.utils.geo import get_2gis_link

# Callback data prefixes
SEEN_HERE = "seen:"
ADD_PHOTO = "addphoto:"
UPDATE_INFO = "update:"
NEXT_DOG = "next:"
SUBSCRIBE = "subscribe:"
REPORT = "report:"


def get_dog_card_keyboard(
    dog: Dog,
    lang: Language = Language.RU,
    show_next: bool = False,
) -> InlineKeyboardMarkup:
    """Get dog card action buttons.

    Layout for identify result:
    [📍 Видел здесь] [📷 Добавить фото]
    [🌍 2GIS]

    Layout for feed:
    [🌍 2GIS] [✏️ Обновить]
    [➡️ Дальше]
    """
    keyboard = []

    if not show_next:
        # Identify result - allow updating location and photo
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=get_text("btn_seen_here", lang),
                    callback_data=f"{SEEN_HERE}{dog.id}",
                ),
                InlineKeyboardButton(
                    text=get_text("btn_add_photo", lang),
                    callback_data=f"{ADD_PHOTO}{dog.id}",
                ),
            ]
        )

    # 2GIS link (URL button - opens directly)
    gis_url = get_2gis_link(dog.location.latitude, dog.location.longitude)
    row = [
        InlineKeyboardButton(
            text=get_text("btn_2gis", lang),
            url=gis_url,
        ),
    ]

    if show_next:
        row.append(
            InlineKeyboardButton(
                text=get_text("btn_update_info", lang),
                callback_data=f"{UPDATE_INFO}{dog.id}",
            )
        )

    keyboard.append(row)

    if show_next:
        # Feed mode - add Next button
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=get_text("btn_next", lang),
                    callback_data=f"{NEXT_DOG}{dog.id}",
                ),
            ]
        )

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


def get_lost_alert_keyboard(
    dog: Dog,
    lang: Language = Language.RU,
) -> InlineKeyboardMarkup:
    """Keyboard for lost dog alert."""
    gis_url = get_2gis_link(dog.location.latitude, dog.location.longitude)
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("btn_2gis", lang),
                url=gis_url,
            ),
        ],
        [
            InlineKeyboardButton(
                text=get_text("btn_seen_here", lang),
                callback_data=f"{SEEN_HERE}{dog.id}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
