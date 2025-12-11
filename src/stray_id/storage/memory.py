"""In-memory storage (placeholder for PostgreSQL)."""

from typing import Optional

from stray_id.models.dog import Dog
from stray_id.models.user import User, Language


class MemoryStorage:
    """Simple in-memory storage for development."""

    def __init__(self):
        self._dogs: dict[int, Dog] = {}
        self._users: dict[int, User] = {}
        self._next_dog_id = 1

    # Dog operations
    def add_dog(self, dog: Dog) -> Dog:
        """Add dog and assign ID."""
        dog.id = self._next_dog_id
        self._next_dog_id += 1
        self._dogs[dog.id] = dog
        return dog

    def get_dog(self, dog_id: int) -> Optional[Dog]:
        return self._dogs.get(dog_id)

    def get_all_dogs(self) -> list[Dog]:
        return list(self._dogs.values())

    def update_dog(self, dog: Dog) -> None:
        if dog.id in self._dogs:
            self._dogs[dog.id] = dog

    # User operations
    def get_or_create_user(self, telegram_id: int) -> User:
        if telegram_id not in self._users:
            self._users[telegram_id] = User(telegram_id=telegram_id)
        return self._users[telegram_id]

    def set_user_language(self, telegram_id: int, language: Language) -> None:
        user = self.get_or_create_user(telegram_id)
        user.language = language


# Global storage instance
storage = MemoryStorage()
