"""Localization package with get_text function."""

from stray_id.models.user import Language
from stray_id.locales import ru, kg

_LOCALES = {
    Language.RU: ru.TEXTS,
    Language.KG: kg.TEXTS,
}


def get_text(key: str, lang: Language = Language.RU) -> str:
    """Get localized text by key.

    Args:
        key: Text key (e.g., "btn_identify")
        lang: Target language

    Returns:
        Localized string, or key itself if not found
    """
    texts = _LOCALES.get(lang, ru.TEXTS)
    return texts.get(key, key)
