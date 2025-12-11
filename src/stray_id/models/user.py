"""User model."""

from dataclasses import dataclass
from enum import Enum


class Language(Enum):
    """Supported languages."""

    RU = "ru"  # 🇷🇺 Русский
    KG = "kg"  # 🇰🇬 Кыргызча


@dataclass
class User:
    """Telegram user entity."""

    telegram_id: int
    language: Language = Language.RU
