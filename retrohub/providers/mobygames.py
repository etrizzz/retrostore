from __future__ import annotations

import logging

import requests

from retrohub.config import AppConfig
from retrohub.models import GameRecord, SearchResult
from retrohub.providers.base import SearchProvider

logger = logging.getLogger(__name__)


class MobyGamesProvider(SearchProvider):
    name = "MobyGames"
    API_URL = "https://api.mobygames.com/v1/games"

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "RetroHubCinema/1.0 (+desktop research client)"})

    def search(self, query: str, limit: int = 5) -> SearchResult:
        if not self.config.mobygames_api_key:
            return SearchResult(query=query, results=[], warnings=["MOBYGAMES_API_KEY absent : source désactivée."])
        response = self.session.get(
            self.API_URL,
            params={"api_key": self.config.mobygames_api_key, "title": query, "limit": limit},
            timeout=self.config.network.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        records = [
            GameRecord(
                title=item.get("title", "Untitled"),
                provider=self.name,
                summary=(item.get("description") or "Métadonnées MobyGames.")[:500],
                source_url=f"https://www.mobygames.com/game/{item.get('game_id')}",
                year=str(item.get("first_release_date", ""))[:4] or None,
                raw=item,
            )
            for item in data.get("games", [])
        ]
        return SearchResult(query=query, results=records)
