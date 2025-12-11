"""Dog model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class DogStatus(Enum):
    """Dog sterilization and safety status."""

    STERILIZED = "sterilized"  # 🟢 Has ear tag
    STRAY = "stray"  # 🟡 Not sterilized
    LOST = "lost"  # 🔴 Owner searching


class DogFeature(Enum):
    """Dog notable features (multiple can be selected)."""

    EAR_TAG = "ear_tag"  # 🦻 Бирка в ухе
    INJURY = "injury"  # 🤕 Травма
    COLLAR = "collar"  # 🐕 Ошейник
    THIN = "thin"  # 🦴 Худая
    AGGRESSIVE = "aggressive"  # 😡 Агрессивная


@dataclass
class Location:
    """Geographical location."""

    latitude: float
    longitude: float
    address: Optional[str] = None


@dataclass
class Dog:
    """Dog entity."""

    id: int
    photo_file_id: str
    location: Location
    status: DogStatus = DogStatus.STRAY
    features: list[DogFeature] = field(default_factory=list)
    name: Optional[str] = None
    owner_contact: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_seen_at: datetime = field(default_factory=datetime.now)

    @property
    def status_emoji(self) -> str:
        """Get status indicator emoji."""
        match self.status:
            case DogStatus.STERILIZED:
                return "🟢"
            case DogStatus.STRAY:
                return "🟡"
            case DogStatus.LOST:
                return "🔴"

    @property
    def has_ear_tag(self) -> bool:
        return DogFeature.EAR_TAG in self.features
