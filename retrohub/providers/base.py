from __future__ import annotations

from abc import ABC, abstractmethod

from retrohub.models import SearchResult


class SearchProvider(ABC):
    name: str

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> SearchResult:
        raise NotImplementedError
