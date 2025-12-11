"""Mock search service for UI testing."""

from stray_id.search.service import SearchService, SearchResult


class MockSearchService(SearchService):
    """Mock implementation that always returns no matches.

    Used for testing the bot UI without ML backend.
    """

    async def search_by_photo(self, photo_bytes: bytes) -> list[SearchResult]:
        """Always returns empty list (no matches)."""
        return []

    async def index_dog(self, dog_id: int, photo_bytes: bytes) -> None:
        """No-op: doesn't actually index anything."""
        pass


# Global mock instance
search_service = MockSearchService()
