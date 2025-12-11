"""Search service interface for ML pipeline."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Dog search result with similarity score."""

    dog_id: int
    similarity: float  # 0.0-1.0


class SearchService(ABC):
    """Abstract interface for dog image search.

    Future implementation will use:
    - Preprocessing (resize, normalize)
    - Feature extraction (embedding model)
    - Similarity search (ChromaDB)
    """

    @abstractmethod
    async def search_by_photo(self, photo_bytes: bytes) -> list[SearchResult]:
        """Search for similar dogs in database.

        Args:
            photo_bytes: Raw image bytes

        Returns:
            List of matches sorted by similarity (highest first)
        """
        pass

    @abstractmethod
    async def index_dog(self, dog_id: int, photo_bytes: bytes) -> None:
        """Add dog embedding to vector database.

        Args:
            dog_id: Dog ID in main storage
            photo_bytes: Raw image bytes
        """
        pass
