from abc import ABC, abstractmethod
from typing import Any


class BaseDiscoveryProvider(ABC):

    @abstractmethod
    def search(
        self,
        query: str,
        location: str,
        limit: int
    ) -> list[dict[str, Any]]:
        """
        Search for businesses using a discovery provider.

        Args:
            query: Business category or niche.
            location: Geographic search location.
            limit: Maximum raw candidates to retrieve.

        Returns:
            A list of raw business records.
        """
        pass