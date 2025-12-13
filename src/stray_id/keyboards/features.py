"""Inline keyboards for dog features selection."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from stray_id.locales import get_text
from stray_id.models.dog import DogFeature
from stray_id.models.user import Language

# Callback data prefixes
FEATURE_PREFIX = "feature:"
FEATURES_DONE = "features_done"


def get_features_keyboard(
    selected: set[DogFeature],
    lang: Language = Language.RU,
) -> InlineKeyboardMarkup:
    """Get features selection keyboard.

    Shows checkmarks for selected features.

    Layout:
    [🦻 Бирка в ухе ✓] [🤕 Травма] [🐕 Ошейник]
    [🦴 Худая] [😡 Агрессивная]
    [✅ Готово]
    """

    def feature_btn(feature: DogFeature, text_key: str) -> InlineKeyboardButton:
        text = get_text(text_key, lang)
        if feature in selected:
            text += " ✓"
        return InlineKeyboardButton(
            text=text,
            callback_data=f"{FEATURE_PREFIX}{feature.value}",
        )

    keyboard = [
        [
            feature_btn(DogFeature.EAR_TAG, "feature_ear_tag"),
            feature_btn(DogFeature.INJURY, "feature_injury"),
            feature_btn(DogFeature.COLLAR, "feature_collar"),
        ],
        [
            feature_btn(DogFeature.THIN, "feature_thin"),
            feature_btn(DogFeature.AGGRESSIVE, "feature_aggressive"),
        ],
        [
            InlineKeyboardButton(
                text=get_text("btn_done", lang),
                callback_data=FEATURES_DONE,
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
